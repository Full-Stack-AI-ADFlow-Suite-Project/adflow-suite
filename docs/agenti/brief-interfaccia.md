# Brief · Corsia 8 · Interfaccia ed esperienza d'uso (T3-80…T3-87)

Per chi fa un task della corsia 8. Decisione: ADR-118. Leggi prima `constitution.md` e `perimetro-mvp.md` (blocco I), poi il §1 di questa pagina, che vale per tutti, e **solo** la sezione del tuo task.

**Che cosa fa questa corsia.** Migliora l'aspetto (UI) e l'esperienza d'uso (UX) delle pagine dell'app e delle pagine statiche, senza cambiare che cosa l'app fa. Questa pagina **non decide** colori, caratteri, stile né scelte di esperienza d'uso: guida chi sviluppa a sceglierli da solo, anche senza esperienza di design. Per ogni scelta spiega prima **a che cosa serve**, poi propone **possibilità reali** già pronte, che si possono prendere così come sono. Le scelte si scrivono nel §4 e le approva il referente dei file comuni prima del task che le applica.

**Che cosa non cambia, mai.** Backend, rotte, chiamate in `src/api/`, campi dei moduli, validazioni, condizioni di visibilità, stati, ordine delle sezioni e dei passi, messaggi che arrivano dal backend, testi fissi (§1.4). Se una scelta di design chiede uno di questi cambi, non è di questa corsia: va nel §7.

**Regole di lavoro per tutti i task.**
- Un branch `feature/<id>-<breve>` da `main`; una PR per task, unibile da sola; fai solo il tuo task.
- Nessuna migrazione, nessun file del backend, nessuna libreria UI nuova (Mantine resta, ADR-04). L'unica libreria che può entrare è una di icone, se la scelta S7 la chiede, in `frontend/package.json`, con nome, motivo e licenza nella PR.
- **App e pagine statiche insieme**: ogni cambio di stile o di testo tocca sia `frontend/` sia `docs/pagine/`, così il passo 7 di converge §4 resta vero.
- Fatto quando, per ogni task che tocca il frontend: `npm run lint` e `npm run build` puliti da `frontend/`, il controllo del §1.5 senza risultati, screenshot prima e dopo nella PR. Poi la checklist di `converge.md` §1 e la casella del task in `tasks.md`.

---

## 1. Non rompere il codice

Questa sezione vale per ogni task e prevale su ogni scelta del §3. In caso di dubbio, la riga resta com'è.

### 1.1 File

| Si toccano (solo nel task che li cita) | Non si toccano mai |
|---|---|
| `frontend/src/tema.ts`, `frontend/src/index.css`, `frontend/index.html` (solo i `<link>` dei caratteri) | tutto `backend/`, `alembic/` |
| i `.module.css` esistenti e nuovi `.module.css` accanto al componente che li usa | `frontend/src/api/` (dati di esempio compresi) |
| i `.tsx` di `frontend/src/pages/` e `frontend/src/components/`, con i limiti del §1.2 | `App.tsx`, `main.tsx`, `auth.tsx`, `contesto-auth.ts` (rotte e accesso) |
| `docs/pagine/assets/adflow.css` e i testi delle pagine di `docs/pagine/` | i file di sola logica: `components/campagne/sezioni.ts`, `components/calendario-date.ts`, `pages/artigiano/campagna/viste/scelta.ts`, `pages/operatore/campagna/util.ts`, `pages/operatore/vedi-campagna/post/regole.ts`, `pages/operatore/vedi-campagna/decisioni/useInvio.ts` |
| `frontend/package.json` e il lock, solo per la libreria di icone di S7 | il codice congelato ("Congelato per l'MVP, ADR-114") |
| questa pagina, §4 | gli altri documenti di `docs/agenti/`, salvo la casella del task |

Nessun file si rinomina, si sposta o si cancella. Nessun nuovo `.tsx`: un pezzo di interfaccia che si ripete si sistema con il tema (proprietà predefinite dei componenti in `tema.ts`) o con una classe CSS.

### 1.2 Dentro un `.tsx`

| Si può cambiare | Non si cambia |
|---|---|
| proprietà visive dei componenti Mantine: `variant`, `color`, `size`, `radius`, `c`, `fw`, `fz`, `ta`, `p`/`m`/`gap`, `w`/`maw`, `fullWidth`, `shadow`, `withBorder`, `hiddenFrom`/`visibleFrom`, `cols` responsive di `SimpleGrid`, `className`, `style` | gestori: `onClick`, `onChange`, `onSubmit` e ogni `on…` |
| componenti di solo layout attorno agli stessi elementi (`Stack`, `Group`, `SimpleGrid`, `Box`, `Flex`), **senza cambiarne l'ordine** | hook di dati o di effetto: `useState`, `useEffect`, `useMemo`, chiamate, `navigate`, `useAuth` |
| icone decorative, con `aria-hidden`, accanto a un testo che resta | condizioni (`&&`, `? :`, `if`), `map`, `filter`, `sort`, `key` |
| i testi permessi, solo in T3-84 (§1.4) | proprietà di comportamento: `type`, `name`, `value`, `required`, `disabled`, `loading`, `href`, `to`, `accept`, `multiple` |
| | l'ordine di sezioni, passi, campi e pulsanti; quali elementi esistono |

