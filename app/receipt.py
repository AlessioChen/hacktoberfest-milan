from datetime import date

from app import shelf_life, vision
from app.models import Item


def parse_receipt(image: bytes) -> list[Item]:
    data = vision.read_receipt(image)
    try:
        bought = date.fromisoformat(data.get("data_acquisto", ""))
    except ValueError:
        bought = date.today()
    cats = set(shelf_life.categorie())
    items = []
    for r in data["righe"]:
        if not r.get("alimentare", True):
            continue
        cat = r["categoria"] if r["categoria"] in cats else "default"
        items.append(Item(
            nome=r["nome"] or r["testo"], categoria=cat, stato="chiuso", qty=r["qty"] or 1,
            prezzo=r["prezzo"], acquistato_il=bought,
            scade_il=shelf_life.estimate(cat, "chiuso", bought), fonte_scadenza="estimated"))
    return items
