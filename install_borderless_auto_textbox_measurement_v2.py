#!/usr/bin/env python3
"""ProxyStudio: accurate Borderless Automatic textbox selection (V2).

Run in the repository root:
    uv run python install_borderless_auto_textbox_measurement_v2.py

Only patches BorderlessVectorTemplate.size in src/templates/normal.py.
Does not change text formatting, font sizes, rules text, or manual textbox sizes.
"""
from __future__ import annotations

import ast
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / 'src' / 'templates' / 'normal.py'
BACKUP_DIR = ROOT / '.git' / 'proxystudio-patch-backups'
START = '    @cached_property\n    def size(self) -> str:\n'
END = '    @cached_property\n    def color_limit(self) -> int:\n'
VERSION_MARKER = 'Borderless Automatic measurement V2'

UPDATED = '''    @cached_property
    def size(self) -> str:
        """Select a Borderless textbox without altering the card's typography.

        Automatic prefers the renderer's actual wrapped lines over the old
        rendered-bounds / leading approximation (which can overcount lines).
        If the line metadata is unavailable, use the existing line thresholds,
        with a bounded, measured Normal-box fit check before selecting Tall.
        """
        if self.is_textless:
            return BorderlessTextbox.Textless

        size = str(
            self.config.get_option(
                section="FRAME", key="Textbox.Size",
                enum_class=BorderlessTextbox,
                default=BorderlessTextbox.Automatic,
            )
        )
        if size != BorderlessTextbox.Automatic:
            return size  # Manual Short/Medium/Normal/Tall always wins.
        if self.is_basic_land:
            return BorderlessTextbox.Short

        test_layer = psd.getLayer(
            self.text_layer_rules_name, [self.text_group, "Tall"]
        )
        if not test_layer:
            getLogger(__name__).warning(
                "Borderless Automatic measurement V2: missing Tall rules layer; "
                "using Tall (%s)", self.layout.name,
            )
            return BorderlessTextbox.Tall

        # The rendered rules-text formatter handles real line wrapping.
        # Probe the same PSD text layer without changing font size/leading.
        test_text = self.layout.oracle_text or ""
        flavor_text = self.layout.flavor_text or ""
        if flavor_text:
            test_text += f"\\r{flavor_text}"
        test_layer.textItem.contents = test_text.replace("\\n", "\\r")

        # Read the calculated glyph bounds before asking PhotoCraft for its
        # wrapped lines; this also ensures the text layer has been laid out.
        approximate = get_line_count(test_layer, self.docref)
        measured = approximate
        method = "bounds/leading approximation"

        type_lines = getattr(test_layer, "_type_lines", None)
        if isinstance(type_lines, list) and type_lines:
            # PhotoCraft's _type_lines entries describe actual wrapped lines.
            # Blank spacer rows still take room, so count all valid entries.
            valid_lines = [
                line for line in type_lines
                if isinstance(line, dict)
                and isinstance(line.get("start"), int)
                and isinstance(line.get("end"), int)
                and line["end"] >= line["start"]
            ]
            if valid_lines:
                measured = len(valid_lines)
                method = "actual wrapped lines"

        # A flavor divider uses some vertical spacing. The text's own wrapped
        # lines already include the flavor paragraph; count only the divider,
        # not the flavor text twice.
        if flavor_text and self.layout.oracle_text:
            measured += 1

        if measured < 5:
            chosen = BorderlessTextbox.Short
        elif measured < 6:
            chosen = BorderlessTextbox.Medium
        elif measured < 8:
            chosen = BorderlessTextbox.Normal
        else:
            chosen = BorderlessTextbox.Tall

        # Conservative fallback for inflated layer-bound measurements:
        # if the measured text is close to fitting the PSD's actual Normal
        # reference height, choose Normal and let the *existing* text fitter
        # make its usual small reductions if necessary. Do not apply a text
        # size change here or rely on character-count guesses.
        normal_reference_height = None
        text_height = None
        if chosen == BorderlessTextbox.Tall and method != "actual wrapped lines":
            reference_group = psd.getLayerSet(
                LAYERS.TEXTBOX_REFERENCE, self.text_group
            )
            normal_ref = (
                psd.get_reference_layer(BorderlessTextbox.Normal, reference_group)
                if reference_group else None
            )
            if normal_ref:
                normal_reference_height = normal_ref.dims.get("height")
                text_height = psd.get_layer_height(test_layer)
                # Permit up to 10% normal text-fitting reduction. This only
                # chooses the textbox; it never increases the native font.
                if (normal_reference_height and text_height
                        and measured <= 9
                        and text_height <= normal_reference_height * 1.10):
                    chosen = BorderlessTextbox.Normal
                    method += " + Normal height fit"

        getLogger(__name__).info(
            "Borderless Automatic measurement V2: %s lines (prior estimate %s), "
            "method=%s, text-height=%s, normal-reference-height=%s, "
            "selected=%s, card=%s",
            measured, approximate, method, text_height,
            normal_reference_height, chosen, self.layout.name,
        )
        return chosen

'''


def patch(text: str) -> str:
    if VERSION_MARKER in text:
        return text
    if text.count(START) != 1 or END not in text:
        raise ValueError('Expected Borderless method anchors; no files changed.')
    start = text.index(START)
    end = text.index(END, start)
    current = text[start:end]
    # Guard against unrelated branch revisions.
    expected_parts = (
        'test_layer = psd.getLayer(',
        'num = get_line_count(test_layer, self.docref)',
        'elif num < 8:',
        '"Borderless Automatic textbox: %s measured lines -> %s (%s)"',
    )
    for part in expected_parts:
        if part not in current:
            raise ValueError(f'Current branch differs from the verified version ({part!r}); no files changed.')
    return text[:start] + UPDATED + text[end:]


def main() -> int:
    if not TARGET.is_file() or not (ROOT / '.git').is_dir():
        print('[ERROR] Extract installer to the ProxyStudio repository root first.')
        return 1
    try:
        original = TARGET.read_text(encoding='utf-8')
        revised = patch(original)
        ast.parse(revised, filename=str(TARGET))
    except (OSError, UnicodeError, SyntaxError, ValueError) as error:
        print(f'[ERROR] {error}')
        return 1
    if original == revised:
        print('[OK] Borderless Automatic measurement V2 is already installed.')
        return 0
    try:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        backup = BACKUP_DIR / 'normal.py.before-borderless-auto-v2.bak'
        if not backup.exists():
            shutil.copy2(TARGET, backup)
        TARGET.write_text(revised, encoding='utf-8')
    except OSError as error:
        print(f'[ERROR] Could not install: {error}')
        return 1
    print('[OK] Updated Borderless Automatic size selection.')
    print('[OK] No changes to fonts, word wrapping, or manual textbox sizes.')
    print(f'[OK] Backup: {backup}')
    print('      Re-render Chatterfang and review the Automatic measurement V2 log.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
