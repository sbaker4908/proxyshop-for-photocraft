"""Pure image-processing helpers for the Trim tab (no Qt dependencies).

Proxyshop Classic output is nominally 2.75 x 3.75 inches, including
1/8 inch bleed per side. The visible Magic-card rectangle is 2.5 x 3.5.
The input can differ by a few pixels due to export rounding, so geometry
is derived from height, then centered to a nominal 5:7 final aspect ratio.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageOps

SOURCE_ASPECT = 2.75 / 3.75
FINISHED_ASPECT = 2.5 / 3.5
BLEED_INCHES = 0.125
CORNER_RADIUS_INCHES = 0.125


@dataclass(frozen=True)
class TrimResult:
    original_width: int
    original_height: int
    width: int
    height: int
    bleed_pixels: int
    radius_pixels: int


def _corner_mask(width: int, height: int, radius: int) -> Image.Image:
    """Create an anti-aliased grayscale transparency mask."""
    scale = 4
    size = (width * scale, height * scale)
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle(
        (0, 0, size[0] - 1, size[1] - 1),
        radius=radius * scale,
        fill=255,
    )
    return mask.resize((width, height), Image.Resampling.LANCZOS)


def create_trim_preview(source_file: Path, destination_png: Path) -> TrimResult:
    """Trim the printer bleed and save an RGBA PNG with transparent corners.

    A tight aspect-ratio guard prevents accidentally cutting an already
    bleed-free scan. A `_trim` input is explicitly rejected as well.
    """
    if source_file.stem.lower().endswith("_trim"):
        raise ValueError("This file already ends in _trim; select the original render instead.")

    with Image.open(source_file) as original:
        original.load()
        oriented = ImageOps.exif_transpose(original)
        width, height = oriented.size
        icc_profile = oriented.info.get("icc_profile")

        if width < 200 or height < 260:
            raise ValueError("Image is too small to trim accurately.")

        aspect = width / height
        if abs(aspect / SOURCE_ASPECT - 1) > 0.015:
            raise ValueError(
                "This image does not have the expected 2.75:3.75 bleed-inclusive "
                "card proportions. Trim is designed for untrimmed Proxyshop exports."
            )

        # Use physical height to calculate the 1/8-inch border on every edge.
        # Slight width adjustment corrects integer rounding in the original export.
        bleed_px = max(1, round(height * BLEED_INCHES / 3.75))
        cropped_height = height - 2 * bleed_px
        cropped_width = round(cropped_height * FINISHED_ASPECT)
        if cropped_width <= 0 or cropped_width > width:
            raise ValueError("Invalid crop dimensions for this image.")

        left = (width - cropped_width) // 2
        upper = bleed_px
        box = (left, upper, left + cropped_width, upper + cropped_height)
        result = oriented.crop(box).convert("RGBA")
        radius_px = max(1, round(cropped_height * CORNER_RADIUS_INCHES / 3.5))
        alpha = ImageChops.multiply(result.getchannel("A"), _corner_mask(
            cropped_width, cropped_height, radius_px
        ))
        result.putalpha(alpha)

        destination_png.parent.mkdir(parents=True, exist_ok=True)
        # Consistent physical-size metadata, although this export is not print-safe.
        dpi = cropped_height / 3.5
        save_kwargs = {"dpi": (dpi, dpi)}
        if isinstance(icc_profile, bytes):
            save_kwargs["icc_profile"] = icc_profile
        result.save(destination_png, format="PNG", **save_kwargs)

        return TrimResult(
            original_width=width,
            original_height=height,
            width=cropped_width,
            height=cropped_height,
            bleed_pixels=bleed_px,
            radius_pixels=radius_px,
        )
