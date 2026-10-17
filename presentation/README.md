# fuorisaver — pitch per Hacktoberfest Milan

Presentazione in 12 slide per raccontare il progetto in circa 6 minuti.
Il nome del prodotto è **fuorisaver**: *il salvatore del fuorisede*.

## File

- `index.html` — deck 16:9, senza dipendenze esterne salvo logo e favicon in `../assets/`
- `Frigo-pitch.pdf` — export pronto da proiettare o consegnare

Il marchio viene da `assets/`:
`fuorisaver-morso-tile.svg` per i loghi piccoli,
`fuorisaver-morso-mark.svg` per il badge della slide finale,
`favicon.png` per la scheda del browser.

## Come presentare

Apri `index.html` nel browser, poi:

- `←` / `→` oppure `Spazio` — cambia slide
- `F` — fullscreen
- `N` — mostra/nasconde le note del relatore
- `Home` / `End` — prima/ultima slide

Le note sono incluse nell'HTML e non compaiono nel PDF.

## Durata

Il percorso completo è pensato per ~6 minuti. Per un pitch da 3 minuti, tieni le slide:

1. Copertina
2. Il problema
3. L'intuizione
4. La soluzione
5. L'inventario (demo)
11. Stato e roadmap
12. Chiusura

Salta le slide tecniche 6–10 e condensa l'impatto in una frase.

## Rigenerare il PDF

```bash
cd presentation
chromium --headless --no-sandbox --disable-gpu \
  --no-pdf-header-footer \
  --print-to-pdf=Frigo-pitch.pdf \
  --virtual-time-budget=3000 \
  file://$PWD/index.html
```

## Nota sui contenuti

La presentazione descrive il prototipo attuale: inventario a semaforo, quattro vie
d'ingresso (foto prodotto, etichetta, codice a barre, scontrino in beta), scadenze a
tre livelli di affidabilità (`label`, `manual`, `estimated`), ricette, notifiche ntfy,
test e stack locale (Gemma 4 via Ollama, Streamlit, SQLite, Open Food Facts opzionale).

Le slide di roadmap distinguono esplicitamente ciò che è già presente da ciò che è previsto.
