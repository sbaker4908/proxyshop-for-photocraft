ProxyStudio — Include Flavor Text toggle relocation
===================================================

Change: Move the existing Include flavor text switch from the left-side
"Flavor text" field header into the right-hand OUTPUT section, above
"Manual edit in PhotoCraft". The switch stays available for every template.
It retains the existing behavior for single-faced and double-faced cards.

INSTALL
=======
1. Close ProxyStudio.
2. Extract apply_flavor_output_move.py into your repository ROOT:
   C:\Projects\proxyshop-for-photocraft\
3. In a terminal opened in the project directory, run:

   uv run python apply_flavor_output_move.py

4. Launch as usual:

   uv run main.py

The installer changes only src/gui/qml/views/StudioWorkspace.qml.
It creates a safety backup in your home directory / ProxyStudio Backups,
so the backup won't be included in your next `git add .`.
It is safe to run the installer a second time (no duplicate toggle).

TEST
====
- Open a single-faced card. Verify Include flavor text is under OUTPUT.
- Disable it: the Scryfall text should remain visible in the editor, while
  the preview badge changes to NEEDS RENDER.
- Open an MDFC/transform card. Toggle the front, switch to back, and verify
  the back retains its own setting; switching back restores the front's.

No render engine, template, or Python model files are replaced.
