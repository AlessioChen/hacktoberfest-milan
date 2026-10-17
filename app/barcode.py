"""Lettura codice a barre da foto + dettagli prodotto da Open Food Facts."""
import re

import cv2
import httpx
import numpy as np

UA = {"User-Agent": "frigo-hack/0.1 (progetto hacktoberfest)"}
OFF_URL = "https://world.openfoodfacts.org/api/v2/product/{code}"

# parola chiave in categories_tags OFF -> nostra categoria (in ordine di priorità)
CATEGORY_MAP = [
    ("formaggi-stagionati", "formaggio_stagionato"), ("parmigiano", "formaggio_stagionato"),
    ("grana", "formaggio_stagionato"), ("formaggi", "formaggio_fresco"), ("mozzarella", "formaggio_fresco"),
    ("ricotta", "formaggio_fresco"), ("latticin", "latticini"), ("milk", "latticini"), ("latte", "latticini"),
    ("yogurt", "latticini"), ("dairies", "latticini"), ("uova", "uova"), ("eggs", "uova"),
    ("salumi", "salumi"), ("prosciutt", "salumi"), ("meats", "carne"), ("carn", "carne"),
    ("pesce", "pesce"), ("fish", "pesce"), ("seafood", "pesce"),
    ("pasta-fresca", "pasta_fresca"), ("breads", "pane"), ("pane", "pane"),
    ("vegetables", "verdura"), ("verdur", "verdura"), ("fruits", "frutta"), ("frutta", "frutta"),
    ("meals", "piatti_pronti"), ("piatti-pronti", "piatti_pronti"),
    ("beverages", "bevande"), ("bevande", "bevande"), ("sauces", "condimenti"), ("condiment", "condimenti"),
]


def valid_ean(code: str) -> bool:
    """Checksum EAN-8/EAN-13/UPC-A."""
    if not re.fullmatch(r"\d{8}|\d{12}|\d{13}", code):
        return False
    digits = [int(c) for c in code]
    body, check = digits[:-1], digits[-1]
    total = sum(d * (3 if i % 2 == 0 else 1) for i, d in enumerate(reversed(body)))
    return (10 - total % 10) % 10 == check


def _try(det, img) -> str | None:
    try:
        texts = det.detectAndDecode(img)[0]
    except cv2.error:
        return None
    if isinstance(texts, str):
        texts = [texts]
    return next((t for t in (texts or []) if valid_ean(t)), None)


def decode(image: bytes) -> str | None:
    """Prima cifra valida trovata nella foto, altrimenti None.

    Il detector di OpenCV funziona meglio su immagini piccole e leggermente sfocate:
    si prova a più larghezze e con/senza blur.
    """
    img = cv2.imdecode(np.frombuffer(image, np.uint8), cv2.IMREAD_GRAYSCALE)
    if img is None:
        return None
    det = cv2.barcode.BarcodeDetector()
    for width in (640, 960, 480, 1280):
        scale = width / img.shape[1]
        small = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        for variant in (small, cv2.GaussianBlur(small, (3, 3), 0)):
            if code := _try(det, variant):
                return code
    return None


def map_category(tags: list[str]) -> str | None:
    joined = " ".join(tags).lower()
    return next((cat for key, cat in CATEGORY_MAP if key in joined), None)


def lookup(code: str) -> dict | None:
    """Dettagli da Open Food Facts; None se non trovato o servizio non raggiungibile."""
    try:
        r = httpx.get(OFF_URL.format(code=code), headers=UA, timeout=8,
                      params={"fields": "product_name,brands,quantity,categories_tags"})
        if r.status_code != 200:
            return None
        data = r.json()
    except (httpx.HTTPError, ValueError):
        return None
    p = data.get("product") if data.get("status") == 1 else None
    if not p or not p.get("product_name"):
        return None
    return {
        "nome": p["product_name"],
        "marca": (p.get("brands") or "").split(",")[0].strip() or None,
        "confezione": p.get("quantity") or None,
        "categoria": map_category(p.get("categories_tags", [])),
    }
