MTG Proxy Studio — UI Polish 06: Card Preview freshness

INSTALL
1. Close MTG Proxy Studio.
2. Extract this ZIP directly into C:\Projects\proxyshop-for-photocraft.
3. Confirm replacement of src/gui/qml/views/StudioWorkspace.qml and
   src/gui/qml/models/studio_render_model.py.
4. Run: uv run main.py

CHANGES
- Open Render and extra preview description removed.
- Compact outline folder button next to Card Preview title.
- Preview badge: NO PREVIEW / NEEDS RENDER / CURRENT PREVIEW / RENDERING.
- Changing a Studio input, art, or template makes prior Studio output stale.
- Only a confirmed successful Studio render can mark its matching preview current.
- Original top-right Render button and original render pipeline unchanged.

TEST
1. On startup see NO PREVIEW.
2. Search Llanowar Elves, render via Studio: CURRENT PREVIEW.
3. Change power from 1 to 7: NEEDS RENDER. Render: CURRENT PREVIEW.
4. Change selected template: NEEDS RENDER.
5. Use the small folder icon to open the output folder.
6. Render from the original toolbar: the new image should not claim CURRENT
   for Studio edits unless it is the previously verified Studio result.

NOTE
This ZIP updates only two files. No new dependency install or npm build needed.
QML was structurally checked and Python compiled; test the UI on Windows
before committing it to GitHub.
