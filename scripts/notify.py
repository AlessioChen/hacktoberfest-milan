"""Notifica opzionale via ntfy.sh per i prodotti in scadenza. Uso: NTFY_TOPIC=xxx uv run python scripts/notify.py"""
import os
import sys
from datetime import date
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parent.parent))
from app import db  # noqa: E402

topic = os.environ["NTFY_TOPIC"]
soon = [i for i in db.list_items() if i.scade_il and (i.scade_il - date.today()).days <= 2]
if soon:
    httpx.post(f"https://ntfy.sh/{topic}", content="In scadenza: " + ", ".join(i.nome for i in soon))
