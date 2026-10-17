from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

Stato = Literal["chiuso", "aperto", "cotto", "congelato"]
FonteScadenza = Literal["estimated", "label", "manual"]


class Item(BaseModel):
    id: int | None = None
    nome: str
    categoria: str = "default"
    stato: Stato = "chiuso"
    qty: float = 1
    prezzo: float | None = None
    acquistato_il: date = Field(default_factory=date.today)
    scade_il: date | None = None
    fonte_scadenza: FonteScadenza = "estimated"
    confidenza: float | None = None
    # None = in frigo; "consumato" | "buttato" quando rimosso
    esito: Literal["consumato", "buttato"] | None = None
