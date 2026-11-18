MTG Proxy Studio - UI Polish 02
================================

This update only replaces:
  src/gui/qml/views/StudioWorkspace.qml

Fixes:
  - Rules and flavor text fields automatically grow to display all entered text.
    The left Card Details panel scrolls for long content.
  - Removes the disabled Render Card hover tooltip that could cause a strange
    vertical bar. Disabled buttons no longer react to hover.
  - Groups render status and helper messaging inside one aligned status panel.

How to install:
  1. Close MTG Proxy Studio.
  2. Extract this archive into C:\Projects\proxyshop-for-photocraft.
     Preserve folders and allow replacement of StudioWorkspace.qml.
  3. In VS Code, run: uv run main.py

Suggested tests:
  - Look up Llanowar Elves. Rules/flavor text should be fully visible.
  - Paste a multi-paragraph rules text and verify the box grows as you type.
  - Scroll down the Card Details panel, then clear the text and verify shrink.
  - Change the name to blank to disable Render Card; hover over it.
    There should be no stray vertical bar or native tooltip.
  - Render again and verify the status text and completion preview.

This update does not change Python models, render logic, or the top Render button.
Do not commit until it passes on your Windows/PhotoCraft installation.