**Unica eccezione**: lo stato aperto/chiuso di un menu o di un pannello puramente visivo (per esempio il menu della barra sul telefono) si tiene con `useDisclosure` di `@mantine/hooks`, già installato. Non legge dati, non chiama niente e non cambia che cosa si vede dopo averlo chiuso.

**I pulsanti dei moduli.** `Accesso.tsx`, `Passo10.tsx`, `Profilo.tsx` e `NuovoArtigiano.tsx` hanno pulsanti `type="submit"` dentro un `<form>`. Un pulsante resta nello stesso componente e nello stesso `<form>`: si sposta, si allarga o si mette in fondo allo schermo solo con il CSS o con le proprietà visive.

### 1.3 Tema e CSS: si cambiano i valori, non i nomi

- In `tema.ts` i nomi dei colori restano `blu`, `verde` e `gray`, anche se il colore scelto non è più blu: le pagine scrivono `color="verde"` (65 volte) e `color="blu"`. L'alias `verde: blu` resta finché #76 non lo toglie. Cambiano solo le 10 tinte dentro ogni tupla. `primaryColor` e `primaryShade` restano; `variabili` resta.
- I colori di stato delle pagine (`red`, `orange`, `yellow`, `green`, `grape`, `gray`, `dark`, `blue`) sono quelli di Mantine: si possono ritoccare in `tema.ts` solo se S5 lo chiede, tenendo lo stesso nome e lo stesso significato.
- In `adflow.css` si cambiano i valori delle variabili di `:root` (`--primary…`, `--bg-…`, `--text-…`, `--border-…`), non i loro nomi né i selettori. Nei `.module.css` le classi usate dai `.tsx` restano con lo stesso nome.
- I colori dei marchi (`--fb-blue`, `--ig-pink`) restano quelli di Facebook e Instagram.

### 1.4 Testi fissi

Restano uguali parola per parola, nell'app e nelle pagine statiche:

- i messaggi d'errore che arrivano dal backend (costituzione §4);
- la dichiarazione R-41: "Le foto mostrano prodotti della mia bottega; le persone riconoscibili hanno dato il consenso." Ha valore legale;
- "Immagine creata con AI" (regola delle immagini AI);
- i testi che spec e converge citano: Bentornato, "Va bene così" e "Modifica" (spec §2.1); «Pubblicazioni ferme» (B5, converge §4 passo 6); "Il consorzio ti chiede…" (`brief-pagine.md` §1.1);
- i nomi delle sezioni (In corso, In lavorazione, Passate, Storico, Da approvare) e le voci delle barre laterali (`brief-pagine.md` §1.1 e §1.3).

Chi vuole cambiare uno di questi testi non lo fa nella corsia: lo propone al referente, che aggiorna spec e converge in un'altra PR.

### 1.5 Controllo prima della PR

Da `frontend/`, uno alla volta:

```bash
npm run lint
npm run build
```

Dalla radice, i file cambiati devono essere solo quelli del task (§1.1):

```bash
git diff --name-only origin/main...HEAD
```

Nelle righe cambiate dei `.tsx` non devono comparire logica né comportamento. Il comando non deve stampare nulla; se stampa una riga, la PR spiega perché quella riga non cambia il comportamento, oppure la riga torna com'era:

```bash
git diff -U0 origin/main...HEAD -- "frontend/src/*.tsx" | grep -E "^[-+][^-+]" | grep -E "use(State|Effect|Memo|Callback|Navigate|Auth)\(|on[A-Z][A-Za-z]*=|navigate\(|\.(map|filter|sort)\(|type=\"|required|disabled=|loading=|from \"[./]*api/"
```

Testi fissi: lo stesso numero di righe prima e dopo, su `main` e sul branch (un comando per testo del §1.4):

```bash
git grep -c -F "Immagine creata con AI" -- frontend/src docs/pagine
```

A mano: i passi 2 e 4 di converge §4 nelle due finestre, operatore e artigiano, alle larghezze scelte in S2, senza errori nella console del browser.

### 1.6 Paracadute

Ogni punto di scelta del §3 ha la possibilità "com'è oggi". Ciò che il 30/10 non è su `main` resta com'è oggi, che funziona: nessuna PR a metà.

---

