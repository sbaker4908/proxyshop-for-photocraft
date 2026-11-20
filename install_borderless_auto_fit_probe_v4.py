#!/usr/bin/env python3
"""ProxyStudio: Borderless Automatic textbox selection using render-fitted text.

Run from ProxyStudio repository root:
    uv run python install_borderless_auto_fit_probe_v4.py

Only replaces BorderlessVectorTemplate.size in src/templates/normal.py.
Manual Short/Medium/Normal/Tall selection is preserved, and formatting of
finished renders is unchanged. Safely handles locally installed V1/V2/V3.
"""
from __future__ import annotations

import ast
from datetime import datetime
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / 'src' / 'templates' / 'normal.py'
START = '    @cached_property\n    def size(self) -> str:\n'
END = '    @cached_property\n    def color_limit(self) -> int:\n'
MARKER = 'Borderless Automatic fit probe V4'

NEW_METHOD = '''    @cached_property
    def size(self) -> str:
        """Select the smallest Borderless box that keeps rules text readable.

        The old Automatic algorithm measured *unfitted* text in a Tall text
        layer, then used fixed wrapped-line thresholds. This misclassifies
        Chatterfang as Tall even though the real renderer fits it in Normal.

        For Automatic only, we now dry-run the SAME FormattedTextArea formatter
        used for a real card, on temporary copies of the PSD text layers.
        Choose the shortest box whose fitted font is reasonably close to the
        font in a Tall box. Actual render typography is never touched.
        """
        if self.is_textless:
            return BorderlessTextbox.Textless

        requested = str(
            self.config.get_option(
                section="FRAME",
                key="Textbox.Size",
                enum_class=BorderlessTextbox,
                default=BorderlessTextbox.Automatic,
            )
        )
        if requested != BorderlessTextbox.Automatic:
            return requested
        if self.is_basic_land:
            return BorderlessTextbox.Short

        log = getLogger(__name__)
        from src.helpers.text import get_font_size

        reference_group = psd.getLayerSet(LAYERS.TEXTBOX_REFERENCE, self.text_group)
        all_sizes = (
            BorderlessTextbox.Short,
            BorderlessTextbox.Medium,
            BorderlessTextbox.Normal,
            BorderlessTextbox.Tall,
        )

        def probe(candidate: str) -> tuple[float, float] | None:
            """Read initial/fitted font sizes without changing source layers."""
            if reference_group is None:
                return None
            original = psd.getLayer(
                self.text_layer_rules_name, [self.text_group, candidate]
            )
            reference = psd.get_reference_layer(candidate, reference_group)
            if original is None or reference is None:
                return None

            copy = None
            try:
                copy = original.duplicate()
                copy.visible = True
                initial_font = float(get_font_size(copy))
                formatter = FormattedTextArea(
                    layer=copy,
                    contents=self.layout.oracle_text or "",
                    flavor=self.layout.flavor_text or "",
                    reference=reference,
                    pt_reference=self.pt_reference,
                )
                if not formatter.validate():
                    return None
                formatter.execute()
                fitted_font = float(get_font_size(copy))
                if initial_font <= 0 or fitted_font <= 0:
                    return None
                return initial_font, fitted_font
            finally:
                # The original PSD layers and finished card remain untouched.
                if copy is not None:
                    copy.remove()

        try:
            # Tall provides our baseline for an acceptable, authentic text size.
            tall = probe(BorderlessTextbox.Tall)
            if tall is not None:
                # Relative to the actual fitted Tall font, not the initial
                # unscaled layer bounds. A modest reduction is acceptable:
                # forced Normal Chatterfang demonstrates this in practice.
                min_legible_ratio = 0.80
                baseline = tall[1]
                records = []
                for candidate in all_sizes[:-1]:
                    result = probe(candidate)
                    if result is None:
                        records.append((str(candidate), "unavailable"))
                        continue
                    initial, fitted = result
                    font_ratio = fitted / baseline
                    records.append((str(candidate), round(font_ratio, 3)))
                    if fitted >= baseline * min_legible_ratio:
                        log.info(
                            "Borderless Automatic fit probe V4: "
                            "selected=%s, Tall font=%.2f, selected font=%.2f, "
                            "relative=%.3f, candidates=%s, card=%s",
                            candidate, baseline, fitted, font_ratio,
                            records, self.layout.name,
                        )
                        return candidate
                log.info(
                    "Borderless Automatic fit probe V4: selected=Tall, "
                    "Tall font=%.2f, candidates=%s, card=%s",
                    baseline, records, self.layout.name,
                )
                return BorderlessTextbox.Tall
        except Exception:
            log.exception(
                "Borderless Automatic fit probe V4: formatter probe unavailable "
                "for %s; falling back to line-count selection",
                self.layout.name,
            )

        # Graceful fallback for PhotoCraft builds that do not support probing
        # copies of text layers. Unlike the original, allow up to ten measured
        # lines in Normal when there is no flavor divider. This is grounded
        # by the successful manual Normal render of ten-line Chatterfang;
        # unusually long cards and flavor cards remain conservative.
        test_layer = psd.getLayer(
            self.text_layer_rules_name, [self.text_group, BorderlessTextbox.Tall]
        )
        if test_layer is None:
            return BorderlessTextbox.Tall
        copy = None
        try:
            copy = test_layer.duplicate()
            copy.textItem.contents = (
                (self.layout.oracle_text or "")
                + ("\\r" + self.layout.flavor_text if self.layout.flavor_text else "")
            ).replace("\\n", "\\r")
            measured = get_line_count(copy, self.docref)
            flavor = bool(self.layout.flavor_text)
            if flavor:
                measured += 1
            if measured < 5:
                chosen = BorderlessTextbox.Short
            elif measured < 6:
                chosen = BorderlessTextbox.Medium
            elif measured <= (7 if flavor else 10):
                chosen = BorderlessTextbox.Normal
            else:
                chosen = BorderlessTextbox.Tall
            log.info(
                "Borderless Automatic fit probe V4: fallback=%s, "
                "measured=%s, flavor=%s, card=%s",
                chosen, measured, flavor, self.layout.name,
            )
            return chosen
        except Exception:
            log.exception("Borderless Automatic fallback failed for %s", self.layout.name)
            return BorderlessTextbox.Tall
        finally:
            if copy is not None:
                copy.remove()

'''


