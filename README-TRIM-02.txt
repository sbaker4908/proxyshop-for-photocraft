MTG PROXY STUDIO — TRIM 02: OPEN FOLDER BUTTON
================================================

This is a SMALL UPDATE for users who already installed Trim 01.

INSTALLATION
------------
1. Close MTG Proxy Studio.
2. Extract this ZIP into C:\Projects\proxyshop-for-photocraft.
3. Preserve the paths and replace BOTH existing files:
   - src/gui/qml/views/TrimWorkspace.qml
   - src/gui/qml/models/trim_model.py
4. Restart: uv run main.py

WHAT CHANGED
------------
- Added the 32px folder icon next to Card Preview, matching Studio's design.
- Before loading a card, it opens Proxyshop's usual output directory.
- After loading a card, it opens that source card's containing folder.
  This is also where Trim saves its _trim.png files.
- Original/Trimmed switch, processing, and saving logic are unchanged.

TEST
----
1. Open the Trim tab and choose a rendered card.
2. Click the small folder icon beside Card Preview.
3. Windows Explorer should open the directory that contains the card.
4. Save a _trim.png and click the icon again. The new PNG should be there.

The Python syntax and package structure were verified here. Confirm the
folder button works in your Windows app before committing.
