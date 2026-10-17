import os
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path

import yaml

PATH = Path(os.environ.get("SHELF_LIFE_PATH", Path(__file__).parent.parent / "data" / "shelf_life.yaml"))


@lru_cache
def _table() -> dict:
    return yaml.safe_load(PATH.read_text())


def categorie() -> list[str]:
    return sorted(_table()["categorie"])


def days(categoria: str, stato: str) -> int:
    t = _table()
    row = t["categorie"].get(categoria, t["default"])
    return row.get(stato, t["default"][stato])


def estimate(categoria: str, stato: str, acquistato_il: date) -> date:
    return acquistato_il + timedelta(days=days(categoria, stato))
