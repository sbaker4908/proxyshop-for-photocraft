#!/usr/bin/env python3
"""ProxyStudio Borderless Automatic textbox measurement V3.

Fixes the V2 skipped Normal-fit probe. Uses nonblank wrapped-line spans when
available, and actually measures the Normal candidate against its PSD reference
before falling back to Tall. Does NOT change font sizing, line breaking, or
manual textbox sizes.

Install: extract to repository root, then:
    uv run python install_borderless_auto_measurement_v3.py
"""
from __future__ import annotations

import ast
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "src" / "templates" / "normal.py"
BACKUP_DIR = ROOT / ".git" / "proxystudio-patch-backups"
START = '    @cached_property\n    def size(self) -> str:\n'
END = '    @cached_property\n    def color_limit(self) -> int:\n'
V2_MARKER = 'Borderless Automatic measurement V2'
V3_MARKER = 'Borderless Automatic measurement V3'

UPDATED = '''    @cached_property
    def size(self) -> str:
        """Choose the smallest sensible Borderless textbox at native font size.

        Automatic reads PhotoCraft's wrapped-line spans when available. Some
        PhotoCraft text layers include empty spacer entries in `_type_lines`;
        these aren't visible text lines and shouldn't force a Tall box. If
        the line count still points to Tall, probe the Normal text layer and
        compare its rendered height with the actual Normal textbox reference.

        This method only selects frame layers: it never changes typography,
        scaling, line breaking, or the saved template configuration.
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
            return size
        if self.is_basic_land:
            return BorderlessTextbox.Short

        test_layer = psd.getLayer(
            self.text_layer_rules_name, [self.text_group, "Tall"]
        )
        if not test_layer:
            getLogger(__name__).warning(
                "Borderless Automatic measurement V3: missing Tall rules layer; "
                "using Tall (%s)", self.layout.name,
            )
            return BorderlessTextbox.Tall

        oracle = self.layout.oracle_text or ""
        flavor = self.layout.flavor_text or ""
        test_text = oracle + (f"\\r{flavor}" if flavor else "")
        normalized_text = test_text.replace("\\n", "\\r")
        test_layer.textItem.contents = normalized_text

        # Keep the old height-based count as a fallback for older PhotoCraft
        # installations without reliable wrapped-line metadata.
        approximate = get_line_count(test_layer, self.docref)
        visible_lines = None
        raw_lines = None
        lines = getattr(test_layer, "_type_lines", None)
        if isinstance(lines, list) and lines:
            valid = [
                item for item in lines
                if isinstance(item, dict)
                and isinstance(item.get("start"), int)
                and isinstance(item.get("end"), int)
                and 0 <= item["start"] <= item["end"] <= len(normalized_text)
            ]
            if valid:
                raw_lines = len(valid)
                # A paragraph separator or empty spacer record can occupy a
                # metadata row without being another printed line. Count
                # nonempty text spans only (the normal formatter already
                # handles real inter-paragraph spacing).
                occupied = [
                    item for item in valid
                    if normalized_text[item["start"]:item["end"]].strip()
                ]
                if occupied:
                    visible_lines = len(occupied)

        # Preserve old behavior if line metadata is missing, except that V2's
        # speculative extra flavor line is no longer added to wrapped spans.
        measured = visible_lines if visible_lines is not None else approximate
        if visible_lines is None and flavor and oracle:
            measured += 1

        if measured < 5:
            chosen = BorderlessTextbox.Short
        elif measured < 6:
            chosen = BorderlessTextbox.Medium
        elif measured < 8:
            chosen = BorderlessTextbox.Normal
        else:
            chosen = BorderlessTextbox.Tall

        # V2 never executed its fit-check when actual line metadata existed.
        # Always inspect the Normal candidate before giving up and using Tall.
        # Crucially, use the Normal text *layer* and Normal *reference* rather
        # than judging a Tall layer against a smaller textbox.
        normal_height = None
        normal_reference_height = None
        usable_height = None
        fit_ratio = None
        if chosen == BorderlessTextbox.Tall:
            references = psd.getLayerSet(LAYERS.TEXTBOX_REFERENCE, self.text_group)
            normal_ref = (
                psd.get_reference_layer(BorderlessTextbox.Normal, references)
                if references else None
            )
            normal_layer = psd.getLayer(
                self.text_layer_rules_name, [self.text_group, BorderlessTextbox.Normal]
            )
            if normal_ref and normal_layer:
                normal_layer.textItem.contents = normalized_text
                normal_height = psd.get_layer_height(normal_layer)
                bounds = normal_ref.dims
                normal_reference_height = float(bounds["height"])
                usable_height = normal_reference_height
                # In creature cards, the P/T box encroaches on the textbox.
                # Apply the same vertical limit used by FormattedTextArea.
                if self.is_creature and self.pt_reference:
                    pt_top = float(self.pt_reference.bounds[1])
                    top = float(bounds["top"])
                    if pt_top > top:
                        usable_height = min(usable_height, pt_top - top)
                # Same DPI-scaled safety margin as the existing rules-text
                # height fitter; not a change to the actual text formatter.
                margin = float(self.app.scale_by_dpi(64))
                usable_height = max(0.0, usable_height - margin)
                if usable_height > 0:
                    fit_ratio = float(normal_height) / usable_height
                    # Prefer Normal for a natural native-size fit, or a very
                    # small reduction that the ordinary text fitter already
                    # supports. This only chooses the textbox size.
                    if fit_ratio <= 1.12:
                        chosen = BorderlessTextbox.Normal

        getLogger(__name__).info(
            "Borderless Automatic measurement V3: raw=%s, nonblank=%s, "
            "prior=%s, Normal height=%s, reference=%s, usable=%s, ratio=%s, "
            "selected=%s, card=%s",
            raw_lines, visible_lines, approximate,
            normal_height, normal_reference_height, usable_height,
            round(fit_ratio, 3) if fit_ratio is not None else None,
            chosen, self.layout.name,
        )
        return chosen

'''


