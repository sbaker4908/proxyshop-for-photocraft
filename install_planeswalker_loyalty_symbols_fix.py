#!/usr/bin/env python3
"""Apply a narrowly scoped planeswalker loyalty-symbol visibility fix.

Modifies only src/templates/planeswalker.py. It does not touch any PSDs,
Studio/editor files, or the working two-face rendering pathway.
"""
from __future__ import annotations

import ast
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / 'src' / 'templates' / 'planeswalker.py'
BACKUP_BASE = Path.home() / 'ProxyStudio Backups' / 'loyalty-symbols-v1'

OLD = '''        # Update ability cost if needed
        if not static:
            if layer := psd.getLayer(LAYERS.COST, icon):
                layer.textItem.contents = ability.get("cost", "0")
            if icon:
                icon = (
                    icon.duplicate(self.icons[-1], ElementPlacement.PlaceBefore)
                    if (self.icons and self.icons[-1])
                    else icon.duplicate()
                )

        # Add ability, icons, and colons'''

NEW = '''        # Configure the DUPLICATED badge, not the hidden PSD source.  In
        # PhotoCraft, copying a hidden symbol/colon can preserve its hidden
        # state; the old code never made those newly generated copies visible.
        if not static:
            if icon:
                icon = (
                    icon.duplicate(self.icons[-1], ElementPlacement.PlaceBefore)
                    if (self.icons and self.icons[-1])
                    else icon.duplicate()
                )
                icon.visible = True
                if cost_layer := psd.getLayer(LAYERS.COST, icon):
                    cost_layer.textItem.contents = ability.get("cost", "0")
                    cost_layer.visible = True
                else:
                    _logger.warning(
                        "Planeswalker icon %r has no Cost text layer in %s",
                        ability.get("icon"), self.layout.template_file.name,
                    )
            else:
                _logger.warning(
                    "Planeswalker loyalty icon group %r missing from %s",
                    ability.get("icon"), self.layout.template_file.name,
                )
            if colon:
                colon.visible = True
            else:
                _logger.warning(
                    "Planeswalker Colon text layer missing from %s",
                    self.layout.template_file.name,
                )

        # Add ability, icons, and colons'''


def main() -> int:
    if not TARGET.is_file():
        print(f'[ERROR] Cannot find {TARGET}. Extract this installer to the ProxyStudio project root.')
        return 1
    old = TARGET.read_text(encoding='utf-8')
    if NEW in old:
        print('[OK] Planeswalker loyalty-symbol fix is already installed.')
        return 0
    if old.count(OLD) != 1:
        print('[ERROR] The Planeswalker renderer has changed. Nothing was modified.')
        print('Send the current src/templates/planeswalker.py if you want a version-specific patch.')
        return 1
    new = old.replace(OLD, NEW, 1)
    try:
        ast.parse(new, filename=str(TARGET))
    except SyntaxError as exc:
        print(f'[ERROR] Updated Python failed syntax validation: {exc}')
        return 1
    backup_dir = BACKUP_BASE / datetime.now().strftime('%Y%m%d-%H%M%S')
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup = backup_dir / TARGET.name
    shutil.copy2(TARGET, backup)
    try:
        temp = TARGET.with_suffix('.py.tmp')
        temp.write_text(new, encoding='utf-8')
        temp.replace(TARGET)
    except Exception:
        shutil.copy2(backup, TARGET)
        raise
    print('[OK] Updated src/templates/planeswalker.py')
    print(f'[BACKUP] {backup}')
    print('Restart ProxyStudio and render Chandra, Torch of Defiance again.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
