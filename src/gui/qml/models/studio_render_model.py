"""Studio-only render action using Proxyshop's existing render queue.

The original top-right Render button and template-list workflow are untouched.
"""
from __future__ import annotations

from asyncio import ensure_future, to_thread
from logging import getLogger
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import requests
from PySide6.QtCore import QObject, Property, QUrl, Signal, Slot

from src import DEFAULT_HEADERS
from src._loader import PluginLibrary
from src.cards import CardDetails
from src._config import AppConfig
from src.enums.settings import BorderlessTextbox, OutputFileType
from src.enums.mtg import LayoutScryfall, LayoutType, Rarity
from src.gui.qml.models.file_dialog_model import FileDialogModel
from src.gui.qml.models.message_dialog_content_model import MessageDialogContentModel
from src.gui.qml.models.studio_card_model import StudioCardModel
from src.gui.qml.models.template_list_model import TemplateListModel
from src.render.render_queue import RenderQueue, RenderResult
from src.render.setup import RenderOperation, prepare_render_operations
from src.utils.scryfall import ScryfallCard

_logger = getLogger(__name__)

# Download bound is deliberately generous for a Scryfall art crop.
_MAX_ART_BYTES = 40 * 1024 * 1024


class StudioRenderModel(QObject):
    """Prepare one Studio card and submit it to the shared Proxyshop queue."""

    changed = Signal()
    _started_on_gui = Signal()
    _finished_on_gui = Signal(bool)

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
        self._status = "Look up a card to begin."
        self._error = ""
        self._last_output_url = ""
        self._active_operation: RenderOperation | None = None
        self._art_temp_dir: TemporaryDirectory[str] | None = None

        self._started_on_gui.connect(self._set_rendering_status)
        self._finished_on_gui.connect(self._finish_render)
        render_queue.started.add_listener(self._on_queue_started)
        render_queue.finished.add_listener(self._on_queue_finished)

    @Property(bool, notify=changed)
    def busy(self) -> bool:
        return self._busy

    @Property(str, notify=changed)
    def phase(self) -> str:
        """One of idle, preparing, queued, rendering, complete or error."""
        return self._phase

    @Property(str, notify=changed)
    def status(self) -> str:
        return self._status

    @Property(str, notify=changed)
    def error(self) -> str:
        return self._error

    @Property(str, notify=changed)
    def last_output_url(self) -> str:
        """Confirmed output URI of the latest successful Studio render."""
        return self._last_output_url

    @Slot(int, str, result=bool)
    def supports_layout(self, template_index: int, layout_kind: str) -> bool:
        """Check the selected installed frame maps to a single-sided layout."""
        kinds = {
            "normal": LayoutType.Normal,
            "planeswalker": LayoutType.Planeswalker,
        }
        layout_type = kinds.get(layout_kind)
        if layout_type is None or not 0 <= template_index < len(self._template_list_model.items):
            return False
        chosen = self._template_list_model.items[template_index]
        if not chosen.is_installed:
            return False
        try:
            match = chosen.assembled_template.get_class_name_and_file_for_layout(layout_type)
            return match is not None and match[1].is_file()
        except Exception:
            _logger.exception("Unable to inspect Studio template layout support")
            return False

    # V1 option support is based on the actual template class, not its display name.
    # Other templates get no custom settings until we explicitly support them.
    @Slot(int, result=bool)
    def supports_borderless_options(self, template_index: int) -> bool:
        if not 0 <= template_index < len(self._template_list_model.items):
            return False
        chosen = self._template_list_model.items[template_index]
        if not chosen.is_installed:
            return False
        try:
            match = chosen.assembled_template.get_class_name_and_file_for_layout(
                LayoutType.Normal
            )
            return match is not None and match[0] == "BorderlessVectorTemplate"
        except Exception:
            _logger.exception("Unable to read Borderless template capabilities")
            return False

    @Slot(int, result="QVariantMap")  # pyright: ignore[reportArgumentType]
    def borderless_defaults(self, template_index: int) -> dict[str, Any]:
        """Load the template's actual saved defaults, without changing them."""
        defaults: dict[str, Any] = {
            "textbox_size": "Automatic",
            "textless": False,
            "drop_shadow": True,
        }
        if not self.supports_borderless_options(template_index):
            return defaults
        try:
            chosen = self._template_list_model.items[template_index]
            match = chosen.assembled_template.get_class_name_and_file_for_layout(
                LayoutType.Normal
            )
            if match is None:
                return defaults
            cfg = chosen.assembled_template.get_config(match[0])
            if cfg is None:
                return defaults
            saved_size = str(cfg.get_setting("FRAME", "Textbox.Size", "Automatic"))
            if saved_size in {"Automatic", "Short", "Medium", "Normal", "Tall"}:
                defaults["textbox_size"] = saved_size
            defaults["textless"] = bool(
                cfg.get_bool_setting("FRAME", "Textless", False)
            ) or saved_size == "Textless"
            defaults["drop_shadow"] = bool(
                cfg.get_bool_setting("TEXT", "Drop.Shadow", True)
            )
        except Exception:
            _logger.exception("Unable to read saved Borderless options")
        return defaults

    @staticmethod
    def _validate_borderless_options(form: dict[str, str]) -> None:
        size = form.get("template_textbox_size", "Automatic")
        if size not in {"Automatic", "Short", "Medium", "Normal", "Tall"}:
            raise ValueError(f"Invalid Borderless textbox size: {size}")
        BorderlessTextbox(size)
        if (form.get("template_textless", "false").lower() not in {"true", "false"}
                or form.get("template_drop_shadow", "true").lower() not in {"true", "false"}):
            raise ValueError("Invalid Borderless switch option")

    @staticmethod
    def _apply_borderless_options(config: AppConfig, form: dict[str, str]) -> None:
        """Override just this render's merged config. Never write to an INI file."""
        size = form.get("template_textbox_size", "Automatic")
        if size not in {"Automatic", "Short", "Medium", "Normal", "Tall"}:
            raise ValueError(f"Invalid Borderless textbox size: {size}")
        # Explicit booleans from the QML payload; do not use bool("false").
        textless = form.get("template_textless", "false").lower()
        shadow = form.get("template_drop_shadow", "true").lower()
        if textless not in {"true", "false"} or shadow not in {"true", "false"}:
            raise ValueError("Invalid Borderless switch option")

        for section in ("FRAME", "TEXT"):
            if not config.file.has_section(section):
                config.file.add_section(section)
        # Borderless size is ignored when Textless is enabled by the renderer.
        config.file.set("FRAME", "Textbox.Size", size)
        config.file.set("FRAME", "Textless", textless)
        config.file.set("TEXT", "Drop.Shadow", shadow)

    @staticmethod
    def _validate_studio_output_options(form: dict[str, str]) -> None:
        for key, description, default in (
            ("include_flavor_text", "flavor text inclusion", "true"),
            ("editable_psd", "PSD output", "false"),
            ("show_set_symbol", "set symbol", "true"),
            ("artist_only_credit", "artist-only credit", "false"),
            ("show_watermark", "watermark", "false"),
        ):
            if form.get(key, default).lower() not in {"true", "false"}:
                raise ValueError(f"Invalid {description} option.")

    @staticmethod
    def _apply_studio_output_options(
        config: AppConfig, form: dict[str, str], layout: Any | None = None
    ) -> None:
        """Apply Studio-only options for this render; never persist configuration.

        The visible expansion symbol and rules-text watermark are independent:
        disabling the first must not prevent rendering the second.
        """
        for section in ("BASE.TEXT", "BASE.SYMBOLS", "BASE.WATERMARKS"):
            if not config.file.has_section(section):
                config.file.add_section(section)

        include_flavor = form.get("include_flavor_text", "true").lower() == "true"
        show_symbol = form.get("show_set_symbol", "true").lower() == "true"
        artist_only = form.get("artist_only_credit", "false").lower() == "true"
        show_watermark = form.get("show_watermark", "false").lower() == "true"

        # Source data and set code remain untouched, even when their printed
        # decorations are disabled.
        config.file.set("BASE.TEXT", "No.Flavor.Text", "false" if include_flavor else "true")
        config.file.set("BASE.SYMBOLS", "Enable.Expansion.Symbol", "true" if show_symbol else "false")
        if artist_only:
            config.file.set("BASE.TEXT", "Collector.Mode", "artist")
        elif config.file.get("BASE.TEXT", "Collector.Mode", fallback="default") == "artist":
            # OFF should restore the regular collector footer, even if global
            # settings happened to use the artist-only mode.
            config.file.set("BASE.TEXT", "Collector.Mode", "default")

        config.file.set("BASE.WATERMARKS", "Watermark.Mode", "Forced" if show_watermark else "Disabled")
        if show_watermark:
            config.file.set("BASE.WATERMARKS", "Default.Watermark", "symbol")

        if form.get("editable_psd", "false").lower() == "true":
            if not config.file.has_section("APP.FILES"):
                config.file.add_section("APP.FILES")
            config.file.set("APP.FILES", "Output.File.Type", OutputFileType.PSD.value)

        # AppConfig stores derived values such as symbol_enabled,
        # collector_mode, watermark_mode and output_file_type.
        config.update_definitions()

        if show_watermark and layout is not None:
            # Proxyshop's `symbol` watermark preset only resolves an existing
            # WM.svg for a known printing, and isn't sufficient for offline
            # custom cards. First try the actual set watermark; if it doesn't
            # exist, reuse the expansion-symbol SVG as a subtle watermark.
            # The symbol file can be resolved even when the visible symbol is
            # disabled; only its placement is governed by symbol_enabled.
            from src.utils.hexapi import get_watermark_svg_from_set

            watermark_asset = get_watermark_svg_from_set(layout.set) or layout.symbol_svg
            if watermark_asset is not None and watermark_asset.is_file():
                # watermark_svg is a cached_property; set only for this
                # render's own layout, without modifying global settings.
                layout.__dict__["watermark_svg"] = watermark_asset
                layout.__dict__.pop("watermark", None)
            else:
                _logger.warning(
                    "Studio watermark requested but no symbol asset was found "
                    "for set %s", layout.set
                )

    @Slot("QVariantMap")  # pyright: ignore[reportArgumentType]
    def render_card(self, values: dict[str, Any]) -> None:
        """Called only by Studio's own button, never the original Render button."""
        if self._busy:
            return
        if self._card_model.loading:
            self._set_error("Finish the Scryfall lookup before rendering.")
            return
        source = self._card_model.copy_source()
        if source is None:
            self._set_error("Search for a Scryfall card first.")
            return
        idx = self._template_list_model.selected_index
        if not 0 <= idx < len(self._template_list_model.items):
            self._set_error("Choose a template first.")
            return
        selected = self._template_list_model.items[idx]
        if not selected.is_installed:
            self._set_error("Install the selected template before rendering.")
            return

        self._busy = True
        # A new attempt cannot inherit the previous render's success URI.
        self._last_output_url = ""
        self._phase = "preparing"
        self._error = ""
        self._status = "Preparing card and artwork..."
        self.changed.emit()
        form = {str(k): str(v) for k, v in values.items()}
        # asyncio is already integrated with the Qt event loop by main.py.
        ensure_future(self._prepare_and_enqueue(form, source, selected.assembled_template))

    async def _prepare_and_enqueue(
        self,
        form: dict[str, str],
        source: ScryfallCard,
        template: Any,
    ) -> None:
        art_temp_dir: TemporaryDirectory[str] | None = None
        try:
            if source.layout not in {LayoutScryfall.Normal, LayoutScryfall.Planeswalker} or source.card_faces:
                raise ValueError(
                    "Studio Render currently supports single-faced Normal and Planeswalker cards. "
                    "Use the original Render button for this card's special layout."
                )

            name = form.get("name", "").strip()
            type_line = form.get("type_line", "").strip()
            if not name or not type_line:
                raise ValueError("Card name and type line are required.")

            is_planeswalker = "Planeswalker" in type_line
            if source.layout == LayoutScryfall.Planeswalker and not is_planeswalker:
                raise ValueError("Planeswalker cards require 'Planeswalker' in the type line.")
            loyalty_value = form.get("loyalty", "").strip()
            if is_planeswalker and not loyalty_value:
                raise ValueError("Enter a starting loyalty for this planeswalker.")
            required_layout = "planeswalker" if is_planeswalker else "normal"
            selected_index = self._template_list_model.selected_index
            if not self.supports_layout(selected_index, required_layout):
                raise ValueError(
                    "Choose an installed template supporting "
                    + ("planeswalkers." if is_planeswalker else "normal cards.")
                )

            rarity = form.get("rarity", "").strip().lower()
            if rarity:
                try:
                    source.rarity = Rarity(rarity)
                except ValueError as exc:
                    raise ValueError(
                        "Unknown rarity. Use common, uncommon, rare, mythic, "
                        "special, bonus or timeshifted."
                    ) from exc

            original_name = source.name
            source.name = name
            source.mana_cost = form.get("mana_cost", "").strip()
            source.type_line = type_line
            source.layout = LayoutScryfall.Planeswalker if is_planeswalker else LayoutScryfall.Normal
            source.loyalty = loyalty_value if is_planeswalker else None
            source.oracle_text = form.get("oracle_text", "")
            source.flavor_text = form.get("flavor_text", "")
            source.power = None if is_planeswalker else (form.get("power", "").strip() or None)
            source.toughness = None if is_planeswalker else (form.get("toughness", "").strip() or None)
            source.artist = form.get("artist", "").strip() or None
            source.set = form.get("set", "").strip().lower() or source.set

            manual_artwork = form.get("manual_artwork", "").strip()
            art_path, art_temp_dir = await to_thread(
                self._resolve_artwork, manual_artwork, source
            )

            card_details: CardDetails = {
                "file": art_path,
                "name": original_name,
                "set": source.set,
                "number": source.collector_number,
                "artist": form.get("artist", "").strip(),
                "creator": "",
                "kwargs": {},
            }

            operations = await to_thread(
                prepare_render_operations,
                template,
                self._plugin_library.template_library,
                ((card_details, source),),
                file_dialog=self._file_dialog_model,
                message_dialog=self._message_dialog_model,
            )
            if len(operations) != 1:
                raise ValueError(
                    "Could not prepare this card with the selected template. "
                    "Check the app log on the Templates tab for details."
                )

            # Render-local options: flavor text and PSD apply to any Studio
            # template, while the Borderless specifics apply only to that class.
            # No saved template config is modified and the old toolbar is untouched.
            operation = operations[0]
            is_borderless = operation.template_class.__name__ == "BorderlessVectorTemplate"
            self._validate_studio_output_options(form)
            if is_borderless:
                self._validate_borderless_options(form)
            previous_callback = operation.before_render_callback

            def apply_studio_options(op: RenderOperation, cfg: AppConfig) -> None:
                if previous_callback is not None:
                    previous_callback(op, cfg)
                if is_borderless:
                    self._apply_borderless_options(cfg, form)
                self._apply_studio_output_options(cfg, form, op.layout)

            operation.before_render_callback = apply_studio_options

            # Keep the temporary Scryfall artwork alive until rendering finishes.
            self._art_temp_dir = art_temp_dir
            art_temp_dir = None
            self._active_operation = operations[0]
            # This marker lets the preview bridge distinguish this Studio
            # render from the original toolbar's independent render jobs.
            setattr(self._active_operation, "_studio_render_source", True)
            self._phase = "queued"
            self._status = "Waiting in render queue..."
            self.changed.emit()
            self._render_queue.enqueue(self._active_operation)
        except Exception as exc:
            if art_temp_dir is not None:
                art_temp_dir.cleanup()
            if self._art_temp_dir is not None:
                self._art_temp_dir.cleanup()
                self._art_temp_dir = None
            _logger.exception("Studio Render failed to prepare the card")
            self._active_operation = None
            self._busy = False
            self._phase = "error"
            self._status = ""
            self._error = str(exc)
            self.changed.emit()

    @staticmethod
    def _resolve_artwork(
        manual_url: str, source: ScryfallCard
    ) -> tuple[Path, TemporaryDirectory[str] | None]:
        """Use an existing image, or download Scryfall's art crop as a temporary file."""
        if manual_url:
            qurl = QUrl(manual_url)
            if qurl.isLocalFile():
                filename = qurl.toLocalFile()
            elif qurl.scheme():
                raise ValueError("Custom artwork must be a local file.")
            else:
                filename = manual_url
            image_path = Path(filename)
            if not image_path.is_file():
                raise FileNotFoundError(f"Artwork file not found: {image_path}")
            if image_path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
                raise ValueError("Choose a PNG, JPG, or WebP artwork image.")
            return image_path, None

        image_uris = source.image_uris
        if image_uris is None:
            raise ValueError("No Scryfall artwork is available. Choose an image manually.")

        temporary = TemporaryDirectory(prefix="mtg-proxy-studio-")
        path = Path(temporary.name) / "scryfall-art.jpg"
        try:
            with requests.get(
                str(image_uris.art_crop), headers=DEFAULT_HEADERS,
                stream=True, timeout=(8, 40),
            ) as response:
                response.raise_for_status()
                content_type = response.headers.get("Content-Type", "")
                if content_type and not content_type.lower().startswith("image/"):
                    raise ValueError("Scryfall returned something other than an image.")
                size = 0
                with path.open("wb") as output:
                    for chunk in response.iter_content(chunk_size=65536):
                        if not chunk:
                            continue
                        size += len(chunk)
                        if size > _MAX_ART_BYTES:
                            raise ValueError("The downloaded artwork is too large.")
                        output.write(chunk)
                if size == 0:
                    raise ValueError("Scryfall artwork download was empty.")
            return path, temporary
        except Exception:
            temporary.cleanup()
            raise

    def _on_queue_started(self, operation: RenderOperation) -> None:
        if operation is self._active_operation:
            self._started_on_gui.emit()

    def _on_queue_finished(self, result: RenderResult) -> None:
        if result["operation"] is self._active_operation:
            self._finished_on_gui.emit(result["result"])

    @Slot()
    def _set_rendering_status(self) -> None:
        if self._busy:
            self._phase = "rendering"
            self._status = "Rendering in PhotoCraft..."
            self.changed.emit()

    @Slot(bool)
    def _finish_render(self, success: bool) -> None:
        if success and self._active_operation is not None:
            instance = self._active_operation.template_instance
            if instance is not None:
                try:
                    output_path = instance.output_file_name
                    if output_path.is_file() and output_path.suffix.lower() in {
                        ".png", ".jpg", ".jpeg", ".psd"
                    }:
                        self._last_output_url = output_path.resolve().as_uri()
                except Exception:
                    _logger.exception("Could not locate Studio render output")
        self._active_operation = None
        if self._art_temp_dir is not None:
            self._art_temp_dir.cleanup()
            self._art_temp_dir = None
        self._busy = False
        self._phase = "complete" if success else "error"
        self._status = "Render complete!" if success else ""
        self._error = "" if success else "Rendering failed. Check the application log."
        self.changed.emit()

    def _set_error(self, message: str) -> None:
        self._phase = "error"
        self._error = message
        self._status = ""
        self.changed.emit()
