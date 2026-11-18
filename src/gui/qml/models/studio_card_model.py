"""Scryfall card lookup for MTG Proxy Studio.

Keeps the full, originally selected printing for subsequent Studio renders.
"""
from __future__ import annotations

from threading import Thread
from typing import TypedDict

from PySide6.QtCore import QObject, Property, Signal, Slot

from src import CFG
from src.cards import get_card_data
from src.utils.scryfall import ScryfallCard


class LookupResult(TypedDict):
    card: dict[str, str]
    error: str
    source: ScryfallCard | None


class StudioCardModel(QObject):
    changed = Signal()
    _lookup_finished = Signal(dict)

    def __init__(self) -> None:
        super().__init__()
        self._card: dict[str, str] = {}
        self._source: ScryfallCard | None = None
        self._loading: bool = False
        self._error: str = ""
        self._lookup_finished.connect(self._finish_lookup)

    @Property("QVariantMap", notify=changed)  # pyright: ignore[reportArgumentType]
    def card(self) -> dict[str, str]:
        return self._card

    @Property(bool, notify=changed)
    def loading(self) -> bool:
        return self._loading

    @Property(str, notify=changed)
    def error(self) -> str:
        return self._error

    def copy_source(self) -> ScryfallCard | None:
        """Return a detached copy of the printing selected in the editor."""
        return self._source.model_copy(deep=True) if self._source else None

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

                art_crop = ""
                if data.image_uris is not None:
                    art_crop = str(data.image_uris.art_crop)
                elif data.card_faces and data.card_faces[0].image_uris is not None:
                    art_crop = str(data.card_faces[0].image_uris.art_crop)

                card: dict[str, str] = {
                    "name": data.name,
                    "mana_cost": data.mana_cost or "",
                    "type_line": data.type_line,
                    "oracle_text": data.oracle_text or "",
                    "flavor_text": data.flavor_text or "",
                    "power": data.power or "",
                    "toughness": data.toughness or "",
                    "artist": data.artist or "",
                    "set": data.set.upper(),
                    "rarity": str(data.rarity),
                    "studio_compatible": "yes" if str(data.layout) == "normal" and not data.card_faces else "no",
                    "art_crop": art_crop,
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
