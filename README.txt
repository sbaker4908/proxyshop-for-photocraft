ProxyStudio — Studio right-panel bottom border fix (V1)
======================================================

Issue: The fixed Render Card/status footer fills the right panel to its edges,
covering the parent's thin border at the bottom and lower corners.

Fix: Inset the footer by 1px on the left, right and bottom, and use a 9px
corner radius so the 10px panel outline remains visible. Other panels and
all saved output settings are unaffected.

Install:
1. Close ProxyStudio.
2. Extract install_footer_border_fix_v1.py into your project folder next to main.py.
3. From PowerShell in that folder run:

   uv run python install_footer_border_fix_v1.py
   uv run main.py

The installer backs up your original StudioWorkspace.qml file and changes
nothing if the expected footer cannot be found. It can be safely rerun.
