#!/usr/bin/env python3
"""Install a full-resolution Copy image action in ProxyStudio's Studio preview.

Run from the repository root: uv run python install_copy_rendered_image_v1.py
Requires the existing Studio pan/zoom UI (V1).
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "main.py"
QML = ROOT / "src/gui/qml/views/StudioWorkspace.qml"
MODEL = ROOT / "src/gui/qml/models/studio_clipboard_model.py"
MARKER = "// Studio preview clipboard V1."

MODEL_SOURCE = '''"""Copy an existing rendered card image to the system image clipboard."""

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
'''


def replace_once(source: str, old: str, new: str, label: str) -> str:
    found = source.count(old)
    if found != 1:
        raise ValueError(f"Expected one {label} insertion point, found {found}. No files changed.")
    return source.replace(old, new, 1)


def patch_main(source: str) -> str:
    source = replace_once(
        source,
        "    from src.gui.qml.models.studio_card_model import StudioCardModel\n",
        "    from src.gui.qml.models.studio_card_model import StudioCardModel\n"
        "    from src.gui.qml.models.studio_clipboard_model import StudioClipboardModel\n",
        "clipboard model import",
    )
    source = replace_once(
        source,
        "    studio_card_model = StudioCardModel()\n",
        "    studio_card_model = StudioCardModel()\n"
        "    studio_clipboard_model = StudioClipboardModel()\n",
        "clipboard model creation",
    )
    source = replace_once(
        source,
        '    root_context.setContextProperty("studioCardModel", studio_card_model)\n',
        '    root_context.setContextProperty("studioCardModel", studio_card_model)\n'
        '    root_context.setContextProperty("studioClipboardModel", studio_clipboard_model)\n',
        "clipboard model QML registration",
    )
    return source


def patch_qml(source: str) -> str:
    if "id: previewViewport" not in source or "id: renderedCardImage" not in source:
        raise ValueError("Expected Studio zoom/pan preview is missing. No files changed.")
    source = replace_once(
        source,
        "    property bool outputDefaultsSavedThisSession: false\n",
        "    property bool outputDefaultsSavedThisSession: false\n\n"
        f"    {MARKER}\n"
        '    property string copyPreviewFeedback: ""\n'
        '    property string copyPreviewError: ""\n'
        '    Timer {\n'
        '        id: copyPreviewFeedbackTimer\n'
        '        interval: 1800\n'
        '        repeat: false\n'
        '        onTriggered: {\n'
        '            workspace.copyPreviewFeedback = "";\n'
        '            workspace.copyPreviewError = "";\n'
        '        }\n'
        '    }\n',
        "clipboard status storage",
    )
    action = '''                    // Copy the original image data, independent of preview zoom or pan.
                    StudioButton {
                        id: copyRenderedImageButton
                        anchors.top: parent.top
                        anchors.right: parent.right
                        anchors.margins: 12
                        z: 3
                        width: 106
                        height: 32
                        subtle: true
                        visible: renderedCardImage.status === Image.Ready
                        enabled: renderedCardImage.status === Image.Ready
                        text: workspace.copyPreviewFeedback.length > 0
                            ? workspace.copyPreviewFeedback : "Copy image"
                        ToolTip.visible: hovered
                        ToolTip.delay: 550
                        ToolTip.text: workspace.copyPreviewError.length > 0
                            ? workspace.copyPreviewError
                            : "Copy full-resolution rendered image to clipboard"
                        onClicked: {
                            const error = studioClipboardModel.copy_image(
                                String(workspace.displayedPreviewUrl));
                            workspace.copyPreviewError = error;
                            workspace.copyPreviewFeedback = error.length > 0
                                ? "Copy failed" : "Copied!";
                            copyPreviewFeedbackTimer.restart();
                        }
                    }

'''
    source = replace_once(
        source,
        "                    // Compact navigation actions over the preview (not in the header).\n",
        action + "                    // Compact navigation actions over the preview (not in the header).\n",
        "copy action in the preview area",
    )
    return source


def self_test() -> None:
    example_main = ('    from src.gui.qml.models.studio_card_model import StudioCardModel\n'
                    '    studio_card_model = StudioCardModel()\n'
                    '    root_context.setContextProperty("studioCardModel", studio_card_model)\n')
    result = patch_main(example_main)
    assert "studioClipboardModel" in result and "StudioClipboardModel()" in result
    example_qml = ('    property bool outputDefaultsSavedThisSession: false\n'
                   '    Item { id: previewViewport; Item { id: renderedCardImage } }\n'
                   '                    // Compact navigation actions over the preview (not in the header).\n')
    result_qml = patch_qml(example_qml)
    assert 'studioClipboardModel.copy_image(' in result_qml
    assert 'id: copyRenderedImageButton' in result_qml
    assert 'id: copyPreviewFeedbackTimer' in result_qml
    assert result_qml.count('Copy image') == 1


def main() -> int:
    if "--self-test" in sys.argv:
        self_test()
        print("Self-test passed.")
        return 0
    try:
        original_main = MAIN.read_text(encoding="utf-8")
        original_qml = QML.read_text(encoding="utf-8")
        installed = MARKER in original_qml
        if installed and "studioClipboardModel" in original_main and MODEL.is_file():
            print("Copy image V1 is already installed. No files changed.")
            return 0
        if installed or "studioClipboardModel" in original_main or MODEL.exists():
            raise ValueError("An incomplete or different clipboard patch exists. No files changed.")
        updated_main = patch_main(original_main)
        updated_qml = patch_qml(original_qml)
        if updated_qml.count('id: copyRenderedImageButton') != 1:
            raise ValueError("Copy button validation failed. No files changed.")
        compile(MODEL_SOURCE, str(MODEL), "exec")
    except (OSError, ValueError, SyntaxError) as exc:
        print("ERROR:", exc)
        return 1

    backups_dir = ROOT / (".git/proxystudio-patch-backups/clipboard-v1"
                         if (ROOT / ".git").is_dir()
                         else ".proxystudio-patch-backups/clipboard-v1")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    saved_paths = []
    try:
        backups_dir.mkdir(parents=True, exist_ok=True)
        for path in (MAIN, QML):
            backup = backups_dir / f"{path.name}.{timestamp}.bak"
            shutil.copy2(path, backup)
            saved_paths.append((path, backup))
        # Write every new version before replacing any project files.
        changes = {MAIN: updated_main, QML: updated_qml, MODEL: MODEL_SOURCE}
        pending = []
        for target, content in changes.items():
            temp = target.with_name(target.name + ".clipboard_v1_pending")
            temp.write_text(content, encoding="utf-8", newline="")
            pending.append((target, temp))
        for target, temp in pending:
            temp.replace(target)
    except OSError as exc:
        print("ERROR installing:", exc)
        for target, backup in saved_paths:
            try:
                shutil.copy2(backup, target)
            except OSError:
                print("Restore manually from:", backup)
        if MODEL.exists():
            try:
                MODEL.unlink()
            except OSError:
                pass
        return 1
    finally:
        for temp_name in ("main.py.clipboard_v1_pending",
                          "StudioWorkspace.qml.clipboard_v1_pending",
                          "studio_clipboard_model.py.clipboard_v1_pending"):
            for parent in (ROOT, QML.parent, MODEL.parent):
                try:
                    (parent / temp_name).unlink(missing_ok=True)
                except OSError:
                    pass

    print("[OK] Copy image button added to the Studio card preview.")
    print("Copied content is the original full-resolution bitmap (not the zoomed view).")
    print("Backups:", backups_dir)
    print("Start with: uv run main.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
