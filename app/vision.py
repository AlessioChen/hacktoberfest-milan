import base64
import json
import os

import httpx

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma4")


def health() -> tuple[bool, str]:
    try:
        r = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        r.raise_for_status()
        names = [m["name"] for m in r.json().get("models", [])]
    except Exception as e:  # noqa: BLE001
        return False, f"Ollama non raggiungibile ({OLLAMA_URL}): {e}"
    if not any(n.split(":")[0] == OLLAMA_MODEL.split(":")[0] for n in names):
        return False, f"Modello '{OLLAMA_MODEL}' non trovato. Esegui: ollama pull {OLLAMA_MODEL}"
    return True, "ok"


def chat_json(prompt: str, schema: dict, image: bytes | None = None) -> dict:
    msg = {"role": "user", "content": prompt}
    if image:
        msg["images"] = [base64.b64encode(image).decode()]
    r = httpx.post(
        f"{OLLAMA_URL}/api/chat",
        json={"model": OLLAMA_MODEL, "messages": [msg], "format": schema, "stream": False,
              "options": {"temperature": 0}},
        timeout=300,
    )
    r.raise_for_status()
    return json.loads(r.json()["message"]["content"])


def chat_text(prompt: str) -> str:
    r = httpx.post(
        f"{OLLAMA_URL}/api/chat",
        json={"model": OLLAMA_MODEL, "messages": [{"role": "user", "content": prompt}], "stream": False},
        timeout=300,
    )
    r.raise_for_status()
    return r.json()["message"]["content"]


def _categories() -> list[str]:
    from app import shelf_life
    return shelf_life.categorie()


def product_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "nome": {"type": "string"},
            "categoria": {"type": "string", "enum": _categories()},
            "stato": {"type": "string", "enum": ["chiuso", "aperto", "cotto", "congelato"]},
            "testo_data": {"type": "string"},
            "confidenza": {"type": "number"},
        },
        "required": ["nome", "categoria", "stato", "testo_data", "confidenza"],
    }


def identify_product(image: bytes) -> dict:
    return chat_json(
        "Identifica il prodotto alimentare nella foto. Rispondi in JSON: nome (italiano), "
        "categoria, stato (chiuso/aperto/cotto/congelato), confidenza tra 0 e 1 e testo_data: "
        "se sulla confezione è visibile una data di scadenza copiala ESATTAMENTE com'è stampata, "
        "altrimenti stringa vuota. Non inventare date.",
        product_schema(), image)


LABEL_SCHEMA = {
    "type": "object",
    "properties": {
        "testo_data": {"type": "string"},
        "tipo": {"type": "string", "enum": ["da_consumare_entro", "preferibilmente_entro", "sconosciuto"]},
        "confidenza": {"type": "number"},
    },
    "required": ["testo_data", "tipo", "confidenza"],
}


def read_label(image: bytes) -> dict:
    return chat_json(
        "Leggi la data di scadenza sull'etichetta. Copia ESATTAMENTE il testo della data in "
        "testo_data (es. '12/10/26', 'EXP 12.10.2026'). Indica se è 'da consumare entro', "
        "'preferibilmente entro' o sconosciuto. Non inventare: se illeggibile lascia testo_data vuoto.",
        LABEL_SCHEMA, image)


RECEIPT_SCHEMA = {
    "type": "object",
    "properties": {
        "data_acquisto": {"type": "string"},
        "righe": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "testo": {"type": "string"},
                    "nome": {"type": "string"},
                    "qty": {"type": "number"},
                    "prezzo": {"type": "number"},
                    "alimentare": {"type": "boolean"},
                    "categoria": {"type": "string"},
                },
                "required": ["testo", "nome", "qty", "prezzo", "alimentare", "categoria"],
            },
        },
    },
    "required": ["righe"],
}


def read_receipt(image: bytes) -> dict:
    cats = ", ".join(_categories())
    return chat_json(
        "Estrai le righe di questo scontrino. Per ogni riga: testo originale, nome espanso e leggibile "
        "in italiano (espandi abbreviazioni), qty, prezzo totale riga, alimentare (false per detersivi, "
        f"buste, ecc.), categoria tra: {cats}. data_acquisto in formato YYYY-MM-DD se presente.",
        RECEIPT_SCHEMA, image)
