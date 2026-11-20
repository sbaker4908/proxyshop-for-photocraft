#!/usr/bin/env python3
"""Install an explicitly saved default preset for ProxyStudio's five Output controls.

Usage, from repository root:
    uv run python install_studio_output_defaults_v2.py

Only src/gui/qml/views/StudioWorkspace.qml is modified. All changes are
validated in memory before writing, and the original QML is backed up.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parent
QML = ROOT / "src/gui/qml/views/StudioWorkspace.qml"
MARKER = "// Studio Output defaults V2 — explicitly saved by the user."
BUTTON_MARKER = "// Studio Output defaults V2 action."
OPTIONS = (
    ("showSetSymbol", "true"),
    ("artistOnlyCredit", "false"),
    ("showWatermark", "false"),
    ("includeFlavorText", "true"),
    ("saveEditablePsd", "false"),
)


class PatchError(Exception):
    pass


def patch(source: str) -> str:
    # The UI may implement its switches with onToggled, onClicked, or another
    # handler. Those details are irrelevant to saving their live root values.
    # Verify the named root properties and exact Output section instead.
    if MARKER in source:
        if BUTTON_MARKER in source and 'text: "Save as Default"' in source:
            return source
        raise PatchError("An incomplete V2 patch was found; nothing changed.")
    if "// Studio Output defaults V1: save explicitly" in source:
        raise PatchError("An older defaults installer appears to be installed; nothing changed.")

    if not re.search(r"(?m)^import QtQuick.Dialogs\s*$", source):
        raise PatchError("Could not find the expected QtQuick.Dialogs import.")
    if not re.search(r"(?m)^Item\s*\{\s*\n\s*id:\s*workspace\s*$", source):
        raise PatchError("Could not find the Studio workspace root.")

    definitions: dict[str, re.Match[str]] = {}
    for name, _fallback in OPTIONS:
        pat = re.compile(rf"(?m)^(?P<indent>[ \t]{{4}})property bool {re.escape(name)}:\s*(?P<value>true|false)[ \t]*$")
        found = list(pat.finditer(source))
        if len(found) != 1:
            raise PatchError(f"Expected one root-level property bool {name} (found {len(found)}).")
        definitions[name] = found[0]
        if len(re.findall(rf"\bworkspace\.{re.escape(name)}\b", source)) < 1:
            raise PatchError(f"No UI binding found for workspace.{name}.")

    output_label = re.search(r'\btext:\s*"OUTPUT"', source)
    footer_label = re.search(r'\btext:\s*"The original Render button at the top remains available', source)
    if output_label is None or footer_label is None or output_label.start() > footer_label.start():
        raise PatchError("Could not locate the Studio Output section and its footer.")
    output_span = source[output_label.start():footer_label.start()]
    # Check for at least the three added controls and the PSD toggle, since the
    # flavor-text switch can be positioned differently or use another signal.
    for text in ('Show set symbol', 'Artist credit only', 'Watermark', 'Manual edit in PhotoCraft'):
        if text not in output_span:
            raise PatchError(f"Expected Output option label missing: {text}.")

    # Locate the divider directly before the Output footer (rather than the
    # other dividers elsewhere in the Studio scroll view).
    divider = re.compile(
        r"(?m)^([ \t]*)Rectangle\s*\{\s*Layout\.fillWidth:\s*true;\s*"
        r"Layout\.preferredHeight:\s*1;\s*Layout\.topMargin:\s*7;\s*"
        r"Layout\.bottomMargin:\s*4;\s*color:\s*workspace\.stroke\s*\}\s*$"
    )
    matching = [m for m in divider.finditer(source, output_label.end(), footer_label.start())]
    if len(matching) != 1:
        raise PatchError(f"Could not uniquely locate the Output footer divider (found {len(matching)}).")
    insertion = matching[0]
    indent = insertion.group(1)

    if not re.search(r"(?m)^import QtCore\s*$", source):
        source = re.sub(
            r"(?m)^(import QtQuick.Dialogs\s*)$",
            lambda m: m.group(1) + "\nimport QtCore",
            source,
            count=1,
        )

    defaults_properties = "\n".join(
        f"        property bool {name}: {definitions[name].group('value')}"
        for name, _ in OPTIONS
    )
    settings_block = (
        f"    {MARKER}\n"
        "    // Persisted values change only when Save as Default is clicked.\n"
        "    Settings {\n"
        "        id: studioOutputDefaults\n"
        '        category: "StudioOutputDefaults"\n'
        f"{defaults_properties}\n"
        "    }\n"
        "    property bool outputDefaultsSavedThisSession: false\n\n"
    )
    root = re.search(r"(?m)^Item\s*\{\s*\n\s*id:\s*workspace\s*\n", source)
    if not root:
        raise PatchError("Studio workspace root changed unexpectedly.")
    source = source[:root.end()] + "\n" + settings_block + source[root.end():]

    for name, _ in OPTIONS:
        definition = re.compile(rf"(?m)^    property bool {re.escape(name)}:\s*(true|false)[ \t]*$")
        if len(definition.findall(source)) != 1:
            raise PatchError(f"Unexpected root property for {name} after insertion.")
        source = definition.sub(
            f"    property bool {name}: studioOutputDefaults.{name}", source, count=1
        )

    assigned = "\n".join(
        f"{indent}        studioOutputDefaults.{name} = workspace.{name};"
        for name, _ in OPTIONS
    )
    check = "\n".join(
        f"{indent}        && workspace.{name} === studioOutputDefaults.{name}"
        for name, _ in OPTIONS
    )
    block = (
        f"{indent}{BUTTON_MARKER}\n"
        f"{indent}StudioButton {{\n"
        f"{indent}    Layout.fillWidth: true\n"
        f"{indent}    subtle: true\n"
        f'{indent}    text: "Save as Default"\n'
        f"{indent}    enabled: !studioRenderModel.busy\n"
        f"{indent}    onClicked: {{\n"
        f"{assigned}\n"
        f"{indent}        studioOutputDefaults.sync();\n"
        f"{indent}        workspace.outputDefaultsSavedThisSession = true;\n"
        f"{indent}    }}\n"
        f"{indent}}}\n"
        f"{indent}Text {{\n"
        f"{indent}    Layout.fillWidth: true\n"
        f"{indent}    visible: workspace.outputDefaultsSavedThisSession\n"
        f"{check}\n"
        f'{indent}    text: "Saved! These Output settings will load next time."\n'
        f'{indent}    color: "#8dc9a6"\n'
        f"{indent}    font.pixelSize: 11\n"
        f"{indent}    wrapMode: Text.WordWrap\n"
        f"{indent}}}\n"
    )

    # Determine divider position afresh after inserting Settings and changing imports.
    output_label2 = source.index('text: "OUTPUT"')
    footer_label2 = source.index('text: "The original Render button at the top remains available')
    match2 = list(divider.finditer(source, output_label2, footer_label2))
    if len(match2) != 1:
        raise PatchError("Output footer divider moved while patching.")
    source = source[:match2[0].start()] + block + source[match2[0].start():]

    if not (source.index('text: "OUTPUT"') < source.index(BUTTON_MARKER)
            < source.index('text: "The original Render button at the top remains available')):
        raise PatchError("Save button is not located in the Output section.")
    return source


def main() -> int:
    if not QML.is_file():
        print("ERROR: Run this script from your ProxyStudio repository root.")
        print(f"Expected: {QML}")
        return 1
    try:
        original = QML.read_text(encoding="utf-8")
        updated = patch(original)
    except (OSError, UnicodeError, PatchError) as err:
        print(f"ERROR: {err}\nNo project files were changed.")
        return 1

    if updated == original:
        print("Save as Default V2 is already installed. Nothing changed.")
        return 0

    backups = (ROOT / '.git' / 'proxystudio-patch-backups' / 'output-defaults-v2'
               if (ROOT / '.git').is_dir()
               else ROOT / '.proxystudio-patch-backups' / 'output-defaults-v2')
    backup = backups / f"StudioWorkspace.{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}.qml"
    pending = QML.with_name(QML.name + '.output_defaults_v2_tmp')
    try:
        backups.mkdir(parents=True, exist_ok=True)
        shutil.copy2(QML, backup)
        pending.write_text(updated, encoding="utf-8", newline="")
        pending.replace(QML)
    except OSError as err:
        if pending.exists():
            pending.unlink()
        print(f"ERROR: {err}\nOriginal backed up to: {backup}")
        return 1

    print("[OK] Save as Default installed for all five Studio Output options.")
    print("Click the button to save the currently selected values.")
    print("Next launch will restore those saved values.")
    print("Backup:", backup)
    print("Start normally with: uv run main.py")
    return 0


if __name__ == '__main__':
    sys.exit(main())
