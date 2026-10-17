import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from app import dates, db, receipt, recipes, shelf_life, vision  # noqa: E402
from app.models import Item  # noqa: E402

st.set_page_config(page_title="Frigo", page_icon="🧊")
db.init()

STATI = ["chiuso", "aperto", "cotto", "congelato"]
CATS = shelf_life.categorie()


def semaforo(item: Item) -> str:
    if not item.scade_il:
        return "⚪"
    d = (item.scade_il - date.today()).days
    return "🔴" if d <= 2 else "🟡" if d <= 5 else "🟢"


def scadenza_label(item: Item) -> str:
    if not item.scade_il:
        return "—"
    d = (item.scade_il - date.today()).days
    when = "scaduto" if d < 0 else "oggi" if d == 0 else f"tra {d} g"
    prefix = "circa " if item.fonte_scadenza == "estimated" else ""
    return f"{prefix}{item.scade_il:%d/%m/%Y} ({when})"


def item_form(proposal: dict, key: str) -> Item | None:
    """Form di conferma: l'utente corregge sempre prima del salvataggio."""
    with st.form(key):
        if "confidenza" in proposal and proposal["confidenza"] is not None:
            st.caption(f"Confidenza modello: {proposal['confidenza']:.0%}")
        nome = st.text_input("Nome", proposal.get("nome", ""))
        c1, c2 = st.columns(2)
        cat = proposal.get("categoria", "default")
        categoria = c1.selectbox("Categoria", CATS, index=CATS.index(cat) if cat in CATS else 0)
        stato = c2.selectbox("Stato", STATI, index=STATI.index(proposal.get("stato", "chiuso")))
        qty = c1.number_input("Quantità", 0.0, value=1.0)
        prezzo = c2.number_input("Prezzo (€)", 0.0, value=0.0)
        bought = st.date_input("Acquistato il", date.today())
        letta = dates.parse(proposal.get("testo_data") or "")
        if letta:
            st.caption(f"Data letta dalla confezione: `{proposal['testo_data']}`")
        manual = st.date_input("Scadenza (se vuota, viene stimata)", value=letta)
        if st.form_submit_button("Salva") and nome:
            fonte = "estimated" if not manual else "label" if manual == letta else "manual"
            return Item(
                nome=nome, categoria=categoria, stato=stato, qty=qty, prezzo=prezzo or None,
                acquistato_il=bought, confidenza=proposal.get("confidenza"),
                scade_il=manual or shelf_life.estimate(categoria, stato, bought),
                fonte_scadenza=fonte)
    return None


def page_inventario():
    items = db.list_items()
    if not items:
        st.info("Il frigo è vuoto. Aggiungi qualcosa dalla pagina Aggiungi.")
    urgenti = [i for i in items if i.scade_il and (i.scade_il - date.today()).days <= 2]
    if urgenti:
        st.warning("In scadenza: " + ", ".join(i.nome for i in urgenti))
    for i in items:
        c1, c2, c3, c4 = st.columns([5, 4, 1, 1])
        c1.write(f"{semaforo(i)} **{i.nome}** ×{i.qty:g} · {i.stato}")
        c2.write(scadenza_label(i))
        if c3.button("✅", key=f"c{i.id}", help="Consumato"):
            db.set_esito(i.id, "consumato"); st.rerun()
        if c4.button("🗑️", key=f"b{i.id}", help="Buttato"):
            db.set_esito(i.id, "buttato"); st.rerun()
    st.metric("Spreco totale", f"{db.wasted_euro():.2f} €")


def page_aggiungi():
    tab_foto, tab_label, tab_scontrino, tab_man = st.tabs(["Foto prodotto", "Etichetta", "Scontrino", "Manuale"])

    with tab_foto:
        img = st.file_uploader("Foto del prodotto", type=["jpg", "jpeg", "png"], key="foto") \
            or st.camera_input("…o scatta", key="cam")
        if img:
            if st.button("Analizza", key="a_foto"):
                with st.spinner("Gemma sta guardando…"):
                    st.session_state.prop = vision.identify_product(img.getvalue())
            if "prop" in st.session_state:
                item = item_form(st.session_state.prop, "f_foto")
                if item:
                    db.add_item(item); del st.session_state["prop"]; st.success("Aggiunto")

    with tab_label:
        items = db.list_items()
        if not items:
            st.info("Nessun prodotto a cui associare l'etichetta.")
        else:
            target = st.selectbox("Prodotto", items, format_func=lambda i: f"{i.nome} ({scadenza_label(i)})")
            img = st.file_uploader("Foto etichetta", type=["jpg", "jpeg", "png"], key="lab")
            if img and st.button("Leggi data"):
                with st.spinner("Lettura…"):
                    st.session_state.lab = vision.read_label(img.getvalue())
            if lab := st.session_state.get("lab"):
                parsed = dates.parse(lab["testo_data"])
                tipo = dates.kind(lab["tipo"].replace("_", " ")) if lab["tipo"] != "sconosciuto" else "unknown"
                st.write(f"Letto: `{lab['testo_data']}` · confidenza {lab['confidenza']:.0%} · tipo: {tipo}")
                final = st.date_input("Data verificata", parsed or date.today())
                if st.button("Conferma data"):
                    db.update_item(target.id, scade_il=final, fonte_scadenza="label")
                    del st.session_state["lab"]; st.success("Aggiornata"); st.rerun()

    with tab_scontrino:
        img = st.file_uploader("Foto scontrino", type=["jpg", "jpeg", "png"], key="rec")
        if img and st.button("Leggi scontrino"):
            with st.spinner("Lettura scontrino…"):
                st.session_state.rec = [i.model_dump() for i in receipt.parse_receipt(img.getvalue())]
        if "rec" in st.session_state:
            cols = ["nome", "categoria", "stato", "qty", "prezzo", "acquistato_il", "scade_il"]
            df = pd.DataFrame(st.session_state.rec, columns=cols)
            edited = st.data_editor(df, num_rows="dynamic", column_config={
                "categoria": st.column_config.SelectboxColumn(options=CATS),
                "stato": st.column_config.SelectboxColumn(options=STATI)})
            st.caption("Le scadenze sono stime (circa) dalla data d'acquisto.")
            if st.button("Aggiungi tutto"):
                for r in edited.to_dict("records"):
                    db.add_item(Item(**{k: (None if pd.isna(v) else v) for k, v in r.items()},
                                     fonte_scadenza="estimated"))
                del st.session_state["rec"]; st.success("Aggiunti"); st.rerun()

    with tab_man:
        item = item_form({}, "f_man")
        if item:
            db.add_item(item); st.success("Aggiunto")


def page_ricette():
    items = db.list_items()
    if st.button("Suggerisci ricette") and items:
        with st.spinner("Penso a qualcosa di buono…"):
            st.markdown(recipes.suggest(items))


ok, msg = vision.health()
(st.sidebar.success if ok else st.sidebar.error)("Ollama OK" if ok else msg)
page = st.sidebar.radio("Pagina", ["Inventario", "Aggiungi", "Ricette"])
st.sidebar.caption("Le scadenze sono stime: l'app non garantisce la sicurezza alimentare. "
                   "Controlla sempre aspetto e odore.")
{"Inventario": page_inventario, "Aggiungi": page_aggiungi, "Ricette": page_ricette}[page]()
