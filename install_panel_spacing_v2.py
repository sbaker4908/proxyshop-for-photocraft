#!/usr/bin/env python3
"""Compact Studio and Trim panel-header spacing after panel alignment V1.

From the project root (next to main.py):
    uv run python install_panel_spacing_v2.py

Modifies only StudioWorkspace.qml and TrimWorkspace.qml. Both patches are
validated before writing, backups are created, and errors trigger rollback.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import os
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parent
FILES = (
    ROOT / "src/gui/qml/views/StudioWorkspace.qml",
    ROOT / "src/gui/qml/views/TrimWorkspace.qml",
)
V1_MARKER = "    // Shared Studio / Trim panel alignment V1."
V2_MARKER = "    // Compact Studio / Trim panel-header spacing V2."


class PatchError(Exception):
    pass


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise PatchError(f"{label}: expected exactly one match; found {count}.")
    return source.replace(old, new, 1)


def patch(source: str, filename: str) -> str:
    if V1_MARKER not in source:
        raise PatchError(f"{filename}: alignment V1 is not installed; install that patch first.")
    if source.count(V1_MARKER) != 1:
        raise PatchError(f"{filename}: ambiguous alignment V1 marker.")
    if V2_MARKER in source:
        return source  # Re-running the installer is harmless.

    # All five top-level panels use these same layout tokens; change the tokens,
    # rather than applying five unrelated sets of pixel offsets.  Heading rows
    # stay 32px high so the folder icon and the other titles remain aligned.
    source = replace_once(
        source,
        "    readonly property int panelPadding: 18\n",
        "    readonly property int panelPadding: 18\n"
        "    readonly property int panelTopPadding: 12\n",
        f"{filename} top-padding metric",
    )
    source = replace_once(source,
        "    readonly property int panelSpacing: 11\n",
        "    readonly property int panelSpacing: 8\n",
        f"{filename} panel-spacing metric")
    source = replace_once(source,
        "    readonly property int panelSubtitleMinHeight: 32\n",
        "    readonly property int panelSubtitleMinHeight: 18\n",
        f"{filename} subtitle-height metric")
    source = replace_once(source,
        "    readonly property int panelSubtitleBottomMargin: 10\n",
        "    readonly property int panelSubtitleBottomMargin: 2\n",
        f"{filename} subtitle-bottom-margin metric")
    source = replace_once(source, V1_MARKER,
        V1_MARKER + "\n" + V2_MARKER,
        f"{filename} version marker")

    # Leave left/right/bottom panel padding at 18px. Only the top edge is
    # tightened, using the same 12px inset for ALL Studio and Trim panels.
    expected_panels = 3 if filename == "StudioWorkspace.qml" else 2
    anchor = re.compile(r"(?m)^([ \t]*)anchors\.margins: workspace\.panelPadding$")
    count = len(anchor.findall(source))
    if count != expected_panels:
        raise PatchError(
            f"{filename}: expected {expected_panels} aligned panel insets, found {count}. "
            "The QML layout may have changed since V1."
        )
    source = anchor.sub(lambda match: (
        match.group(0) + "\n" + match.group(1)
        + "anchors.topMargin: workspace.panelTopPadding"
    ), source)

    # Existing QML binding remains dynamic: if a subtitle wraps at narrow
    # widths, Math.max(panelSubtitleMinHeight, implicitHeight) expands to fit.
    if source.count("Layout.preferredHeight: Math.max(workspace.panelSubtitleMinHeight, implicitHeight)") != expected_panels:
        raise PatchError(f"{filename}: expected {expected_panels} responsive subtitle elements.")
    if source.count(V2_MARKER) != 1 or source.count("anchors.topMargin: workspace.panelTopPadding") != expected_panels:
        raise PatchError(f"{filename}: compact header validation failed.")
    return source


def main() -> int:
    try:
        originals = {p: p.read_text(encoding="utf-8") for p in FILES}
        changed = {p: patch(originals[p], p.name) for p in FILES}
    except (OSError, UnicodeError, PatchError) as exc:
        print(f"ERROR: {exc}\nNo files changed.")
        return 1

    need = [p for p in FILES if originals[p] != changed[p]]
    if not need:
        print("[OK] Compact panel spacing V2 is already installed. No changes necessary.")
        return 0
    if len(need) != len(FILES):
        print("ERROR: Only one workspace has V2. Refusing to leave Studio and Trim inconsistent.")
        return 1

    backups = ROOT / (".git/proxystudio-patch-backups/panel-spacing-v2"
                      if (ROOT / ".git").is_dir()
                      else ".proxystudio-patch-backups/panel-spacing-v2")
    dest = backups / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    temps: dict[Path, Path] = {}
    replaced: list[Path] = []
    try:
        dest.mkdir(parents=True, exist_ok=False)
        for path in FILES:
            shutil.copy2(path, dest / path.name)
        for path in FILES:
            temp = path.with_name(path.name + ".panel_spacing_v2_tmp")
            temp.write_text(changed[path], encoding="utf-8", newline="")
            temps[path] = temp
        for path in FILES:
            os.replace(temps[path], path)
            replaced.append(path)
    except OSError as exc:
        for path in replaced:
            try:
                shutil.copy2(dest / path.name, path)
            except OSError as recovery:
                print(f"WARNING: Failed to restore {path}: {recovery}")
        print(f"ERROR: {exc}\nOriginal files backed up to: {dest}")
        return 1
    finally:
        for temp in temps.values():
            try:
                temp.unlink(missing_ok=True)
            except OSError:
                pass
    print("[OK] Tightened header and subtitle spacing across Studio (3 panels) and Trim (2 panels).")
    print("Original QML files backed up to:", dest)
    print("Restart ProxyStudio with: uv run main.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