def install_text(source: str) -> str:
    matches = source.count(START)
    if matches != 1:
        raise ValueError(f'Expected exactly one Borderless size method, found {matches}. No changes made.')
    start = source.index(START)
    end = source.find(END, start)
    if end == -1:
        raise ValueError('Cannot locate next Borderless property. No changes made.')
    current = source[start:end]
    if MARKER in current:
        return source
    # Guard the patch so new upstream code does not get replaced silently.
    if ('BorderlessTextbox.Automatic' not in current
        or 'get_line_count' not in current
        and 'measurement V3' not in current):
        raise ValueError('Unknown Borderless size implementation; refusing to patch.')
    return source[:start] + NEW_METHOD + source[end:]


def main() -> int:
    if not TARGET.is_file() or not (ROOT / '.git').is_dir():
        print('[ERROR] Extract the installer into the root of your ProxyStudio Git repository.')
        return 1
    try:
        original = TARGET.read_text(encoding='utf-8')
        modified = install_text(original)
        ast.parse(modified, filename=str(TARGET))
    except (OSError, UnicodeError, ValueError, SyntaxError) as exc:
        print(f'[ERROR] Installation cancelled: {exc}')
        return 1

    if modified == original:
        print('[OK] Borderless Automatic V4 is already installed.')
        return 0

    try:
        backup_dir = ROOT / '.git' / 'proxystudio-patch-backups'
        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        backup_path = backup_dir / f'normal.py.before-borderless-v4.{timestamp}.bak'
        shutil.copy2(TARGET, backup_path)
        TARGET.write_text(modified, encoding='utf-8')
    except OSError as exc:
        print(f'[ERROR] Failed writing patch: {exc}')
        return 1

    print('[OK] Installed Borderless Automatic fitted-text selection V4.')
    print('[OK] Changed only src/templates/normal.py; manual options and render text are untouched.')
    print('[OK] Backup:', backup_path)
    print('[NEXT] Render Chatterfang with Automatic and check the V4 line in the app log.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
