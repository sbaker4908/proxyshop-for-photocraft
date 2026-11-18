MTG Proxy Studio — UI Bug Fix 07: Preview freshness

PROBLEM
A newly completed Studio render could appear correctly but show NEEDS RENDER.
The previous freshness check compared the QML URL string to Python's output
URI text exactly, which can differ after Qt URL normalization.

FIX
- Tag Studio-created jobs as they enter Proxyshop's existing queue.
- The existing completed-render preview bridge now reports whether the actual
  displayed export came from Studio or from the original Render workflow.
- CURRENT PREVIEW requires: a loaded image, Studio provenance, and the same
  editor values/template/artwork as the last successfully submitted render.
- Edits, artwork changes, or template changes still show NEEDS RENDER.
- A completed original-toolbar render can never falsely show CURRENT PREVIEW.
- No change to Proxyshop's original Render button or rendering engine.

INSTALL
1. Close MTG Proxy Studio.
2. Extract this ZIP directly into C:\Projects\proxyshop-for-photocraft.
3. Approve replacement of the three source files.
4. Launch with: uv run main.py

TEST
1. In Studio, look up Llanowar Elves and render via Render Card.
   Expect CURRENT PREVIEW after the card appears.
2. Change Power from 1 to 7. Expect NEEDS RENDER immediately.
3. Render again. Expect CURRENT PREVIEW.
4. Change template or replace artwork. Expect NEEDS RENDER.
5. Optional: render using the original top-right button. Its export should
   appear, but must NOT claim CURRENT PREVIEW for Studio's fields.

If the issue persists, report whether the image loads and the displayed
status, plus any errors in the VS Code terminal. Do not commit until tested.
