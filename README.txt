ProxyStudio: Save as Default persistence fix (V3)
================================================
Applies to the pushed branch feature/proxy-studio-ui.

Problem:
 - QtCore Settings had no organization/application name configured in main.py.
 - Each freshly loaded card set include_flavor_text to true, overriding the
   user's saved preference as soon as a card was loaded.

Install:
 1. Extract install_studio_output_defaults_v3.py into the repo root, beside main.py.
 2. From that folder run:
      uv run python install_studio_output_defaults_v3.py
 3. Launch normally:
      uv run main.py
 4. Choose your desired five Output switches and CLICK Save as Default AGAIN.
    The previous saved values may not have been written by V2.
 5. Close the app completely, launch again, and check settings before and
    after loading/creating a card.

Only main.py and src/gui/qml/views/StudioWorkspace.qml are modified.
The patch validates all code anchors before changing files and makes backups
under .git/proxystudio-patch-backups/output-defaults-v3 (if Git is present).
It does not change rendering, templates, or borderless textbox algorithms.
