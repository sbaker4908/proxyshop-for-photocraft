ProxyStudio — Two-Face Preview Badge Fix (01)
==============================================

Fixes the two-sided Studio preview badge using a separate successful-render
snapshot for each face. Editing Front no longer makes an untouched Back
preview appear stale (and vice versa).

Shared rendering settings such as selected template, Borderless options,
and PSD mode still make both faces NEEDS RENDER, as expected.

INSTALL
1. Close ProxyStudio.
2. Extract this ZIP into C:\Projects\proxyshop-for-photocraft
   with folder structure preserved and replace the one QML file.
3. Run: uv run main.py

NO INSTALLER OR PYTHON CHANGES NEEDED.

TEST
1. Render both faces of Delver of Secrets successfully.
2. Front should display CURRENT PREVIEW; Back should display CURRENT PREVIEW.
3. Change only front rules text. Front should display NEEDS RENDER.
4. Switch to Back. Back should still display CURRENT PREVIEW.
5. Change only Back artwork/text. Back should display NEEDS RENDER.
6. Render again. Both should return to CURRENT PREVIEW.
7. Optionally change the shared template. Both should show NEEDS RENDER.

The single-faced workflow, Trim, rendering engines, and PhotoCraft integration
are unchanged. Only StudioWorkspace.qml is replaced.

TESTED
The per-face snapshot comparison was tested with a JavaScript harness.
A live Qt/PhotoCraft run requires your Windows installation.
