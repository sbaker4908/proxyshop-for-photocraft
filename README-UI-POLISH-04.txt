MTG Proxy Studio - UI Polish 04: Compact Status Label
===================================================

Replaces only:
  src/gui/qml/views/StudioWorkspace.qml

Changes:
  - Removes the status box's second explanation line.
  - Uses a single centered status label (ready, not ready, working, complete, failed).
  - Reduces status box height to 40 px (Render Card button is 48 px).
  - Tones down state colors while retaining yellow/green/blue/red distinctions.
  - Shrinks the fixed right-panel action area to return space to template settings.
  - No changes to Python, queues, Scryfall, rendering, artwork, or the original Render button.

Install:
  1. Close MTG Proxy Studio.
  2. Extract this ZIP into C:\Projects\proxyshop-for-photocraft.
  3. Allow replacement of StudioWorkspace.qml, keeping its folder structure.
  4. Run: uv run main.py

Test:
  - With no card selected: compact, muted amber "Not ready to render".
  - With Llanowar Elves and Classic: compact, muted green "Ready to render".
  - During a render: subdued blue-gray, centered working status.
  - After success: subdued green "Render complete".
  - Render action remains a separate button and continues to work.

Check the UI locally before committing: this sandbox cannot run the
full Qt/PhotoCraft application on your Windows desktop.
