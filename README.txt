ProxyStudio: Borderless MDFC rules/flavor text overlapping bottom bar
===================================================================

Fixes: On a modal double-faced card (e.g. Bala Ged Recovery), Borderless
currently allows rules/flavor text to extend into the bottom strip that
shows the opposite face's type and mana/tap symbol.

Installation:
  1. Close ProxyStudio.
  2. Put install_borderless_mdfc_fix.py in the PROJECT ROOT
     (C:\Projects\proxyshop-for-photocraft).
  3. From a terminal in that root, run:
         uv run python install_borderless_mdfc_fix.py
  4. Restart with:
         uv run main.py

This edits ONLY src/templates/normal.py and preserves all other project files.
It creates a backup named normal.py.pre_mdfc_text_fix.bak. It refuses to install
if the expected code isn't present and is safe to run more than once.

Suggested tests:
  - Bala Ged Recovery, Borderless, Automatic textbox size, flavor included:
    no glyphs or flavor credit should overlap the bottom MDFC information strip.
  - Bala Ged Sanctuary back face: verify the textbox and bottom strip.
  - A regular Borderless card: no text positioning regression.
  - Try Manual Edit mode: PSD export behavior should be unchanged.

The patch is syntactically checked but requires real PhotoCraft render testing.
