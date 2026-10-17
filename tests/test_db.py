from datetime import date

from app import db
from app.models import Item


def test_order_and_waste(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "t.db"))
    db.init()
    db.add_item(Item(nome="b", scade_il=date(2026, 12, 1), prezzo=2))
    a = db.add_item(Item(nome="a", scade_il=date(2026, 11, 1), prezzo=3))
    assert [i.nome for i in db.list_items()] == ["a", "b"]
    db.set_esito(a, "buttato")
    assert db.wasted_euro() == 3
    assert [i.nome for i in db.list_items()] == ["b"]
