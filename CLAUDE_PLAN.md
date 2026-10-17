Context

PLAN.md descrive un'app locale (Streamlit + SQLite + Gemma 4 via Ollama) che traccia il cibo in frigo e avvisa prima della scadenza. La repo è vuota (solo PLAN.md), quindi si parte da zero. Implementazione per fasi, committando (solo se richiesto) a fine di ogni fase.

Decisioni: scadenza = data_acquisto + shelf_life(categoria, stato), marcata estimated; sostituita da data label (label) o manual. Il modello estrae/classifica; date e regole di sicurezza vengono da dati/codice. Ogni inserimento passa da conferma utente.

Fase 1 – Scaffolding

- pyproject.toml (uv): streamlit, pydantic, httpx, pyyaml, pillow; dev: pytest. uv lock.
- Dockerfile (immagine uv, uv sync --frozen, streamlit run app/main.py), compose.yaml (servizio app, volume ./data-db:/db, OLLAMA_URL=http://host.docker.internal:11434, porta 8501, extra_hosts host-gateway).
- app/main.py: navigazione Inventario / Aggiungi / Ricette, disclaimer, healthcheck Ollama (GET /api/tags, verifica presenza modello Gemma configurabile via env OLLAMA_MODEL).
- app/vision.py (parte client): chat_json(image_bytes, prompt, schema) verso /api/chat con format=<json schema>.

Fase 2 – Foto prodotto → inventario

- app/models.py: Item pydantic (nome, categoria, stato [chiuso/aperto/cotto/congelato], qty, prezzo, acquistato_il, scade_il, fonte_scadenza [estimated|label|manual], confidenza).
- app/db.py: SQLite (path da env), init(), add_item, list_items ordinato per scadenza, update, delete.
- data/shelf_life.yaml + app/shelf_life.py: giorni per (categoria, stato), estimate(categoria, stato, acquistato_il); fallback conservativo per categoria ignota.
- app/vision.py: prompt + JSON schema per riconoscimento prodotto.
- UI Aggiungi (foto): upload/camera → proposta modificabile con confidenza → conferma → salva. Inventario con semaforo (rosso ≤2gg/scaduto, giallo ≤5gg, verde) e "circa" per le stime.

Fase 3 – Etichetta

- app/dates.py: parser formati (EXP 12/10/26, 12.10.2026, L:2610A, ecc.) e distinzione "da consumare entro" (hard) vs "preferibilmente entro" (soft).
- Prompt/schema etichetta in vision.py; UI: foto etichetta → data verificata (fonte_scadenza=label) su item esistente o nuovo.

Fase 4 – Scontrino

- app/receipt.py: immagine → righe (modello) → espansione abbreviazioni → filtro non-food → stima scadenze via shelf_life → inserimento in blocco con tabella editabile(st.data_editor) e conferma.

Fase 5 – Ricette, spreco, notifiche

- app/recipes.py: prompt testuale a Gemma con leftovers ordinati per scadenza.
- Pagina statistiche: euro sprecati (item scaduti/buttati × prezzo). Notifiche: banner in app + script/cron opzionale (es. ntfy) per items in scadenza.

Fase 6 – Opzionale

Barcode (Open Food Facts), lista della spesa, meal planner. Da fare solo dopo conferma, fuori dallo scope iniziale.

Test e verifica

- tests/test_dates.py, tests/test_shelf_life.py (uv run pytest); tests/fixtures/ con immagini reali + output atteso.
- Benchmark scripts/bench_labels.py su 20 foto di etichette: se l'accuratezza sulle date è insufficiente, aggiungere fallback Tesseract/PaddleOCR nel container.
- End-to-end: Ollama su host con Gemma 4 → docker compose up → apri http://localhost:8501 → carica foto prodotto, etichetta e scontrino → verifica ordinamento inventario, semaforo efonte_scadenza.