## 2. Come si sceglie

Chi non è esperto di design segue questo metodo, un punto di scelta alla volta.

1. **Leggi la funzione.** Che cosa deve ottenere quella scelta in AdFlow, per chi e su quale schermo.
2. **Guarda i criteri.** Sono il modo di capire se una possibilità funziona: accessibilità, leggibilità, coerenza con Mantine, giorni di lavoro, rischio per il codice.
3. **Guarda le possibilità.** Sono esempi reali e completi: si possono prendere così come sono, oppure si mescolano rispettando i criteri. La prima è sempre "com'è oggi".
4. **Se non sai scegliere**, rispondi alle domande del punto: ti portano a una possibilità.
5. **Prova prima di decidere** quando la scelta è visiva (S4–S7): su copie delle pagine statiche, non nell'app (T3-82).
6. **Scrivi la scelta nel §4**, con una frase di motivazione che si possa dire anche nel pitch (T3-05). Il referente la approva con la data.

**Ordine.** Prima le scelte d'uso (S1, S2, S3, S8, in T3-81), poi quelle visive (S4–S7, in T3-82): lo stile segue il modo in cui le persone usano l'app, non il contrario.

**Una tabella per confrontare.** Quando le possibilità sono più di due, la PR del task porta una tabella così, con un voto da 1 a 3:

| Possibilità | Adatta a chi la usa | Leggibile sul telefono | Coerente con Mantine | Giorni di lavoro | Rischio per il codice |
|---|---|---|---|---|---|
| … | | | | | |

**Criteri che valgono per tutte le scelte.**
- Contrasto WCAG 2.1 AA: almeno 4,5:1 per il testo normale, 3:1 per il testo grande (dai 24 px, o 19 px in grassetto), bordi, icone e badge. Si verifica con WebAIM Contrast Checker o con la formula WCAG.
- Nessuna informazione affidata solo al colore: uno stato ha anche una parola o un'icona.
- Focus della tastiera visibile su ogni elemento cliccabile.
- Sul telefono, bersagli da toccare di almeno 44 × 44 px; campi dei moduli con testo di almeno 16 px (sotto, iOS ingrandisce la pagina).
- Due ruoli, due contesti: l'artigiano spesso dal telefono, in bottega; l'operatore dal PC, con molte campagne da guardare.

---

## 3. Punti di scelta

Ogni punto ha: funzione, criteri propri, possibilità, domande per chi non sa scegliere, che cosa non si tocca. Le possibilità citano riferimenti noti per farsi un'idea: si guardano, non si copiano.

### S1 · Modo d'uso per ruolo (paradigma UX) · T3-81

**Funzione.** Decidere come ragiona chi usa ogni pagina, così che ogni altra scelta abbia un perché. Si sceglie per l'artigiano e per l'operatore, anche in modo diverso; per ogni ruolo una o più possibilità.

**Criteri.** Il ruolo e il suo schermo; che cosa la persona deve fare per prima cosa sulla pagina; ciò che la possibilità chiede deve stare nel §1.

**Possibilità.**

| | Che cos'è | Riferimenti | In AdFlow c'è già | Che cosa si può fare | Che cosa no |
|---|---|---|---|---|---|
| **U0 · Com'è oggi** | Nessun paradigma nuovo | — | — | Solo lo stile di T3-83 | — |
| **U1 · Doppia densità** | Pagine comode e ariose per chi usa poco e dal telefono; pagine dense e compatte per chi lavora molte ore al PC | Shopify (app e admin), Airbnb (ospite e host) | Tabella degli artigiani con intestazione fissa (`Artigiani.tsx`) | Spaziature, dimensioni del testo, colonne e larghezze diverse per ruolo, con il CSS e le proprietà visive | Togliere o aggiungere colonne, informazioni o pulsanti |
| **U2 · Domande guidate** | Ogni campo è una domanda diretta, come al telefono con il consorzio; i passi si sentono come una conversazione | Typeform, Airbnb "Diventa un host", Duolingo | I passi 1–9 del profilo e 10–12 della campagna | Testi delle etichette, delle descrizioni e dei segnaposto (S8, T3-84); un titolo per passo più evidente | Cambiare il numero, l'ordine o il contenuto dei passi; una domanda per schermata |
| **U3 · Una sola azione principale** | In ogni schermata un solo pulsante pieno, gli altri leggeri; sul telefono il pulsante principale è grande e vicino al pollice | Apple HIG, Material Design 3, Revolut, N26 | — | `variant`, `fullWidth`, `size`, posizione con il CSS (S3) | Spostare un pulsante in un altro componente o fuori dal suo `<form>`; cambiare `onClick`, `disabled`, `loading` |
| **U4 · Prima ciò che chiede un'azione** | In cima e in evidenza ciò che aspetta la persona; ciò che va da sé resta più quieto | Basecamp, Linear Triage, Todoist | La richiesta del consorzio in cima all'Ingresso (H1); Campagne da approvare ordinate per "entro quando" (`DaApprovare.tsx`) | Dare più risalto visivo a ciò che è già in cima: colore, bordo, dimensione, icona | Cambiare l'ordine delle sezioni o l'ordinamento dei dati |
| **U5 · Il post come apparirà** | L'operatore approva l'oggetto finito, simile a come uscirà sul social, non un record di testo | Buffer, Later, Meta Business Suite | `PostCard.tsx` con foto, testo e "Immagine AI" | Stile della card vicino a quello di un post: bordi, proporzioni della foto con il CSS, gerarchia dei testi | Spostare o riordinare le azioni del post (`AzioniPost.tsx`); mostrare all'artigiano i post prima dell'approvazione (H1, §7) |

