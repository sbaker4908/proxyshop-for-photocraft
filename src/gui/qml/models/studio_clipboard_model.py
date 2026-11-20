"""Copy an existing rendered card image to the system image clipboard."""

from pathlib import Path

from PySide6.QtCore import QObject, QUrl, Slot
from PySide6.QtGui import QGuiApplication, QImageReader


class StudioClipboardModel(QObject):
    """Clipboard operations must run on the Qt GUI thread."""

    @Slot(str, result=str)
    def copy_image(self, source_url: str) -> str:
        """Copy the original image pixels, not the zoomed/cropped QML preview.

        Returns an empty string for success, or an error message for the UI.
        """
        url = QUrl(source_url)
        if not url.isLocalFile():
            return "Only a local rendered image can be copied."

        image_path = Path(url.toLocalFile())
        if image_path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
            return "The current preview is not a supported image file."
        if not image_path.is_file():
            return "The rendered image could not be found on disk."

        reader = QImageReader(str(image_path))
        reader.setAutoTransform(True)
        image = reader.read()
        if image.isNull():
            return reader.errorString() or "Unable to read the rendered image."

        clipboard = QGuiApplication.clipboard()
        if clipboard is None:
            return "The system clipboard is unavailable."
        try:
            clipboard.setImage(image)
        except Exception as exc:
            return f"Unable to copy rendered image: {exc}"
        return ""
