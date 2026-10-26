# Brief · Corsia 7 · Pagine, archivio foto e calendario (T3-71…T3-78)

Per chi fa un task della corsia 7. Decisione: ADR-117. Leggi prima `constitution.md` e `perimetro-mvp.md` (blocco H), poi **solo** la sezione del tuo task qui sotto e le regole che cita. Firme, messaggi d'errore e schemi di questa pagina sono il contratto tra i task: non cambiarli senza chiedere. Dove il codice di `main` è diverso da come è descritto qui, fermati e chiedi.

**Che cosa nasce.**
- **Artigiano**: una pagina d'ingresso con gli avvisi delle sue campagne, la richiesta del consorzio in evidenza e la settimana in corso; l'elenco delle sue campagne; l'archivio delle sue foto; il calendario settimanale. La pagina Campagna resta com'è e si apre anche su una campagna scelta.
- **Operatore**: l'elenco degli artigiani, la pagina dell'artigiano (profilo in sola lettura), le campagne dell'artigiano, il suo archivio foto e il calendario settimanale di tutti gli artigiani.
- **Pagine in comune**: campagne, archivio foto e calendario sono lo stesso componente per i due ruoli, con dati, sezioni e pulsanti diversi.

**Regole di lavoro per tutti i task.**
- Un branch `feature/<id>-<breve>` da `main`; fai solo il tuo task; tocca i file elencati e i loro test. Se ti serve un file che non è nell'elenco, fermati e chiedi.
- **Nessuna migrazione, nessuna libreria nuova (né nel backend né nel frontend), nessun file in `core/`.** La foto ha già `profilo_id` e `campagna_id`: l'archivio è una lettura, non una tabella nuova.
- Il codice congelato resta congelato: `campagne/archivio.py`, le rotte `/archivio` e la sezione Archivio del passo 7 non si toccano.
- **Nessun cambio di stile**: le pagine nuove usano il tema e i componenti di oggi (`tema.ts`, `index.css`, `Guscio`). Palette, caratteri e restyling sono la corsia 8 (ADR-118, `brief-interfaccia.md`).
- Messaggi in italiano, esattamente quelli di questa pagina; codici solo tra quelli di costituzione §4.
- Test su PostgreSQL con le fixture di plan §7 e le fabbriche; il nome porta il CA (`test_ca92_…`). Nessuna chiamata reale ad AI, social o email.
- Fatto quando, per ogni task di backend: `uv run alembic upgrade head`, `uv run pytest`, `uv run black --check .` verdi da `backend/`, `tests/test_confini.py` compreso. Per ogni task di frontend: `npm run lint` e `npm run build` puliti da `frontend/`, screenshot nella PR. Poi la checklist di `converge.md` §1 e la casella del task in `tasks.md`.

---

## 1. Contratti comuni

### 1.1 Sezioni delle campagne (spec §4)

