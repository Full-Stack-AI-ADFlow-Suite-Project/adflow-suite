---
name: AdFlow Suite
description: La comunicazione social delle botteghe artigiane, curata dal consorzio.
colors:
  primary: "#2f5d46"
  primary-hover: "#254b38"
  primary-light: "#eef5f1"
  primary-border: "#b8d5c4"
  bg-app: "#f7f5ef"
  bg-surface: "#ffffff"
  bg-surface-subtle: "#efeae0"
  border-hairline: "#ddd6c7"
  border-strong: "#c7bfb0"
  text-main: "#1f2a24"
  text-secondary: "#474239"
  text-muted: "#635d52"
  text-faint: "#6b655a"
  accent-walnut: "#7a5230"
  success: "#16a34a"
  warning: "#d97706"
  danger: "#dc2626"
  info: "#0284c7"
  fb-blue: "#1877f2"
  ig-pink: "#e1306c"
typography:
  display:
    fontFamily: '"Inter Tight", "Source Sans 3", sans-serif'
    fontWeight: 800
    letterSpacing: "-0.045em"
    lineHeight: 1
  headline:
    fontFamily: '"Source Sans 3", -apple-system, "Segoe UI", Roboto, sans-serif'
    fontWeight: 700
    letterSpacing: "-0.015em"
  body:
    fontFamily: '"Source Sans 3", -apple-system, "Segoe UI", Roboto, sans-serif'
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: '"Source Sans 3", -apple-system, "Segoe UI", Roboto, sans-serif'
    fontSize: "12px"
    fontWeight: 600
    letterSpacing: "0.14em"
  mono:
    fontFamily: '"JetBrains Mono", ui-monospace, Menlo, monospace'
    fontSize: "13px"
rounded:
  sm: "6px"
  md: "10px"
  lg: "14px"
  xl: "18px"
  full: "9999px"
spacing:
  sm: "8px"
  md: "16px"
  lg: "24px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "#ffffff"
    rounded: "{rounded.md}"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
    textColor: "#ffffff"
    rounded: "{rounded.md}"
  card:
    backgroundColor: "{colors.bg-surface}"
    textColor: "{colors.text-main}"
    rounded: "{rounded.lg}"
    padding: "20px"
  nav-item:
    backgroundColor: "transparent"
    textColor: "{colors.text-secondary}"
    rounded: "{rounded.md}"
    padding: "9px 12px"
  nav-item-active:
    backgroundColor: "{colors.primary-light}"
    textColor: "{colors.primary}"
    rounded: "{rounded.md}"
    padding: "9px 12px"
---

# Design System: AdFlow Suite

## Overview

**Creative North Star: "La Bottega Editoriale"**

AdFlow Suite è lo strumento di lavoro di un consorzio di artigiani: un banco ordinato dove le foto della bottega diventano campagne social. L'estetica unisce la materia dell'artigianato — carta calda, verde bosco, un accento di noce — con la cura tipografica di una rivista: gerarchie pulite, respiro, un marchio in due voci. È un'app Operate/Read: la precisione conta più dell'espressione, e ogni scelta visiva serve a far capire all'artigiano cosa gli si chiede e all'operatore cosa richiede un giudizio.

Non è un SaaS generico: niente gradienti viola-blu, niente card dentro card, niente blu elettrico, niente estetica da template. Ogni colore ha un nome e un perché.

**Key Characteristics:**
- Neutri caldi su carta (`#f7f5ef`, `#efeae0`), mai grigi freddi
- Un solo accento portante: il Verde Consorzio `#2f5d46`
- Separazioni con bordi sottili `#ddd6c7`, non con ombre
- Tipografia Source Sans 3 con gerarchia marcata; marchio in Inter Tight + Instrument Serif corsivo
- Solo tema chiaro; il percorso dell'artigiano nasce a 375 px

## Colors

La palette è piccola e dichiarata: un verde, una scala di caldi neutri di carta, un accento noce, quattro colori di stato.

