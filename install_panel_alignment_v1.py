#!/usr/bin/env python3
"""Align Studio's three panels and both Trim panels to one visual rhythm.

From the ProxyStudio project root:
    uv run python install_panel_alignment_v1.py

Only edits:
    src/gui/qml/views/StudioWorkspace.qml
    src/gui/qml/views/TrimWorkspace.qml

The script validates both complete patches before writing either file, backs up
both originals, and attempts to restore both if replacing a file fails.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import os
import shutil
import sys

ROOT = Path(__file__).resolve().parent
STUDIO = ROOT / 'src/gui/qml/views/StudioWorkspace.qml'
TRIM = ROOT / 'src/gui/qml/views/TrimWorkspace.qml'
MARKER = '    // Shared Studio / Trim panel alignment V1.'


class PatchError(Exception):
    pass


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise PatchError(f'{label}: expected exactly one match, found {count}.')
    return text.replace(old, new, 1)


def divided(text: str, *markers: str) -> list[str]:
    """Split by unique ordered comment anchors, retaining each marker."""
    positions = []
    for m in markers:
        if text.count(m) != 1:
            raise PatchError(f'Expected exactly one section marker {m!r}.')
        positions.append(text.index(m))
    if positions != sorted(positions):
        raise PatchError('QML panel sections have changed order.')
    return [text[a:b] for a, b in zip([0, *positions], [*positions, len(text)])]


def make_metrics() -> str:
    return '''    // Shared Studio / Trim panel alignment V1.
    // Keep these values identical in StudioWorkspace and TrimWorkspace.
    readonly property int panelPadding: 18
    readonly property int panelSpacing: 11
    readonly property int panelHeadingHeight: 32
    readonly property int panelHeadingFontSize: 20
    readonly property int panelSubtitleFontSize: 12
    readonly property int panelSubtitleMinHeight: 32
    readonly property int panelSubtitleBottomMargin: 10
'''


def make_description(indent: str, description: str, color: str) -> str:
    return f'''{indent}Text {{
{indent}    Layout.fillWidth: true
{indent}    Layout.preferredHeight: Math.max(workspace.panelSubtitleMinHeight, implicitHeight)
{indent}    Layout.bottomMargin: workspace.panelSubtitleBottomMargin
{indent}    text: {description}
{indent}    color: {color}
{indent}    font.pixelSize: workspace.panelSubtitleFontSize
{indent}    wrapMode: Text.WordWrap
{indent}}}'''


def patch_studio(source: str) -> str:
    if MARKER in source:
        raise PatchError('Studio panel alignment V1 is already installed.')
    source = once(source, 'Item {\n    id: workspace\n',
                  'Item {\n    id: workspace\n\n' + make_metrics(), 'Studio layout metrics')
    before, left, center, right = divided(
        source, '// LEFT: Card editor', '// CENTER: Automatically refreshed PhotoCraft exports.',
        '// RIGHT: Template selection and Studio-only render controls.'
    )
    # Left: same header row, paragraph space and baseline as center/right.
    left = once(left, 'anchors.margins: 18\n', 'anchors.margins: workspace.panelPadding\n', 'Studio editor inset')
    left = once(left, 'width: editorScroll.availableWidth\n                    spacing: 9',
                'width: editorScroll.availableWidth\n                    spacing: workspace.panelSpacing', 'Studio editor rhythm')
    left = once(left,
        'Text { text: "Card Details"; font.pixelSize: 20; font.bold: true; color: "#f5f6f7" }',
        '''Text {
                        Layout.preferredHeight: workspace.panelHeadingHeight
                        text: "Card Details"
                        font.pixelSize: workspace.panelHeadingFontSize
                        font.bold: true
                        color: "#f5f6f7"
                        verticalAlignment: Text.AlignVCenter
                    }''', 'Studio editor heading')
    left = once(left,
        '''                    Text {
                        text: "Find an existing card or create one from scratch."
                        color: workspace.muted
                        font.pixelSize: 12
                        Layout.fillWidth: true
                        Layout.bottomMargin: 10
                        wrapMode: Text.WordWrap
                    }''',
        make_description('                    ', '"Find an existing card or create one from scratch."', 'workspace.muted'),
        'Studio editor subtitle')
    # Center: header contains a folder button; reserve the same 32px height as all headings.
    center = once(center, 'anchors.margins: 18\n', 'anchors.margins: workspace.panelPadding\n', 'Studio preview inset')
    center = once(center,
        'anchors.margins: workspace.panelPadding\n                spacing: 11',
        'anchors.margins: workspace.panelPadding\n                spacing: workspace.panelSpacing',
        'Studio preview rhythm')
    center = once(center,
        '''                RowLayout {
                    Layout.fillWidth: true
                    spacing: 9

                    Text {
                        text: "Card Preview"
                        color: "#f5f6f7"
                        font.pixelSize: 20
                        font.bold: true
                    }''',
        '''                RowLayout {
                    Layout.fillWidth: true
                    Layout.preferredHeight: workspace.panelHeadingHeight
                    spacing: 9

                    Text {
                        text: "Card Preview"
                        color: "#f5f6f7"
                        font.pixelSize: workspace.panelHeadingFontSize
                        font.bold: true
                        Layout.alignment: Qt.AlignVCenter
                    }''', 'Studio preview heading')
    center = once(center,
        '''                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.minimumHeight: 230
                    radius: 8''',
        make_description('                ', '"Your latest Studio render appears here."', 'workspace.muted') + '''

                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.minimumHeight: 230
                    radius: 8''', 'Studio preview subtitle')
    # Right: render settings follow exact same header and subtitle metrics.
    right = once(right, 'anchors.margins: 18\n', 'anchors.margins: workspace.panelPadding\n', 'Studio render settings inset')
    right = once(right,
        '''                    spacing: 11
                    Text { text: "Render Settings"; color: "#f5f6f7"; font.pixelSize: 20; font.bold: true }''',
        '''                    spacing: workspace.panelSpacing
                    Text {
                        Layout.preferredHeight: workspace.panelHeadingHeight
                        text: "Render Settings"
                        color: "#f5f6f7"
                        font.pixelSize: workspace.panelHeadingFontSize
                        font.bold: true
                        verticalAlignment: Text.AlignVCenter
                    }''', 'Studio render settings heading and rhythm')
    right = once(right,
        '''                    Text {
                        text: workspace.isDualFace ? "Choose a frame supporting both faces."
                            : workspace.isPlaneswalker ? "Choose an installed planeswalker frame."
                            : "Choose an installed frame for your card."
                        color: workspace.muted
                        font.pixelSize: 12
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                        Layout.bottomMargin: 12
                    }''',
        make_description('                    ', '''workspace.isDualFace ? "Choose a frame supporting both faces."
                            : workspace.isPlaneswalker ? "Choose an installed planeswalker frame."
                            : "Choose an installed frame for your card."''', 'workspace.muted'),
        'Studio render settings subtitle')
    result = ''.join((before, left, center, right))
    if result.count(MARKER) != 1 or result.count('panelSubtitleMinHeight') != 4:
        raise PatchError('Studio alignment post-check failed.')
    return result


def patch_trim(source: str) -> str:
    if MARKER in source:
        raise PatchError('Trim panel alignment V1 is already installed.')
    source = once(source, 'Item {\n    id: workspace\n',
                  'Item {\n    id: workspace\n\n' + make_metrics(), 'Trim layout metrics')
    before, left, right = divided(
        source, '// Controls and source information', '// Original-versus-trimmed card preview'
    )
    left = once(left, 'anchors.margins: 18\n', 'anchors.margins: workspace.panelPadding\n', 'Trim controls inset')
    left = once(left,
        'anchors.margins: workspace.panelPadding\n                spacing: 9',
        'anchors.margins: workspace.panelPadding\n                spacing: workspace.panelSpacing', 'Trim controls rhythm')
    left = once(left,
        '''                Text {
                    text: "Trim"
                    color: workspace.textPrimary
                    font.bold: true
                    font.pixelSize: 20
                }''',
        '''                Text {
                    Layout.preferredHeight: workspace.panelHeadingHeight
                    text: "Trim"
                    color: workspace.textPrimary
                    font.bold: true
                    font.pixelSize: workspace.panelHeadingFontSize
                    verticalAlignment: Text.AlignVCenter
                }''', 'Trim controls heading')
    left = once(left,
        '''                Text {
                    Layout.fillWidth: true
                    text: "Remove print bleed and round the corners of a completed card render."
                    color: workspace.textMuted
                    font.pixelSize: 12
                    Layout.bottomMargin: 10
                    wrapMode: Text.WordWrap
                }''',
        make_description('                ', '"Remove print bleed and round the corners of a completed card render."',
                         'workspace.textMuted'), 'Trim controls subtitle')
    right = once(right, 'anchors.margins: 18\n', 'anchors.margins: workspace.panelPadding\n', 'Trim preview inset')
    right = once(right,
        'anchors.margins: workspace.panelPadding\n                spacing: 11',
        'anchors.margins: workspace.panelPadding\n                spacing: workspace.panelSpacing', 'Trim preview rhythm')
    right = once(right,
        '''                RowLayout {
                    Layout.fillWidth: true
                    spacing: 9

                    Text {
                        text: "Card Preview"
                        color: workspace.textPrimary
                        font.pixelSize: 20
                        font.bold: true
                    }''',
        '''                RowLayout {
                    Layout.fillWidth: true
                    Layout.preferredHeight: workspace.panelHeadingHeight
                    spacing: 9

                    Text {
                        text: "Card Preview"
                        color: workspace.textPrimary
                        font.pixelSize: workspace.panelHeadingFontSize
                        font.bold: true
                        Layout.alignment: Qt.AlignVCenter
                    }''', 'Trim preview heading')
    right = once(right,
        '''                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    radius: 8
                    color: "#242a2f"''',
        make_description('                ', '"Compare the original and trimmed card."', 'workspace.textMuted') + '''

                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    radius: 8
                    color: "#242a2f"''', 'Trim preview subtitle')
    result = ''.join((before, left, right))
    if result.count(MARKER) != 1 or result.count('panelSubtitleMinHeight') != 3:
        raise PatchError('Trim alignment post-check failed.')
    return result


def main() -> int:
    try:
        originals = {STUDIO: STUDIO.read_text(encoding='utf-8'),
                     TRIM: TRIM.read_text(encoding='utf-8')}
        updated = {STUDIO: patch_studio(originals[STUDIO]),
                   TRIM: patch_trim(originals[TRIM])}
    except (OSError, UnicodeError, PatchError) as exc:
        print(f'ERROR: {exc}\nNo project files were changed.')
        return 1
    base = ROOT / ('.git/proxystudio-patch-backups/panel-alignment-v1'
                   if (ROOT / '.git').is_dir() else '.proxystudio-patch-backups/panel-alignment-v1')
    dest = base / datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    temps = {}
    replaced = []
    try:
        dest.mkdir(parents=True, exist_ok=False)
        for path in originals:
            shutil.copy2(path, dest / path.name)
        for path, content in updated.items():
            temp = path.with_name(path.name + '.panel_alignment_v1_tmp')
            temp.write_text(content, encoding='utf-8', newline='')
            temps[path] = temp
        for path, temp in temps.items():
            os.replace(temp, path)
            replaced.append(path)
    except OSError as exc:
        for path in replaced:
            try:
                shutil.copy2(dest / path.name, path)
            except OSError as recovery:
                print('RESTORE FAILED for', path, recovery)
        print(f'ERROR: {exc}\nBackups: {dest}')
        return 1
    finally:
        for temp in temps.values():
            try:
                temp.unlink(missing_ok=True)
            except OSError:
                pass
    print('[OK] Aligned Studio (3 panels) and Trim (2 panels).')
    print('Both QML originals backed up to:', dest)
    print('Restart ProxyStudio with: uv run main.py')
    return 0


if __name__ == '__main__':
    sys.exit(main())
