
"""
Card lookup model for MTG Proxy Studio.
Uses Proxyshop's existing Scryfall integration.
"""

from threading import Thread
from typing import TypedDict

from PySide6.QtCore import QObject, Property, Signal, Slot

from src import CFG
from src.cards import get_card_data


class LookupResult(TypedDict):
    card: dict[str, str]
    error: str


class StudioCardModel(QObject):
    changed = Signal()
    _lookup_finished = Signal(dict)

    def __init__(self) -> None:
        super().__init__()

        self._card: dict[str, str] = {}
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

    @Slot(str)
    def lookup(self, name: str) -> None:
        name = name.strip()

        if not name or self._loading:
            return

        self._loading = True
        self._error = ""
        self._card = {}
        self.changed.emit()

        def worker() -> None:
            try:
                data = get_card_data({"name": name}, CFG)

                if data is None:
                    raise ValueError("Card not found on Scryfall.")

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
                }

                result: LookupResult = {
                    "card": card,
                    "error": "",
                }

            except Exception as exc:
                result = {
                    "card": {},
                    "error": str(exc),
                }

            self._lookup_finished.emit(result)

        Thread(target=worker, daemon=True).start()

    @Slot(dict)
    def _finish_lookup(self, result: LookupResult) -> None:
        self._card = result["card"]
        self._error = result["error"]
        self._loading = False
        self.changed.emit()
