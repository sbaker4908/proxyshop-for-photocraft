"""Expose successfully completed Proxyshop renders to MTG Proxy Studio's QML UI."""

from pathlib import Path
from logging import getLogger

from PySide6.QtCore import QObject, Property, Signal, Slot

from src.render.render_queue import RenderQueue, RenderResult

_logger = getLogger(__name__)


class StudioRenderPreviewModel(QObject):
    """Listen for completed renders, then notify QML on the GUI thread."""

    changed = Signal()
    _render_ready = Signal(str)

    def __init__(self, render_queue: RenderQueue) -> None:
        super().__init__()
        self._preview_url: str = ""
        self._render_ready.connect(self._update_preview)
        render_queue.finished.add_listener(self._on_render_finished)

    @Property(str, notify=changed)
    def preview_url(self) -> str:
        return self._preview_url

    def _on_render_finished(self, result: RenderResult) -> None:
        """Called by the render queue, potentially on its worker thread."""
        if not result["result"]:
            return

        template = result["operation"].template_instance
        if template is None:
            return

        try:
            output_path: Path = template.output_file_name
            if output_path.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
                _logger.info("Preview skipped: output is not a viewable image: %s", output_path)
                return
            if not output_path.is_file():
                _logger.warning("Render succeeded but output was not found: %s", output_path)
                return

            # Cross-thread signal; the connected slot runs on the UI thread.
            self._render_ready.emit(output_path.resolve().as_uri())
        except Exception:
            _logger.exception("Could not resolve output path for Studio preview")

    @Slot(str)
    def _update_preview(self, url: str) -> None:
        self._preview_url = url
        self.changed.emit()
