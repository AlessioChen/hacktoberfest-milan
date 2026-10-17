"""Normalizzazione delle date d'etichetta (EXP 12/10/26, 12.10.2026, 12 OTT 2026, TMC 03/2027...).

Convenzioni: giorno/mese/anno all'italiana. Mese+anno -> ultimo giorno del mese.
Se nel testo ci sono più date (es. confezionamento e scadenza) si preferisce quella
vicina a una parola chiave di scadenza, altrimenti la più lontana nel tempo.
"""
import re
from calendar import monthrange
from datetime import date

# "da consumare entro" = hard (sicurezza); "preferibilmente entro" = soft (qualità)
HARD = re.compile(r"da consumarsi|da consumare|consumare entro|use by", re.I)
SOFT = re.compile(r"preferibilmente|best before|tmc|\bbbe?\b", re.I)
EXPIRY_KW = re.compile(r"scad|exp|entro|tmc|use by|best before|\bbbe?\b|consum", re.I)

MONTHS = {
    "gen": 1, "feb": 2, "mar": 3, "apr": 4, "mag": 5, "giu": 6, "lug": 7, "ago": 8, "set": 9,
    "ott": 10, "nov": 11, "dic": 12, "jan": 1, "may": 5, "jun": 6, "jul": 7, "aug": 8, "sep": 9,
    "oct": 10, "dec": 12,
}
_MON = "|".join(MONTHS)
_SEP = r"[\s/.\-]*"
_YEAR = r"(20\d{2}|\d{2})"
_D = r"(0?[1-9]|[12]\d|3[01])"
_M = r"(0?[1-9]|1[0-2])"
_LOT = re.compile(r"\b(?:lotto|lot|l)\s*[:.\-]?\s*[A-Z0-9]{3,}\b", re.I)

# (regex, handler) in ordine di specificità; i match già coperti da uno precedente sono scartati
_PATTERNS = [
    ("ymd", re.compile(rf"(?<!\d)(20\d{{2}})\s*[/.\-\s]\s*{_M}\s*[/.\-\s]\s*{_D}(?!\d)")),
    ("dmy", re.compile(rf"(?<!\d){_D}\s*[/.\-\s]\s*{_M}\s*[/.\-\s]\s*{_YEAR}(?!\d)")),
    ("dMony", re.compile(rf"(?<!\d){_D}\s*[/.\-\s]?\s*({_MON})[a-z]*\.?\s*[/.\-\s]?\s*{_YEAR}(?!\d)", re.I)),
    ("Mony", re.compile(rf"\b({_MON})[a-z]*\.?\s*[/.\-\s]?\s*{_YEAR}(?!\d)", re.I)),
    ("my", re.compile(rf"(?<![\d/.\-]){_M}\s*[/.\-]\s*(20\d{{2}}|\d{{2}})(?![\d/.\-]\d)")),
    ("compact", re.compile(rf"(?<!\d){_D}{_M}(20\d{{2}}|\d{{2}})(?!\d)")),
]


def _year(y: str) -> int:
    return int(y) if len(y) == 4 else 2000 + int(y)


def _plausible(d: date, partial: bool) -> bool:
    # date complete: anche vecchie (foto di test); mese/anno: "12/10" è quasi sempre giorno/mese
    low = date.today().year - 1 if partial else 2000
    return low <= d.year <= date.today().year + 20


def _make(kind: str, g: tuple[str, ...]) -> date | None:
    try:
        if kind == "ymd":
            d = date(int(g[0]), int(g[1]), int(g[2]))
        elif kind in ("dmy", "compact"):
            d = date(_year(g[2]), int(g[1]), int(g[0]))
        elif kind == "dMony":
            d = date(_year(g[2]), MONTHS[g[1].lower()[:3]], int(g[0]))
        else:  # mese + anno
            mo, y = (MONTHS[g[0].lower()[:3]], _year(g[1])) if kind == "Mony" else (int(g[0]), _year(g[1]))
            d = date(y, mo, monthrange(y, mo)[1])
    except (ValueError, KeyError):
        return None
    return d if _plausible(d, kind in ("my", "Mony")) else None


def kind(text: str) -> str:
    """'hard' | 'soft' | 'unknown'."""
    if SOFT.search(text):
        return "soft"
    if HARD.search(text):
        return "hard"
    return "unknown"


def parse_all(text: str) -> list[tuple[int, date]]:
    """Tutte le date plausibili trovate, come (posizione, data)."""
    text = _LOT.sub(" ", text)  # il lotto (L:2610A) non è una data
    found, taken = [], []
    for name, rx in _PATTERNS:
        for m in rx.finditer(text):
            if any(m.start() < e and s < m.end() for s, e in taken):
                continue
            if d := _make(name, m.groups()):
                found.append((m.start(), d))
                taken.append((m.start(), m.end()))
    return sorted(found)


def parse(text: str) -> date | None:
    found = parse_all(text)
    if not found:
        return None
    for m in EXPIRY_KW.finditer(text):  # data subito dopo una parola chiave di scadenza
        after = [(p, d) for p, d in found if p >= m.start()]
        if after:
            return after[0][1]
    return max(d for _, d in found)
