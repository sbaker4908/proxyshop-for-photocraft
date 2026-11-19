"""Two-face Studio rendering, using Proxyshop's native Transform/MDFC operations.

Isolated from the original toolbar and the existing single-face Studio renderer.
"""
from __future__ import annotations

from asyncio import ensure_future, to_thread
from logging import getLogger
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from PySide6.QtCore import QObject, Property, Signal, Slot

from src._config import AppConfig
from src._loader import PluginLibrary
from src.cards import CardDetails
from src.enums.mtg import LayoutScryfall, LayoutType, Rarity
from src.gui.qml.models.file_dialog_model import FileDialogModel
from src.gui.qml.models.message_dialog_content_model import MessageDialogContentModel
from src.gui.qml.models.studio_card_model import StudioCardModel
from src.gui.qml.models.studio_render_model import StudioRenderModel
from src.gui.qml.models.template_list_model import TemplateListModel
from src.render.render_queue import RenderQueue, RenderResult
from src.render.setup import RenderOperation, prepare_render_operations
from src.utils.scryfall import ScryfallCard

_logger = getLogger(__name__)

_DUAL_LAYOUT_TYPES: dict[str, tuple[LayoutType, LayoutType]] = {
    "transform": (LayoutType.TransformFront, LayoutType.TransformBack),
    "mdfc": (LayoutType.MDFCFront, LayoutType.MDFCBack),
}


