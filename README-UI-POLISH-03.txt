MTG Proxy Studio - UI Polish 03: Status card refinement
======================================================

This release replaces just one file:
  src/gui/qml/views/StudioWorkspace.qml

Changes in this update:
  - Removes the small status circle and working spinner from the status panel.
  - Gives the whole status panel a muted color: amber for attention,
    green for ready/complete, blue-gray for working, red for error.
  - Centers both the status heading and the supporting text.
  - Puts missing requirements ahead of an older success state so the panel
    doesn't imply the form is ready when required fields are missing.
  - Leaves the Render Card button, original toolbar Render action,
    rendering backend, Scryfall lookup, growing text areas, and artwork
    selection untouched.

Installation:
  1. Close MTG Proxy Studio.
  2. Extract this ZIP into C:\Projects\proxyshop-for-photocraft,
     preserving folders and accepting replacement of StudioWorkspace.qml.
  3. In VS Code run: uv run main.py

Tests:
  - Open Studio without finding a card. The status card should be muted amber,
    with centered text and no status dot.
  - Look up Llanowar Elves. The status card should become muted green,
    centered, and the render button should be enabled.
  - Click Render Card. The status card should turn blue-gray during work;
    afterward it should turn muted green.
  - Clear the required Name field. It should become amber again.
  - Confirm Rules/Flavor Text still grow as you type.

This patch was structurally checked in the sandbox but has not been
executed on a Windows installation with PhotoCraft.
Do not commit before testing it locally.
