"""Normalizzazione delle date d'etichetta (EXP 12/10/26, 12.10.2026, L:2610A...)."""
import re
from calendar import monthrange
from datetime import date

# "da consumare entro" = hard (sicurezza); "preferibilmente entro" = soft (qualità)
HARD = re.compile(r"da consumarsi|da consumare|consumare entro|use by", re.I)
SOFT = re.compile(r"preferibilmente|da consumarsi preferibilmente|best before|tmc|\bbbe?\b", re.I)

_DMY = re.compile(r"(?<!\d)(\d{1,2})\s*[/.\-]\s*(\d{1,2})\s*[/.\-]\s*(\d{4}|\d{2})(?!\d)")
_MY = re.compile(r"(?<!\d)(\d{1,2})\s*[/.\-]\s*(\d{4}|\d{2})(?!\d)")


def _year(y: str) -> int:
    n = int(y)
    return n if len(y) == 4 else 2000 + n


def kind(text: str) -> str:
    """'hard' | 'soft' | 'unknown'."""
    if SOFT.search(text):
        return "soft"
    if HARD.search(text):
        return "hard"
    return "unknown"


def parse(text: str) -> date | None:
    """Estrae la prima data valida (giorno/mese/anno). Mese+anno -> ultimo giorno del mese."""
    if m := _DMY.search(text):
        d, mo, y = int(m[1]), int(m[2]), _year(m[3])
        try:
            return date(y, mo, d)
        except ValueError:
            return None
    if m := _MY.search(text):
        mo, y = int(m[1]), _year(m[2])
        if 1 <= mo <= 12:
            return date(y, mo, monthrange(y, mo)[1])
    return None
