#!/usr/bin/env python3
"""Install zoom and pan for the center Studio render preview.

Run from the ProxyStudio repository root:
    uv run python install_preview_panzoom_v1.py

Only src/gui/qml/views/StudioWorkspace.qml is changed.
The original file is backed up before modification.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "src" / "gui" / "qml" / "views" / "StudioWorkspace.qml"
MARKER = "// Studio preview pan and zoom V1."

OLD_IMAGE = '''                    Image {
                        id: renderedCardImage
                        anchors.fill: parent
                        anchors.margins: 15
                        source: workspace.displayedPreviewUrl
                        fillMode: Image.PreserveAspectFit
                        asynchronous: true
                        cache: false
                    }
'''

NEW_IMAGE = '''                    // Studio preview pan and zoom V1.
                    // Navigation affects the preview only; the rendered file is untouched.
                    Item {
                        id: previewViewport
                        anchors.fill: parent
                        clip: true

                        property real zoomFactor: 1.0
                        property real panX: 0.0
                        property real panY: 0.0
                        readonly property real maxZoom: 8.0

                        function clampPan() {
                            // Width changes can fire before the image finishes loading.
                            if (!renderedCardImage || renderedCardImage.status !== Image.Ready) {
                                panX = 0.0;
                                panY = 0.0;
                                return;
                            }
                            // Keep the card centered along axes where it still fits,
                            // and prevent dragging it completely outside the viewport.
                            const limitX = Math.max(0,
                                (renderedCardImage.paintedWidth * zoomFactor - width) / 2);
                            const limitY = Math.max(0,
                                (renderedCardImage.paintedHeight * zoomFactor - height) / 2);
                            panX = Math.max(-limitX, Math.min(limitX, panX));
                            panY = Math.max(-limitY, Math.min(limitY, panY));
                        }

                        function resetView() {
                            zoomFactor = 1.0;
                            panX = 0.0;
                            panY = 0.0;
                        }

                        function zoomAt(multiplier, anchorX, anchorY) {
                            if (renderedCardImage.status !== Image.Ready)
                                return;
                            const previous = zoomFactor;
                            const next = Math.max(1.0, Math.min(maxZoom, previous * multiplier));
                            if (Math.abs(next - previous) < 0.0001)
                                return;
                            // Keep the image position under the mouse stable while zooming.
                            const ratio = next / previous;
                            panX = (anchorX - width / 2) * (1 - ratio) + panX * ratio;
                            panY = (anchorY - height / 2) * (1 - ratio) + panY * ratio;
                            zoomFactor = next;
                            clampPan();
                        }

                        onWidthChanged: clampPan()
                        onHeightChanged: clampPan()

                        Item {
                            id: previewPanLayer
                            width: parent.width
                            height: parent.height
                            x: previewViewport.panX
                            y: previewViewport.panY
                            scale: previewViewport.zoomFactor
                            transformOrigin: Item.Center

                            Image {
                                id: renderedCardImage
                                anchors.fill: parent
                                anchors.margins: 15
                                source: workspace.displayedPreviewUrl
                                fillMode: Image.PreserveAspectFit
                                asynchronous: true
                                cache: false
                                onSourceChanged: previewViewport.resetView()
                            }
                        }

                        MouseArea {
                            anchors.fill: parent
                            enabled: renderedCardImage.status === Image.Ready
                            acceptedButtons: Qt.LeftButton
                            hoverEnabled: true
                            cursorShape: previewViewport.zoomFactor > 1.001
                                ? (pressed ? Qt.ClosedHandCursor : Qt.OpenHandCursor)
                                : Qt.ArrowCursor
                            property real lastX: 0
                            property real lastY: 0

                            onPressed: function(mouse) {
                                lastX = mouse.x;
                                lastY = mouse.y;
                            }
                            onPositionChanged: function(mouse) {
                                if (pressed && previewViewport.zoomFactor > 1.001) {
                                    previewViewport.panX += mouse.x - lastX;
                                    previewViewport.panY += mouse.y - lastY;
                                    previewViewport.clampPan();
                                }
                                lastX = mouse.x;
                                lastY = mouse.y;
                            }
                            onWheel: function(wheel) {
                                // Mouse-wheel notches and precision touchpad scrolling.
                                let steps = wheel.angleDelta.y / 120;
                                if (steps === 0 && wheel.pixelDelta.y !== 0)
                                    steps = wheel.pixelDelta.y / 70;
                                if (steps !== 0)
                                    previewViewport.zoomAt(Math.pow(1.22, steps), wheel.x, wheel.y);
                                wheel.accepted = true;
                            }
                            onDoubleClicked: previewViewport.resetView()
                        }
                    }
'''

OLD_END = '''                        }
                    }
                }
            }
        }

        // RIGHT: Template selection and Studio-only render controls.
'''

NEW_END = '''                        }
                    }

                    // Compact navigation actions over the preview (not in the header).
                    Rectangle {
                        id: previewZoomControls
                        anchors.right: parent.right
                        anchors.bottom: parent.bottom
                        anchors.margins: 12
                        width: previewZoomRow.implicitWidth + 14
                        height: 40
                        z: 2
                        radius: 7
                        color: "#262d31"
                        border.color: "#4b555b"
                        visible: renderedCardImage.status === Image.Ready

                        Row {
                            id: previewZoomRow
                            anchors.centerIn: parent
                            spacing: 5

                            StudioButton {
                                text: "−"
                                width: 30
                                height: 30
                                enabled: previewViewport.zoomFactor > 1.001
                                onClicked: previewViewport.zoomAt(1 / 1.22,
                                    previewViewport.width / 2, previewViewport.height / 2)
                            }
                            Text {
                                width: 45
                                height: 30
                                text: Math.round(previewViewport.zoomFactor * 100) + "%"
                                color: "#d3dbdf"
                                font.pixelSize: 11
                                font.bold: true
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                            StudioButton {
                                text: "+"
                                width: 30
                                height: 30
                                enabled: previewViewport.zoomFactor < previewViewport.maxZoom - 0.001
                                onClicked: previewViewport.zoomAt(1.22,
                                    previewViewport.width / 2, previewViewport.height / 2)
                            }
                            StudioButton {
                                text: "Fit"
                                width: 42
                                height: 30
                                enabled: previewViewport.zoomFactor > 1.001
                                    || Math.abs(previewViewport.panX) > 0.01
                                    || Math.abs(previewViewport.panY) > 0.01
                                onClicked: previewViewport.resetView()
                            }
                        }
                    }
                }
            }
        }

        // RIGHT: Template selection and Studio-only render controls.
'''


def patch(source: str) -> str:
    if MARKER in source:
        if ("id: previewViewport" in source and "id: previewZoomControls" in source):
            return source
        raise ValueError("An incomplete preview pan/zoom patch was found; no files changed.")

    # Explicitly verify the exact currently supported Studio preview structure.
    if source.count(OLD_IMAGE) != 1:
        raise ValueError("Preview image markup does not match the expected version; no files changed.")
    if source.count(OLD_END) != 1:
        raise ValueError("Preview closing markup does not match the expected version; no files changed.")
    if source.index(OLD_IMAGE) > source.index(OLD_END):
        raise ValueError("Unexpected preview placement; no files changed.")

    updated = source.replace(OLD_IMAGE, NEW_IMAGE, 1)
    updated = updated.replace(OLD_END, NEW_END, 1)
    for expected in ("id: renderedCardImage", "workspace.displayedPreviewUrl", "id: previewViewport", "id: previewZoomControls", "// RIGHT: Template selection"):
        if expected not in updated:
            raise ValueError(f"Required preview element missing: {expected}")
    if updated.count("id: renderedCardImage") != 1:
        raise ValueError("Preview image was duplicated; no files changed.")
    return updated


def main() -> int:
    if not TARGET.is_file():
        print(f"ERROR: StudioWorkspace.qml not found at: {TARGET}")
        print("Place this installer beside main.py in the project root.")
        return 1

    try:
        original = TARGET.read_text(encoding="utf-8")
        updated = patch(original)
    except (ValueError, OSError, UnicodeError) as exc:
        print(f"ERROR: {exc}")
        return 1

    if original == updated:
        print("[OK] Preview pan and zoom is already installed. Nothing changed.")
        return 0

    backup_root = (ROOT / ".git" / "proxystudio-patch-backups" / "preview-panzoom-v1"
                   if (ROOT / ".git").is_dir()
                   else ROOT / ".proxystudio-patch-backups" / "preview-panzoom-v1")
    backup = backup_root / f"StudioWorkspace.{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}.qml"
    pending = TARGET.with_suffix(".qml.preview_panzoom_pending")
    try:
        backup_root.mkdir(parents=True, exist_ok=True)
        shutil.copy2(TARGET, backup)
        pending.write_text(updated, encoding="utf-8", newline="")
        pending.replace(TARGET)
    except OSError as exc:
        print(f"ERROR: Could not install patch: {exc}")
        try:
            pending.unlink(missing_ok=True)
        except OSError:
            pass
        print(f"Backup: {backup}")
        return 1

    print("[OK] Studio preview pan + zoom installed.")
    print("Use mouse wheel to zoom, drag to pan, double-click or press Fit to reset.")
    print(f"Backup: {backup}")
    print("Launch the app with: uv run main.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
