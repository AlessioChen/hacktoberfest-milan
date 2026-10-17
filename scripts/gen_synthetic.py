"""Genera etichette sintetiche con date di scadenza + CSV con il valore atteso.

Uso: uv run python scripts/gen_synthetic.py [--n 60] [--out tests/fixtures/synthetic] [--seed 1]
Output: <out>/NNN.jpg e <out>/labels.csv (file, testo, data_attesa, tipo).
Le foto reali (anche trovate online) vanno in tests/fixtures/real/ con lo stesso labels.csv.
"""
import argparse
import csv
import random
from calendar import monthrange
from datetime import date, timedelta
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONTS = ["/System/Library/Fonts/Menlo.ttc", "/System/Library/Fonts/Courier.ttc",
         "/System/Library/Fonts/Supplemental/Arial.ttf", "/Library/Fonts/Arial.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"]

# (formato strftime, prefissi possibili, tipo, solo mese/anno?)
FORMATS = [
    ("%d/%m/%y", ["EXP ", "SCAD. ", "Da consumarsi entro ", ""], "hard"),
    ("%d.%m.%Y", ["EXP ", "Da consumare entro ", "Scad. "], "hard"),
    ("%d-%m-%Y", ["Da consumarsi entro ", "USE BY "], "hard"),
    ("%d/%m/%Y", ["Da consumarsi preferibilmente entro ", "TMC ", "BEST BEFORE "], "soft"),
    ("%m/%Y", ["Da consumarsi preferibilmente entro ", "TMC ", "BBE "], "soft"),
    ("%m.%y", ["TMC ", "BB "], "soft"),
]


def font(size: int) -> ImageFont.FreeTypeFont:
    for p in FONTS:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def expected(d: date, fmt: str) -> date:
    return date(d.year, d.month, monthrange(d.year, d.month)[1]) if fmt.startswith("%m") else d


def render(text: str, rng: random.Random) -> Image.Image:
    f = font(rng.randint(26, 44))
    w, h = 80 + int(f.getlength(text)), 40 + f.size * 2
    bg = rng.choice([(245, 245, 240), (230, 235, 245), (250, 240, 220), (200, 200, 205), (255, 255, 255)])
    img = Image.new("RGB", (w, h), bg)
    d = ImageDraw.Draw(img)
    ink = rng.choice([(20, 20, 20), (40, 40, 90), (90, 20, 20), (10, 10, 10)])
    d.text((40 + rng.randint(-8, 8), f.size // 2 + rng.randint(-6, 6)), text, font=f, fill=ink)
    # riflesso e puntini d'inchiostro mancanti
    if rng.random() < 0.4:
        x = rng.randint(0, w)
        d.polygon([(x, 0), (x + 60, 0), (x + 20, h), (x - 40, h)], fill=tuple(min(255, c + 25) for c in bg))
    for _ in range(rng.randint(0, 40)):
        x, y = rng.randint(0, w), rng.randint(0, h)
        d.ellipse([x, y, x + 2, y + 2], fill=bg)
    img = img.rotate(rng.uniform(-6, 6), expand=True, fillcolor=bg, resample=Image.BICUBIC)
    if rng.random() < 0.6:
        img = img.filter(ImageFilter.GaussianBlur(rng.uniform(0.3, 1.4)))
    px = img.load()
    for _ in range(img.width * img.height // 40):  # rumore
        x, y = rng.randrange(img.width), rng.randrange(img.height)
        v = rng.randint(-30, 30)
        px[x, y] = tuple(max(0, min(255, c + v)) for c in px[x, y])
    return img


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=60)
    ap.add_argument("--out", default="tests/fixtures/synthetic")
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    rng = random.Random(a.seed)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for i in range(a.n):
        fmt, prefixes, tipo = rng.choice(FORMATS)
        d = date(2026, 1, 1) + timedelta(days=rng.randint(0, 900))
        text = rng.choice(prefixes) + d.strftime(fmt)
        name = f"{i:03d}.jpg"
        render(text, rng).save(out / name, quality=rng.randint(60, 90))
        rows.append([name, text, expected(d, fmt).isoformat(), tipo])
    with open(out / "labels.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["file", "testo", "data_attesa", "tipo"])
        w.writerows(rows)
    print(f"{a.n} etichette in {out}")


if __name__ == "__main__":
    main()
