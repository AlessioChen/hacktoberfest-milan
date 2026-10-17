import os
import sqlite3
from contextlib import contextmanager
from datetime import date
from pathlib import Path

from app.models import Item

DB_PATH = os.environ.get("DB_PATH", "frigo.db")


@contextmanager
def _conn():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    try:
        yield c
        c.commit()
    finally:
        c.close()


def init() -> None:
    with _conn() as c:
        c.execute(
            """CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL, categoria TEXT, stato TEXT, qty REAL,
                prezzo REAL, acquistato_il TEXT, scade_il TEXT,
                fonte_scadenza TEXT, confidenza REAL, esito TEXT)"""
        )


def add_item(item: Item) -> int:
    d = item.model_dump(mode="json", exclude={"id"})
    cols = ",".join(d)
    with _conn() as c:
        cur = c.execute(f"INSERT INTO items ({cols}) VALUES ({','.join('?' * len(d))})", list(d.values()))
        return cur.lastrowid


def list_items(active_only: bool = True) -> list[Item]:
    q = "SELECT * FROM items" + (" WHERE esito IS NULL" if active_only else "")
    with _conn() as c:
        rows = c.execute(q + " ORDER BY scade_il IS NULL, scade_il").fetchall()
    return [Item(**dict(r)) for r in rows]


def update_item(id: int, **fields) -> None:
    fields = {k: (v.isoformat() if isinstance(v, date) else v) for k, v in fields.items()}
    sets = ",".join(f"{k}=?" for k in fields)
    with _conn() as c:
        c.execute(f"UPDATE items SET {sets} WHERE id=?", [*fields.values(), id])


def set_esito(id: int, esito: str) -> None:
    update_item(id, esito=esito)


def wasted_euro() -> float:
    with _conn() as c:
        r = c.execute("SELECT COALESCE(SUM(prezzo),0) FROM items WHERE esito='buttato'").fetchone()
    return r[0]
