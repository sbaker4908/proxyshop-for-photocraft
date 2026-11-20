ProxyStudio — Card Preview Pan + Zoom V1
========================================

Adds navigation to the center Card Preview pane in Studio.

Controls:
- Mouse wheel over the rendered card: zoom in / out (up to 800%, minimum Fit)
- Left-click and drag on a zoomed card: pan
- Plus and minus buttons: step zoom in / out
- Fit button or double-click inside the preview: reset to fit
- Loading a new render, or switching preview faces: reset to fit

How to install:
1. Close ProxyStudio.
2. Extract install_preview_panzoom_v1.py beside main.py in your project root.
3. Run: uv run python install_preview_panzoom_v1.py
4. Run: uv run main.py

Changes only src/gui/qml/views/StudioWorkspace.qml.
Does not modify the exported card image, render logic, Trim view, or settings.
Creates a timestamped backup under .git/proxystudio-patch-backups/preview-panzoom-v1/.
Idempotent: running it again will not duplicate the controls.

If the installer says preview markup does not match, it has left the source
unchanged; please share the error so the patch can be adjusted safely.