**Se non sai scegliere.**
- L'artigiano userà l'app dal telefono, in bottega? Se sì, U3, con U2 se i testi oggi lo bloccano.
- L'operatore guarda molte campagne di seguito? Se sì, U1, con U5 in Vedi campagna.
- Una persona entra e non capisce che cosa deve fare? U4.
- Mancano i giorni? U0 per il ruolo che conta meno nella demo.

### S2 · Schermi e pagine da telefono · T3-81

**Funzione.** Decidere a quali larghezze ogni pagina deve funzionare, così T3-85 sa dove lavorare e T3-87 dove provare.

**Criteri.** Il percorso della demo (converge §4, passi 2 e 4) prima di tutto; nessuno scorrimento orizzontale e nessuno zoom alle larghezze scelte; il PC (1280 px) resta com'è dopo T3-83.

**In AdFlow c'è già.** Sotto gli 860 px la barra laterale va in alto (`Guscio.module.css`); sotto i 768 px il calendario settimanale diventa un elenco per giorno (`CalendarioSettimana.module.css`).

**Possibilità.**

| | Pagine | Larghezze |
|---|---|---|
| **L0 · Com'è oggi** | — | PC; sul telefono quello che c'è già |
| **L1 · Il percorso della demo** | Accesso, Ingresso, pagina Campagna (passi 10–12, viste per stato, richiesta del consorzio) | 375 px e 1280 px |
| **L2 · Tutto l'artigiano** | L1, più Profilo bottega (passi 1–9), Campagne, Archivio foto, Calendario | 375 px e 1280 px |
| **L3 · Anche l'operatore su tablet** | L2, più le pagine dell'operatore | 375 px per l'artigiano, 768 px e 1280 px per l'operatore |

**Se non sai scegliere.** Quanti giorni restano prima del 30/10? Due o meno: L1. Tre o più: L2. L3 solo se il consorzio ha detto che l'operatore usa un tablet.

### S3 · Gerarchia delle azioni · T3-81

**Funzione.** Far capire a colpo d'occhio qual è il prossimo passo, e rendere difficile premere per errore un'azione che non si voleva.

**Criteri.** Un'azione che annulla, respinge o sospende non deve sembrare l'azione principale; i pulsanti sul telefono rispettano i 44 px; il §1.2 sui pulsanti dei moduli.

**Possibilità.**

| | Pulsante principale | Gli altri | Sul telefono |
|---|---|---|---|
| **G0 · Com'è oggi** | com'è | com'è | com'è |
| **G1 · Uno pieno, gli altri leggeri** | `variant="filled"`, uno per schermata | `variant="light"` o `"subtle"` | il principale `fullWidth` |
| **G2 · Uno pieno, gli altri con il bordo** | `variant="filled"` | `variant="outline"` (secondari), `"subtle"` (terziari) | il principale `fullWidth`, in fondo alla sua sezione |
| **G3 · Come G1, con le azioni distruttive in rosso** | `variant="filled"` | `"light"`; annulla, respingi, sospendi con `color="red"` e `variant="light"` | come G1 |

**Se non sai scegliere.** Le schermate di oggi hanno più pulsanti pieni uno accanto all'altro? G1. L'operatore preme spesso azioni che non volevi rendere facili? G3.

### S4 · Stile visivo · T3-82

**Funzione.** Dare all'app un carattere che dica in mezzo secondo per chi è: un consorzio di artigiani, non un gestionale. Si può scegliere uno stile per l'artigiano e uno per l'operatore, purché il tema resti uno solo (stessa palette e stessi caratteri, densità diverse).

**Criteri.** Coerente con S1; realizzabile con il tema di Mantine e con `adflow.css`, senza librerie; le pagine statiche lo seguono.

**Possibilità.**

