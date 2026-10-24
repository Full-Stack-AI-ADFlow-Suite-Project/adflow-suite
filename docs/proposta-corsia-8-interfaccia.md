# Corsia 8 · Interfaccia ed esperienza d'uso

> **⚠️ DOCUMENTO PRELIMINARE, DA APPROVARE.**
> È una proposta: non è approvata e non fa testo. Non cambia il perimetro dell'MVP, i task di `docs/agenti/tasks.md` né le regole di `docs/agenti/`; dove qualcosa non torna valgono quei documenti. Il branch serve solo a consultarla. Se il team la approva, le modifiche del §5 si fanno in T3-80, con una PR a parte da `main`.

**Stato:** bozza da approvare · **Data:** 24/10/2026 · **Base:** `main` a `6a8e2ed` · **Scadenza della corsia:** 30/10, blocco del codice

## Indice

0. [Sintesi](#0-sintesi)
1. [Da dove nasce](#1-da-dove-nasce)
2. [Domande da decidere, con la proposta](#2-domande-da-decidere-con-la-proposta)
3. [Come procedere: calendario](#3-come-procedere-calendario)
4. [La corsia 8](#4-la-corsia-8)
5. [Modifiche necessarie ai documenti](#5-modifiche-necessarie-ai-documenti)
6. [Strumenti e modelli pronti](#6-strumenti-e-modelli-pronti)
7. [Fuori dalla corsia (roadmap)](#7-fuori-dalla-corsia-roadmap)
8. [Rischi](#8-rischi)

---

## 0. Sintesi

L'aspetto conta: al pitch del 6/11 l'app si giudica anche da come appare. L'interfaccia di oggi ha tre problemi:

- è corretta ma fredda: blu e grigi da gestionale;
- non è pensata per il telefono;
- in molte pagine dell'artigiano parla con le parole del database: "Descrizione del gruppo \*", "Da usare verso il (facoltativa)", "Valori della bottega".

Da qui la sensazione di "parlare con l'algoritmo".

La proposta:

- **Il restyling diventa una corsia.** T3-79 esce dalla corsia 7 e diventa la **corsia 8** (ADR-118, da scrivere), con 8 task da T3-80 a T3-87 e due persone.
- **Cosa cambia:**
  - lo stile, nell'app e nelle pagine statiche insieme;
  - i testi delle pagine dell'artigiano;
  - l'uso da telefono per l'artigiano.

  Prima del blocco si fa anche una prova con due artigiani veri.
- **Cosa non cambia:** il backend, le rotte, i campi, le chiamate, gli stati, i messaggi d'errore e i testi fissati dalla spec.
- **Nessuna libreria UI nuova.** Mantine resta e i modelli si prendono da Mantine UI. Unica eccezione proposta: le icone Tabler.
- **Paracadute.** Ciò che il 30/10 non è su `main` resta com'è oggi, che funziona.

## 1. Da dove nasce

Una risposta generica, ricevuta da un altro assistente, suggeriva come rifare UI e UX. Verificata sul codice di `main`, si divide in tre parti.

**Già fatto: non si rifà, si mostra nel pitch**

| Proposta | Dove c'è già |
|---|---|
| Percorso a passi invece di un modulo unico | Profilo ai passi 1–9 (`pages/artigiano/profilo/Profilo.tsx`), campagna ai passi 10–12 (`pages/artigiano/campagna/Bozza.tsx`) |
| Salvataggio in bozza | Bozza della campagna, riaperta dal passo 10 con dati e foto (CA-08) |
| Foto compresse e ritagliate in automatico | C1: Pillow ruota, toglie il GPS, ritaglia a 1:1 o 4:5, porta a 1080 px |
| Anteprima del post come card social | `pages/operatore/campagna/PostCard.tsx`, pagine statiche (ADR-113) |
| Tono umano nelle viste per stato | `pages/artigiano/campagna/viste/VistaStato.tsx`: "Stiamo preparando i post…", "Non siamo riusciti a preparare i post." |

**Utile, entra nella corsia 8**

| Proposta | Task |
|---|---|
| Esperienze distinte: artigiano da telefono, operatore da PC | T3-84 e T3-85 |
| Palette calda, non da gestionale | T3-81 e T3-82 |
| Testi umani nella raccolta dei dati | T3-83 |
| Una sola azione principale per schermata | T3-84 |
| Prova "da corridoio" con 2 artigiani | T3-86 |
| Partire da modelli già pronti | §6: Mantine UI |

**Scartato**

| Proposta | Perché |
|---|---|
| Passare a Tailwind UI, shadcn/ui o MUI | Vorrebbe dire riscrivere il frontend a sei giorni dal blocco. ADR-04 ha già scelto Mantine e scartato MUI e Tailwind |
| Riscrivere i componenti in percorsi guidati nuovi | Il percorso a passi c'è già; ripensarlo è un cambio di comportamento (§7) |
| Anteprima del post per l'artigiano mentre la campagna è in lavorazione | La vista dell'artigiano mostra "l'esito del lavoro, mai il lavoro in corso: niente piano né post" (H1, `VistaStato.tsx`). Cambiarla è una regola nuova, non stile (§2, D7) |

## 2. Domande da decidere, con la proposta

Le decide il referente dei file comuni con il team, **entro domenica 25/10**. Ogni risposta finisce nell'ADR-118 o nel brief della corsia 8.

### D1 · T3-79 si toglie dalla corsia 7?

**Proposta:** sì. Si toglie la riga di T3-79 dalla corsia 7 e la corsia 7 si dichiara chiusa con T3-78. Il lavoro rinasce in T3-82, con un perimetro più largo.

**Perché:** `allinea.py` legge la corsia dal titolo `### Corsia N` e la numerazione dei task la segue: un T3-79 nella corsia 8 confonderebbe. Se la riga restasse da spuntare, comparirebbe ancora come pronto.

### D2 · I testi si possono cambiare?

**Proposta:** sì, i **testi visibili del frontend** nelle pagine dell'artigiano: etichette, descrizioni, segnaposto, titoli, avvisi scritti nel frontend. Restano uguali parola per parola:

- i messaggi d'errore che arrivano dal backend (costituzione §4);
- la dichiarazione R-41: "Le foto mostrano prodotti della mia bottega; le persone riconoscibili hanno dato il consenso." Ha valore legale;
- "Immagine creata con AI" (regola delle immagini AI);
- i testi che spec e converge citano:
  - Bentornato, "Va bene così" e "Modifica" (spec §2.1);
  - «Pubblicazioni ferme» (B5, converge §4 passo 6);
  - "Il consorzio ti chiede…" (brief-pagine §1.1);
- i nomi delle sezioni (In corso, In lavorazione, Passate, Storico) e le voci delle barre laterali (brief-pagine §1.1 e §1.3).

**Perché:** così spec, converge e la prova della chiusura (T3-07) non cambiano. Chi vuole cambiare uno di quei testi lo propone in §2 del brief della corsia 8 e aggiorna spec e converge nella stessa PR.

**Alternativa:** non toccare nessun testo e fare solo lo stile. Si perde la leva più forte contro l'effetto "algoritmo".

### D3 · Librerie nuove

**Proposta:**
- **Icone:** `@tabler/icons-react` (licenza MIT), il set che usa la documentazione di Mantine. Poche icone ben scelte (foto, calendario, bottega, campagna, avviso) scaldano molto le pagine. Entra in `frontend/package.json` nella PR di T3-82, con nome, motivo e licenza.
- **Caratteri:** da Google Fonts con il `<link>` già presente in `frontend/index.html` e nelle pagine statiche. Nessun pacchetto nuovo.
- **Nient'altro:** niente librerie di animazioni, kit di componenti o temi esterni.

**Alternativa:** nessuna libreria, come chiedeva la corsia 7. Si possono usare le emoji o gli SVG inline delle pagine statiche.

### D4 · Palette e caratteri

**Proposta:** T3-81 prepara tre direzioni e il referente ne sceglie una, entro lunedì 26/10 alle 12. Il contrasto è calcolato con la formula WCAG 2.1; la soglia AA per il testo normale è 4,5:1.

| Direzione | Primario | Fondo | Testo | Accento | Contrasto primario/fondo · bianco su primario · testo/fondo |
|---|---|---|---|---|---|
| **A · Bottega** | terracotta `#9A4422` | crema `#FBF7F2` | `#2B2420` | salvia `#6B8F71` | 6,1 · 6,5 · 14,3 |
| **B · Legno e bosco** | verde bosco `#2F5D46` | avorio `#F7F5EF` | `#1F2A24` | noce | 6,9 · 7,6 · 13,6 |
| **C · Blu notte caldo** | blu petrolio `#1F5A6B` | `#F8F6F1` | `#1C2A30` | ocra `#B7791F` | 7,1 · 7,7 · 13,7 |
| Oggi | blu `#2563EB` | `#F8FAFC` | `#0F172A` | — | 4,9 · 5,2 · 17,1 |

Note sulla tabella:
- Gli accenti salvia e ocra hanno un contrasto di circa 3,4:1: vanno bene per bordi, icone e badge, **non per il testo**.
- La terracotta più chiara, `#B4532A`, si ferma a 4,7:1 sul fondo: si usa solo per i titoli grandi.
- Le tinte sono un punto di partenza: T3-81 genera le 10 sfumature per Mantine e le verifica tutte.

**Caratteri proposti:**
- testo: **Source Sans 3** o **Nunito Sans**, sans umaniste, leggibili su un telefono anche con poca luce;
- titoli: lo stesso carattere in grassetto oppure, per la direzione A, **Fraunces**, un serif caldo;
- codici e numeri: JetBrains Mono resta.

**Suggerimento:** la **A · Bottega** è la più vicina a un consorzio di artigiani e la più lontana dal "gestionale". La B è più sobria. La C cambia meno rispetto a oggi.

### D5 · Chi fa cosa

**Proposta:** con due persone la corsia si divide in due filoni che toccano file diversi.

| Persona | Filone | Task |
|---|---|---|
| **A · Stile** | tema, CSS, pagine statiche, operatore | T3-81, T3-82, T3-85, T3-87 |
| **B · Artigiano** | testi e telefono, sui file `.tsx` dell'artigiano | T3-83, T3-84 |
| Insieme | prova con gli artigiani | T3-86 |
| Referente dei file comuni | preparazione e scelte | T3-80, D1–D9 |

I nomi li scrive il referente nel titolo `### Corsia 8 · … (…)` di `tasks.md`.

### D6 · Quali pagine devono funzionare sul telefono?

**Proposta:**

| Livello | Pagine | Cosa deve funzionare |
|---|---|---|
| **Obbligatorio** | Accesso, Ingresso, pagina Campagna (passi 10–12, viste per stato, richiesta del consorzio) | Sono il percorso della demo (converge §4, passi 2 e 4) |
| **Se c'è tempo** | Profilo bottega (passi 1–9), Campagne, Archivio foto, Calendario settimanale | Sul telefono il calendario diventa un elenco per giorno, solo con il CSS |
| **No** | Pagine dell'operatore | Restano pensate per il PC; lo stile nuovo arriva da T3-82 e T3-85 |

### D7 · L'artigiano vede l'anteprima dei post?

**Proposta:** no, nell'MVP. Oggi l'artigiano vede i post solo dopo l'approvazione, nel calendario. Mostrarli prima cambia la regola H1. Va in roadmap (§7).

### D8 · La prova con gli artigiani

**Proposta:** giovedì 29/10 mattina, 30 minuti per persona.
- **Chi:** 2 artigiani del consorzio. In mancanza, 2 persone fuori dal team che usano il telefono per lavoro.
- **Su cosa:** l'app restylata in ambiente di prova, sul loro telefono.
- **Compiti:**
  1. entra e trova la campagna in corso;
  2. prepara una nuova campagna con 3 foto;
  3. rispondi alla richiesta del consorzio.
- **Come si osserva:** chi osserva non aiuta. Annota dove la persona si ferma, cosa sbaglia e cosa dice.

Chi recluta gli artigiani va deciso **oggi**: è l'unico passo che non dipende dal team.

### D9 · Coordinamento con T3-08 parte 2 e con T3-07

**Proposta:**
- **Ordine con T3-08.** La parte 2 di T3-08 (entro il 29/10) tocca `frontend/src/components/Guscio.tsx` (brief-sistemazione, riga 5) e forse l'hook di prettier (riga 52). Quella parte va su `main` **entro lunedì 26/10**, prima di T3-84. Se slitta, T3-84 parte dalla sua versione e chi arriva secondo risolve i conflitti.
- **Attesa di T3-07.** T3-07 dipende da "tutti i task dello sprint": aspetta anche la corsia 8. Va bene così, perché la chiusura e il video si fanno sull'app restylata. Un task della corsia 8 che il 30/10 non è su `main` si toglie dalla tabella in T3-07, come fa la corsia 7 (ADR-117).

## 3. Come procedere: calendario

| Giorno | Persona A · Stile | Persona B · Artigiano | Referente |
|---|---|---|---|
| **sab 24/10** | — | — | Legge la proposta; trova chi recluta gli artigiani (D8) |
| **dom 25/10** | T3-81: tre direzioni su 2 pagine statiche | T3-83: inventario dei testi e guida al tono | Risponde a D1–D9; T3-80 (ADR-118 e documenti) su `main` |
| **lun 26/10** | Alle 12 la scelta; T3-82 parte | T3-83: riscrittura, PR | T3-08 parte 2, la parte del frontend, su `main` |
| **mar 27/10** | T3-82 su `main` (tema, CSS, pagine statiche) | T3-84: Guscio sul telefono, Ingresso | Rivede le PR |
| **mer 28/10** | T3-85: operatore | T3-84: pagina Campagna, poi Profilo | Rivede le PR |
| **gio 29/10** | T3-86 al mattino, correzioni al pomeriggio | T3-86 al mattino, correzioni al pomeriggio | Organizza la prova |
| **ven 30/10** | T3-87: prova della corsia, screenshot prima e dopo | Ultime PR entro le 16 | Unisce; ciò che manca resta fuori |
| **2–6/11** | Solo correzioni; slide (T3-05) e video (T3-07) sull'app nuova | Solo correzioni; slide (T3-05) e video (T3-07) sull'app nuova | Prove del pitch |

**Se il tempo manca**, si taglia in questo ordine:
1. T3-85, l'operatore: si tiene solo lo stile che arriva da T3-82;
2. Profilo, Archivio e Calendario sul telefono;
3. i testi fuori dal percorso della demo.

Il minimo che cambia la percezione nel pitch è **T3-82 più T3-83 e T3-84 sulle sole pagine Ingresso e Campagna**.

## 4. La corsia 8

### 4.1 Righe per `tasks.md`

Le righe sono già nel formato che `allinea.py` legge: titolo `### Corsia N · nome (chi)`, 6 celle, casella in fondo. Prima di incollarle si sostituiscono `<A>`, `<B>` e il referente.

```markdown
### Corsia 8 · Interfaccia ed esperienza d'uso (<A>, <B>)

Ogni task ha in `brief-interfaccia.md` i file da toccare e da non toccare e i testi che restano fissi: si legge la sezione del proprio task, non tutto il brief. Nessun cambio di comportamento: rotte, campi, chiamate, stati e messaggi del backend restano quelli di prima.

| ID | Task | Leggi | Dipende da | Fatto quando | ☐ |
|---|---|---|---|---|---|
| T3-80 | **Preparazione della corsia 8** (ADR-118): perimetro (riga H7 e blocco I), i task, `brief-interfaccia.md`, T3-79 tolto dalla corsia 7. Il referente con Claude | ADR-118; `perimetro-mvp.md` | T3-78 | documenti coerenti tra loro; comandi di converge §1 verdi; `tests/test_allinea.py` verde con la corsia 8 | ☐ |
| T3-81 | **Direzione visiva**: tre proposte di palette e caratteri su Ingresso artigiano e Vedi campagna statiche; la scelta del referente scritta nel brief | `brief-interfaccia.md` §T3-81 | T3-80 | tre proposte con screenshot; contrasti AA verificati; scelta scritta in §T3-82 | ☐ |
| T3-82 | **Tema e componenti di base**: palette, caratteri, icone, barra laterale, card e pulsanti nell'app e nelle pagine statiche insieme (assorbe T3-79) | `brief-interfaccia.md` §T3-82; ADR-113 | T3-81 | tutte le pagine con lo stesso stile, app e statiche; build e lint puliti; screenshot prima e dopo nella PR | ☐ |
| T3-83 | **Testi dell'artigiano**: guida al tono e riscrittura dei testi visibili delle sue pagine, senza i testi fissi | `brief-interfaccia.md` §T3-83 | T3-80 | tabella prima → dopo nella PR; testi fissi invariati; build e lint puliti | ☐ |
| T3-84 | **Artigiano sul telefono**: barra che diventa menu, una sola azione principale per schermata, pulsanti e caricamento delle foto comodi; Accesso, Ingresso, pagina Campagna, poi le altre | `brief-interfaccia.md` §T3-84 | T3-82, T3-83 | percorso della demo dell'artigiano senza scorrimento orizzontale a 375 px; build e lint puliti; screenshot a 375 px e a 1280 px nella PR | ☐ |
| T3-85 | **Operatore**: densità di tabelle e card, numeri in evidenza, solo stile | `brief-interfaccia.md` §T3-85 | T3-82 | pagine dell'operatore con lo stile nuovo; build e lint puliti; screenshot prima e dopo | ☐ |
| T3-86 | **Prova con due artigiani** e correzioni piccole | `brief-interfaccia.md` §T3-86 | T3-84 | note della prova nella PR; correzioni solo di stile o testo; build e lint puliti | ☐ |
| T3-87 | **Prova della corsia 8**: percorso della demo a 1280 px e a 375 px, in due finestre, operatore e artigiano | `brief-interfaccia.md` §T3-87; converge §4 | T3-82, T3-83, T3-84, T3-85, T3-86 | passi 1–9 di converge §4 senza errori; screenshot prima e dopo di ogni pagina della demo; pagine statiche uguali all'app | ☐ |
```

T3-80 dipende da T3-78, che è già spuntato: la corsia può partire subito.

### 4.2 Brief dei task

Il testo che segue diventa `docs/agenti/brief-interfaccia.md` in T3-80.

**Regole di lavoro per tutti i task**

- Un branch `feature/<id>-<breve>` da `main`. Una PR per task, unibile da sola.
- **Nessun cambio di comportamento:**
  - non cambiano rotte, chiamate in `src/api/`, campi dei moduli, validazioni, condizioni di visibilità e stati;
  - si cambiano solo stile, layout e i testi permessi in T3-83;
  - nessun file del backend, nessuna migrazione.
- **Librerie:** solo `@tabler/icons-react`, se D3 lo approva. Componenti e modelli si prendono da Mantine UI copiando il codice, senza dipendenze.
- **App e pagine statiche insieme:** ogni cambio di stile tocca sia `frontend/` sia `docs/pagine/assets/adflow.css`, così il passo 7 di converge §4 resta vero.
- **Testi fissi:** quelli elencati in D2. In caso di dubbio, il testo resta com'è.
- **Fatto quando, per ogni task:**
  - `npm run lint` e `npm run build` puliti da `frontend/`;
  - screenshot prima e dopo nella PR;
  - poi la checklist di converge §1 e la casella in `tasks.md`.

#### T3-80 · Preparazione della corsia 8

**Chi:** il referente con Claude.

**Cosa fa:**
- applica le modifiche del §5 di questo documento, con le risposte di D1–D9;
- toglie questo documento da `docs/` oppure lo lascia come storia: lo decide il referente.

**Fatto quando:**
- `uv run pytest tests/test_allinea.py` è verde;
- `uv run python allinea.py 8` stampa T3-81 e T3-83 come pronti.

#### T3-81 · Direzione visiva

**Tocca:** copie di prova di `docs/pagine/AdFlow-ingresso.html` e `AdFlow-operatore-campagna.html`, con un foglio di stile per ogni direzione. Le copie non si uniscono: vanno solo negli screenshot della PR, oppure in una cartella `docs/pagine/prove/` che T3-82 cancella.

**Cosa fa:**
- applica le tre direzioni di D4;
- per ognuna genera le 10 sfumature di Mantine;
- verifica i contrasti di testo, pulsanti e badge.

**Fatto quando:** la scelta del referente, con le tinte esatte e i caratteri, è scritta nel brief in §T3-82.

#### T3-82 · Tema e componenti di base

**Tocca:**
- `frontend/src/tema.ts`: colori, caratteri, raggi, ombre e proprietà predefinite dei componenti Mantine (Button, Card, Badge, Paper, AppShell);
- `frontend/src/index.css`;
- `frontend/src/components/Guscio.module.css` e `CalendarioSettimana.module.css`;
- `frontend/index.html` e i `<link>` delle pagine statiche, per i caratteri;
- `docs/pagine/assets/adflow.css`;
- `frontend/package.json` e il lock, per le icone se D3 le approva;
- le icone nel `Guscio`: solo la parte visiva delle voci, non le voci stesse.

**Non tocca:** la logica dei `.tsx`, `src/api/`, le rotte, i testi.

**Attenzione:** l'alias `verde: blu` in `tema.ts` resta finché #76 non lo toglie. Il nuovo primario prende il posto di `blu` e l'alias lo segue.

**Fatto quando:** le pagine dell'app e quelle statiche hanno lo stesso stile, con gli screenshot prima e dopo di ogni pagina della mappa `docs/pagine/index.html`.

#### T3-83 · Testi dell'artigiano

**Tocca:** i testi visibili, e solo quelli, dei `.tsx` in `frontend/src/pages/artigiano/` e in `frontend/src/components/` dove li vede l'artigiano. Aggiunge in questo brief la **guida al tono**:
- dare del tu;
- frasi brevi;
- parole della bottega (lavoro, foto, clienti, fiera), non del database (gruppo, asset, descrizione, campo);
- una domanda per campo;
- dire perché si chiede una cosa, quando non è ovvio;
- negli avvisi, cosa fare e non solo cosa non va.

**Esempi da `main`** (le proposte si decidono nella PR):

| Oggi | Proposta |
|---|---|
| Descrizione del gruppo \* | Cosa mostrano queste foto? |
| Da usare verso il (facoltativa) | C'è un giorno in cui vuoi che escano? (facoltativo) |
| Descrizione e commenti della campagna | Cosa vuoi far sapere con questa campagna? |
| Valori della bottega | Cosa ti sta a cuore nel tuo lavoro? |
| Tono della comunicazione | Come parli di solito ai tuoi clienti? |
| Orari e disponibilità | Quando possono trovarti i clienti? |
| Da sistemare prima dell'invio | Manca ancora qualcosa prima di inviare |

**Non tocca:** i testi fissi di D2, i nomi dei campi nel codice, le chiavi delle API, i messaggi che arrivano dal backend.

**Fatto quando:** la PR porta la tabella completa dei testi "prima → dopo", pagina per pagina, e `git grep` dei testi fissi trova le stesse righe di prima.

#### T3-84 · Artigiano sul telefono

**Tocca:**
- `frontend/src/components/Guscio.tsx` e il suo `.module.css`: la barra laterale diventa un menu con `Burger` e `AppShell` di `@mantine/core`, già installato;
- le pagine di `frontend/src/pages/artigiano/` e `frontend/src/pages/Accesso.tsx`, solo per le proprietà di layout: colonne che si adattano, `Stack` al posto delle righe sotto i 768 px, pulsante principale a tutta larghezza in fondo allo schermo, area di caricamento delle foto grande;
- `CalendarioSettimana.module.css`: sotto i 768 px la griglia diventa un elenco per giorno.

**Non tocca:**
- le condizioni di visibilità, i campi e le chiamate;
- le voci della barra (brief-pagine §1.3);
- le pagine dell'operatore, a parte ciò che cambia nel `Guscio` per tutti, da provare su entrambi i ruoli.

**Ordine:**
1. Guscio;
2. Accesso;
3. Ingresso;
4. pagina Campagna (passi 10–12, viste per stato, richiesta del consorzio);
5. se c'è tempo, Profilo, Campagne, Archivio e Calendario.

**Una sola azione principale per schermata:** un solo pulsante pieno, gli altri secondari (`variant="light"` o `"subtle"`).

**Fatto quando:** a 375 px il percorso dell'artigiano nella demo (converge §4, passi 2 e 4) si fa senza scorrimento orizzontale e senza zoom. A 1280 px tutto resta come dopo T3-82.

#### T3-85 · Operatore

**Tocca:** solo gli stili delle pagine di `frontend/src/pages/operatore/`, cioè proprietà visive di Mantine e `.module.css`: tabelle più leggibili, numeri in evidenza, stati con badge del colore giusto, `PostCard` con lo stile della card social.

**Non tocca:** pulsanti, azioni, testi, ordine delle sezioni.

**Fatto quando:** le pagine dell'operatore hanno lo stile nuovo, con gli screenshot prima e dopo.

#### T3-86 · Prova con due artigiani

**Cosa fa:**
- svolge la prova come descritta in D8 e scrive le note nella PR: dove la persona si è fermata, cosa ha sbagliato, cosa ha detto;
- corregge solo ciò che si risolve con lo stile o con un testo permesso.

Il resto va in `docs/ROADMAP.md` ed entra nel pitch come "che cosa abbiamo imparato".

**Fatto quando:** le note e le correzioni sono su `main`, oppure le correzioni sono in roadmap se non sono piccole.

#### T3-87 · Prova della corsia 8

**Cosa fa:** il percorso di converge §4, passi 1–9, in due finestre: operatore a 1280 px, artigiano a 375 px. Poi il passo 7, il controllo visivo, con le pagine statiche restylate.

**Fatto quando:** nessun errore; gli screenshot prima e dopo di ogni pagina della demo sono nella PR. Sono gli stessi che servono alle slide di T3-05.

## 5. Modifiche necessarie ai documenti

Le fa T3-80, dopo l'approvazione e con le risposte di D1–D9.

| File | Modifica |
|---|---|
| `docs/ADR.md` | Riga **118**: corsia 8, interfaccia ed esperienza d'uso. Decisione: il restyling esce da T3-79 e diventa una corsia; stile di app e pagine statiche insieme; testi dell'artigiano tranne quelli fissi; artigiano sul telefono; prova con 2 artigiani; nessun cambio di comportamento; eventuale libreria di icone. Perché: al pitch l'aspetto conta e la sensazione di "parlare con l'algoritmo" viene da testi, gerarchia e uso da PC. Alternative scartate: cambiare libreria UI; ripensare i percorsi; anteprima dei post per l'artigiano; solo lo stile senza testi. Scadenza: ciò che il 30/10 non è su `main` resta com'è. Precisa ADR-117 per T3-79 |
| `docs/agenti/perimetro-mvp.md` | Intestazione: "e con ADR-118 del 25/10/2026 (interfaccia ed esperienza d'uso: blocco I)". La riga **H7** rimanda al blocco I. Nuovo **blocco I · Interfaccia ed esperienza d'uso (ADR-118)**: I1 stile di app e pagine statiche (T3-81, T3-82, T3-85); I2 testi dell'artigiano, con l'elenco dei testi fissi (T3-83); I3 artigiano sul telefono, con le pagine obbligatorie di D6 (T3-84); I4 prova con gli artigiani (T3-86); I5 anteprima dei post per l'artigiano e ripensamento dei percorsi: roadmap. Sotto il blocco: "ciò che il 30/10 non è su `main` resta com'è" |
| `docs/agenti/tasks.md` | Tabella delle aree: riga **8 · Interfaccia ed esperienza d'uso**, con le persone di D5; nella riga 7 "restyling grafico dedicato" diventa "il restyling è passato alla corsia 8". Via la riga di T3-79 dalla corsia 7. Nuova sezione **Corsia 8** del §4.1, prima di "Dopo l'MVP". Nel paragrafo **Date**: "Corsia 8 (ADR-118): due persone, dal 25 al 30/10; ciò che il 30/10 non è su `main` resta fuori" |
| `docs/agenti/brief-pagine.md` | La riga 14 resta per la corsia 7. La sezione **§T3-79** diventa un rimando: "Passato alla corsia 8 (ADR-118): `brief-interfaccia.md`". Nel §2, il punto 4 si toglie |
| `docs/agenti/brief-interfaccia.md` | **Nuovo**: il §4.2 di questo documento, con le scelte di D3–D6 e, dopo T3-81, palette e caratteri esatti |
| `docs/agenti/converge.md` | §4, passo 7: aggiungere "anche a 375 px per le pagine dell'artigiano (corsia 8)" e le pagine nuove della corsia 7 nell'elenco del controllo visivo |
| `AGENTS.md` | Nell'elenco dei brief, al punto 2: aggiungere `brief-interfaccia.md` |
| `docs/ROADMAP.md` | Le voci del §7 di questo documento |
| `backend/tests/test_allinea.py` | Solo se un test conta le corsie o cita T3-79: da verificare in T3-80 |
| `docs/agenti/spec.md` | Nessuna modifica, se D2 resta com'è proposto |

Nessuna modifica a `backend/app/`, `alembic/`, `core/`, `requirements.txt` né ai `domain.py`.

## 6. Strumenti e modelli pronti

| Bisogno | Strumento | Uso nella corsia | Costo |
|---|---|---|---|
| Componenti di partenza | **Mantine UI** (ui.mantine.dev) | Card con statistiche, intestazioni, barra laterale, aree di caricamento, elenchi: si copia il codice e si adatta al tema | gratis, MIT |
| Bozze veloci | **Figma**, con un kit Mantine della community, oppure il design generato con Claude sulle pagine statiche | T3-81: le tre direzioni senza toccare il codice | gratis |
| Palette | **Realtime Colors** (anteprima della palette su una pagina vera), **Coolors** | T3-81 | gratis |
| Sfumature per Mantine | Il generatore di colori della documentazione di Mantine | T3-81 e T3-82: le 10 tinte di ogni colore | gratis |
| Contrasto | **WebAIM Contrast Checker**, oppure la formula WCAG in uno script | T3-81 e T3-82 | gratis |
| Caratteri | **Google Fonts** | T3-82 | gratis |
| Icone | **Tabler Icons** | T3-82, se D3 lo approva | gratis, MIT |
| Telefono | Strumenti per sviluppatori del browser a 375 px, poi un telefono vero | T3-84 e T3-87 | gratis |
| Prova con gli artigiani | Telefono, 3 compiti scritti, un foglio di note | T3-86 | gratis |

Strumenti che generano interfacce (v0, Galileo e simili) producono codice per Tailwind o shadcn: servono come ispirazione, il codice non si incolla.

## 7. Fuori dalla corsia (roadmap)

Queste voci vanno in `docs/ROADMAP.md` e nel pitch come prossimi passi:

- **Anteprima dei post per l'artigiano**: vedere come appariranno su Facebook e Instagram e dire "mi piace" prima dell'approvazione. È una regola nuova, perché oggi l'artigiano vede l'esito, non il lavoro in corso.
- **Ripensamento dei percorsi**: per esempio un caricamento delle foto "scatta e racconta" dal telefono, o passi del profilo più corti.
- **Testi fissati dalla spec**: rivederli insieme, con spec e converge.
- **Tema scuro.**
- **Analisi dell'uso** (Hotjar e simili, con il consenso).
- **Prove con più artigiani** dopo il 6/11, insieme al piano di accettazione.
- **Ingresso dell'operatore** con "Da sistemare": già in roadmap (H3).

## 8. Rischi

| Rischio | Effetto | Contromisura |
|---|---|---|
| Sei giorni al blocco | Lavoro a metà su `main` | Una PR per task, unibile da sola; ordine di taglio del §3; paracadute: lo stile di oggi |
| Un cambio di testo rompe la demo o la spec | Il percorso di converge §4 non torna | Testi fissi di D2; `git grep` prima e dopo in T3-83 |
| App e pagine statiche divergono | Il passo 7 di converge §4 fallisce | T3-82 le tocca nella stessa PR |
| Conflitti su `Guscio.tsx` con T3-08 parte 2 | PR bloccate | D9: prima T3-08, frontend entro il 26/10 |
| Conflitti tra T3-83 e T3-84 sugli stessi `.tsx` | Rifacimenti | Li fa la stessa persona, uno dopo l'altro |
| Lo stile nuovo rompe le pagine dell'operatore | Regressione nella demo | Screenshot prima e dopo di ogni pagina in T3-82; T3-87 |
| Nessun artigiano disponibile il 29/10 | T3-86 senza dati veri | Due persone fuori dal team; reclutare **oggi** (D8) |
| Il perimetro si allarga ("già che ci siamo…") | Si sfora il 30/10 | Ogni idea che cambia una rotta, un campo, una chiamata o una condizione va nel §7, senza discussione |
