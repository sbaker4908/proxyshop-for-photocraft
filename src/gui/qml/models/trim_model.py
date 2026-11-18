"""Qt/QML bridge for opening, previewing and saving trimmed card images."""
from __future__ import annotations

from logging import getLogger
from pathlib import Path
from shutil import copyfileobj
from tempfile import TemporaryDirectory
from threading import Thread
from typing import Any

from PySide6.QtCore import QObject, Property, QUrl, Signal, Slot

from src.gui.qml.models.trim_processing import create_trim_preview

_logger = getLogger(__name__)


class TrimModel(QObject):
    """The Trim utility is independent of PhotoCraft and the render queue."""

    changed = Signal()
    _opened = Signal(dict)
    _saved = Signal(dict)

    def __init__(self) -> None:
        super().__init__()
        self._temp = TemporaryDirectory(prefix="mtg_proxy_trim_")
        self._generation = 0
        self._busy = False
        self._source_url = ""
        self._source_name = ""
        self._source_path: Path | None = None
        self._preview_path: Path | None = None
        self._preview_url = ""
        self._original_dimensions = ""
        self._output_dimensions = ""
        self._error = ""
        self._saved_path = ""
        self._status = "Open a rendered card to begin."
        self._opened.connect(self._on_opened)
        self._saved.connect(self._on_saved)

    @Property(bool, notify=changed)
    def busy(self) -> bool:
        return self._busy

    @Property(bool, notify=changed)
    def can_save(self) -> bool:
        return not self._busy and self._preview_path is not None

    @Property(str, notify=changed)
    def source_url(self) -> str:
        return self._source_url

    @Property(str, notify=changed)
    def source_name(self) -> str:
        return self._source_name

    @Property(str, notify=changed)
    def source_folder_url(self) -> str:
        """Local URL of the folder containing input and saved _trim images."""
        if self._source_path is None:
            return ""
        return self._source_path.parent.resolve().as_uri()

    @Property(str, notify=changed)
    def preview_url(self) -> str:
        return self._preview_url

    @Property(str, notify=changed)
    def original_dimensions(self) -> str:
        return self._original_dimensions

    @Property(str, notify=changed)
    def output_dimensions(self) -> str:
        return self._output_dimensions

    @Property(str, notify=changed)
    def output_name(self) -> str:
        return f"{self._source_path.stem}_trim.png" if self._source_path else "_trim.png"

    @Property(str, notify=changed)
    def status(self) -> str:
        return self._status

    @Property(str, notify=changed)
    def error(self) -> str:
        return self._error

    @Property(str, notify=changed)
    def saved_path(self) -> str:
        return self._saved_path

    @Slot(str)
    def open_image(self, input_url: str) -> None:
        """Accept a Windows file:// URL from QML's native FileDialog."""
        if self._busy:
            return

        parsed = QUrl(input_url)
        if parsed.scheme() and not parsed.isLocalFile():
            self._error = "Please choose a file on your computer."
            self.changed.emit()
            return

        file_path = Path(parsed.toLocalFile() if parsed.isLocalFile() else input_url)
        self._generation += 1
        generation = self._generation
        self._busy = True
        self._source_path = None
        self._source_url = ""
        self._source_name = file_path.name
        self._preview_url = ""
        self._preview_path = None
        self._original_dimensions = ""
        self._output_dimensions = ""
        self._saved_path = ""
        self._error = ""
        self._status = "Preparing trimmed preview..."
        self.changed.emit()

        def worker() -> None:
            try:
                if not file_path.is_file():
                    raise FileNotFoundError("The selected image no longer exists.")
                output = Path(self._temp.name) / f"preview_{generation}.png"
                dimensions = create_trim_preview(file_path, output)
                result: dict[str, Any] = {
                    "generation": generation,
                    "source": str(file_path.resolve()),
                    "preview": str(output.resolve()),
                    "original": f"{dimensions.original_width:,} × {dimensions.original_height:,} px",
                    "final": f"{dimensions.width:,} × {dimensions.height:,} px",
                    "error": "",
                }
            except Exception as exc:
                _logger.warning("Trim preview failed for %s: %s", file_path, exc)
                result = {"generation": generation, "error": str(exc)}
            self._opened.emit(result)

        Thread(target=worker, daemon=True).start()

    @Slot(dict)
    def _on_opened(self, result: dict[str, Any]) -> None:
        if result["generation"] != self._generation:
            return
        self._busy = False
        self._error = str(result["error"])
        if not self._error:
            self._source_path = Path(result["source"])
            self._preview_path = Path(result["preview"])
            self._source_url = self._source_path.as_uri()
            self._preview_url = self._preview_path.as_uri()
            self._original_dimensions = str(result["original"])
            self._output_dimensions = str(result["final"])
            self._status = "Ready to save transparent PNG."
        else:
            self._status = "Unable to trim selected image."
        self.changed.emit()

    @Slot()
    def save_trim(self) -> None:
        if not self.can_save or not self._source_path or not self._preview_path:
            return

        source_path = self._source_path
        preview_path = self._preview_path
        generation = self._generation
        self._busy = True
        self._error = ""
        self._status = "Saving cropped PNG..."
        self.changed.emit()

        def worker() -> None:
            candidate: Path | None = None
            try:
                folder = source_path.parent
                base_name = f"{source_path.stem}_trim"
                # Never overwrite the source or a previously exported trim.
                for index in range(1, 10001):
                    suffix = "" if index == 1 else f" ({index})"
                    path = folder / f"{base_name}{suffix}.png"
                    try:
                        # 'xb' is atomic: existing files cannot be overwritten.
                        with preview_path.open("rb") as src:
                            with path.open("xb") as target:
                                candidate = path
                                copyfileobj(src, target)
                        break
                    except FileExistsError:
                        continue
                else:
                    raise FileExistsError("Could not find an unused _trim filename.")
                result: dict[str, Any] = {
                    "generation": generation,
                    "path": str(candidate),
                    "error": "",
                }
            except Exception as exc:
                if candidate is not None:
                    try:
                        candidate.unlink(missing_ok=True)
                    except OSError:
                        pass
                _logger.warning("Trim PNG save failed: %s", exc)
                result = {"generation": generation, "path": "", "error": str(exc)}
            self._saved.emit(result)

        Thread(target=worker, daemon=True).start()

    @Slot(dict)
    def _on_saved(self, result: dict[str, Any]) -> None:
        if result["generation"] != self._generation:
            return
        self._busy = False
        self._error = str(result["error"])
        if self._error:
            self._status = "Could not save trimmed PNG."
        else:
            self._saved_path = str(result["path"])
            self._status = f"Saved {Path(self._saved_path).name}"
        self.changed.emit()