class StudioDualRenderModel(QObject):
    """Batch two coordinated face renders and publish both output paths together."""

    changed = Signal()
    _started_on_gui = Signal(int)
    _finished_on_gui = Signal(int, bool, str)

    def __init__(
        self,
        card_model: StudioCardModel,
        template_list_model: TemplateListModel,
        plugin_library: PluginLibrary,
        render_queue: RenderQueue,
        file_dialog_model: FileDialogModel,
        message_dialog_model: MessageDialogContentModel,
    ) -> None:
        super().__init__()
        self._card_model = card_model
        self._template_list_model = template_list_model
        self._plugin_library = plugin_library
        self._render_queue = render_queue
        self._file_dialog_model = file_dialog_model
        self._message_dialog_model = message_dialog_model
        self._busy = False
        self._phase = "idle"
        self._status = ""
        self._error = ""
        self._launch_warning = ""
        self._front_output_url = ""
        self._back_output_url = ""
        self._last_output_url = ""
        self._render_generation = 0
        self._pending: dict[RenderOperation, int] = {}
        self._results: dict[int, str] = {}
        self._failed = False
        self._art_temp_dirs: list[TemporaryDirectory[str]] = []
        self._editable_psd = False

        self._started_on_gui.connect(self._mark_started)
        self._finished_on_gui.connect(self._mark_finished)
        render_queue.started.add_listener(self._on_queue_started)
        render_queue.finished.add_listener(self._on_queue_finished)

    @Property(bool, notify=changed)
    def busy(self) -> bool:
        return self._busy

    @Property(str, notify=changed)
    def phase(self) -> str:
        return self._phase

    @Property(str, notify=changed)
    def status(self) -> str:
        return self._status

    @Property(str, notify=changed)
    def error(self) -> str:
        return self._error

    @Property(str, notify=changed)
    def launch_warning(self) -> str:
        return self._launch_warning

    @Property(str, notify=changed)
    def front_output_url(self) -> str:
        return self._front_output_url

    @Property(str, notify=changed)
    def back_output_url(self) -> str:
        return self._back_output_url

    @Property(str, notify=changed)
    def last_output_url(self) -> str:
        return self._last_output_url

    @Slot(int, str, result=bool)
    def supports_layout(self, template_index: int, layout: str) -> bool:
        """Only offer templates with working mappings for BOTH faces."""
        types = _DUAL_LAYOUT_TYPES.get(layout)
        if types is None or not 0 <= template_index < len(self._template_list_model.items):
            return False
        selection = self._template_list_model.items[template_index]
        if not selection.is_installed:
            return False
        try:
            return all(
                selection.assembled_template.get_class_name_and_file_for_layout(kind)
                is not None for kind in types
            )
        except Exception:
            _logger.exception("Could not inspect double-faced template capabilities")
            return False

    @Slot("QVariantMap")  # pyright: ignore[reportArgumentType]
    def render_card(self, values: dict[str, Any]) -> None:
        if self._busy:
            return
        if self._card_model.loading:
            self._set_error("Finish the Scryfall lookup before rendering.")
            return
        source = self._card_model.copy_source()
        if source is None or source.layout not in {LayoutScryfall.Transform, LayoutScryfall.MDFC}:
            self._set_error("Find an ordinary Transform or MDFC card first.")
            return
        if not source.card_faces or len(source.card_faces) != 2:
            self._set_error("This card doesn't have exactly two editable faces.")
            return

        index = self._template_list_model.selected_index
        kind = "mdfc" if source.layout == LayoutScryfall.MDFC else "transform"
        if not self.supports_layout(index, kind):
            self._set_error("Choose an installed template supporting both faces of this card.")
            return

        forms = values.get("faces")
        if not isinstance(forms, list) or len(forms) != 2 or not all(isinstance(f, dict) for f in forms):
            self._set_error("Both front and back card details are required.")
            return
        forms = [{str(k): str(v) for k, v in f.items()} for f in forms]
        for idx, form in enumerate(forms):
            if not form.get("name", "").strip() or not form.get("type_line", "").strip():
                self._set_error(f"Complete the {'front' if idx == 0 else 'back'} face name and type line.")
                return
        if forms[0]["name"].strip().casefold() == forms[1]["name"].strip().casefold():
            self._set_error("Front and back must have different names so Proxyshop can identify them.")
            return

        options = {str(k): str(v) for k, v in values.items() if k != "faces"}
        try:
            StudioRenderModel._validate_studio_output_options(options)
        except ValueError as exc:
            self._set_error(str(exc))
            return

        self._busy = True
        self._render_generation += 1
        self._phase = "preparing"
        self._status = "Preparing front and back artwork..."
        self._error = ""
        self._launch_warning = ""
        self._front_output_url = ""
        self._back_output_url = ""
        self._last_output_url = ""
        self._pending.clear()
        self._results.clear()
        self._failed = False
        self._editable_psd = options.get("editable_psd", "false") == "true"
        self.changed.emit()
        chosen = self._template_list_model.items[index].assembled_template
        ensure_future(self._prepare_and_enqueue(source, forms, options, chosen))

    async def _prepare_and_enqueue(
        self,
        source: ScryfallCard,
        forms: list[dict[str, str]],
        options: dict[str, str],
        template: Any,
    ) -> None:
        temporary_dirs: list[TemporaryDirectory[str]] = []
        try:
            # Both render operations carry BOTH edited faces. Proxyshop's
            # process_card_data then selects one by matching CardDetails.name.
            edited_faces = source.model_copy(deep=True)
            assert edited_faces.card_faces is not None
            for face, form in zip(edited_faces.card_faces, forms, strict=True):
                face.name = form["name"].strip()
                face.mana_cost = form.get("mana_cost", "").strip()
                face.type_line = form["type_line"].strip()
                face.oracle_text = form.get("oracle_text", "")
                face.flavor_text = form.get("flavor_text", "")
                face.power = form.get("power", "").strip() or None
                face.toughness = form.get("toughness", "").strip() or None
                face.artist = form.get("artist", "").strip() or None

            assets: list[tuple[CardDetails, ScryfallCard]] = []
            for i, form in enumerate(forms):
                face_source = edited_faces.model_copy(deep=True)
                assert face_source.card_faces is not None
                face_source.image_uris = face_source.card_faces[i].image_uris
                face_source.set = form.get("set", "").strip().lower() or source.set
                rarity = form.get("rarity", "").strip().lower()
                if rarity:
                    try:
                        face_source.rarity = Rarity(rarity)
                    except ValueError as exc:
                        raise ValueError("Rarity must be common, uncommon, rare, mythic, special, bonus or timeshifted.") from exc
                art_path, temp_dir = await to_thread(
                    StudioRenderModel._resolve_artwork,
                    form.get("manual_artwork", ""),
                    face_source,
                )
                if temp_dir is not None:
                    temporary_dirs.append(temp_dir)

                card_details: CardDetails = {
                    "file": art_path,
                    "name": face_source.card_faces[i].name,
                    "set": face_source.set,
                    "number": face_source.collector_number,
                    "artist": form.get("artist", "").strip(),
                    "creator": "",
                    "kwargs": {},
                }
                assets.append((card_details, face_source))

            operations = await to_thread(
                prepare_render_operations,
                template,
                self._plugin_library.template_library,
                assets,
                file_dialog=self._file_dialog_model,
                message_dialog=self._message_dialog_model,
            )
            if len(operations) != 2:
                raise ValueError("Could not prepare both faces with the chosen template. See the Templates log.")

            mapped: dict[RenderOperation, int] = {}
            for op in operations:
                face_index = 0 if op.layout.is_front else 1
                if face_index in mapped.values():
                    raise ValueError("Proxyshop did not identify a unique front and back face.")
                mapped[op] = face_index
                is_borderless = op.template_class.__name__ == "BorderlessVectorTemplate"
                previous_callback = op.before_render_callback
                per_face_options = dict(options)
                per_face_options["include_flavor_text"] = forms[face_index].get("include_flavor_text", "true")
                StudioRenderModel._validate_studio_output_options(per_face_options)
                if is_borderless:
                    StudioRenderModel._validate_borderless_options(per_face_options)

                def apply_options(
                    operation: RenderOperation,
                    config: AppConfig,
                    prior: Any = previous_callback,
                    borderless: bool = is_borderless,
                    form_options: dict[str, str] = per_face_options,
                ) -> None:
                    if prior is not None:
                        prior(operation, config)
                    if borderless:
                        StudioRenderModel._apply_borderless_options(config, form_options)
                    StudioRenderModel._apply_studio_output_options(config, form_options)

                op.before_render_callback = apply_options
                setattr(op, "_studio_render_source", True)
                setattr(op, "_studio_open_psd_in_photocraft", self._editable_psd)

            if sorted(mapped.values()) != [0, 1]:
                raise ValueError("Proxyshop did not return one render operation for each face.")
            self._pending = mapped
            self._art_temp_dirs = temporary_dirs
            temporary_dirs = []
            self._phase = "queued"
            self._status = "Both faces queued for rendering..."
            self.changed.emit()
            # Both operations use the existing shared queue and PhotoCraft renderer.
            for op in operations:
                self._render_queue.enqueue(op)
        except Exception as exc:
            _logger.exception("Two-face Studio render could not be prepared")
            self._set_error(str(exc))
            self._busy = False
            self.changed.emit()
        finally:
            for temp_dir in temporary_dirs:
                temp_dir.cleanup()
            if not self._busy:
                self._cleanup_artwork()

    def _on_queue_started(self, operation: RenderOperation) -> None:
        index = self._pending.get(operation)
        if index is not None:
            self._started_on_gui.emit(index)

    def _on_queue_finished(self, result: RenderResult) -> None:
        operation = result["operation"]
        index = self._pending.get(operation)
        if index is None:
            return
        success = bool(result["result"])
        url = ""
        if success and operation.template_instance is not None:
            try:
                output = operation.template_instance.output_file_name
                if output.is_file() and output.suffix.lower() in {".jpg", ".jpeg", ".png", ".psd"}:
                    url = output.resolve().as_uri()
                else:
                    success = False
            except Exception:
                _logger.exception("Unable to locate rendered face output")
                success = False
        self._finished_on_gui.emit(index, success, url)

    @Slot(int)
    def _mark_started(self, index: int) -> None:
        if self._busy:
            self._phase = "rendering"
            self._status = f"Rendering {'front' if index == 0 else 'back'} face..."
            self.changed.emit()

    @Slot(int, bool, str)
    def _mark_finished(self, index: int, success: bool, url: str) -> None:
        if not self._busy:
            return
        for op, face_idx in list(self._pending.items()):
            if face_idx == index:
                del self._pending[op]
                break
        if success and url:
            self._results[index] = url
        else:
            self._failed = True
        if self._pending:
            self._status = f"{'Front' if index == 0 else 'Back'} face finished; waiting for other face..."
            self.changed.emit()
            return

        self._busy = False
        self._front_output_url = self._results.get(0, "")
        self._back_output_url = self._results.get(1, "")
        self._last_output_url = self._back_output_url or self._front_output_url
        self._phase = "error" if self._failed else "complete"
        self._status = "Both faces rendered!" if not self._failed else "A face failed to render."
        self._error = "One or both faces failed. Check the application log." if self._failed else ""
        self._cleanup_artwork()
        self.changed.emit()

        if not self._failed and self._editable_psd:
            # Use QUrl for correct Windows file URI decoding (spaces, Unicode, drive letters).
            from PySide6.QtCore import QUrl
            paths = [Path(QUrl(url).toLocalFile()) for url in (self._front_output_url, self._back_output_url)]
            ensure_future(self._open_psds(paths, self._render_generation))

    async def _open_psds(self, paths: list[Path], generation: int) -> None:
        try:
            for path in paths:
                await to_thread(StudioRenderModel._launch_photocraft, path)
        except Exception as exc:
            _logger.exception("Could not open both PhotoCraft PSDs")
            if generation == self._render_generation:
                self._launch_warning = f"PSDs saved, but PhotoCraft did not open both: {exc}"
                self._status = "PSDs saved — open manually"
                self.changed.emit()
        else:
            if generation == self._render_generation:
                self._status = "Opened both PSDs in PhotoCraft"
                self.changed.emit()

    def _cleanup_artwork(self) -> None:
        for temp_dir in self._art_temp_dirs:
            temp_dir.cleanup()
        self._art_temp_dirs.clear()

    def _set_error(self, message: str) -> None:
        self._error = message
        self._phase = "error"
        self._status = ""
        self.changed.emit()
