# 🧊 Fuorisaver

> Il peggior nemico del fuorisede, e del mondo, è il cibo scaduto: il pomodoro comprato la settimana scorsa per fare la pasta e mai usato. Per questo nasce **Fuorisaver**, il salvatore del fuorisede.

Fuorisaver è un tracker del cibo in frigo che gira **interamente in locale**. Fotografi quello che compri, lui capisce di cosa si tratta, stima (o legge) la scadenza e ti avvisa prima che tu butti via soldi e cibo. Quando qualcosa sta per scadere, ti suggerisce anche una ricetta per usarlo.

## Il problema

Chi vive fuori sede fa la spesa per sé, cucina a orari strani e spesso dimentica cosa c'è in frigo. Risultato: verdura appassita, latticini scaduti, soldi buttati. Le app di inventario esistenti richiedono di inserire tutto a mano, e quindi non le usa nessuno.

## Come funziona

Un modello multimodale open (**Gemma 4**, via Ollama) fa il lavoro noioso: guarda le foto ed estrae le informazioni. L'utente conferma sempre prima del salvataggio.

- 📷 **Foto del prodotto**: riconosce nome, categoria e stato (chiuso, aperto, cotto, congelato).
- 🏷️ **Foto dell'etichetta**: legge la data di scadenza vera (`EXP 12/10/26`, `12.10.2026`, `L:2610A`…) e distingue "da consumare entro" da "preferibilmente entro".
- 🔢 **Codice a barre**: decodifica l'EAN dalla foto e recupera nome, marca, confezione e categoria da [Open Food Facts](https://world.openfoodfacts.org).
- 🧾 **Scontrino**: una foto e tutti i prodotti finiscono in inventario in blocco, con prezzi e scadenze stimate; le voci non alimentari vengono filtrate.
- 🚦 **Inventario a semaforo**: 🔴 scade entro 2 giorni (o già scaduto), 🟡 entro 5, 🟢 il resto. Con un tap segni un prodotto come consumato ✅ o buttato 🗑️.
- 🍝 **Ricette**: propone cosa cucinare partendo dai prodotti più vicini alla scadenza.
- 🔔 **Notifiche** (opzionale): uno script manda un avviso via [ntfy](https://ntfy.sh) per i prodotti in scadenza.

### Da dove viene la scadenza

Lo scontrino non riporta le scadenze, quindi Fuorisaver le gestisce con tre livelli di affidabilità, sempre visibili in UI:

| Fonte       | Significato                                                                   |
| ----------- | ----------------------------------------------------------------------------- |
| `label`     | letta dall'etichetta della confezione                                         |
| `manual`    | inserita o corretta dall'utente                                               |
| `estimated` | data d'acquisto + durata tipica per categoria e stato (mostrata come "circa") |

Le durate tipiche stanno in `data/shelf_life.yaml`, ispirate a USDA FoodKeeper.

### Principi di design

- **Il modello estrae e classifica**; date e regole di sicurezza vengono da dati e codice, non dal modello.
- **Ogni inserimento passa da una conferma**, con la confidenza del modello in vista.
- **Privacy**: foto e dati restano sul tuo computer. Nessun cloud (a parte la ricerca opzionale su Open Food Facts).
- Fuorisaver **stima, non garantisce la sicurezza alimentare**: in caso di dubbio, fidati di naso e buon senso.

## Stack

- Python + [uv](https://docs.astral.sh/uv/)
- [Streamlit](https://streamlit.io) per la UI (usabile anche dal telefono in LAN)
- SQLite per i dati
- Gemma 4 su [Ollama](https://ollama.com) (sul Mac host, per sfruttare la GPU)
- OpenCV per la lettura dei codici a barre
- Docker Compose per il deploy

## Avvio rapido

Prerequisito: [Ollama](https://ollama.com) installato e con il modello scaricato.

```bash
ollama pull gemma4:e4b
```

**Con Docker** (l'app nel container, Ollama sull'host):

```bash
make up        # build e avvio
make logs      # log
make down      # stop
```

**In locale** con uv:

```bash
make install
make run
```

Poi apri <http://localhost:8501>.

Per usare un altro modello: `OLLAMA_MODEL=nome-modello make up`.

## Comandi utili

| Comando       | Cosa fa                                              |
| ------------- | ---------------------------------------------------- |
| `make test`   | esegue i test (parser date, shelf life, barcode, db) |
| `make bench`  | benchmark della lettura date sulle foto di etichette |
| `make notify` | invia le notifiche ntfy (richiede `NTFY_TOPIC`)      |

## Struttura del progetto

```
app/
  main.py        UI Streamlit (Inventario, Aggiungi, Ricette)
  vision.py      client Ollama, prompt e JSON schema
  dates.py       parsing e normalizzazione delle date in etichetta
  barcode.py     lettura EAN e lookup su Open Food Facts
  receipt.py     scontrino → righe → prodotti
  shelf_life.py  stima della scadenza da tabella
  recipes.py     ricette sui prodotti in scadenza
  models.py      modello dati (Item)
  db.py          storage SQLite
data/shelf_life.yaml   durate di conservazione per categoria e stato
scripts/               benchmark, notifiche, fixture
tests/                 test e fixture reali
```

## Roadmap

- Statistiche sullo spreco (euro buttati)
- Lista della spesa
- Meal planner

Contributi benvenuti. 🍅