| Sezione | Stati | Artigiano | Operatore |
|---|---|---|---|
| In corso | `attiva`, `sospesa` | prima sezione | prima sezione |
| Da approvare | `inviata`, `in_generazione`, `generazione_fallita`, `in_revisione` | si chiama "In lavorazione"; con una richiesta aperta "Il consorzio ti chiede…" | seconda sezione |
| Bozza | `bozza` | dentro "In lavorazione", in cima | una riga informativa, non si apre (Vedi campagna si apre solo dopo l'invio) |
| Passate | `conclusa`, `annullata`, `scaduta`, `respinta` | ultima sezione, respinte comprese | ultima sezione, si chiama "Storico" |

In ogni sezione dalla più recente (id decrescente). Gli stati per sezione stanno in un solo posto per lato: `frontend/src/components/campagne/sezioni.ts` nel frontend (T3-74), `revisione/letture.py` nel backend (T3-71, per i conteggi). Le etichette degli stati per l'artigiano restano quelle di oggi della pagina Campagna.

### 1.2 Dove porta un clic

| Da | Artigiano | Operatore |
|---|---|---|
| una campagna | `/campagna?id={id}`: la pagina Campagna aperta su quella campagna (passi 10–12 se è in bozza, la vista per stato altrimenti) | `/campagne/{id}`, Vedi campagna; la bozza non si apre |
| un post del calendario | `/campagna?id={campagna_id}` | `/campagne/{campagna_id}` |
| un artigiano | — | `/artigiani/{utente_id}` |

### 1.3 Barre laterali

- **Artigiano**: Ingresso (`/ingresso`), Campagne (`/campagne`, accesa anche su `/campagna`), Calendario (`/calendario`), Archivio foto (`/archivio`), Profilo bottega (`/profilo`), Esci.
- **Operatore** e admin: Da approvare (`/da-approvare`), Artigiani (`/artigiani`, accesa anche su `/artigiani/…`), Calendario (`/calendario`), Nuovo artigiano (`/nuovo-artigiano`), Esci.

Dopo l'accesso (spec R-29): artigiano → `/ingresso` (`/profilo` se non ha un profilo); operatore e admin → `/da-approvare`, come oggi.

### 1.4 Schemi nuovi (backend → frontend)

I tipi del frontend rispecchiano questi schemi (costituzione §4) e vanno nel file `api/` indicato.

```python
# revisione/schemas.py → frontend/src/api/revisione.ts (T3-71)
class ArtigianoElenco(BaseModel):
    """Una riga di GET /artigiani (spec R-38)."""
    id: int                      # id dell'utente artigiano
    nome: str                    # nome dell'account
    email: str
    attivo: bool
    bottega: str | None          # None: profilo da compilare
    referente: str | None
    citta: str | None
    canali_collegati: list[str]
    n_da_approvare: int
    n_in_corso: int
    prossima_scadenza: datetime | None  # entro_quando più vicino tra le da approvare

# artigiani/schemas.py → frontend/src/api/artigiani.ts (T3-71)
class SchedaArtigiano(BaseModel):
    """GET /artigiani/{id}: account e profilo in sola lettura."""
    id: int
    nome: str
    email: str
    attivo: bool
    profilo: ProfiloPubblico | None  # lo schema di GET /profilo
    canali_collegati: list[str]

# campagne/schemas.py → frontend/src/api/campagne.ts (T3-72)
class CampagnaDelBlocco(BaseModel):
    id: int
    titolo: str
    stato: str
    inizio: date
    fine: date

class FotoArchivio(BaseModel):
    id: int
    url: str                     # /api/foto/{id}/file
    origine: str                 # caricata | creata_ai
    mime: str
    larghezza: int
    altezza: int
    pubblicata_su: dict[str, datetime]  # {canale: ultima pubblicazione}

class BloccoArchivio(BaseModel):
    """Un blocco di GET /archivio-foto: le foto di una campagna (spec R-47)."""
    campagna: CampagnaDelBlocco | None  # None: foto senza campagna (archivio di prima)
    foto: list[FotoArchivio]

# contenuti/schemas.py → frontend/src/api/campagne.ts (T3-73)
class PostSettimana(PostCalendario):
    """Un post del calendario settimanale (spec R-48)."""
    campagna_id: int
    campagna_titolo: str
    bottega: str | None

class GiornoSettimana(BaseModel):
    data: date
    post: list[PostSettimana]

class CalendarioSettimana(BaseModel):
    dal: date                    # lunedì
    al: date                     # domenica
    giorni: list[GiornoSettimana]  # sempre 7, anche vuoti
```

---

## T3-71 · Artigiani per l'operatore, backend

**Leggi**: spec R-38, R-29; plan §3 (righe `GET /artigiani`, `GET /artigiani/{id}`, `GET /campagne?artigiano=`), §6; questo brief §1.1, §1.4.

**File da toccare**: `backend/app/moduli/accesso/service.py`; `artigiani/router.py`, `artigiani/service.py`, `artigiani/schemas.py`; `campagne/router.py`, `campagne/service.py`; `revisione/letture.py`, `revisione/router.py`, `revisione/schemas.py`; `docs/agenti/plan.md` §6 (una riga); i test in `tests/moduli/artigiani/`, `tests/moduli/campagne/`, `tests/moduli/revisione/`.
**Da non toccare**: `contenuti/`, `pubblicazione/`, i `domain.py`, `GET /da-approvare` (stesso risultato di oggi).

**Passi**
1. `accesso/service.py`: `artigiani(db) -> list[Utente]`, gli utenti con ruolo `artigiano`, anche non attivi, in ordine di id. Aggiungi la riga in plan §6 (Usata da: revisione; Scritta in: T3-71).
2. `artigiani/service.py` e `router.py`: `GET /artigiani/{utente_id}` → `SchedaArtigiano`, con `richiede_ruolo("operatore")`. `accesso.utente()` (404 se manca) e, se `ruolo != "artigiano"`, `NonTrovato("Artigiano non trovato.")`; `profilo` è quello di `GET /profilo` o `None`; `canali_collegati` da `canali_collegati()` (vuoto senza profilo).
3. `revisione/letture.py`: `elenco_artigiani(db) -> list[ArtigianoElenco]`. Per ogni `accesso.artigiani()`: il profilo con `artigiani.profilo_di()`, le campagne con `campagne.campagne_di()`, i conteggi con gli stati del §1.1, `prossima_scadenza` = il più vicino `entro_quando` (R-38) tra le campagne da approvare. Il calcolo di `entro_quando` diventa una funzione privata usata anche da `da_approvare()`, che non cambia risultato. Ordine: prima per `prossima_scadenza` (chi non ce l'ha va in fondo), poi per bottega (o nome dell'account, senza profilo), senza maiuscole.
4. `revisione/router.py`: `GET /artigiani` → `list[ArtigianoElenco]`, con `richiede_ruolo("operatore")`.
5. `campagne/router.py` e `service.py`: `GET /campagne` accetta `artigiano: int | None` (id dell'utente). Per operatore e admin filtra le campagne del suo profilo: senza profilo `[]`; id che non è di un artigiano → `NonTrovato("Artigiano non trovato.")`. Per l'artigiano il parametro non conta: vede solo le sue, come oggi.

**Test** (nomi da usare)
- `tests/moduli/revisione/test_artigiani.py` (nuovo): `test_ca92_elenco_con_la_situazione_delle_campagne`, `test_ca92_artigiano_senza_profilo_e_non_attivo`, `test_ca92_ordine_per_scadenza_poi_bottega`, `test_ca92_artigiano_403_admin_passa`.
- `tests/moduli/artigiani/test_scheda_artigiano.py` (nuovo): `test_ca93_scheda_con_profilo_e_canali`, `test_ca93_senza_profilo`, `test_ca93_operatore_o_inesistente_404`, `test_ca93_artigiano_403`.
- `tests/moduli/campagne/test_elenco_campagne.py` (o il file di oggi dell'elenco): `test_ca94_operatore_filtra_per_artigiano`, `test_ca94_artigiano_non_trovato_404`, `test_ca94_artigiano_vede_solo_le_sue`.
- `CA-69` (`GET /da-approvare`) resta verde senza cambiare le asserzioni.

**Fatto quando**: CA-92, CA-93, CA-94 verdi; CA-69 ancora verde; comandi del backend verdi.

---

## T3-72 · Archivio foto, backend

**Leggi**: spec R-47, §4; plan §3 (riga `GET /archivio-foto`); questo brief §1.4.

**File da toccare**: `backend/app/moduli/campagne/archivio_foto.py` (nuovo), `campagne/router.py`, `campagne/schemas.py`; `tests/moduli/campagne/test_archivio_foto.py` (nuovo).
**Da non toccare**: `campagne/archivio.py` e le rotte `/archivio` (congelati), `GET /foto/{id}/file` (vale già per proprietario e operatore).

**Passi**
1. `archivio_foto.py`: `leggi(db, utente_id, ruolo, artigiano=None) -> list[BloccoArchivio]`.
   - Artigiano: il suo profilo con `artigiani.profilo_di()`; `artigiano` non conta. Operatore e admin: `artigiano` obbligatorio, altrimenti `DatiNonValidi("Indica l'artigiano di cui vedere le foto.")`; `accesso.utente()` e ruolo `artigiano`, altrimenti `NonTrovato("Artigiano non trovato.")`. Senza profilo → `[]`.
   - Le foto sono quelle con `profilo_id` del profilo e `origine` `caricata` o `creata_ai` (le `cartolina` mai).
   - **Artigiano**: le immagini AI solo delle campagne `attiva`, `sospesa`, `conclusa`, `annullata`: prima dell'approvazione il piano non lo vede (spec §4, CA-31). Le sue foto caricate in ogni stato.
   - Un blocco per campagna, dalla più recente (id decrescente), con le foto in ordine di id; le campagne senza foto da mostrare non hanno blocco. Le foto senza campagna (archivio di prima, R-27) stanno in un ultimo blocco con `campagna = None`, se ci sono.
2. `router.py`: `GET /archivio-foto?artigiano=` → `list[BloccoArchivio]`, con `utente_corrente`; ruoli diversi da artigiano, operatore, admin → 403. Nessun metodo di scrittura.

**Test**: `test_ca95_artigiano_blocchi_per_campagna`, `test_ca95_immagini_ai_solo_dopo_l_approvazione`, `test_ca95_niente_cartoline_niente_foto_di_altri`, `test_ca96_operatore_tutte_le_foto_dell_artigiano`, `test_ca96_operatore_senza_artigiano_422`, `test_ca96_id_non_artigiano_404`.

**Fatto quando**: CA-95, CA-96 verdi; i test dell'archivio congelato ancora verdi; comandi del backend verdi.

---

## T3-73 · Calendario settimanale, backend

**Leggi**: spec R-45, R-48; plan §3 (riga `GET /calendario`); questo brief §1.4.

**File da toccare**: `backend/app/moduli/contenuti/settimana.py` (nuovo), `contenuti/router.py`, `contenuti/schemas.py`; `tests/moduli/contenuti/test_settimana.py` (nuovo).
**Da non toccare**: `contenuti/calendario.py` e `GET /campagne/{id}/calendario` (stesso risultato di oggi), i `domain.py`.

**Passi**
1. `settimana.py`: `leggi(db, utente_id, ruolo, dal: date | None, adesso) -> CalendarioSettimana`.
   - `dal` vuoto → il lunedì della settimana di `adesso` in Europe/Rome (`ROMA` di `core/orologio.py`); `dal` che non è un lunedì → `DatiNonValidi("La settimana comincia di lunedì.")`.
   - Periodo: da `dal` 00:00 a `dal + 7 giorni` 00:00, Europe/Rome.
   - Campagne: per l'artigiano le sue (`artigiani.profilo_di()`, `campagne.campagne_di()`), per operatore e admin tutte (`campagne.campagne_in_stato()`); in entrambi i casi solo `attiva`, `sospesa`, `conclusa`, `annullata`.
   - Post: quelli di queste campagne nel periodo, negli stati `approvato`, `pubblicato`, `fallito`, `annullato` (come R-45), letti dentro `contenuti` con una query sulla sua tabella `post`; in ordine di istante e id. Testo, hashtag e foto della versione corrente come in `calendario.py` (riusa la costruzione di `PostCalendario`, spostandola in una funzione privata condivisa se serve, senza cambiare `GET /campagne/{id}/calendario`).
   - `campagna_titolo` dalla campagna, `bottega` da `artigiani.profilo()`.
   - Sempre 7 giorni, da lunedì a domenica, anche vuoti.
2. `router.py`: `GET /calendario?dal=` → `CalendarioSettimana`, con `utente_corrente` e `Cache-Control: no-store`; `adesso` dalla dipendenza di oggi.

**Test**: `test_ca97_artigiano_solo_i_suoi_post_negli_stati_visibili`, `test_ca97_sette_giorni_anche_vuoti`, `test_ca97_senza_dal_la_settimana_di_oggi`, `test_ca98_operatore_tutti_gli_artigiani_con_la_bottega`, `test_ca98_dal_non_lunedi_422`, `test_ca98_confine_di_settimana_in_europe_rome` (un post la domenica alle 23:30 di Roma resta nella settimana).

**Fatto quando**: CA-97, CA-98 verdi; CA-56 ancora verde; comandi del backend verdi.

---

## T3-74 · Ingresso e campagne dell'artigiano (frontend)

**Leggi**: spec §4, R-29; `docs/pagine/AdFlow-ingresso.html`, `docs/pagine/AdFlow-campagne.html`; questo brief §1.1–§1.3.

**File da toccare**: `frontend/src/pages/artigiano/Ingresso.tsx` (nuovo), `pages/artigiano/Campagne.tsx` (nuovo), `components/campagne/ElencoCampagne.tsx` e `components/campagne/sezioni.ts` (nuovi), `pages/artigiano/Campagna.tsx` (solo per leggere `?id=`), `App.tsx`, `contesto-auth.ts`, `components/Guscio.tsx`.
**Usa**: `GET /campagne` (già su `main`, con `richiesta`). Nessun endpoint nuovo.

**Passi**
1. `Ingresso.tsx`, in quest'ordine:
   - **Il consorzio ti chiede…**: per ogni campagna `in_revisione` con `richiesta = "aperta"` un riquadro in evidenza con il titolo e "Rispondi" → `/campagna?id=`.
   - **Avvisi**, solo testo e un link: la bozza ("Hai una campagna in bozza", "Continua"), quelle in lavorazione ("Il consorzio sta preparando la campagna"), la respinta e la scaduta non ancora sostituite (le stesse che oggi sceglie `campagna/viste/scelta.ts`).
   - **Nuova campagna**: pulsante → `/campagna`, come il "Nuova campagna" di oggi; non c'è se esiste una bozza.
   - **In corso**: le campagne `attiva` e `sospesa` (titolo, periodo, canali, "In corso" o "Pubblicazioni ferme"), un clic → `/campagna?id=`.
   - Il posto per **Questa settimana** resta vuoto: lo riempie T3-77.
2. `Campagne.tsx`: `ElencoCampagne` con le sezioni dell'artigiano del §1.1.
3. `ElencoCampagne.tsx`: riceve l'elenco, le sezioni e la funzione che dà il link di una campagna; nessuna chiamata dentro. Lo riusa T3-75.
4. `Campagna.tsx`: con `?id=` chiama `carica(id)` (la preferita c'è già); senza parametro tutto come oggi (CA-70).
5. `App.tsx`: rotte `/ingresso` e `/campagne` per l'artigiano (con `RichiedeProfilo`). `contesto-auth.ts`: `paginaIniziale("artigiano")` → `/ingresso`. `Guscio.tsx`: voci dell'artigiano del §1.3 (Calendario e Archivio foto portano a pagine che arrivano con T3-76 e T3-77: le voci entrano con quei task).

**Fatto quando**: build e lint puliti; dopo l'accesso l'artigiano arriva sull'Ingresso; screenshot nella PR con una richiesta aperta, una bozza e una campagna in corso.

---

## T3-75 · Artigiani per l'operatore (frontend)

**Leggi**: spec §4, R-38; `docs/pagine/AdFlow-operatore-elenco.html`, `AdFlow-operatore-artigiano.html`, `AdFlow-operatore-artigiano-campagne.html`; questo brief §1.1–§1.4.

**File da toccare**: `frontend/src/pages/operatore/Artigiani.tsx`, `pages/operatore/Artigiano.tsx`, `pages/operatore/CampagneArtigiano.tsx` (nuovi), `api/revisione.ts`, `api/artigiani.ts`, `api/campagne.ts` (parametro `artigiano` di `elenco()`), i dati di esempio in `api/esempi/`, `App.tsx`, `components/Guscio.tsx`.
**Usa**: gli endpoint di T3-71; dati di esempio finché non sono su `main`.

**Passi**
1. `Artigiani.tsx` (`/artigiani`): una tabella dentro un riquadro con altezza fissa e scorrimento proprio, intestazione ferma; colonne bottega (o "Profilo da compilare" con il nome dell'account), referente, città, canali collegati, da approvare, in corso, prossima scadenza; ricerca nel browser su bottega, referente, città ed email; la riga intera porta a `/artigiani/{id}`; "Nuovo artigiano" in alto.
2. `Artigiano.tsx` (`/artigiani/:id`): account (nome, email, attivo), canali collegati, il profilo in sola lettura diviso come i passi 1–9 (etichette da `ETICHETTE` e `PASSI` di `api/artigiani.ts`), "Profilo da compilare" se manca; due pulsanti: Campagne → `/artigiani/{id}/campagne`, Archivio foto → `/artigiani/{id}/archivio`.
3. `CampagneArtigiano.tsx` (`/artigiani/:id/campagne`): `ElencoCampagne` di T3-74 con le sezioni dell'operatore del §1.1, link a Vedi campagna.
4. `App.tsx`: le tre rotte con `RichiedeRuolo ruoli={["operatore", "admin"]}`. `Guscio.tsx`: voce Artigiani (§1.3).

**Fatto quando**: build e lint puliti; dati di esempio finché T3-71 non è su `main`, poi API vere; screenshot nella PR.

---

## T3-76 · Archivio foto (frontend)

**Leggi**: spec R-47; `docs/pagine/AdFlow-archivio-foto.html`; questo brief §1.2–§1.4.

**File da toccare**: `frontend/src/components/ArchivioFoto.tsx` (nuovo), `pages/artigiano/Archivio.tsx` e `pages/operatore/ArchivioArtigiano.tsx` (nuovi), `api/campagne.ts`, `api/esempi/campagne.ts`, `App.tsx`, `components/Guscio.tsx`.
**Da non toccare**: `api/archivio.ts` e il passo 7 (archivio congelato).

**Passi**
1. `ArchivioFoto.tsx`: riceve i blocchi; per ogni blocco l'intestazione (titolo, periodo, stato; "Foto senza campagna" se `campagna` è `null`) e una griglia di miniature; sulle immagini AI l'etichetta "Immagine AI"; sotto la miniatura "Pubblicata su Facebook, Instagram" se `pubblicata_su` non è vuoto. Un clic apre la foto grande in una finestra (Mantine `Modal`). Nessun pulsante per caricare, cambiare o eliminare.
2. `Archivio.tsx` (`/archivio`, artigiano) e `ArchivioArtigiano.tsx` (`/artigiani/:id/archivio`, operatore, con il nome della bottega e il ritorno alla pagina dell'artigiano).
3. `App.tsx` le due rotte; `Guscio.tsx` la voce Archivio foto dell'artigiano.

**Fatto quando**: build e lint puliti; dati di esempio finché T3-72 non è su `main`, poi API vere; screenshot nella PR dei due lati.

---

## T3-77 · Calendario settimanale (frontend)

**Leggi**: spec R-48; `docs/pagine/AdFlow-calendario.html`; questo brief §1.2–§1.4.

**File da toccare**: `frontend/src/components/CalendarioSettimana.tsx` e `CalendarioSettimana.module.css` (nuovi), `pages/Calendario.tsx` (nuovo, per i due ruoli), `pages/artigiano/Ingresso.tsx` (la sezione Questa settimana), `api/campagne.ts`, `api/esempi/campagne.ts`, `App.tsx`, `components/Guscio.tsx`.
**Da non toccare**: `components/CalendarioCampagnaView.tsx` (il calendario della campagna resta l'elenco per giorno).

**Passi**
1. `CalendarioSettimana.tsx`, **fatto a mano, senza librerie** (E1): una griglia CSS di 7 colonne, da lunedì a domenica, con il giorno e la data in testa e oggi evidenziato. In ogni colonna i post in ordine d'ora: una scheda piccola con ora, canale, stato ("In programma", "Pubblicato", "Non pubblicato" per fallito e annullato), titolo della campagna e, per l'operatore, la bottega; la miniatura della prima foto se c'è. Un clic porta dove dice il §1.2. Sotto i 768 px le colonne diventano un elenco per giorno.
2. Navigazione: "← Settimana prima", "Oggi", "Settimana dopo →". Il lunedì della prima settimana lo dà il server (`dal` vuoto); le altre si ottengono sommando ±7 giorni alla data `dal` in formato `AAAA-MM-GG`, con un aiuto che lavora in UTC sulla sola data (nessun fuso da calcolare nel browser).
3. Operatore: un filtro per bottega nel browser, tra le botteghe presenti nella settimana.
4. `Calendario.tsx` (`/calendario`, artigiano, operatore e admin) e, nell'Ingresso dell'artigiano, la sezione **Questa settimana** con lo stesso componente sulla settimana in corso.
5. `App.tsx` la rotta; `Guscio.tsx` la voce Calendario dei due ruoli.

**Fatto quando**: build e lint puliti; dati di esempio finché T3-73 non è su `main`, poi API vere; screenshot nella PR: settimana con post di due artigiani (operatore), settimana dell'artigiano, vista da telefono.

---

## T3-78 · Prova della corsia 7

**Leggi**: converge §4; questo brief.

**Passi**
1. `tests/percorsi/test_pagine_corsia7.py`: `test_ca99_percorso_pagine` — un artigiano con una campagna approvata e una in revisione con una richiesta aperta: l'operatore trova l'artigiano nell'elenco, ne apre la scheda, le campagne e l'archivio (le immagini AI della campagna approvata ci sono); l'artigiano nel suo archivio non vede le immagini AI della campagna in revisione; il calendario della settimana del primo post ha quel post per tutti e due.
2. Percorso a mano in due finestre, operatore e artigiano, sui dati della demo (T3-06): accesso dell'artigiano sull'Ingresso; richiesta in evidenza; campagne; archivio; calendario; dall'operatore elenco → artigiano → campagne → Vedi campagna; calendario d'insieme.

**Fatto quando**: CA-99 verde; i passi della demo di converge §4 senza errori; screenshot nella PR.

---

## T3-79 · Restyling grafico

Passato alla corsia 8 (ADR-118): `brief-interfaccia.md`.

---

## 2. Ordine di lavoro

1. **Backend**: T3-71, T3-72, T3-73, uno alla volta, ognuno con la sua PR.
2. **Frontend**: T3-74 subito (non aspetta il backend); T3-75, T3-76, T3-77 con i dati di esempio finché il loro endpoint non è su `main`.
3. **T3-78** quando tutti sono su `main`.

Date: lavoro dal 22 al 27/10, tutto su `main` entro il **28/10**; ciò che il 28/10 non è su `main` resta fuori dall'MVP e la sua parte di regole torna com'era (ADR-117).

## 3. Fuori da questi task (ADR-117, `docs/ROADMAP.md`)

- Archivio foto modificabile (caricare, eliminare, organizzare) e archivio come rimpiazzo nel piano (A10, congelato).
- Calendario mensile, con trascinamento o con una libreria.
- Pagina d'ingresso dell'operatore con "Da sistemare" (R-29 fuori MVP).
- Anagrafica completa, cambio password, collegamento degli account (R-37, D3).
- Ogni ristrutturazione del database delle foto.
