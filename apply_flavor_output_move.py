"""Move Studio's existing per-face flavor-text switch into the OUTPUT section.

Run once from the ProxyStudio repository root:
    uv run python apply_flavor_output_move.py

The renderer and toggle behavior are unchanged. A safety backup is saved in
~/ProxyStudio Backups (outside the Git repository).
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sys


QML_PATH = Path(__file__).resolve().parent / "src/gui/qml/views/StudioWorkspace.qml"
LEFT_START = (
    '                    RowLayout {\n'
    '                        Layout.fillWidth: true\n'
    '                        spacing: 8\n'
    '                        Text { text: "Flavor text"; color: "#c4cbd0"; font.pixelSize: 12; Layout.fillWidth: true }\n'
)
LEFT_END = '                    StudioArea {\n                        id: flavorText\n'
OLD_SWITCH_START = '                        Switch {\n                            id: includeFlavorSwitch\n'
ROW_END = '                    }\n'
OUTPUT_HEADER = (
    '                    Text {\n'
    '                        text: "OUTPUT"\n'
    '                        font.pixelSize: 11\n'
    '                        font.bold: true\n'
    '                        color: "#a8b5bd"\n'
    '                    }\n'
)


def update_qml(source: str) -> str:
    if 'text: "Include flavor text"' in source and LEFT_START not in source:
        return source  # Already patched; safe to rerun.

    if source.count(LEFT_START) != 1 or source.count(LEFT_END) != 1:
        raise ValueError("Expected the existing Flavor text header and toggle, but could not find them exactly once. No changes made.")
    if source.count(OUTPUT_HEADER) != 1:
        raise ValueError("Expected exactly one OUTPUT section. No changes made.")
    if source.count('id: includeFlavorSwitch') != 1:
        raise ValueError("Expected exactly one Include flavor text switch. No changes made.")

    start = source.index(LEFT_START)
    end = source.index(LEFT_END, start)
    old_block = source[start:end]
    if old_block.count(OLD_SWITCH_START) != 1 or not old_block.endswith(ROW_END):
        raise ValueError("Flavor-text switch markup was changed. No changes made.")

    switch_start = old_block.index(OLD_SWITCH_START)
    # Keep the existing Switch, its styling, its mouse cursor, and critically
    # its onToggled handler (which saves the setting to the selected face).
    switch_markup = old_block[switch_start:-len(ROW_END)]
    if 'workspace.captureCurrentFace()' not in switch_markup:
        raise ValueError("The existing per-face change handler was not found. No changes made.")

    source = source[:start] + (
        '                    Text { text: "Flavor text"; color: "#c4cbd0"; font.pixelSize: 12 }\n'
    ) + source[end:]

    output_row = (
        '                    RowLayout {\n'
        '                        Layout.fillWidth: true\n'
        '                        spacing: 8\n'
        '                        Text {\n'
        '                            text: "Include flavor text"\n'
        '                            color: "#c4cbd0"\n'
        '                            font.pixelSize: 12\n'
        '                            Layout.fillWidth: true\n'
        '                        }\n'
        + switch_markup
        + '                    }\n'
    )
    source = source.replace(OUTPUT_HEADER, OUTPUT_HEADER + output_row, 1)

    if source.count('id: includeFlavorSwitch') != 1 or source.count('text: "Include flavor text"') != 1:
        raise ValueError("Post-patch validation failed. No changes made.")
    return source


def main() -> int:
    if not QML_PATH.is_file():
        print(f"ERROR: Could not find {QML_PATH}\nExtract this installer into your ProxyStudio project root.", file=sys.stderr)
        return 1

    try:
        original = QML_PATH.read_text(encoding="utf-8")
        updated = update_qml(original)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if updated == original:
        print("Already installed — the Include flavor text toggle is in OUTPUT.")
        return 0

    backups = Path.home() / "ProxyStudio Backups"
    backups.mkdir(parents=True, exist_ok=True)
    backup = backups / f"StudioWorkspace.before-flavor-output.{datetime.now():%Y%m%d-%H%M%S}.qml"
    shutil.copy2(QML_PATH, backup)
    QML_PATH.write_text(updated, encoding="utf-8", newline="")
    print("Success: Moved Include flavor text into the always-visible OUTPUT settings.")
    print("Single-face and per-face toggle behavior remain unchanged.")
    print(f"Backup: {backup}")
    print(f"Modified: {QML_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
