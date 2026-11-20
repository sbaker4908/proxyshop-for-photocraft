ProxyStudio: Save as Default for Studio Output (V2 fix)
=======================================================

This replaces the V1 installer that stopped at:
    ERROR: Missing Studio Output switch for includeFlavorText

The old V1 installer aborted before modifying any files; no rollback is needed.
V2 accepts alternate switch event handlers and uses the correct Studio render
busy state, while continuing to require the 5 Output properties and section.

Install:
1. Extract install_studio_output_defaults_v2.py into your project root:
      C:\Projects\proxyshop-for-photocraft
   (The same folder containing main.py.)
2. Run in PowerShell:
      uv run python install_studio_output_defaults_v2.py
3. Restart:
      uv run main.py

In Studio > Output, set the five switches how you prefer and click
'Save as Default'. You will see 'Saved!' once those values are stored.
On the next application launch the saved values should be restored.
Changing switches without pressing Save as Default does not change the saved defaults.

Changes: only src/gui/qml/views/StudioWorkspace.qml
Backups: .git/proxystudio-patch-backups/output-defaults-v2/ (if git is present)

Does not modify borderless automatic sizing, templates, rendering models,
Scryfall parsing, or other controls.
