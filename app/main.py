import base64
import hashlib
import html
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from app import barcode, dates, db, receipt, recipes, shelf_life, vision  # noqa: E402
from app.models import Item  # noqa: E402

ROOT = Path(__file__).parent.parent
st.set_page_config(page_title="Fuorisaver", page_icon=str(ROOT / "assets" / "favicon.png"))
st.markdown(f"<style>{(Path(__file__).parent / 'style.css').read_text()}</style>", unsafe_allow_html=True)
db.init()

STATI = ["chiuso", "aperto", "cotto", "congelato"]
CATS = shelf_life.categorie()


def semaforo(item: Item) -> str:
    if not item.scade_il:
        return "grey"
    d = (item.scade_il - date.today()).days
    return "red" if d <= 2 else "yellow" if d <= 5 else "green"


def logo_b64() -> str:
    # logo a tessera arancione: identico in tema chiaro e scuro
    return base64.b64encode((ROOT / "assets" / "fuorisaver.png").read_bytes()).decode()


def scadenza_label(item: Item) -> str:
    if not item.scade_il:
        return "—"
    d = (item.scade_il - date.today()).days
    when = "scaduto" if d < 0 else "oggi" if d == 0 else f"tra {d} g"
    prefix = "circa " if item.fonte_scadenza == "estimated" else ""
    return f"{prefix}{item.scade_il:%d/%m/%Y} ({when})"


def applica_barcode(prop: dict, code: str) -> dict:
    """Aggiunge i dettagli del codice a barre (Open Food Facts) alla proposta."""
    prop = {k: v for k, v in prop.items() if k != "da_barcode"}
    prop["barcode"] = code
    if info := barcode.lookup(code):
        prop["nome"] = info["nome"]
        prop["marca"], prop["confezione"] = info["marca"], info["confezione"]
        if info["categoria"]:
            prop["categoria"] = info["categoria"]
        prop["da_barcode"] = True
    return prop


def analizza_prodotto(image: bytes) -> dict:
    """Foto -> proposta: Gemma (nome, categoria, data) + dettagli da codice a barre se leggibile."""
    prop = vision.identify_product(image)
    if not dates.parse(prop.get("testo_data") or ""):
        # seconda passata dedicata alla sola data: più affidabile del prompt "tutto in uno"
        prop["testo_data"] = vision.read_label(image).get("testo_data", "")
    if code := barcode.decode(image):
        prop = applica_barcode(prop, code)
    return prop


def item_form(proposal: dict, key: str) -> Item | None:
    """Form di conferma: l'utente corregge sempre prima del salvataggio."""
    with st.form(key):
        if "confidenza" in proposal and proposal["confidenza"] is not None:
            st.caption(f"Confidenza modello: {proposal['confidenza']:.0%}")
        nome = st.text_input("Nome", proposal.get("nome", ""))
        c0, c0b = st.columns(2)
        marca = c0.text_input("Marca", proposal.get("marca") or "")
        confezione = c0b.text_input("Confezione", proposal.get("confezione") or "")
        codice = proposal.get("barcode") or ""
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
                marca=marca or None, confezione=confezione or None, barcode=codice or None,
                scade_il=manual or shelf_life.estimate(categoria, stato, bought),
                fonte_scadenza=fonte)
    return None


def page_inventario():
    items = db.list_items()
    st.markdown(f'<div class="page-head"><h1>Inventario</h1><span>{date.today():%d/%m/%Y}</span></div>',
                unsafe_allow_html=True)
    if not items:
        st.info("Il frigo è vuoto. Aggiungi qualcosa dalla pagina Aggiungi.")
    urgenti = [i for i in items if i.scade_il and (i.scade_il - date.today()).days <= 2]
    if urgenti:
        nomi = html.escape(", ".join(i.nome for i in urgenti))
        st.markdown(f'<div class="alert">In scadenza: {nomi}</div>', unsafe_allow_html=True)
    for i in items:
        col = semaforo(i)
        c1, c2, c3 = st.columns([20, 1, 1])
        meta = html.escape(f"{i.categoria} · {i.stato}" + (f" · {i.marca}" if i.marca else ""))
        c1.markdown(
            f'<div class="row"><span class="dot {col}"></span>'
            f'<span class="name">{html.escape(i.nome)} <small>×{i.qty:g}</small></span>'
            f'<span class="meta">{meta}</span>'
            f'<span class="when {col}">{scadenza_label(i)}</span></div>', unsafe_allow_html=True)
        if c2.button("✓", key=f"c{i.id}", help="Consumato"):
            db.set_esito(i.id, "consumato"); st.rerun()
        if c3.button("⌫", key=f"b{i.id}", help="Buttato"):
            db.set_esito(i.id, "buttato"); st.rerun()
        with st.expander(f"Modifica {i.nome}"):
            with st.form(f"e{i.id}"):
                nome = st.text_input("Nome", i.nome)
                e1, e2 = st.columns(2)
                cat = e1.selectbox("Categoria", CATS, index=CATS.index(i.categoria) if i.categoria in CATS else 0)
                stato = e2.selectbox("Stato", STATI, index=STATI.index(i.stato))
                qty = e1.number_input("Quantità", 0.0, value=float(i.qty))
                scad = e2.date_input("Scadenza", i.scade_il)
                if st.form_submit_button("Salva modifiche"):
                    fields = dict(nome=nome, categoria=cat, stato=stato, qty=qty)
                    if scad and scad != i.scade_il:
                        fields.update(scade_il=scad, fonte_scadenza="manual")
                    db.update_item(i.id, **fields); st.rerun()
    spreco = f"{db.wasted_euro():.2f}".replace(".", ",")
    st.markdown(
        f'<div class="waste"><span class="lbl">Spreco totale</span>'
        f'<span class="val">{spreco} €</span></div>', unsafe_allow_html=True)


