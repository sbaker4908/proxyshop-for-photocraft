#!/usr/bin/env python3
"""Add a persistent, explicitly saved default preset to Studio Output options.

From the ProxyStudio repository root:
    uv run python install_studio_output_defaults_v1.py

Only changes src/gui/qml/views/StudioWorkspace.qml. This does not alter the
rendering engine, existing render output logic, or Borderless Automatic V4.

Changes are validated in memory before writing. Backups are stored in
.git/proxystudio-patch-backups/output-defaults-v1 when Git is available.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "src/gui/qml/views/StudioWorkspace.qml"
MARKER = "// Studio Output defaults V1: save explicitly, restore on next launch."

# These are the live Studio Output fields, not global Proxyshop / render settings.
SWITCHES = (
    ("showSetSymbol", "true"),
    ("artistOnlyCredit", "false"),
    ("showWatermark", "false"),
    ("includeFlavorText", "true"),
    ("saveEditablePsd", "false"),
)


class PatchError(Exception):
    pass


def replace_exact_once(text: str, old: str, new: str, description: str) -> str:
    matches = text.count(old)
    if matches != 1:
        raise PatchError(
            f"{description}: expected exactly one matching location, found {matches}. "
            "No files have been changed."
        )
    return text.replace(old, new, 1)


def patch_qml(source: str) -> str:
    if MARKER in source:
        return source

    # Don't silently install this into an older version without the 5 toggles.
    for name, default in SWITCHES:
        definition = re.compile(
            rf"(?m)^(?P<indent>[ \t]*)property bool {re.escape(name)}: "
            rf"(?P<value>true|false)[ \t]*$"
        )
        matches = list(definition.finditer(source))
        if len(matches) != 1:
            raise PatchError(f"Missing or ambiguous Studio Output property: {name}")
        if matches[0].group("value") != default:
            raise PatchError(
                f"Unexpected baseline value for {name}. Source is different "
                "from the last verified version; no changes made."
            )
        if f"onToggled: workspace.{name} = checked" not in source:
            raise PatchError(f"Missing Studio Output switch for {name}")

    source = replace_exact_once(
        source,
        "import QtQuick.Dialogs\n",
        "import QtQuick.Dialogs\nimport QtCore\n",
        "QtCore Settings import",
    )

    settings_body = "\n".join(
        f"        property bool {name}: {default}" for name, default in SWITCHES
    )
    settings_block = (
        f"    {MARKER}\n"
        "    // The Qt Settings object stores values in the user's application settings.\n"
        "    // It is NOT bound to the switches: changing a switch does not save it.\n"
        "    Settings {\n"
        "        id: studioOutputDefaults\n"
        '        category: "StudioOutputDefaults"\n'
        f"{settings_body}\n"
        "    }\n\n"
        "    // True only after clicking Save as Default in this launch.\n"
        "    property bool outputDefaultsSavedThisSession: false\n\n"
    )
    source = replace_exact_once(
        source,
        "Item {\n    id: workspace\n\n",
        "Item {\n    id: workspace\n\n" + settings_block,
        "Studio root / settings placement",
    )

    for name, default in SWITCHES:
        # The Settings block also declares properties with these names, so
        # match the root-level indentation exactly, anchored at line start.
        pattern = re.compile(
            rf"(?m)^    property bool {re.escape(name)}: {default}$"
        )
        if len(pattern.findall(source)) != 1:
            raise PatchError(f"Startup default for {name}: expected one root property.")
        source = pattern.sub(
            f"    property bool {name}: studioOutputDefaults.{name}",
            source,
            count=1,
        )

    # The inline divider is the footer of the Output group, after its five switches.
    # Adding the action just above it keeps it inside Output (not Template Options).
    footer_divider = (
        "                    Rectangle { Layout.fillWidth: true; "
        "Layout.preferredHeight: 1; Layout.topMargin: 7; "
        "Layout.bottomMargin: 4; color: workspace.stroke }\n"
    )
    stored_values = "\n".join(
        f"                            studioOutputDefaults.{name} = workspace.{name};"
        for name, _ in SWITCHES
    )
    equalities = "\n".join(
        f"                            && workspace.{name} === studioOutputDefaults.{name}"
        for name, _ in SWITCHES
    )
    action_block = (
        "                    // Save only when requested; render output settings remain independent.\n"
        "                    StudioButton {\n"
        "                        Layout.fillWidth: true\n"
        "                        subtle: true\n"
        "                        text: \"Save as Default\"\n"
        "                        enabled: !workspace.renderBusy\n"
        "                        onClicked: {\n"
        f"{stored_values}\n"
        "                            workspace.outputDefaultsSavedThisSession = true;\n"
        "                        }\n"
        "                    }\n"
        "                    Text {\n"
        "                        Layout.fillWidth: true\n"
        "                        visible: workspace.outputDefaultsSavedThisSession\n"
        f"{equalities}\n"
        "                        text: \"Saved! These Output settings will load next time.\"\n"
        "                        color: \"#8dc9a6\"\n"
        "                        font.pixelSize: 11\n"
        "                        wrapMode: Text.WordWrap\n"
        "                    }\n"
    )
    source = replace_exact_once(
        source, footer_divider, action_block + footer_divider,
        "Save as Default button placement",
    )

    # Extra guard against accidentally injecting into the wrong scroll view.
    if not (source.index('text: "OUTPUT"') < source.index('text: "Save as Default"')
            < source.index('text: "The original Render button at the top remains available')):
        raise PatchError("Could not verify Save as Default is in the Output section.")
    return source


def main() -> int:
    if not TARGET.is_file():
        print("ERROR: Run this from the ProxyStudio repository root.")
        print(f"Expected project file: {TARGET.relative_to(ROOT)}")
        return 1

    try:
        original = TARGET.read_text(encoding="utf-8")
        updated = patch_qml(original)
        if updated == original:
            print("Studio Save as Default is already installed. Nothing changed.")
            return 0
    except (OSError, UnicodeError, PatchError) as exc:
        print(f"ERROR: {exc}")
        print("No project files were changed.")
        return 1

    git_dir = ROOT / ".git"
    base_dir = (
        git_dir / "proxystudio-patch-backups" / "output-defaults-v1"
        if git_dir.exists() else ROOT / ".proxystudio-patch-backups" / "output-defaults-v1"
    )
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup = base_dir / f"StudioWorkspace.{stamp}.qml"
    try:
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(TARGET, backup)
        # Atomic same-directory replacement avoids truncated QML if interrupted.
        temporary = TARGET.with_suffix(".qml.output_defaults_pending")
        temporary.write_text(updated, encoding="utf-8", newline="")
        temporary.replace(TARGET)
    except OSError as exc:
        print(f"ERROR: Installation did not complete: {exc}")
        print("Your original file is backed up at:", backup)
        return 1

    print("[OK] Added Save as Default to all five Studio Output options.")
    print("Saved values will be loaded the next time the application starts.")
    print("Backup:", backup)
    print("Start normally with: uv run main.py")
    try:
        Path(__file__).unlink()
    except OSError:
        print("You may delete install_studio_output_defaults_v1.py after testing.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
