#!/usr/bin/env python3
"""Fix the Studio right-panel footer hiding its parent's bottom border.

Run from the ProxyStudio repository root:
    uv run python install_footer_border_fix_v1.py

This patch only changes the fixed footer Rectangle in StudioWorkspace.qml.
It works whether or not the recent Borderless toggle-spacing patch was applied.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "src" / "gui" / "qml" / "views" / "StudioWorkspace.qml"

OLD = '''            // Persistent action area — stays visible while settings scroll.
            // One grouped status card replaces the scattered status/footer lines.
            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                height: workspace.renderStatusDetail.length > 0 ? 166 : 128
                radius: 10
                color: "#1d2124"
'''
NEW = '''            // Persistent action area — stays visible while settings scroll.
            // One grouped status card replaces the scattered status/footer lines.
            Rectangle {
                // Inset the footer so it cannot paint over the parent panel border.
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                anchors.leftMargin: 1
                anchors.rightMargin: 1
                anchors.bottomMargin: 1
                height: workspace.renderStatusDetail.length > 0 ? 166 : 128
                radius: 9
                color: "#1d2124"
'''

def apply_patch(source: str) -> str:
    if source.count(NEW) == 1:
        return source
    if source.count(OLD) != 1:
        raise ValueError(
            f"Expected exactly one original Studio fixed footer; found {source.count(OLD)}. "
            "No changes made."
        )
    updated = source.replace(OLD, NEW, 1)
    if updated.count(NEW) != 1:
        raise ValueError("Patched footer validation failed; no changes made.")
    return updated

def main() -> int:
    if not TARGET.is_file():
        print(f"ERROR: Could not find {TARGET}")
        print("Extract this installer beside main.py in your ProxyStudio project.")
        return 1
    try:
        original = TARGET.read_text(encoding="utf-8")
        updated = apply_patch(original)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"ERROR: {error}")
        return 1
    if updated == original:
        print("[OK] Studio footer border fix is already installed. No changes needed.")
        return 0
    backup_dir = ROOT / ".git" / "proxystudio-patch-backups" / "footer-border-v1"
    if not (ROOT / ".git").exists():
        backup_dir = ROOT / ".proxystudio-patch-backups" / "footer-border-v1"
    backup = backup_dir / f"StudioWorkspace.{datetime.now():%Y%m%d-%H%M%S-%f}.qml"
    temp = TARGET.with_suffix(".qml.footer_border_pending")
    try:
        backup_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(TARGET, backup)
        temp.write_text(updated, encoding="utf-8", newline="")
        temp.replace(TARGET)
    except OSError as error:
        print(f"ERROR writing patch: {error}")
        try:
            temp.unlink(missing_ok=True)
        except OSError:
            pass
        print(f"Original backed up at: {backup}")
        return 1
    print("[OK] Studio right-panel border now remains visible behind its fixed footer.")
    print("Only StudioWorkspace.qml was changed; no settings or rendering code modified.")
    print(f"Backup: {backup}")
    print("Start app with: uv run main.py")
    return 0

if __name__ == "__main__":
    sys.exit(main())
