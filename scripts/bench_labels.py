"""Benchmark lettura date: foto -> Gemma -> app.dates.parse, confronto con labels.csv.

Uso: uv run python scripts/bench_labels.py [cartella ...]   (default: tests/fixtures/synthetic tests/fixtures/real)
Serve Ollama attivo (OLLAMA_URL / OLLAMA_MODEL).
"""
import csv
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from app import dates, vision  # noqa: E402

dirs = [Path(p) for p in sys.argv[1:]] or [Path("tests/fixtures/synthetic"), Path("tests/fixtures/real")]
for d in dirs:
    csv_path = d / "labels.csv"
    if not csv_path.exists():
        continue
    rows = list(csv.DictReader(csv_path.open()))
    ok = 0
    for r in rows:
        res = vision.read_label((d / r["file"]).read_bytes())
        got = dates.parse(res["testo_data"])
        good = got == date.fromisoformat(r["data_attesa"])
        ok += good
        if not good:
            print(f"  KO {d.name}/{r['file']}: atteso {r['data_attesa']} ({r['testo']!r}), letto {res['testo_data']!r} -> {got}")
    print(f"{d.name}: {ok}/{len(rows)} corrette ({ok / len(rows):.0%})")
