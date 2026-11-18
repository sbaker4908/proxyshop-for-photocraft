MTG PROXY STUDIO — TRIM TAB (FIRST IMPLEMENTATION)
====================================================

This package adds a NEW Trim tab. It does not change Studio rendering,
PhotoCraft, the top-right Render button, or any other source files beyond
registering the new tab and model.

INSTALLATION — WINDOWS / POWERSHELL
---------------------------------
1. Make sure your current branch is committed (you already made a checkpoint).
2. Close MTG Proxy Studio.
3. Extract this ZIP directly into:
      C:\Projects\proxyshop-for-photocraft
   Keep the folder structure. Only main.py is intentionally replaced;
   trim_model.py, trim_processing.py and TrimWorkspace.qml are new files.
4. Open the VS Code terminal at the project root and run:
      uv run python install_trim.py
   This safely adds Trim to your existing App.qml, preserving custom UI changes.
   It is safe to run again if needed.
5. Launch normally:
      uv run main.py

TEST THE FEATURE
----------------
1. Click Trim (fourth tab).
2. Click Open Rendered Card... and select an UNTRIMMED card JPG from out/.
3. The default preview should show transparent rounded corners.
   Click Original / Trimmed to compare.
4. Click Save Trimmed PNG.
5. Verify the new PNG appears next to the source, named:
      Original Card Name_trim.png
   The original JPG is untouched.
6. Open the new PNG in an app that supports transparency and check the corners.

IMPORTANT
---------
- Trim assumes the input includes 1/8 inch bleed around a 2.5 x 3.5 inch card.
  It validates the source aspect ratio to avoid cutting a regular card scan.
- Rounded corners are antialiased and fully transparent at their outer tips.
- Saved output is a PNG with a nominal 2.5 x 3.5 inch proportion.
- This image is NOT print-safe (bleed is removed).
- Existing destination files are NOT overwritten. Additional saves become
  "_trim (2).png", "_trim (3).png", etc.
- If you select an existing "_trim.png" file or a bleed-free aspect ratio,
  the app will show an error instead of cropping it twice.
- Pillow is already included in this project's Python dependencies.

WHAT'S NEXT
-----------
This is the first functional version. Test original JPGs and PNGs, compare
corners and final dimensions. Once the workflow is verified in PhotoCraft's
Windows GUI, we'll refine any visual details you want.

You may see a small QML warning only if your local Qt differs from the repo.
Don't commit this update until you confirm Trim works on your machine.
