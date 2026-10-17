"""Scarica da Open Food Facts prodotti italiani con foto e (se presente) data di scadenza.

Uso: uv run python scripts/fetch_off.py [--n 100] [--out tests/fixtures/off]
Salva le immagini in <out>/<code>.jpg e i metadati in <out>/products.csv
(code, nome, categorie, expiration_date, image_url).
Nota: `expiration_date` è inserita a mano dai contributori, può essere vuota o imprecisa.
"""
import argparse
import csv
import time
from pathlib import Path

import httpx

UA = {"User-Agent": "frigo-hack/0.1 (progetto hacktoberfest)"}
API = "https://world.openfoodfacts.org/api/v2/search"
FIELDS = "code,product_name,categories_tags,expiration_date,image_front_url"


def fetch_page(client: httpx.Client, page: int, size: int) -> list[dict]:
    for attempt in range(4):
        try:
            r = client.get(API, params={"countries_tags_en": "italy", "fields": FIELDS,
                                        "page": page, "page_size": size,
                                        "sort_by": "unique_scans_n"})
            r.raise_for_status()
            return r.json().get("products", [])
        except (httpx.HTTPError, ValueError):
            time.sleep(2 ** attempt)  # il servizio a volte è "temporarily unavailable"
    raise SystemExit("Open Food Facts non risponde, riprova più tardi.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--out", default="tests/fixtures/off")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rows, page = [], 1
    with httpx.Client(headers=UA, timeout=30, follow_redirects=True) as c:
        while len(rows) < a.n:
            products = fetch_page(c, page, 50)
            if not products:
                break
            for p in products:
                url = p.get("image_front_url")
                if not url or not p.get("product_name"):
                    continue
                img = c.get(url)
                if img.status_code != 200:
                    continue
                (out / f"{p['code']}.jpg").write_bytes(img.content)
                rows.append([p["code"], p["product_name"], ";".join(p.get("categories_tags", [])),
                             p.get("expiration_date", ""), url])
                if len(rows) >= a.n:
                    break
                time.sleep(0.2)
            page += 1
    with open(out / "products.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["code", "nome", "categorie", "expiration_date", "image_url"])
        w.writerows(rows)
    print(f"{len(rows)} prodotti salvati in {out}")


if __name__ == "__main__":
    main()