| | Che cos'è | Riferimenti | Quando ha senso |
|---|---|---|---|
| **V0 · SaaS essenziale (com'è oggi, ADR-113)** | Fondo chiaro, card bianche con bordo sottile, pochi colori, un carattere monospaziato per numeri, date e costi; il colore quasi solo nei badge di stato | Linear, Stripe Dashboard, Raycast, Cal.com | Per l'operatore funziona già; per l'artigiano risulta freddo |
| **V1 · Caldo editoriale ("bottega")** | Fondo color carta, card bianche con bordi color sabbia, colori della materia, un carattere con le grazie nei titoli e uno senza grazie nel testo | Airbnb, Etsy, Substack, Kinfolk | Quando si vuole che si capisca subito che è per artigiani |
| **V2 · Istituzionale naturale ("consorzio")** | Un colore profondo e sobrio su fondo avorio, accenti caldi, un solo carattere morbido per titoli e testo | Shopify Admin, Patagonia, Slow Food, Wise | Quando si vuole trasmettere solidità e fiducia; facile da tenere anche nelle tabelle |
| **V3 · A riquadri (card-first)** | La pagina divisa in riquadri arrotondati, uno per concetto, che sul PC stanno affiancati e sul telefono uno sotto l'altro. Si combina con V0, V1 o V2 | Apple, Buffer, Mantine UI | Quando le pagine hanno già blocchi separati, come l'Ingresso |

**Se non sai scegliere.** Nel pitch vuoi dire "è fatto per gli artigiani"? V1. Vuoi dire "è uno strumento serio del consorzio"? V2. Vuoi cambiare poco? V0 con la palette di S5. In ogni caso, V3 si aggiunge se le pagine hanno già riquadri.

### S5 · Palette · T3-82

**Funzione.** Scegliere i colori che portano lo stile di S4: uno primario (pulsanti, link, voce attiva), il fondo, il testo, eventualmente un accento. I colori di stato (successo, avviso, errore) restano riconoscibili.

**Criteri.** I contrasti del §2; l'accento sotto 4,5:1 si usa per bordi, icone e badge, mai per il testo; il primario deve distinguersi dai colori di stato.

**Possibilità** (contrasti calcolati con la formula WCAG 2.1):

| | Primario | Fondo | Testo | Accento | Primario sul fondo | Bianco sul primario | Testo sul fondo | Accento sul fondo |
|---|---|---|---|---|---|---|---|---|
| **P0 · Com'è oggi** | blu `#2563EB` | `#F8FAFC` | `#0F172A` | — | 4,9 | 5,2 | 17,1 | — |
| **P1 · Bottega** (va con V1) | terracotta `#9A4422` | crema `#FBF7F2` | `#2B2420` | salvia `#6B8F71` | 6,1 | 6,5 | 14,3 | 3,4 |
| **P2 · Legno e bosco** (va con V2) | verde bosco `#2F5D46` | avorio `#F7F5EF` | `#1F2A24` | noce `#7A5230` | 6,9 | 7,6 | 13,6 | 6,3 |
| **P3 · Blu notte caldo** (va con V0 o V2) | blu petrolio `#1F5A6B` | `#F8F6F1` | `#1C2A30` | ocra `#B7791F` | 7,1 | 7,7 | 13,7 | 3,4 |

Le tinte sono un punto di partenza: si possono spostare, purché i contrasti restino nei criteri.

**Come si applica (T3-83).** Per ogni colore scelto si generano le 10 tinte con il generatore di colori della documentazione di Mantine; il colore scelto va all'indice 6, perché `primaryShade` è 6. Le tinte vanno nella tupla `blu` di `tema.ts` (il nome resta, §1.3); fondo, bordi e testo nella tupla `gray`; gli stessi valori nelle variabili di `:root` di `adflow.css`.

**Se non sai scegliere.** Segui S4: V1 → P1, V2 → P2, V0 → P0 o P3. Strumenti per vederla su una pagina vera: Realtime Colors, Coolors.

### S6 · Caratteri · T3-82

**Funzione.** Rendere i testi facili da leggere anche su un telefono con poca luce, e dare voce allo stile di S4.

**Criteri.** Leggibili a 14–16 px; lettere che non si confondono (I, l, 1; 0, O); accenti italiani; pesi da 400 a 700; licenza libera (OFL di Google Fonts); al massimo due famiglie, più il monospaziato per numeri e codici.

**Possibilità.**

| | Titoli | Testo | Numeri e codici | Va con |
|---|---|---|---|---|
| **F0 · Com'è oggi** | Inter | Inter | JetBrains Mono | V0 |
| **F1 · Grazie nei titoli** | Fraunces | Source Sans 3 | JetBrains Mono | V1 |
| **F2 · Un solo carattere umanista** | Source Sans 3 | Source Sans 3 | JetBrains Mono | V2, V0 |
| **F3 · Un solo carattere morbido** | Nunito Sans | Nunito Sans | JetBrains Mono | V2, V3 |

**Come si applica (T3-83).** Il `<link>` di Google Fonts in `frontend/index.html`; `fontFamily` e `headings.fontFamily` in `tema.ts`; l'`@import` in cima ad `adflow.css` e le sue `font-family`. Nessun pacchetto npm.

**Se non sai scegliere.** Segui S4: V1 → F1, V2 → F2, V0 → F0.

### S7 · Icone · T3-82

**Funzione.** Aiutare a riconoscere al volo voci, sezioni e avvisi (foto, calendario, bottega, campagna, avviso). Un'icona accompagna un testo, non lo sostituisce.

**Criteri.** Poche e sempre le stesse per lo stesso concetto; decorative (`aria-hidden`); un solo set in tutta l'app; licenza compatibile.

**Possibilità.**

| | Come | Costo |
|---|---|---|
| **I0 · Com'è oggi** | Nessuna icona nell'app | — |
| **I1 · SVG inline** | Le stesse icone SVG già nelle pagine statiche, copiate nei `.tsx` dove servono | nessuna libreria; più righe nei `.tsx` |
| **I2 · Una libreria di icone React** | Per esempio `@tabler/icons-react` (MIT, il set della documentazione di Mantine) o `lucide-react` (ISC) | una dipendenza in `frontend/package.json`, con nome, motivo e licenza nella PR di T3-83 |

**Se non sai scegliere.** Ti servono più di cinque icone? I2. Meno: I1.

### S8 · Tono dei testi · T3-81

**Funzione.** Far sentire all'artigiano che parla con il consorzio, non con un database. Vale per i testi visibili scritti nel frontend; i testi fissi (§1.4) restano.

**Criteri.** L'app dà già del tu ("Il consorzio ti chiede…", Bentornato): il tono resta al tu. Parole della bottega (lavoro, foto, clienti, fiera), non del database (gruppo, asset, descrizione, campo). Frasi brevi. Dire perché si chiede una cosa, quando non è ovvio. Negli avvisi, che cosa fare e non solo che cosa non va.

**Possibilità.**

| | Che cos'è | Dove |
|---|---|---|
| **T0 · Com'è oggi** | Nessun testo cambia | — |
| **T1 · Domande dirette** | Le etichette diventano domande, come al telefono | pagine dell'artigiano |
| **T2 · Etichette brevi e chiare** | Le etichette restano etichette, ma con le parole della bottega e una riga di aiuto sotto | pagine dell'artigiano |
| **T3 · T1 o T2, anche per l'operatore** | La stessa pulizia anche nelle sue pagine, con un tono più asciutto | tutte le pagine |

**Esempi da `main`** (si scelgono e si completano in T3-84):

| Oggi | T1 · Domande dirette | T2 · Etichette brevi |
|---|---|---|
| Descrizione del gruppo \* | Cosa mostrano queste foto? | Che cosa c'è nelle foto |
| Da usare verso il (facoltativa) | C'è un giorno in cui vuoi che escano? (facoltativo) | Giorno preferito (facoltativo) |
| Valori della bottega | Cosa ti sta a cuore nel tuo lavoro? | Ciò in cui credi |
| Tono della comunicazione | Come parli di solito ai tuoi clienti? | Come parli ai clienti |
| Orari e disponibilità | Quando possono trovarti i clienti? | Quando ti trovano |
| Da sistemare prima dell'invio | Manca ancora qualcosa prima di inviare | Prima di inviare manca |

**Se non sai scegliere.** I moduli dell'artigiano oggi lo bloccano o gli fanno chiedere "che cosa devo scrivere qui"? T1. Le etichette sono chiare ma fredde? T2.

---

## 4. Scelte (da compilare)

Si compila in T3-81 (S1, S2, S3, S8) e in T3-82 (S4–S7). Il referente approva con la data; finché la riga non è approvata, il task che la applica non parte.

| Punto | Scelta (sigla e, se serve, che cosa si cambia) | Perché, in una frase (anche per il pitch) | Approvata (referente, data) |
|---|---|---|---|
| S1 · Modo d'uso, artigiano | | | |
| S1 · Modo d'uso, operatore | | | |
| S2 · Schermi e pagine | | | |
| S3 · Gerarchia delle azioni | | | |
| S8 · Tono dei testi | | | |
| S4 · Stile visivo | | | |
| S5 · Palette | | | |
| S6 · Caratteri | | | |
| S7 · Icone | | | |

**Valori esatti** (T3-82, dopo l'approvazione): le 10 tinte di ogni colore, i caratteri con i pesi e il `<link>`, la libreria di icone con la versione e la licenza.

---

## T3-80 · Preparazione della corsia 8

**Chi**: il referente dei file comuni, con Claude.

**Cosa fa**: ADR-118; blocco I e riga H7 di `perimetro-mvp.md`; la corsia 8 in `tasks.md` e T3-79 tolto dalla corsia 7; questa pagina; i rimandi in `brief-pagine.md`, `converge.md`, `AGENTS.md`; `allinea.py` che accetta la corsia 8.

**Fatto quando**: documenti coerenti tra loro; `uv run pytest tests/test_allinea.py` verde da `backend/`; `uv run python allinea.py 8` stampa T3-81 pronto.

## T3-81 · Scelte d'uso

**Leggi**: §2; §3, punti S1, S2, S3, S8; converge §4, passi 2 e 4.

**Tocca**: solo il §4 di questa pagina. Nessun codice.

**Cosa fa**: fa il percorso della demo nelle due finestre, operatore e artigiano, a 1280 px e a 375 px, e annota dove ci si ferma, cosa non si capisce, quali pulsanti si confondono. Con quelle note sceglie S1, S2, S3 e S8 seguendo il §2, con la tabella di confronto dove le possibilità sono più di due.

**Fatto quando**: le righe S1, S2, S3, S8 del §4 compilate e approvate; nella PR le note del percorso e gli screenshot di oggi alle due larghezze, che servono come "prima" a tutta la corsia.

## T3-82 · Scelte visive

**Leggi**: §2; §3, punti S4–S7; la riga S1 del §4.

**Tocca**: il §4 di questa pagina; copie di prova di `docs/pagine/AdFlow-ingresso.html` e `docs/pagine/AdFlow-operatore-campagna.html` in `docs/pagine/prove/`, con un foglio di stile per possibilità. Le prove non entrano nella mappa `index.html` e T3-83 le cancella.

**Cosa fa**: prepara da due a tre combinazioni di S4, S5, S6 e S7 sulle due pagine di prova, ne fa gli screenshot a 1280 px e a 375 px, verifica i contrasti; il referente sceglie. Poi scrive nel §4 i valori esatti.

**Fatto quando**: le righe S4–S7 del §4 compilate e approvate, con i valori esatti; screenshot delle combinazioni e contrasti nella PR.

## T3-83 · Tema e componenti di base

**Leggi**: §1; il §4 (S4–S7).

**Tocca**: `frontend/src/tema.ts` (tinte, caratteri, raggi, ombre e proprietà predefinite dei componenti Mantine come Button, Card, Badge, Paper); `frontend/src/index.css`; `Guscio.module.css` e `CalendarioSettimana.module.css`; `frontend/index.html` (solo il `<link>` dei caratteri); `docs/pagine/assets/adflow.css`; `frontend/package.json` e il lock, solo con I2; `Guscio.tsx` solo per le icone delle voci (I1 o I2), non per le voci stesse. Cancella `docs/pagine/prove/`.

**Non tocca**: la logica dei `.tsx`, i testi, il layout delle singole pagine (T3-85).

**Fatto quando**: le pagine dell'app e quelle statiche con lo stesso stile; il controllo del §1.5 senza risultati; screenshot prima e dopo di ogni pagina della mappa `docs/pagine/index.html`.

## T3-84 · Testi

**Leggi**: §1.4; il §4 (S8); §3, S8.

**Tocca**: i testi visibili, e solo quelli, dei `.tsx` di `frontend/src/pages/` e `frontend/src/components/` che S8 indica; gli stessi testi nelle pagine di `docs/pagine/`. Se un titolo ha un `aria-label` uguale, cambiano insieme.

**Non tocca**: i testi fissi del §1.4; i nomi dei campi nel codice; i messaggi del backend; `sezioni.ts`; i dati di esempio.

**Cosa fa**: l'inventario dei testi delle pagine scelte in S8, poi la riscrittura con il tono scelto.

**Fatto quando**: nella PR la tabella completa "prima → dopo", pagina per pagina; `git grep -c` dei testi fissi uguale prima e dopo; il controllo del §1.5 senza risultati; build e lint puliti.

## T3-85 · Layout e telefono

**Leggi**: §1.2; il §4 (S1, S2, S3).

**Tocca**: le proprietà visive e di layout dei `.tsx` delle pagine scelte in S2 e i loro `.module.css`; `Guscio.tsx` e `Guscio.module.css` per la barra sul telefono; le regole `@media` di `adflow.css`.

**Ordine**: barra (`Guscio`), Accesso, Ingresso, pagina Campagna (passi 10–12, viste per stato, richiesta del consorzio); poi le altre di S2; per ultime le pagine dell'operatore, se S1 lo chiede.

**Come, per la barra.** Se S2 vuole il telefono e la barra in alto non basta, un menu che si apre con `Burger` di `@mantine/core` e `useDisclosure` (l'eccezione del §1.2): stesse voci, stesso ordine, stessi collegamenti.

**Non tocca**: condizioni di visibilità, campi, chiamate, testi; le voci della barra (`brief-pagine.md` §1.3). Ciò che cambia nel `Guscio` vale per i due ruoli: si prova su entrambi.

**Fatto quando**: alle larghezze di S2 il percorso della demo dell'artigiano (converge §4, passi 2 e 4) senza scorrimento orizzontale e senza zoom; a 1280 px tutto come dopo T3-83; il controllo del §1.5 senza risultati; screenshot alle larghezze di S2 nella PR.

## T3-86 · Prova con due persone

**Leggi**: §2; il §4.

**Chi prova**: due artigiani del consorzio; in mancanza, due persone fuori dal team che usano il telefono per lavoro. Ognuna per 30 minuti, sul proprio telefono, sull'app con le PR della corsia già su `main`.

**Compiti**:
1. entra e trova la campagna in corso;
2. prepara una nuova campagna con 3 foto;
3. rispondi alla richiesta del consorzio.

**Come si osserva**: chi osserva non aiuta. Annota dove la persona si ferma, che cosa sbaglia, che cosa dice.

**Cosa corregge**: solo ciò che si risolve con lo stile o con un testo permesso, nel rispetto del §1. Il resto va in `docs/ROADMAP.md` ed entra nel pitch come "che cosa abbiamo imparato".

**Fatto quando**: note della prova nella PR; correzioni su `main` oppure in roadmap; il controllo del §1.5 senza risultati.

## T3-87 · Prova della corsia 8

**Leggi**: §1.5; converge §4.

**Cosa fa**: il percorso di converge §4, passi 1–9, in due finestre: operatore a 1280 px, artigiano alle larghezze di S2. Poi il passo 7, il controllo visivo, con le pagine statiche aggiornate. Poi il controllo del §1.5 su tutto ciò che la corsia ha portato su `main`: `git diff --name-only` e `git diff` dal commit di `main` prima di T3-81.

**Fatto quando**: nessun errore; testi fissi uguali a prima; screenshot prima e dopo di ogni pagina della demo nella PR, gli stessi che servono alle slide di T3-05.

---

## 5. Ordine e date

1. **T3-80**, il 26/10.
2. **T3-81**, poi **T3-82**: le scelte, entro il 27/10.
3. **T3-83** e **T3-84** insieme, su file diversi: entro il 28/10.
4. **T3-85**, dopo T3-83 e T3-84, perché tocca gli stessi `.tsx` di T3-84: entro il 29/10.
5. **T3-86** il 29/10, **T3-87** il 30/10.

Ciò che il 30/10 non è su `main` resta com'è oggi (ADR-118). Se il tempo manca, si taglia in quest'ordine: le pagine dell'operatore in T3-85; le pagine di S2 fuori dal percorso della demo; T3-86 con una persona sola. Il minimo che cambia la percezione nel pitch è T3-83, anche da solo.

**Con T3-08 parte 2.** Tocca anche `Guscio.tsx` (`brief-sistemazione.md`, riga 5) e forse l'hook di prettier (riga 52). Chi arriva secondo parte da `main` aggiornato con `uv run python allinea.py` e risolve i conflitti tenendo il lavoro di entrambi.

**Con T3-07.** La chiusura aspetta anche la corsia 8: il video e la prova si fanno sull'app nuova.

## 6. Strumenti

| Bisogno | Strumento | Costo |
|---|---|---|
| Componenti di partenza | Mantine UI (ui.mantine.dev): si copia il codice e lo si adatta al tema, senza dipendenze | gratis, MIT |
| Palette | Realtime Colors, Coolors | gratis |
| Tinte per Mantine | il generatore di colori della documentazione di Mantine | gratis |
| Contrasto | WebAIM Contrast Checker | gratis |
| Caratteri | Google Fonts | gratis, OFL |
| Telefono | strumenti per sviluppatori del browser a 375 px, poi un telefono vero | gratis |

Gli strumenti che generano interfacce (v0 e simili) producono codice per Tailwind o shadcn/ui: servono come ispirazione, il codice non si incolla.

## 7. Fuori da questa corsia (`docs/ROADMAP.md`)

- Anteprima dei post per l'artigiano prima dell'approvazione: è una regola nuova (H1), non stile.
- Ripensare i percorsi: passi diversi, una domanda per schermata, caricamento "scatta e racconta".
- Cambiare i testi fissi del §1.4, insieme a spec e converge.
- Ordinamenti, filtri, sezioni o pulsanti nuovi.
- Una libreria UI diversa da Mantine, temi esterni, librerie di animazioni.
- Tema scuro.
- Analisi dell'uso con strumenti esterni.
