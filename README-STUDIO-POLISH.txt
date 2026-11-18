MTG PROXY STUDIO — STUDIO POLISH PASS 1
======================================

Based on the working Studio Render update that you just tested with Llanowar Elves.

INSTALL
1. Save/commit your previous working version first if you haven't already.
2. Close the MTG Proxy Studio application.
3. Extract this ZIP into C:\Projects\proxyshop-for-photocraft.
   Choose to replace existing files and keep the folder structure.
4. Open the VS Code terminal from your project root, then run:
      uv run main.py

FILES (complete replacements)
- src/gui/qml/views/StudioWorkspace.qml
  Unified card/editor styling, section hierarchy, loading and empty states,
  source-art indicator, clearer preview messaging, template controls, and
  persistent green Studio-only Render Card button.
- src/gui/qml/models/studio_render_model.py
  Adds a simple render phase property: idle, preparing, queued, rendering,
  complete, error. This is a stage indicator; NOT a fabricated percentage.
- src/gui/qml/models/studio_card_model.py
  Exposes whether the searched card is currently supported by Studio Render.

SAFETY / SCOPE
- Does NOT change main.py, App.qml, Proxyshop's top-right Render button,
  render queue, template engine, or PhotoCraft rendering code.
- Studio remains limited to single-faced normal Scryfall cards for now.
- Existing user edits remain session-only; project save/load is future work.
- Preview is the most recently opened or successfully exported image, not a
  continuously updating card simulation.

TEST CHECKLIST
1. Launch and open Studio. Confirm all three panels display.
2. Search Llanowar Elves. Confirm details and artwork load.
3. Click Choose artwork, select custom file, then Use Scryfall; both should work.
4. Select Classic. Verify preview and installed state update. Switch to
   Templates and back; the shared selection should persist.
5. With Llanowar Elves selected, change power to 7. Click Studio Render Card.
   Expect a spinner and text as job moves through preparing/queued/rendering.
6. Confirm final card has 7/1 and appears automatically in center.
7. Confirm top-right original Render still opens the original file-picker flow.
8. Clear the card's Name field: Studio button should disable and show why.
9. Optionally search a double-faced card: Studio should explain that this
   layout still uses the original Render workflow.

If you see a QML import/type error or Python traceback, copy the first error
from the VS Code terminal and send it to ChatGPT; do not commit this version.

ROLLBACK
This ZIP only changes the three files above. Your previous Git commit
remains available to restore them if needed. Do not run git reset --hard if
there are other uncommitted changes you want to keep.
