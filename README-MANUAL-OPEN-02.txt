MTG Proxy Studio — Manual Edit in PhotoCraft 02
==================================================

BUILD BASIS: Flavor & Editable PSD 01 (includes Borderless Template Options V1).

FILES (complete replacements)
  src/gui/qml/models/studio_render_model.py
  src/gui/qml/views/StudioWorkspace.qml

INSTALL
  1. CLOSE MTG Proxy Studio and PhotoCraft before installing.
  2. Extract this archive into C:\Projects\proxyshop-for-photocraft.
     Keep the folder structure and allow the two files to be replaced.
  3. In the VS Code terminal: uv run main.py

BEHAVIOR
  - 'Manual edit in PhotoCraft' is the updated Studio-only output toggle.
  - OFF: existing JPG/PNG rendering and automatic preview work as before.
  - ON: Studio renders and SAVES a layered .psd to the normal output folder,
        then launches the PhotoCraft desktop application with that PSD.
  - The PSD is persistent, not a temporary file. Studio does not close PhotoCraft.
  - No automatic .pcraft is created: use File > Save As in PhotoCraft.
  - If PhotoCraft cannot be found/launched, the PSD remains saved; a warning
    appears in the right panel and the folder icon still opens the output folder.
  - The existing 'Include flavor text' toggle and Borderless settings remain.
  - The top-right Render button and original Manual Edit pause workflow are
    unchanged.

TEST
  1. Search a card in Studio. Leave manual-edit toggle OFF; render and verify
     normal JPG/PNG preview shows CURRENT PREVIEW.
  2. Turn ON 'Manual edit in PhotoCraft'; click 'Render & Edit'.
  3. Wait for successful render. Verify that a .psd appears in output folder,
     PhotoCraft automatically opens it, and the card remains editable.
  4. Check Studio shows 'PSD EXPORTED' (not CURRENT PREVIEW).
  5. Use PhotoCraft File > Save As to save a separate .pcraft if desired.
  6. Close PhotoCraft. Verify Studio remains open and source PSD remains saved.
  7. Turn OFF manual-edit toggle; render again and verify normal image mode.

LIMITATION
  PhotoCraft must be installed and discoverable by the existing manual-edit
  launcher. This package can't verify the desktop application in this runtime.
  The launcher reuses '--new-instance', already used by Proxyshop's manual-edit
  workflow. Do not commit until the launch is confirmed on your Windows PC.
