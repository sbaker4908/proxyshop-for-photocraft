ProxyStudio — Compact Panel Spacing V2
======================================

This is a follow-up to the Studio & Trim Alignment Fix V1. Install V1 first
(it is already installed if the Studio preview shows the new subtitle).

INSTALL
1. Close ProxyStudio.
2. Extract install_panel_spacing_v2.py into your project root beside main.py:
   C:\Projects\proxyshop-for-photocraft
3. From PowerShell in that folder, run:

      uv run python install_panel_spacing_v2.py
      uv run main.py

CHANGES (both Studio and Trim)
- Panel top padding: 18px -> 12px. Horizontal and bottom padding stay 18px.
- Main vertical gap: 11px -> 8px.
- Subtitle reserved minimum height: 32px -> 18px.
- Subtitle extra bottom margin: 10px -> 2px.
- Header rows remain 32px, maintaining alignment with the folder action.
- Long subtitles still grow and wrap naturally if necessary.

Only these files change:
  src/gui/qml/views/StudioWorkspace.qml
  src/gui/qml/views/TrimWorkspace.qml

SAFETY
- Installer validates both files before changing either one.
- Both original files are backed up under .git/proxystudio-patch-backups/
  panel-spacing-v2/<timestamp>/ (when the project is a Git checkout).
- Re-running after successful installation is safe (no-op).
- Rendering behavior, card models, templates, output defaults, and Trim logic
  are not touched.

REVIEW
Use `git diff -- src/gui/qml/views/StudioWorkspace.qml src/gui/qml/views/TrimWorkspace.qml`
to review the exact changes, then commit/push when satisfied.
