MTG Proxy Studio — UI Polish 08: Hover cursors

PURPOSE
- Pointing-hand cursor on interactive Studio buttons (Find, artwork, Render Card)
- Pointing-hand cursor on Studio's output-folder icon and installed template selection
- Pointing-hand cursor on the original app's shared buttons, tab buttons, and list/tree item delegates
- I-beam cursor in Studio text entry fields, including Rules and Flavor Text
- Disabled actions keep the normal arrow cursor (no misleading click affordance)

IMPLEMENTATION
Uses Qt Quick HoverHandler with cursorShape to change the pointer without
intercepting clicks or changing existing onClicked behavior. Existing rendering,
card data, artwork selection, and preview freshness logic remain unchanged.

INSTALL
1. CLOSE MTG Proxy Studio (and any other running instance).
2. Extract the ZIP directly into C:\Projects\proxyshop-for-photocraft
3. Approve replacing the four source files while preserving folder structure.
4. Run: uv run main.py

TEST
1. Hover enabled Render Card, Find, Choose artwork, output folder icon and frame dropdown:
   expect pointing-hand cursor (similar to a browser link).
2. Hover disabled Render Card: expect ordinary arrow cursor.
3. Hover Name, Rules Text, Flavor Text: expect I-beam text cursor.
4. Hover Templates/Studio tabs and original top-right Render button:
   expect pointing-hand cursor.
5. Click all buttons as usual; no rendering behavior should have changed.

IMPORTANT
Built from last verified UI Preview Fix 07. Do not commit until you test on Windows.
If you have made further local QML edits beyond that update, back those up
before extracting this ZIP because it replaces the entire StudioWorkspace.qml.
