"""Install a targeted Borderless MDFC text-fit correction.

Run from the ProxyStudio project directory:
    uv run python install_borderless_mdfc_fix.py

Only patches src/templates/normal.py. Creates a one-time backup, and refuses to
modify the file if the expected upstream method has changed.
"""
from __future__ import annotations

import ast
from pathlib import Path
import shutil
import sys

OLD = '''        if (
            self.is_mdfc
            and ref
            and (
                layer := psd.getLayer(
                    LAYERS.MDFC, [self.mask_group, LAYERS.TEXTBOX_REFERENCE]
                )
            )
        ):
            psd.copy_layer_mask(layer_from=layer, layer_to=ref)
            psd.apply_mask(ref)
            ref.visible = False
        return ref
'''

NEW = '''        if (
            self.is_mdfc
            and ref
            and (
                layer := psd.getLayer(
                    LAYERS.MDFC, [self.mask_group, LAYERS.TEXTBOX_REFERENCE]
                )
            )
        ):
            psd.copy_layer_mask(layer_from=layer, layer_to=ref)
            psd.apply_mask(ref)
            ref.visible = False

        # A modal DFC has a reverse-face information bar across the bottom of
        # the text box. Its mask changes the visible reference shape, but a
        # reference layer's rectangular bounds can still extend into the bar.
        # FormattedTextArea uses those bounds to choose the font size, causing
        # longer flavor text to overlap the bar (e.g. Bala Ged Recovery).
        # Keep this adjustment limited to Borderless MDFC faces.
        if self.is_mdfc and ref:
            dims = ref.dims
            top = float(dims["top"])
            bottom = float(dims["bottom"])
            bar_top = None

            # Prefer the actual bar background, which is more accurate than
            # measuring its text. The named color layer is the same one used
            # when enabling the MDFC bar in MDFCMod.
            bar = psd.getLayer(
                self.mdfc_bar_color, [self.dfc_group, LAYERS.BOTTOM]
            )
            if bar:
                candidate = float(bar.bounds[1])
                if top < candidate < bottom:
                    bar_top = candidate

            # Some PhotoCraft versions report a vector layer's untrimmed
            # bounds. Fall back to the text already positioned on the strip.
            if bar_top is None:
                labels = [
                    layer for layer in (
                        self.text_layer_mdfc_left,
                        self.text_layer_mdfc_right,
                    ) if layer
                ]
                candidates = [
                    float(layer.bounds[1]) - self.app.scale_by_dpi(22)
                    for layer in labels
                ]
                candidates = [n for n in candidates if top < n < bottom]
                if candidates:
                    bar_top = min(candidates)

            if bar_top is not None:
                # A little breathing room above the bar, in document pixels.
                safe_bottom = int(bar_top - self.app.scale_by_dpi(22))
                # Never collapse the text area if a template's layer bounds
                # are unexpected; retain the original bounds in that case.
                if top + self.app.scale_by_dpi(80) < safe_bottom < bottom:
                    ref.dims = {
                        **dims,
                        "bottom": safe_bottom,
                        "height": safe_bottom - int(top),
                        "center_y": round((top + safe_bottom) / 2),
                    }
        return ref
'''

MARKER = "A modal DFC has a reverse-face information bar across the bottom"


def install(root: Path) -> None:
    path = root / "src" / "templates" / "normal.py"
    if not path.is_file():
        raise FileNotFoundError(
            f"Can't find {path}. Run this script from the ProxyStudio folder."
        )

    source = path.read_text(encoding="utf-8")
    if MARKER in source:
        print("Already installed: Borderless MDFC text-fit fix.")
        return
    if source.count(OLD) != 1:
        raise RuntimeError(
            "Expected Borderless textbox_reference code not found exactly once. "
            "No files changed. This installer will not overwrite your other work."
        )

    # Confirm the anchor belongs to BorderlessVectorTemplate, not another class.
    class_pos = source.find("class BorderlessVectorTemplate(")
    reference_pos = source.find(OLD)
    if class_pos < 0 or reference_pos < class_pos:
        raise RuntimeError("Could not verify the Borderless template location.")

    patched = source.replace(OLD, NEW, 1)
    ast.parse(patched, filename=str(path))
    backup = path.with_name("normal.py.pre_mdfc_text_fix.bak")
    if not backup.exists():
        shutil.copy2(path, backup)
    path.write_text(patched, encoding="utf-8")
    print(f"Patched: {path}")
    print(f"Backup:  {backup}")
    print("Restart ProxyStudio and re-render Bala Ged Recovery with Borderless.")


if __name__ == "__main__":
    try:
        install(Path.cwd())
    except Exception as exc:
        print(f"INSTALL FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
