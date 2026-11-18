MTG PROXY STUDIO — UI POLISH 05
================================

Change: required field labels show live validation color.
- Name and Type line are muted red when empty or whitespace-only.
- Both turn muted green as soon as non-whitespace text is entered.
- Asterisks removed. All optional labels keep their existing neutral color.

INSTALLATION
1. Close MTG Proxy Studio.
2. Extract this ZIP into C:\Projects\proxyshop-for-photocraft.
3. Allow Windows to replace src\gui\qml\views\StudioWorkspace.qml.
4. Restart with: uv run main.py

TEST
1. With no card selected, Name and Type line labels should appear red.
2. Type a name in Name; only Name should become green.
3. Enter a type line; its label should become green.
4. Clear either field; its label returns to red.
5. Search Scryfall for a card: both labels become green automatically.

Only StudioWorkspace.qml changes; the renderer and top-right Render button are unchanged.
