MTG Proxy Studio - Template Options V1 (Borderless)

INSTALLATION
1. Make sure your current working version is backed up with Git.
2. Close MTG Proxy Studio.
3. Extract this ZIP into C:\Projects\proxyshop-for-photocraft (preserve folders).
4. Overwrite the existing two files.
5. In VS Code terminal run: uv run main.py

FILES
- src/gui/qml/views/StudioWorkspace.qml (whole-file replacement)
- src/gui/qml/models/studio_render_model.py (whole-file replacement)

TEST
1. Studio -> choose Borderless -> Template Options appears.
2. Choose Classic -> Template Options disappears; Classic render remains unchanged.
3. Borderless -> change Textbox size to Tall; render and compare to Short.
4. Enable Textless mode -> render: the rules textbox should disappear.
5. Disable Textless, test Drop Shadow off/on. Shadow effect may be subtle; compare zoomed exports.
6. After rendering, preview badge should say CURRENT PREVIEW; changing any Borderless option should say NEEDS RENDER.
7. Switch to Classic, then back to Borderless: Borderless choices should be retained within this Studio session.
8. Verify original top-right Render still works independently.

DESIGN DETAILS
- Config overrides are applied to the render operation's private AppConfig FILE (before template.execute), not written to the template INI files.
- Only the built-in BorderlessVectorTemplate normal layout is enabled in this version.
- The options load the template's saved initial values on first selection, then retain your chosen values in memory.
- Two-sided cards are still unsupported by Studio Render.

PLEASE DO NOT COMMIT until tested on Windows.
