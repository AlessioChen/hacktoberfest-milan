from app import vision
from app.models import Item


def suggest(items: list[Item]) -> str:
    # items già ordinati per scadenza da db.list_items
    elenco = "\n".join(f"- {i.nome} (scade {i.scade_il})" for i in items[:15])
    return vision.chat_text(
        "Ho questi ingredienti in frigo, ordinati per scadenza:\n" + elenco +
        "\nProponi 3 ricette semplici in italiano che usino prima quelli in scadenza. "
        "Per ognuna: titolo, ingredienti dal frigo, passaggi brevi.")