### Primary
- **Verde Consorzio** (#2f5d46): azioni primarie, voce attiva di navigazione, elementi del marchio. Nel codice il ramp si chiama `blu` per eredità storica (alias `verde`): i nomi Mantine non cambiano.
- **Verde Profondo** (#254b38): hover del primario, testo del marchio su sfondo chiaro alternativo.
- **Verde Nebbia** (#eef5f1): fondo degli stati attivi e selezionati (nav attiva, badge chiari).
- **Verde Bordo** (#b8d5c4): bordi degli elementi selezionati o in evidenza.

### Neutral
- **Carta Calda** (#f7f5ef): fondo dell'app, sempre.
- **Bianco Foglio** (#ffffff): superfici che portano contenuto — card, barra laterale.
- **Carta Sfumata** (#efeae0): fondi secondari, hover delle voci, fondo del piede della barra.
- **Hairline Carta** (#ddd6c7): ogni separazione strutturale.
- **Bordo Fermo** (#c7bfb0): bordi che devono reggere da soli.
- **Inchiostro** (#1f2a24): testo principale, mai nero puro.
- **Inchiostro Secondo** (#474239), **Inchiostro Tenue** (#635d52), **Inchiostro Fievole** (#6b655a): gerarchia del testo secondario. Sono stati scuriti rispetto al foglio statico per il contrasto WCAG (4,5:1): non si schiariscono.

### Accento e stato
- **Noce** (#7a5230): unico accento caldo, per segni rari del marchio o del dettaglio editoriale.
- Stati: verde `#16a34a`, ambra `#d97706`, rosso `#dc2626`, azzurro `#0284c7`, sempre con il loro fondo chiaro (variante `light`). Canali: `#1877f2` Facebook, `#e1306c` Instagram.

### Named Rules
**La Regola dell'Unica Voce.** Il Verde Consorzio parla per l'azione o lo stato attivo: poche aree per schermata. La sua rarità è il punto.
**La Regola dell'Inchiostro Mai Nero.** Il testo è `#1f2a24`; i grigi freddi di default non esistono in questa palette.

## Typography

**Display Font:** Inter Tight 800 (solo la parola «ad» del marchio) con Instrument Serif corsivo per «flow»
**Body Font:** Source Sans 3 (con fallback di sistema)
**Label/Mono Font:** Source Sans 3 per le etichette; JetBrains Mono per codice e valori tecnici

**Character:** una voce editoriale sobria: una sola famiglia per tutta l'interfaccia, peso e misura a fare la gerarchia; la coppia Inter Tight/Instrument Serif vive solo nel marchio, come una firma.

### Hierarchy
- **Display** (Inter Tight 800, −0,045 em): solo il wordmark; il «flow» in Instrument Serif corsivo, più leggero e lievemente più grande, in Verde Consorzio.
- **Headline** (Source Sans 3 700, `text-wrap: balance`, −0,015 em): titoli di pagina e di sezione.
- **Title** (600): titoli di card, nomi di campagne e botteghe.
- **Body** (400, 14 px, interlinea 1,5): testo di lavoro, testi dei post, spiegazioni.
- **Label** (600, 12 px, maiuscoletto con 0,14 em di tracking): sopratitoli e metadati (es. sottotitolo della card di accesso).
- **Mono** (JetBrains Mono, 13 px): ID, orari tecnici, conteggi.

### Named Rules
**La Regola della Firma Unica.** Inter Tight e Instrument Serif non entrano mai nel corpo dell'interfaccia: compaiono solo nel wordmark.

## Layout

- Cornice con barra laterale fissa di **250 px**, bordo destro hairline, marchio in testa, voci in colonna, piede con l'utente su fondo Carta Calda.
- Il contenuto respira su Carta Calda; le superfici che portano azione o contenuto sono Bianco Foglio separate da hairline.
- Densità da strumento: spaziature su scala Mantine (md 16 px di base), pagine dell'operatore più dense di quelle dell'artigiano.
- **Il percorso dell'artigiano nasce a 375 px**: la barra si chiude su telefono e il nome della bottega resta visibile anche a menu chiuso; i target di tocco seguono le linee guida AA.
- La pagina di accesso è l'unica eccezione "vetrina": fotografia a tutto schermo con velatura scura e card con `backdrop-filter: blur(6px)`.

## Elevation & Depth

Piatta con bordi sottili: le ombre del tema sono quasi impercettibili (inchiostro al 5% di opacità) e servono solo a staccare la card dal fondo; la struttura la portano gli hairline e la stratificazione dei neutri caldi.

### Shadow Vocabulary
- **Appoggio** (`0 1px 2px 0 rgba(31,42,36,0.05)` — xs): default di card e superfici.
- **Separazione** (`0 1px 3px 0 rgba(31,42,36,0.05)` — sm): superfici che leggono sopra un fondo sfumato.
- Ombre più lunghe (md–xl) esistono nella scala ma non entrano nei componenti ordinari: riserva a popover e overlay.

### Named Rules
**La Regola del Piatto di Default.** Le superfici sono piatte a riposo e si distinguono per bordo, non per ombra. L'ombra non è mai il motivo di una gerarchia.

## Shapes

Scala di raggi morbidi e brevi: **6 / 10 / 14 px** (sm/md/lg), 18 px per i contenitori ampi, `9999 px` solo per pallini e pillole (puntino di stato, badge). Nessun angolo vivo, nessun raggio teatrale: la curva è quella degli strumenti da banco, non quella delle app consumer.

## Components

### Buttons
- **Shape:** raggio medio (10 px)
- **Primary:** Verde Consorzio pieno, testo bianco; hover Verde Profondo
- **Hover / Focus:** transizione breve di fondo; focus con outline da 2 px nel colore primario e offset 2 px (uguale alle pagine statiche)
- **Secondary / subtle:** testo e bordo sui grigi caldi, mai un secondo accento

### Badges e stati
- **Style:** variante `light` — testo del colore di stato su fondo chiaro, con un pallino pieno di 6 px a sinistra
- **Contenuto:** l'etichetta è sempre una parola umana (mai il valore del database); al passaggio del mouse un tooltip spiega lo stato
- Il testo dei badge chiari usa il valore corretto `#1f6a2f` per il contrasto 5,8:1

### Cards / Containers
- **Corner Style:** 14 px
- **Background:** Bianco Foglio
- **Shadow Strategy:** appoggio xs (Regola del Piatto di Default)
- **Border:** hairline `#ddd6c7`; hover con fondo `#efeae0` dove la card è interattiva
- **Internal Padding:** scala Mantine, ~20 px

### Inputs / Fields
- **Style:** bordo su grigio caldo, fondo Bianco Foglio, raggio medio
- **Focus:** bordo `#3f7a5b` (Verde Medio) — l'outline da 2 px resta il segnale universale di tastiera
- **Error / Disabled:** rosso di stato per errore; disabilitato su Carta Sfumata con testo tenue

### Navigation
- Barra laterale bianca su Carta Calda, voci da 13,5 px peso 500 con icona lineare da 19 px
- Voce attiva: fondo Verde Nebbia, testo Verde Consorzio peso 600
- Hover: fondo Carta Sfumata
- Su telefono la barra si chiude; restano identità della bottega e azioni essenziali

### Wordmark
- «ad» in Inter Tight 800 colore inchiostro + «flow» in Instrument Serif corsivo Verde Consorzio; variante `chiaro` (bianco + verde chiaro) su foto e sfondi scuri. Mai ricomposto a mano: si usa il componente `Wordmark`.

## Do's and Don'ts

### Do:
- **Do** usare i token del tema (`--mantine-color-blu-*`, `--bg-app`, `--text-*`): i nomi restano quelli del foglio `adflow.css`, i valori vivono in `tema.ts`.
- **Do** separare con gli hairline `#ddd6c7` e stratificare i neutri caldi invece di aggiungere ombre.
- **Do** tenere l'outline di focus da 2 px Verde Consorzio su ogni elemento interattivo.
- **Do** mostrare stati come parole umane con tooltip esplicativo, mai come valori del backend.
- **Do** verificare il percorso dell'artigiano a 375 px ad ogni cambio visivo.

### Don't:
- **Don't** introdurre un secondo accento, gradienti o colori freddi fuori palette: un solo verde parla.
- **Don't** usare Inter Tight o Instrument Serif nel corpo: sono la firma del marchio.
- **Don't** schiarire i grigi del testo sotto `#6b655a`: sono già al limite WCAG AA.
- **Don't** annidare card dentro card: si usa Carta Sfumata o un divisore hairline.
- **Don't** cambiare comportamento per un intervento visivo: rotte, campi, stati e ordine dei passi restano (perimetro I6).
