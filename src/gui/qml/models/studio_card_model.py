"""Scryfall card lookup for Studio, including ordinary Transform and MDFC faces.

Keep a deep-copyable, unmodified Scryfall printing for Studio's render actions.
"""
from __future__ import annotations

from threading import Thread
from typing import Any, TypedDict

from PySide6.QtCore import QObject, Property, Signal, Slot

from src import CFG
from src.cards import get_card_data
from src.enums.mtg import LayoutScryfall
from src.utils.scryfall import ScryfallCard, ScryfallCardFace


class LookupResult(TypedDict):
    card: dict[str, Any]
    error: str
    source: ScryfallCard | None


class StudioCardModel(QObject):
    changed = Signal()
    _lookup_finished = Signal(dict)

    def __init__(self) -> None:
        super().__init__()
        self._card: dict[str, Any] = {}
        self._source: ScryfallCard | None = None
        self._loading = False
        self._error = ""
        self._lookup_finished.connect(self._finish_lookup)

    @Property("QVariantMap", notify=changed)  # pyright: ignore[reportArgumentType]
    def card(self) -> dict[str, Any]:
        return self._card

    @Property(bool, notify=changed)
    def loading(self) -> bool:
        return self._loading

    @Property(str, notify=changed)
    def error(self) -> str:
        return self._error

    def copy_source(self) -> ScryfallCard | None:
        return self._source.model_copy(deep=True) if self._source else None

    @staticmethod
    def _face_as_editor_data(face: ScryfallCard | ScryfallCardFace, source: ScryfallCard) -> dict[str, str]:
        image_uris = face.image_uris
        return {
            "name": face.name,
            "mana_cost": face.mana_cost or "",
            "type_line": face.type_line or "",
            "oracle_text": face.oracle_text or "",
            "flavor_text": face.flavor_text or "",
            "power": face.power or "",
            "toughness": face.toughness or "",
            "artist": face.artist or source.artist or "",
            "set": source.set.upper(),
            "rarity": str(source.rarity),
            "art_crop": str(image_uris.art_crop) if image_uris else "",
            "include_flavor_text": "true",
            "manual_artwork": "",
        }

    @Slot(str)
    def lookup(self, name: str) -> None:
        name = name.strip()
        if not name or self._loading:
            return

        self._loading = True
        self._error = ""
        self._card = {}
        self._source = None
        self.changed.emit()

        def worker() -> None:
            try:
                data = get_card_data({"name": name}, CFG)
                if data is None:
                    raise ValueError("Card not found on Scryfall.")

                normal = data.layout == LayoutScryfall.Normal and not data.card_faces
                dual = (
                    data.layout in {LayoutScryfall.Transform, LayoutScryfall.MDFC}
                    and data.card_faces is not None
                    and len(data.card_faces) == 2
                    # The original renderer uses specialized layouts for these.
                    and not any(
                        any(term in (face.type_line or "") for term in ("Planeswalker", "Saga", "Battle"))
                        for face in data.card_faces
                    )
                )
                kind = (
                    "normal" if normal else
                    ("mdfc" if data.layout == LayoutScryfall.MDFC else "transform") if dual else
                    "unsupported"
                )
                faces = (
                    [self._face_as_editor_data(face, data) for face in data.card_faces]
                    if dual and data.card_faces is not None
                    else [self._face_as_editor_data(data, data)]
                )
                card: dict[str, Any] = {
                    **faces[0],
                    "layout_kind": kind,
                    "studio_compatible": "yes" if normal or dual else "no",
                    "faces": faces,
                }
                result: LookupResult = {"card": card, "error": "", "source": data}
            except Exception as exc:
                result = {"card": {}, "error": str(exc), "source": None}
            self._lookup_finished.emit(result)

        Thread(target=worker, daemon=True).start()

    @Slot(dict)
    def _finish_lookup(self, result: LookupResult) -> None:
        self._card = result["card"]
        self._source = result["source"]
        self._error = result["error"]
        self._loading = False
        self.changed.emit()
