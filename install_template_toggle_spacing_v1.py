#!/usr/bin/env python3
"""Match Borderless template switch spacing to Studio Output switches.

Run from anywhere: uv run python install_template_toggle_spacing_v1.py
Only modifies src/gui/qml/views/StudioWorkspace.qml in the repository.
Creates a timestamped backup inside .git/proxystudio-patch-backups/.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "src/gui/qml/views/StudioWorkspace.qml"


class PatchError(Exception):
    pass


def patch(source: str) -> str:
    # Scope all modifications to the Borderless-specific template options.
    begin_marker = "// Template-specific options appear only when the selected"
    end_marker = 'text: "OUTPUT"'
    if source.count(begin_marker) != 1 or source.count(end_marker) != 1:
        raise PatchError("Could not uniquely locate Template Options and Output sections.")
    start = source.index(begin_marker)
    end = source.index(end_marker, start)
    chunk = source[start:end]

    # Nested Template Options previously overrode the shared 8px spacing.
    old_column = (
        "ColumnLayout {\n"
        "                        Layout.fillWidth: true\n"
        "                        visible: workspace.showBorderlessOptions\n"
        "                        spacing: 11"
    )
    new_column = old_column.replace("spacing: 11", "spacing: workspace.panelSpacing")
    if chunk.count(old_column) == 1:
        chunk = chunk.replace(old_column, new_column, 1)
    elif chunk.count(new_column) != 1:
        raise PatchError("Unexpected Borderless ColumnLayout structure; no files changed.")

    # Output switches have implicitHeight: 23. Add the same to Borderless
    # switches, which otherwise use the platform's taller default height.
    for switch_id in ("borderlessTextlessSwitch", "borderlessShadowSwitch"):
        original = (
            "Switch {\n"
            f"                                id: {switch_id}\n"
            '                                text: ""\n'
            "                                enabled:"
        )
        updated = original.replace(
            '                                text: ""\n',
            '                                text: ""\n                                implicitHeight: 23\n',
        )
        if chunk.count(original) == 1:
            chunk = chunk.replace(original, updated, 1)
        elif chunk.count(updated) != 1:
            raise PatchError(f"Unexpected {switch_id} definition; no files changed.")

    result = source[:start] + chunk + source[end:]
    # Guard against accidental changes to existing Output switch layout.
    if result[result.index(end_marker):] != source[source.index(end_marker):]:
        raise PatchError("Output section unexpectedly changed; no files changed.")
    return result


def main() -> int:
    if not TARGET.is_file():
        print(f"ERROR: Studio QML not found: {TARGET}")
        print("Place this installer beside main.py in your ProxyStudio project.")
        return 1
    try:
        original = TARGET.read_text(encoding="utf-8")
        updated = patch(original)
        if updated == original:
            print("[OK] Borderless toggle spacing is already aligned. Nothing changed.")
            return 0

        backup_dir = (
            ROOT / ".git/proxystudio-patch-backups/template-toggle-spacing-v1"
            if (ROOT / ".git").is_dir()
            else ROOT / ".proxystudio-patch-backups/template-toggle-spacing-v1"
        )
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup = backup_dir / (
            "StudioWorkspace."
            + datetime.now().strftime("%Y%m%d-%H%M%S-%f")
            + ".qml"
        )
        shutil.copy2(TARGET, backup)
        temp = TARGET.with_name(TARGET.name + ".toggle_spacing_tmp")
        try:
            temp.write_text(updated, encoding="utf-8", newline="")
            temp.replace(TARGET)
        finally:
            temp.unlink(missing_ok=True)
    except (OSError, UnicodeError, PatchError) as exc:
        print(f"ERROR: {exc}")
        print("If no backup path was printed, project files were not changed.")
        return 1

    print("[OK] Borderless switch spacing now matches Output switches.")
    print("    - Template Options inner spacing uses panelSpacing (8px)")
    print("    - Textless and Drop Shadow switch heights set to 23px")
    print(f"Backup: {backup}")
    print("Launch normally: uv run main.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