def patch(text: str) -> str:
    if text.count(START) != 1:
        raise ValueError("Borderless size method not found uniquely; nothing changed.")
    start = text.index(START)
    end = text.index(END, start)
    current = text[start:end]
    if V3_MARKER in current:
        return text
    if V2_MARKER not in current or 'method != "actual wrapped lines"' not in current:
        raise ValueError(
            "Expected installed V2 textbox code, but it differs. "
            "No files changed. Confirm the V2 patch is installed first."
        )
    return text[:start] + UPDATED + text[end:]


def main() -> int:
    if not TARGET.is_file() or not (ROOT / ".git").is_dir():
        print("[ERROR] Extract this installer into the root of your ProxyStudio Git repository.")
        return 1
    try:
        original = TARGET.read_text(encoding="utf-8")
        modified = patch(original)
        ast.parse(modified, filename=str(TARGET))
    except (OSError, UnicodeError, ValueError, SyntaxError) as exc:
        print(f"[ERROR] Installation cancelled: {exc}")
        return 1
    if modified == original:
        print("[OK] Borderless Auto measurement V3 is already installed.")
        return 0
    try:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        backup = BACKUP_DIR / "normal.py.before-borderless-auto-v3.bak"
        if not backup.exists():
            shutil.copy2(TARGET, backup)
        TARGET.write_text(modified, encoding="utf-8")
    except OSError as exc:
        print(f"[ERROR] Installation cancelled: {exc}")
        return 1
    print("[OK] Installed Borderless Automatic measurement V3.")
    print("[OK] Manual textbox sizes and all text rendering remain unchanged.")
    print("[OK] Backup:", backup)
    print("[NEXT] Re-render Chatterfang with Automatic and check the V3 log line.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
