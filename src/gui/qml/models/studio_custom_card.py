"""Offline, synthetic Scryfall-shaped records for original Studio cards.

Proxyshop's existing layouts and rendering API operate on ScryfallCard objects;
this factory supplies the structural fields without querying or impersonating
an actual Scryfall printing.  Only Studio uses these objects.
"""

from __future__ import annotations

from datetime import date
from uuid import uuid4

from src.enums.mtg import LayoutScryfall
from src.utils.scryfall import ScryfallCard, ScryfallCardFace


_CUSTOM_LAYOUTS: dict[str, LayoutScryfall] = {
    "normal": LayoutScryfall.Normal,
    "planeswalker": LayoutScryfall.Planeswalker,
    "transform": LayoutScryfall.Transform,
    "mdfc": LayoutScryfall.MDFC,
}


def create_blank_card_source(layout_kind: str) -> ScryfallCard:
    """Return a valid, offline-backed card source with optional blank faces.

    The internal placeholder names are not displayed.  They exist only so
    the card model is valid until the user fills the Studio form.  Image URIs
    and oracle IDs deliberately remain absent, preventing accidental lookup.
    """
    if layout_kind not in _CUSTOM_LAYOUTS:
        raise ValueError(f"Unsupported custom card layout: {layout_kind}")

    # These URLs satisfy ScryfallCard's required URL metadata. No request is
    # made to them when an already-instantiated source is passed to the renderer.
    placeholder_url = "https://scryfall.com/"
    payload = {
        "id": str(uuid4()),
        "lang": "en",
        "object": "card",
        "layout": _CUSTOM_LAYOUTS[layout_kind],
        "prints_search_uri": placeholder_url,
        "rulings_uri": placeholder_url,
        "scryfall_uri": placeholder_url,
        "uri": placeholder_url,
        "name": "Custom Card",
        "type_line": "",
        "booster": False,
        "border_color": "black",
        "collector_number": "1",
        "digital": False,
        "finishes": ["nonfoil"],
        "frame": "2015",
        "full_art": False,
        "games": ["paper"],
        "highres_image": False,
        "image_status": "missing",
        "oversized": False,
        "prices": {},
        "promo": False,
        "rarity": "common",
        "related_uris": {},
        "released_at": date.today().isoformat(),
        "reprint": False,
        "scryfall_set_uri": placeholder_url,
        "set_name": "Custom Set",
        "set_search_uri": placeholder_url,
        "set_type": "expansion",
        "set_uri": placeholder_url,
        "set": "CST",
        "set_id": str(uuid4()),
        "story_spotlight": False,
        "textless": False,
        "variation": False,
        # Avoid looking up a first-print or fetching missing image artwork.
        "oracle_id": None,
        "image_uris": None,
        "artist": None,
        "keywords": [],
        "frame_effects": [],
    }

    if layout_kind in {"transform", "mdfc"}:
        payload["name"] = "Custom Front // Custom Back"
        payload["card_faces"] = [
            ScryfallCardFace(
                object="card_face", name="Custom Front", type_line="",
                image_uris=None,
            ).model_dump(),
            ScryfallCardFace(
                object="card_face", name="Custom Back", type_line="",
                image_uris=None,
            ).model_dump(),
        ]

    return ScryfallCard.model_validate(payload)
