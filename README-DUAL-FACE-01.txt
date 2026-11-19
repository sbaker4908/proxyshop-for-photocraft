PROXYSTUDIO — TWO-SIDED STUDIO CARDS (Transform + MDFC)
=======================================================

WHAT CHANGES
- Studio recognizes ordinary 2-face Transform and MDFC Scryfall cards.
- Front/Back editor tabs independently preserve names, mana, type lines,
  rules, flavor toggles, power/toughness, artist, set/rarity, and artwork.
- Front/Back preview tabs show both finished exports.
- Render Both Faces submits TWO jobs to Proxyshop's existing rendering queue.
- Render & Edit Both saves TWO layered PSDs and opens both in PhotoCraft.
- The original top-right Render workflow, Trim tab, and existing single-face
  rendering are not replaced.

INSTALL
1. Close ProxyStudio/MTG Proxy Studio.
2. Extract this ZIP into C:\Projects\proxyshop-for-photocraft
   and keep the included folder structure. Replace existing files.
3. Open a VS Code terminal at the repository root and run:

       uv run python install_dual_faces.py

   This modifies main.py to register the new two-face model. It does not
   replace the full main.py, so your custom window name is preserved.
   It is safe to rerun. If .git exists, a backup of the original main.py
   is stored INSIDE .git (never staged by git add .).

4. Start the app:

       uv run main.py

FIRST TEST — TRANSFORM
1. Search for "Delver of Secrets" in Studio.
2. Confirm Front/Back buttons appear and the fields + artwork change.
3. Change the Back face rules text, return Front, then Back.
   Confirm that your edit is still there.
4. Select an INSTALLED template that supports Transform front AND back.
   Borderless is a good candidate if installed. Unsupported templates
   will show a non-ready state, not attempt a broken render.
5. Render Both Faces. The app should create TWO separate output images,
   named for the front and back face, and display both in the preview.
6. Change only the back face: preview should show NEEDS RENDER.
   Switching tabs alone must NOT mark the preview outdated.

SECOND TEST — MDFC
Search "Bala Ged Recovery" (back: "Bala Ged Sanctuary") and repeat.
Choose an installed MDFC-compatible template. Check land-side artwork.

OPTIONAL — PSD / FLAVOR
- Toggle Include Flavor Text separately on each face.
- Enable Manual edit in PhotoCraft; both faces export as PSDs and
  PhotoCraft is launched for each finished file. The rendered PSDs
  remain in your usual output folder.

SCOPE / LIMITS
- Standard two-face Transform and MDFC only for this first release.
- Specialized transforming planeswalkers, Sagas, Battles, Meld,
  split/adventure layouts, and other uncommon layouts remain unsupported.
- Borderless template options currently apply to BOTH faces together.
- Both faces must have different names for Proxyshop to distinguish them.
- PhotoCraft rendering must be tested on your Windows machine; this package
  has passed static Python/QML delimiter checks and simulated dual-queue tests,
  NOT a live PhotoCraft end-to-end render.

If a render fails, please send the Proxyshop log and a screenshot of the
Studio status. Don't commit this update until both tests pass.
