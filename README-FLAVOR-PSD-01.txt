MTG Proxy Studio - Flavor & Editable PSD 01
===========================================

BUILD BASIS: Template Options V1 (the version previously committed and tested).

FILES
  src/gui/qml/views/StudioWorkspace.qml
  src/gui/qml/models/studio_render_model.py

INSTALL
1. Close MTG Proxy Studio.
2. Extract the archive into C:\Projects\proxyshop-for-photocraft, preserving folder structure.
3. Confirm replacement of the two files.
4. Launch with: uv run main.py

CHANGES
- Include flavor text switch in the Card Details header. The editor always
  retains Scryfall flavor text; only the render is affected.
- 'Save editable PSD' switch in the Render Settings output section.
- Render PSD triggers PhotoCraft/Proxyshop's existing layered PSD save path.
- When a PSD is created, Studio confirms PSD EXPORTED instead of claiming
  to display a current PNG/JPG preview. Open the output folder to edit it.
- Regular image output and the top-right legacy Render button are unchanged.
- Borderless template-specific options are preserved.

TEST
1. Llanowar Elves: render with Include ON, then OFF. Flavor text must disappear
   from the output with OFF, without disappearing from the editable text box.
2. Turn ON again and ensure flavor text renders again.
3. Enable Save editable PSD and render; verify a .psd exists in the output folder.
4. Open PSD in PhotoCraft and check that its layers are editable. (Untested here.)
5. Toggle PSD OFF; render and confirm normal JPG/PNG preview returns.
6. If using Borderless, verify Textbox Size/Textless/Drop Shadow still work.
7. Check the preview badge for PSD EXPORTED rather than CURRENT PREVIEW.

IMPORTANT
The existing Proxyshop 'Manual.Edit' PAUSE workflow is NOT enabled here.
This switch saves a .psd for later manual editing, as requested. The Photoshop
layer-editing experience may depend on PhotoCraft's PSD support. No Windows
PhotoCraft integration test was possible in this environment. Do not commit
until you verify the PSD opens with editable layers in PhotoCraft.
