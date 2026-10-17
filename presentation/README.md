# Frigo — pitch per Hacktoberfest Milan

Presentazione in 11 slide per raccontare il progetto in circa 6 minuti.

## File

- `index.html` — deck 16:9, senza dipendenze esterne salvo il logo in `../assets/`
- `Frigo-pitch.pdf` — export pronto da proiettare o consegnare

Il logo (favicon, footer e badge di chiusura) viene da `assets/`:
`fuorisaver-morso-tile.svg` per i marchi piccoli,
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
2. Problema
3. Intuizione
4. Soluzione
5. Demo
9. Stato e roadmap
11. Chiusura

Salta le slide tecniche 6–8 e condensa l'impatto in una frase.

## Rigenerare il PDF

```bash
cd presentation
chromium --headless --no-sandbox --disable-gpu \
  --no-pdf-header-footer \
  --print-to-pdf=Frigo-pitch.pdf \
  --virtual-time-budget=2000 \
  file://$PWD/index.html
```

## Nota sui contenuti

La presentazione descrive il prototipo attuale: inventario, inserimento da scontrino/prodotto/etichetta, ricette, notifiche e stack locale. Le slide di roadmap distinguono esplicitamente ciò che è già presente da ciò che è previsto.
