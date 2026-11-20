#!/usr/bin/env python3
"""Fix persistent Studio Output defaults on the feature/proxy-studio-ui branch.
Run from repo root: uv run python install_studio_output_defaults_v3.py
"""
from __future__ import annotations
import ast
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / 'main.py'
UI = ROOT / 'src/gui/qml/views/StudioWorkspace.qml'
MAIN_MARK = '# Studio Output Defaults V3: stable identity for persistent Qt settings.'
UI_MARK = '// Studio Output Defaults V3: use saved flavor text on new cards.'


def replace_once(text: str, before: str, after: str, label: str) -> str:
    n = text.count(before)
    if n != 1:
        raise ValueError(f'{label}: expected exactly 1 match, found {n}')
    return text.replace(before, after, 1)


def patch_main(text: str) -> str:
    if MAIN_MARK in text:
        if 'app.setOrganizationName("ProxyStudio")' in text and 'app.setApplicationName("ProxyStudio")' in text:
            return text
        raise ValueError('main.py contains incomplete V3 settings configuration')
    if 'app.setOrganizationName(' in text or 'app.setApplicationName(' in text:
        raise ValueError('main.py already sets an application identity; refusing to override')
    before = '    app = QGuiApplication(applicationDisplayName="MTG Proxy Studio")\n'
    after = before + ('    ' + MAIN_MARK + '\n'
                      '    app.setOrganizationName("ProxyStudio")\n'
                      '    app.setApplicationName("ProxyStudio")\n')
    return replace_once(text, before, after, 'Qt application initialization')


def patch_ui(text: str) -> str:
    for key in ['showSetSymbol', 'artistOnlyCredit', 'showWatermark', 'includeFlavorText', 'saveEditablePsd']:
        if f'studioOutputDefaults.{key} = workspace.{key};' not in text:
            raise ValueError(f'Save as Default V2 is missing option {key}')
    if UI_MARK in text:
        if 'include_flavor_text: studioOutputDefaults.includeFlavorText ? "true" : "false"' in text:
            return text
        raise ValueError('Incomplete V3 flavor-text patch found')
    before = ('        faceDrafts = (card.faces || []).map(function(f) {\n'
              '            return Object.assign({}, f);\n'
              '        });')
    after = ('        ' + UI_MARK + '\n'
             '        faceDrafts = (card.faces || []).map(function(f) {\n'
             '            return Object.assign({}, f, {\n'
             '                include_flavor_text: studioOutputDefaults.includeFlavorText ? "true" : "false"\n'
             '            });\n'
             '        });')
    text = replace_once(text, before, after, 'New card face initialization')
    return replace_once(
        text,
        '                        enabled: !studioRenderModel.busy\n                        onClicked: {\n                            studioOutputDefaults.showSetSymbol = workspace.showSetSymbol;',
        '                        enabled: !workspace.renderBusy\n                        onClicked: {\n                            studioOutputDefaults.showSetSymbol = workspace.showSetSymbol;',
        'Save button busy guard',
    )


def atomic_write(path: Path, content: str) -> None:
    temp = path.with_name(path.name + '.v3tmp')
    try:
        temp.write_text(content, encoding='utf-8', newline='')
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def main() -> int:
    try:
        if not MAIN.is_file() or not UI.is_file():
            raise ValueError('Place this installer beside main.py at the repo root')
        before = {MAIN: MAIN.read_text(encoding='utf-8'), UI: UI.read_text(encoding='utf-8')}
        after = {MAIN: patch_main(before[MAIN]), UI: patch_ui(before[UI])}
        ast.parse(after[MAIN])
        changed = [path for path in (MAIN, UI) if before[path] != after[path]]
        if not changed:
            print('V3 already installed. Nothing changed.')
            return 0
    except (ValueError, OSError, UnicodeError, SyntaxError) as exc:
        print('ERROR:', exc, '\nNo project files were changed.')
        return 1
    base = ROOT / ('.git/proxystudio-patch-backups' if (ROOT / '.git').is_dir() else '.proxystudio-patch-backups')
    backup_dir = base / 'output-defaults-v3' / datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    written = []
    try:
        for path in changed:
            target = backup_dir / path.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
        for path in changed:
            atomic_write(path, after[path])
            written.append(path)
    except OSError as exc:
        for path in written:
            try: atomic_write(path, before[path])
            except OSError: print('WARNING: manual restore needed for', path)
        print('ERROR:', exc, '\nBackups:', backup_dir)
        return 1
    print('[OK] Output Defaults V3 installed.')
    print('Changed:', ', '.join(str(path.relative_to(ROOT)) for path in changed))
    print('Backups:', backup_dir)
    print('Next: uv run main.py; click Save as Default again; close and relaunch to verify.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
