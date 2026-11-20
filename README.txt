ProxyStudio - Copy Rendered Image V1
====================================

1. Close ProxyStudio.
2. Extract install_copy_rendered_image_v1.py to your project root,
   C:\Projects\proxyshop-for-photocraft, beside main.py.
3. Run in PowerShell:
      uv run python install_copy_rendered_image_v1.py
      uv run main.py

A compact "Copy image" button appears in the upper-right of the image preview,
when a rendered PNG/JPG is visible. Click it to put the entire original-resolution
image on the system image clipboard. "Copied!" confirms the operation; "Copy
failed" shows an error tooltip on hover. This copies an image, NOT a filename.
The existing Fit, +/- zoom, pan, and card rendering are unchanged.

Files changed by the installer:
  main.py
  src/gui/qml/views/StudioWorkspace.qml
New file:
  src/gui/qml/models/studio_clipboard_model.py

The installer stores backups inside .git/proxystudio-patch-backups/clipboard-v1.
It does not modify render output files or saved defaults.