def page_aggiungi():
    st.markdown('<div class="page-head"><h1>Aggiungi</h1></div>', unsafe_allow_html=True)
    tab_foto, tab_label, tab_man, tab_scontrino = st.tabs(
        ["Foto prodotto", "Etichetta", "Manuale", "Scontrino (beta)"])

    with tab_foto:
        img = st.file_uploader("Foto del prodotto", type=["jpg", "jpeg", "png"], key="foto") \
            or st.camera_input("…o scatta", key="cam")
        if img:
            data = img.getvalue()
            key = hashlib.md5(data).hexdigest()
            if st.session_state.get("prop_key") != key:  # analisi automatica a ogni nuova foto
                with st.spinner("Analisi in corso…"):
                    try:
                        st.session_state.prop = analizza_prodotto(data)
                    except Exception as e:  # noqa: BLE001
                        st.session_state.pop("prop", None)
                        st.error(f"Analisi non riuscita, riprova o inserisci a mano ({e})")
                st.session_state.prop_key = key
            if "prop" in st.session_state:
                prop = st.session_state.prop
                codice = st.text_input("Codice a barre", prop.get("barcode") or "", key=f"ean_{key}",
                                       help="Se non si legge dalla foto, scrivilo qui per cercare i dettagli.")
                if codice and codice != prop.get("barcode") and barcode.valid_ean(codice):
                    prop = st.session_state.prop = applica_barcode(prop, codice)
                if prop.get("da_barcode"):
                    st.caption("Dettagli presi dal codice a barre (Open Food Facts). Puoi correggerli.")
                elif prop.get("barcode"):
                    st.caption("Codice letto ma prodotto non trovato: dettagli stimati dalla foto.")
                item = item_form(prop, f"f_foto_{key}")
                if item:
                    db.add_item(item)
                    for k in ("prop", "prop_key"):
                        st.session_state.pop(k, None)
                    st.success("Aggiunto")

    with tab_label:
        items = db.list_items()
        if not items:
            st.info("Nessun prodotto a cui associare l'etichetta.")
        else:
            target = st.selectbox("Prodotto", items, format_func=lambda i: f"{i.nome} ({scadenza_label(i)})")
            img = st.file_uploader("Foto etichetta", type=["jpg", "jpeg", "png"], key="lab")
            if img and st.button("Leggi data"):
                with st.spinner("Analisi in corso…"):
                    st.session_state.lab = vision.read_label(img.getvalue())
            if lab := st.session_state.get("lab"):
                parsed = dates.parse(lab["testo_data"])
                tipo = dates.kind(lab["tipo"].replace("_", " ")) if lab["tipo"] != "sconosciuto" else "unknown"
                st.write(f"Letto: `{lab['testo_data']}` · tipo: {tipo}")
                final = st.date_input("Data verificata", parsed or date.today())
                if st.button("Conferma data"):
                    db.update_item(target.id, scade_il=final, fonte_scadenza="label")
                    del st.session_state["lab"]; st.success("Aggiornata"); st.rerun()

    with tab_scontrino:
        img = st.file_uploader("Foto scontrino", type=["jpg", "jpeg", "png"], key="rec")
        if img and st.button("Leggi scontrino"):
            with st.spinner("Analisi in corso…"):
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
    st.markdown('<div class="page-head"><h1>Ricette</h1></div>', unsafe_allow_html=True)
    items = db.list_items()
    if st.button("Suggerisci ricette") and items:
        with st.spinner("Sto preparando le idee…"):
            st.markdown(recipes.suggest(items))


ok, msg = vision.health()
with st.sidebar:
    st.markdown(f'<div class="brand"><img src="data:image/png;base64,{logo_b64()}">Fuorisaver</div>',
                unsafe_allow_html=True)
    page = st.radio("Pagina", ["Inventario", "Aggiungi", "Ricette"], label_visibility="collapsed")
    st.caption("Le scadenze sono stime: l'app non garantisce la sicurezza alimentare. "
               "Controlla sempre aspetto e odore.")
    st.markdown(f'<div class="sidebar-foot"><span class="dot {"ok" if ok else "ko"}"></span>'
                f'{"Ollama OK" if ok else html.escape(msg)}</div>', unsafe_allow_html=True)
{"Inventario": page_inventario, "Aggiungi": page_aggiungi, "Ricette": page_ricette}[page]()
