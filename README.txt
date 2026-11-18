MTG Proxy Studio - Dedicated Studio Render Card Button
===================================================

This update preserves the original top-right Render button exactly as-is.
It adds a green 'Render Card' button INSIDE Studio's right-hand panel.

Included replacement files (relative to your repository root):
  main.py
  src/gui/qml/views/StudioWorkspace.qml
  src/gui/qml/models/studio_card_model.py
  src/gui/qml/models/studio_render_model.py  [NEW]

Other source files, including App.qml, Proxyshop's render queue, its
rendering engine, and the existing automatic preview model, are unchanged.

INSTALL
-------
1. Close MTG Proxy Studio and stop its terminal process.
2. Confirm your latest checkpoint was committed/pushed to GitHub.
3. Extract the ZIP into C:\Projects\proxyshop-for-photocraft
   and choose to REPLACE the existing files. Keep folder structure.
4. In VS Code's terminal run: uv run main.py

TEST
----
1. Switch to Studio and search for "Llanowar Elves".
2. Keep Classic selected. Leave the automatic Scryfall artwork selected.
3. Make an obvious edit, e.g. change power from 1 to 7.
4. Click the new green "Render Card" in Studio's right panel.
5. The status should go from Preparing to Queued/Rendering to Complete.
6. After PhotoCraft finishes, the center should show the completed card
   with 7/1 and the selected artwork (provided export is PNG or JPG).
7. Next choose your own JPG or PNG artwork and test again.
8. The ORIGINAL top-right Render button should still open the original
   file picker when clicked, as before.

IMPORTANT LIMITATIONS (FIRST VERSION)
-------------------------------------
- Studio Render currently handles single-faced cards with Scryfall's
  normal layout, such as Llanowar Elves, Earthbind and Black Lotus.
  Use the original top-right Render for special layouts for now.
- You must search for an existing card before Studio rendering;
  cards created entirely from scratch are a later feature.
- Edits to text, name, mana cost, type, power/toughness, artist,
  set code and rarity are passed to the render. Changing the set
  code does NOT select a different Scryfall printing; its original
  collector number and other printing metadata remain unchanged.
- Automatic Scryfall art is downloaded temporarily when you render.
  It is cleaned up after the queue reports completion.
- The existing preview bridge displays PNG/JPG completed renders.
  PSD-only exports won't automatically appear as images.
- Existing Proxyshop template configuration still controls output
  quality and file format; Studio doesn't yet override those settings.

IF SOMETHING FAILS
------------------
- The new button displays preparation failures in Studio.
- Rendering errors also appear in Proxyshop's log under Templates.
- Do not commit a failed version; send the error and terminal output.
- If necessary, restore tracked changes from Git using:
  git restore main.py src/gui/qml/views/StudioWorkspace.qml src/gui/qml/models/studio_card_model.py
  Then delete src/gui/qml/models/studio_render_model.py.
  NOTE: git restore discards uncommitted edits in those tracked files.

Once verified:
  git add main.py src/gui/qml/views/StudioWorkspace.qml src/gui/qml/models/studio_card_model.py src/gui/qml/models/studio_render_model.py
  git commit -m "Add dedicated Studio render workflow"
  git push

This update has passed syntax checks and an isolated simulated queue
and artwork test. A full PhotoCraft desktop render must be tested on
Windows because this environment does not contain PySide6/PhotoCraft.
