"""One-time, idempotent registration of the Trim tab in the existing App.qml.

Run from the repository root using `uv run python install_trim.py`.
This preserves the user's customized App.qml rather than replacing it.
"""
from __future__ import annotations

from pathlib import Path


APP = Path(__file__).resolve().parent / "src/gui/qml/App.qml"


def apply_trim_tab(text: str) -> tuple[str, list[str]]:
    changes: list[str] = []

    # Insert as the fourth tab; the last existing tab is Studio.
    if 'text: "Trim"' not in text:
        anchor = "            RowLayout {\n                parent: viewTabBar"
        if text.count(anchor) != 1 or 'text: "Studio"' not in text:
            raise ValueError("Could not locate the existing Studio tab. App.qml was not changed.")
        tab = '''            CustomTabButton {
                systemPalette: appSystemPalette
                text: "Trim"
                implicitHeight: viewTabBar.implicitHeight
                background.implicitHeight: viewTabBar.implicitHeight
            }

'''
        text = text.replace(anchor, tab + anchor, 1)
        changes.append("added Trim tab")

    if 'source: "views/TrimWorkspace.qml"' not in text:
        anchor = '''                Loader {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    source: "views/StudioWorkspace.qml"
                }'''
        if text.count(anchor) != 1:
            raise ValueError("Could not locate the Studio loader. App.qml was not changed.")
        next_loader = '''
                Loader {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    source: "views/TrimWorkspace.qml"
                }'''
        text = text.replace(anchor, anchor + next_loader, 1)
        changes.append("registered TrimWorkspace.qml")

    # Console is useful in legacy tabs but wastes space in both Studio and Trim.
    if "visible: viewTabBar.currentIndex !== 2" in text:
        text = text.replace(
            "visible: viewTabBar.currentIndex !== 2",
            "visible: viewTabBar.currentIndex < 2",
            1,
        )
        changes.append("hid console on Trim tab")
    elif "visible: viewTabBar.currentIndex < 2" not in text:
        raise ValueError("Unexpected console visibility rule. App.qml was not changed.")

    return text, changes


def main() -> None:
    if not APP.is_file():
        raise SystemExit(f"App.qml not found at {APP}")

    for path in (
        Path(__file__).parent / "src/gui/qml/views/TrimWorkspace.qml",
        Path(__file__).parent / "src/gui/qml/models/trim_model.py",
        Path(__file__).parent / "src/gui/qml/models/trim_processing.py",
    ):
        if not path.is_file():
            raise SystemExit(f"Trim file missing: {path}")

    original = APP.read_text(encoding="utf-8-sig")
    try:
        modified, changes = apply_trim_tab(original)
    except ValueError as error:
        raise SystemExit(f"Trim installer stopped safely: {error}") from error

    if modified != original:
        APP.write_text(modified, encoding="utf-8")
        print("Trim tab registered in src/gui/qml/App.qml:")
        for change in changes:
            print(f"  - {change}")
    else:
        print("Trim tab already installed. No App.qml changes needed.")
    print("You can now launch: uv run main.py")


if __name__ == "__main__":
    main()
