Context

App locale che usa un modello open multimodale (Gemma 4) per tenere traccia del cibo in frigo e avvisare prima che scada, per ridurre sprechi e spesa buttata. La repo hacktoberfest-milan è vuota (nessun commit), quindi si parte da zero.

Nota di design: lo scontrino non contiene scadenze. Fornisce nomi, quantità, prezzi e data d'acquisto. La scadenza è quindi data_acquisto + shelf_life(tipo, stato), marcata come estimated, e viene sostituita da una data label quando l'utente fotografa l'etichetta.

Stack

- Python gestito con uv (pyproject.toml, uv.lock)
- UI Streamlit (web app, accessibile dal telefono in LAN)
- Storage SQLite (volume Docker)
- Modello Gemma 4 via Ollama sul Mac host (GPU Metal). Il container chiama http://host.docker.internal:11434. Ollama dentro Docker su macOS girerebbe solo su CPU, quindi no.
- App containerizzata: Dockerfile (immagine uv) + compose.yaml (app + volume dati)
- OCR: prima si valuta Gemma 4 da solo. Il fallback Tesseract/PaddleOCR nel container serve solo se il benchmark sulle date è insufficiente (Apple Vision non è disponibile in Docker).
- Tabella shelf-life in YAML (basata su USDA FoodKeeper), versionata nella repo

Struttura

- pyproject.toml, Dockerfile, compose.yaml
- app/main.py: entry Streamlit, con le pagine Inventario, Aggiungi (foto / etichetta / scontrino) e Ricette
- app/models.py: Item(nome, categoria, stato, qty, prezzo, acquistato_il, scadel | estimated | manual, confidenza)
- app/db.py: SQLite
- app/shelf_life.py + data/shelf_life.yaml: giorni per (categoria, stato: chius
- app/vision.py: client Ollama, prompt e JSON schema per prodotto, etichetta e
- app/dates.py: normalizzazione formati (EXP 12/10/26, 12.10.2026, L:2610A) e dd) da "preferibilmente entro" (soft)
- app/receipt.py: scontrino → righe → espansione abbreviazioni → filtro non-fooata
- app/recipes.py: ricette sui leftovers ordinati per scadenza (fase 5)

Principi

- Il modello estrae e classifica. Date e regole di sicurezza vengono da dati dee dal modello.
- Ogni inserimento passa da conferma utente, con confidenza visibile.
- Le stime da scontrino sono marcate in UI ("circa").
- L'app stima, non garantisce la sicurezza alimentare (disclaimer in UI).

Fasi

1. Scaffolding uv + Docker + Streamlit, healthcheck verso Ollama
2. Foto prodotto → JSON → scadenza da tabella → inventario ordinato con semafor
3. Foto etichetta → data verificata
4. Scontrino → inserimento in blocco con stime e prezzi
5. Ricette, statistiche spreco (euro), notifiche
6. Barcode (Open Food Facts), lista della spesa, meal planner

Verifica

- Benchmark preliminare: 20 foto reali di etichette con Gemma 4. Misura l'accur se serve il fallback OCR.
- Test unitari (uv run pytest) su parser date e shelf_life
- Fixture reali in tests/fixtures/ con output atteso
- End-to-end: docker compose up, apri Streamlit, carica una foto e uno scontrino, controlla che l'inventario sia ordinato e che fonte_scadenza sia corretta
