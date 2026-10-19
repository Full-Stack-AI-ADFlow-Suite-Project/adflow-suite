# Brief · Corsia 6 · Interventi e richiesta all'artigiano (T3-61…T3-66)

Per l'agente o la persona che fa un task della corsia 6. Decisione: ADR-116. Leggi prima `constitution.md`, `perimetro-mvp.md` (righe B5, B8–B10), poi **solo** la sezione del tuo task qui sotto e le regole che cita. Le firme, i messaggi d'errore e gli schemi di questa pagina sono il contratto tra i task: non cambiarli senza chiedere. Dove il codice di `main` è diverso da come è descritto qui, fermati e chiedi.

**Le due funzioni.**
- **Dopo l'approvazione** (spec R-16, R-33, R-34, R-36): su un post `approvato` che esce tra almeno 15 minuti, in campagna `attiva` o `sospesa`, l'operatore modifica a mano, cambia foto, sposta o annulla con una nota, senza sospendere. La versione che scrive nasce approvata da lui. Sospendi (con una nota facoltativa), riattiva, annulla e riprogramma tornano visibili.
- **Richiesta all'artigiano** (spec R-46, R-36): in revisione l'operatore cambia foto e sposta; se manca ciò che può dare solo l'artigiano gli chiede una risposta e fino a 3 foto da sostituire. L'artigiano risponde dalla sua pagina Campagna, con il suo accesso. La campagna resta in revisione; la foto nuova la usa l'operatore con Cambia foto.

**Già su `main` con T3-60** (non si rifà): le regole in costituzione, spec e plan; i valori in `contenuti/domain.py` (`MODIFICA`, `RIGENERA`, `CAMBIA_FOTO`, `SPOSTA`, `ANNULLA`, `RIPROGRAMMA`, `INTERVENTI`, `INTERVENTI_AMMESSI`, `STATI_CHE_USANO_LA_FOTO`) e in `campagne/domain.py` (`ESITO_POST_ANNULLATO`, `ESITO_INTEGRAZIONE`, `ESITO_INTEGRAZIONE_FOTO`, `ESITO_INTEGRAZIONE_RISPOSTA`, `MAX_FOTO_RICHIESTA`, `STATI_RICHIESTA`); le pagine statiche di riferimento (`docs/pagine/AdFlow-operatore-campagna.html`, `docs/pagine/AdFlow-campagna-stati.html`).

**Regole di lavoro per tutti i task.**
- Un branch `feature/<id>-<breve>` da `main`; fai solo il tuo task; tocca i file elencati e i loro test. Se ti serve un file che non è nell'elenco, fermati e chiedi.
- Il codice congelato resta congelato, **tranne** quello che il tuo task scongela per nome (qui sotto). Nota interna, togli canale, spunta, archivio e caroselli restano congelati e nascosti.
- Nessuna migrazione, nessuna libreria nuova, nessun file in `core/`.
- Messaggi in italiano, esattamente quelli di questa pagina; codici solo tra quelli di costituzione §4.
- Test su PostgreSQL con le fixture di plan §7 e le fabbriche; il nome porta il CA (`test_ca84_…`). Nessuna chiamata reale ad AI, social o email.
- Fatto quando, per ogni task di backend: `uv run alembic upgrade head`, `uv run pytest`, `uv run black --check .` verdi da `backend/`, `tests/test_confini.py` compreso. Per ogni task di frontend: `npm run lint` e `npm run build` puliti da `frontend/`. Poi la checklist di `converge.md` §1 e la casella del task in `tasks.md`.

---

## 1. Contratti comuni

### 1.1 Interventi ammessi (spec R-16)

`INTERVENTI_AMMESSI` (in `contenuti/domain.py`, già su `main`) dà, per `(stato della campagna, stato del post)`, l'insieme degli interventi. `interventi_ammessi()` aggiunge le condizioni sul singolo post. Algoritmo, da scrivere in `contenuti/interventi.py` (T3-61):

```python
def interventi_ammessi(post: Post, stato_campagna: str, adesso: datetime) -> list[str]:
    ammessi = set(INTERVENTI_AMMESSI.get((stato_campagna, post.stato), ()))
    if not ammessi or _intervento_attivo(post, adesso):
        return []
    margine = timedelta(minutes=leggi_impostazioni().margine_slot_minuti)
    if post.stato == APPROVATO and post.data_ora < adesso + margine:
        return []
    if post.versione_corrente is None:
        ammessi -= {MODIFICA, RIGENERA, CAMBIA_FOTO}
    if post.riempitivo is not None:
        ammessi -= {CAMBIA_FOTO}
    if post.n_rigenerazioni_testo >= MAX_RIGENERAZIONI:
        ammessi -= {RIGENERA}
    return [uno for uno in INTERVENTI if uno in ammessi]
```

`verifica_intervento(db, post, intervento, adesso) -> Campagna` restituisce la campagna se `intervento in interventi_ammessi(...)`; altrimenti solleva `StatoNonValido` (409) con il primo messaggio che vale, in quest'ordine:

| Caso | Messaggio |
|---|---|
| intervento in corso (R-31) | `Sul post c'è un intervento in corso.` |
| post `approvato` in campagna attiva o sospesa, entro il margine | `Il post esce tra meno di {margine} minuti: non si tocca più.` |
| `CAMBIA_FOTO` su un post con `riempitivo` | `Un post con un'immagine AI non cambia foto.` |
| `RIGENERA` a cicli finiti | `Le 3 rigenerazioni del testo sono finite: resta la modifica a mano.` |
| versione corrente mancante | `Il post non ha ancora un testo.` |
| ogni altro caso | `Questo intervento non è ammesso: la campagna è «{stato_campagna}», il post è «{stato_post}».` |

### 1.2 Approvazione delle versioni nate dopo l'approvazione

Quando la campagna è `attiva` o `sospesa`, la versione nuova di modifica e cambia foto ha subito la sua riga `approvazione` (`versione_id`, `utente_id` dell'operatore, `ruolo` dell'operatore, `esito="approvato"`). La scrive `revisione` (proprietario della tabella) con una funzione privata in `revisione/interventi.py`:

```python
def _approva_se_approvata(db: Session, versione, utente: accesso.Utente) -> None:
    """Dopo l'approvazione la versione dell'operatore nasce approvata (spec R-16)."""
```

La campagna si legge con `campagne.campagna(db, versione.post.campagna_id)`.

### 1.3 Decisioni nuove (tutte con `campagne.registra_decisione()`)

| Esito | Chi | `nota` | `foto_segnate` | `post_id` |
|---|---|---|---|---|
| `sospesa` (esiste) | operatore | la nota di sospendi, o `None` | `[]` | — |
| `riprogrammato` (esiste) | operatore | riprogramma: `None`; sposta: `Spostato dal {gg/mm/aaaa hh:mm} al {gg/mm/aaaa hh:mm}` (Europe/Rome) | `[]` | il post |
| `post_annullato` | operatore | la nota (obbligatoria) | `[]` | il post |
| `integrazione` | operatore | la domanda | le foto da sostituire, 0–3 | — |
| `integrazione_foto` | artigiano | `None` | `[foto segnata, foto nuova]` | — |
| `integrazione_risposta` | artigiano | la risposta, o `None` | le foto nuove | — |

### 1.4 Schemi nuovi o cambiati (backend → frontend)

```python
# revisione/schemas.py
class PostSchema(BaseModel):          # campo nuovo, in fondo
    interventi: list[str] = []        # interventi_ammessi() adesso

class PostSposta(BaseModel):          # POST /post/{id}/sposta
    model_config = ConfigDict(extra="forbid")
    data_ora: datetime

class PostAnnulla(BaseModel):         # POST /post/{id}/annulla
    model_config = ConfigDict(extra="forbid")
    nota: str = Field(min_length=1)

class CampagnaSospendi(BaseModel):    # POST /campagne/{id}/sospendi, corpo facoltativo
    model_config = ConfigDict(extra="forbid")
    nota: str | None = None

class PostCambiaFoto(BaseModel):      # POST /post/{id}/cambia-foto (T3-62)
    model_config = ConfigDict(extra="forbid")
    foto_id: int

class FotoPossibile(BaseModel):       # GET /post/{id}/foto-possibili (T3-62)
    foto_id: int
    punteggio: float | None
    analizzata: bool                  # False: arrivata con una richiesta, senza analisi

class CampagnaDaApprovare(BaseModel): # campo nuovo, in fondo (T3-63)
    richiesta: str | None = None      # "aperta", "inviata" o None

# campagne/schemas.py (T3-63)
class RichiestaCrea(BaseModel):       # POST /campagne/{id}/richiesta
    model_config = ConfigDict(extra="forbid")
    domanda: str
    foto: list[int] = []

class RichiestaInvia(BaseModel):      # POST /campagne/{id}/richiesta/invia
    model_config = ConfigDict(extra="forbid")
    risposta: str | None = None

class FotoDaSostituire(BaseModel):
    foto_id: int
    gruppo_id: int | None
    nuova_foto_id: int | None = None

class RichiestaArtigiano(BaseModel):
    stato: Literal["aperta", "inviata", "decaduta"]
    domanda: str
    creata_il: datetime
    foto: list[FotoDaSostituire]
    risposta: str | None = None
    inviata_il: datetime | None = None

class CampagnaDettaglio(BaseModel):   # campo nuovo, in fondo
    richiesta: RichiestaArtigiano | None = None

class CampagnaElencoItem(BaseModel):  # campo nuovo, in fondo
    richiesta: str | None = None      # stato della richiesta, solo nell'elenco dell'artigiano
```

```ts
// frontend/src/api/revisione.ts (T3-64)
export type Intervento =
  | "modifica" | "rigenera" | "cambia_foto" | "sposta" | "annulla" | "riprogramma";
// PostVista: interventi: Intervento[];
export interface FotoPossibile { foto_id: number; punteggio: number | null; analizzata: boolean; }

// frontend/src/api/campagne.ts (T3-65)
export type StatoRichiesta = "aperta" | "inviata" | "decaduta";
export interface FotoDaSostituire { foto_id: number; gruppo_id: number | null; nuova_foto_id: number | null; }
export interface RichiestaArtigiano {
  stato: StatoRichiesta; domanda: string; creata_il: string;
  foto: FotoDaSostituire[]; risposta: string | null; inviata_il: string | null;
}
// CampagnaDettaglio: richiesta?: RichiestaArtigiano | null;
// CampagnaElencoItem: richiesta?: StatoRichiesta | null;

// frontend/src/api/decisioni.ts (T3-65)
// CampagnaDaApprovare: richiesta: "aperta" | "inviata" | null;
```

---

## T3-61 · Interventi sul post, backend

**Leggi**: spec R-16, R-30, R-31, R-33, R-34, R-36 (solo *Sposta*); plan §3 (righe di `revisione`), §6; questo brief §1.

**File da toccare**: `backend/app/moduli/contenuti/interventi.py`, `contenuti/service.py`; `revisione/interventi.py`, `revisione/sospensione.py`, `revisione/router.py`, `revisione/schemas.py`, `revisione/service.py`; i test in `tests/moduli/contenuti/` e `tests/moduli/revisione/`.
**Da non toccare**: `campagne/`, `pubblicazione/`, i `domain.py` (i valori ci sono già), la spunta (`segna_controllato()`, rotta `/controllato`), nota interna, togli canale.
**Scongela**: `revisione/sospensione.py` (intestazione), le rotte `sospendi`, `riattiva`, `annulla`, `riprogramma` di `revisione/router.py`, `revisione/interventi.riprogramma()`: togli il commento "Congelato per l'MVP, ADR-114".

**Passi**
1. `contenuti/interventi.py`: scrivi `interventi_ammessi()` e `verifica_intervento()` come al §1.1. Togli `_si_puo_intervenire()`: `puo_rigenerare()` diventa `RIGENERA in interventi_ammessi(record, campagna.stato, adesso)`; in `accendi_intervento()` il ramo delle rigenerazioni resta su `puo_rigenerare()` con il suo messaggio di oggi, il ramo `ritocco_foto` (fuori MVP, senza rotta) resta ammesso solo in `in_revisione` su un post `da_approvare` senza intervento in corso.
2. `contenuti/interventi.modifica()`: i primi controlli (campagna in revisione, post da approvare, intervento in corso, versione) diventano `campagna = verifica_intervento(db, record, MODIFICA, adesso)`. Il resto non cambia (validatore, 422 con un blocco o senza cambiamenti, spunta azzerata).
3. `contenuti/service.py`:
   - `interventi_ammessi(post, stato_campagna, adesso) -> list[str]`: espone quella di `interventi.py` (import dentro la funzione, come `puo_rigenerare()`). Senza `db`.
   - `_verifica_nuova_data(campagna, data_ora, adesso) -> None`: i tre controlli di oggi di `riprogramma_post()` (fuso, margine, periodo), con gli stessi messaggi.
   - `riprogramma_post()`: lo stato si controlla con `verifica_intervento(db, record, RIPROGRAMMA, adesso)`, poi `_verifica_nuova_data()`. Comportamento invariato (CA-67).
   - `sposta_post(db, post_id, data_ora, adesso) -> tuple[Post, datetime]`: `verifica_intervento(…, SPOSTA, …)` (409), `_verifica_nuova_data()` (422), data uguale a quella di prima → `DatiNonValidi("La nuova data è uguale a quella di prima.")`; poi `data_ora` nuova, spunta azzerata, `flush`. Restituisce il post e la data di prima. Lo stato del post non cambia.
   - `annulla_un_post(db, post_id, adesso) -> Post`: `verifica_intervento(…, ANNULLA, …)` (409), poi `annulla_post(db, post.campagna_id, post_ids=[post_id])` e restituisce il post.
4. `revisione/interventi.py`:
   - `modifica(db, post_id, utente, testo, hashtag, adesso)`: riceve l'utente (non più l'id), chiama `contenuti.modifica_post(db, post_id, utente.id, …)`, poi `_approva_se_approvata()` (§1.2).
   - `sposta(db, post_id, utente_id, data_ora, adesso)`: `contenuti.sposta_post()`, poi decisione `riprogrammato` con il post e la nota «Spostato dal … al …» (§1.3, date in `ROMA` di `core/orologio.py`, formato `%d/%m/%Y %H:%M`).
   - `annulla(db, post_id, utente_id, nota, adesso)`: nota vuota dopo `strip()` → `DatiNonValidi("Per annullare un post serve la nota.")`, prima di ogni altro controllo; poi `contenuti.annulla_un_post()` e la decisione `post_annullato` con il post e la nota.
   - `riprogramma()`: com'è, scongelata.
5. `revisione/sospensione.sospendi(db, campagna_id, utente, nota=None)`: la nota (`strip()`, vuota → `None`) va nella decisione `sospesa`. `riattiva()` e `annulla()` non cambiano.
6. `revisione/service.py`: `vedi_campagna(db, campagna_id, stato=None, adesso=None)` (con `adesso` vuoto usa `core.orologio.adesso()`); `_post(post, stato_campagna, adesso)` riempie `interventi` con `contenuti.interventi_ammessi()`.
7. `revisione/schemas.py`: `PostSchema.interventi`, `PostSposta`, `PostAnnulla`, `CampagnaSospendi` (§1.4).
8. `revisione/router.py`:
   - `GET /campagne/{id}/post` passa `ora` (dipendenza `adesso`) a `vedi_campagna()`.
   - `POST /post/{id}/modifica` passa `utente` a `interventi.modifica()`.
   - `POST /campagne/{id}/sospendi` con corpo facoltativo `CampagnaSospendi | None = None`.
   - Rotte nuove, in un blocco in fondo al file con il commento `# Corsia 6 (ADR-116): interventi dopo l'approvazione e sposta.`:
     - `POST /post/{post_id}/sposta` (`PostSposta`) → `{"stato": <stato del post>}`;
     - `POST /post/{post_id}/annulla` (`PostAnnulla`) → `{"stato": "annullato"}`.
   - Tutte con `richiede_ruolo("operatore")`.

**Test** (nomi da usare)
- `tests/moduli/contenuti/test_interventi_ammessi.py` (nuovo), con `ADESSO` fisso: `test_in_revisione_quattro_interventi`, `test_approvato_oltre_il_margine`, `test_approvato_entro_il_margine_nessuno`, `test_con_un_intervento_in_corso_nessuno`, `test_fallito_solo_riprogramma`, `test_immagine_ai_senza_cambia_foto`, `test_rigenerazioni_finite_senza_rigenera`, `test_stati_chiusi_nessuno` (parametrizzato su pubblicato, annullato, scaduto, scartato).
- `tests/moduli/contenuti/test_modifica_a_mano.py`: `test_ca29_in_campagna_attiva_409` diventa `test_ca29_dopo_l_approvazione_entro_15_minuti_409` (post approvato con `data_ora = ADESSO + 10 minuti`); nuovo `test_ca84_dopo_l_approvazione_oltre_15_minuti_nasce_la_versione`.
- `tests/moduli/revisione/test_interventi.py`:
  - `test_ca29_in_campagna_attiva_o_sospesa_gli_interventi_409` riscritto come CA-29: rigenera e spunta → 409 su un post qualunque; modifica, sposta e annulla → 409 su un post con `data_ora = adesso reale + 5 minuti`;
  - `test_ca84_modifica_dopo_l_approvazione_ha_la_riga_approvazione`, `test_ca84_modifica_dopo_l_approvazione_con_un_blocco_422`;
  - `test_ca85_annulla_il_post_con_la_nota`, `test_ca85_annulla_senza_nota_422`, `test_ca85_annulla_in_revisione_409`;
  - `test_ca72_sposta_in_revisione`, `test_ca72_sposta_dopo_l_approvazione`, `test_ca72_sposta_fuori_periodo_nel_passato_o_uguale_422`;
  - `test_vedi_campagna_dice_gli_interventi_ammessi`.
- `tests/moduli/revisione/test_sospensione.py`: `test_ca32_sospendi_con_la_nota`, `test_ca32_sospendi_senza_corpo`.
- `CA-67` e gli altri test di oggi restano verdi senza cambiare le asserzioni sui codici di stato.

**Fatto quando**: CA-29, CA-32, CA-67, CA-72, CA-84, CA-85 verdi; comandi del backend verdi.

---

## T3-62 · Cambia foto, backend

**Leggi**: spec R-16, R-36 (*Cambia foto*), costituzione §1.9; questo brief §1.1, §1.2, §1.4. **Dipende da** T3-61 su `main`.

**File da toccare**: `contenuti/interventi.py`, `contenuti/service.py`, `revisione/interventi.py`, `revisione/router.py`, `revisione/schemas.py`; test in `tests/moduli/contenuti/` e `tests/moduli/revisione/`.
**Da non toccare**: `campagne/` (si usano `gruppi_della_campagna()`, `aggiorna_foto()`, `foto_per_id()` come sono), i `domain.py`.

**Passi**
1. `contenuti/interventi.foto_possibili(db, post_id, adesso) -> list[Foto]`:
   - `record = _post(db, post_id)`; `campagna = verifica_intervento(db, record, CAMBIA_FOTO, adesso)` (409).
   - Il gruppo è quello dell'uscita (`Uscita.gruppo_id`); senza gruppo → `StatoNonValido("Un post con un'immagine AI non cambia foto.")`.
   - Le foto del gruppo da `campagne.gruppi_della_campagna(db, campagna.id)`, tenendo quelle con `origine == "caricata"` e con analisi vuota **oppure** `analisi_ai["idonea"] is True`.
   - Fuori: le foto della versione corrente del post; le foto della versione corrente di ogni altro post della campagna sullo stesso canale con stato in `STATI_CHE_USANO_LA_FOTO`.
   - Ordine: prima quelle senza analisi (arrivate con una richiesta), poi per `punteggio` decrescente (senza punteggio = 0), poi per id.
2. `contenuti/interventi.cambia_foto(db, post_id, foto_id, utente_id, adesso) -> VersionePost`:
   - `possibili = foto_possibili(…)`; `foto_id` non tra queste → `DatiNonValidi("Questa foto non si può usare per il post: deve essere del gruppo dell'uscita, idonea o arrivata con una richiesta, e non già su questo canale.")`.
   - Versione nuova: `numero + 1`, stesso `testo`, stessi `hashtag`, `autore_id=utente_id`, `tipo_intervento="cambio_foto"`, `errori_validazione` copiati dalla corrente. I legami: la foto scelta al posto di quella nella posizione più bassa; le altre posizioni (caroselli, congelati) copiate.
   - `da_rivedere` non cambia; spunta azzerata; `campagne.aggiorna_foto(db, scelta.id, scelta.analisi_ai, scelta.n_utilizzi + 1)`; `flush` ed `expire` come in `modifica()`.
3. `contenuti/service.py`: `foto_possibili()` e `cambia_foto()` esposte con l'import dentro la funzione.
4. `revisione/interventi.py`: `foto_possibili(db, post_id, adesso) -> list[FotoPossibile]` (`punteggio` da `analisi_ai`, `analizzata = analisi_ai is not None`); `cambia_foto(db, post_id, foto_id, utente, adesso)`: `contenuti.cambia_foto(…)`, poi `_approva_se_approvata()`.
5. `revisione/schemas.py`: `PostCambiaFoto`, `FotoPossibile` (§1.4).
6. `revisione/router.py`, nel blocco della corsia 6: `GET /post/{post_id}/foto-possibili` → `list[FotoPossibile]`; `POST /post/{post_id}/cambia-foto` (`PostCambiaFoto`) → `{"stato": "ok"}`.

**Test**
- `tests/moduli/contenuti/test_cambia_foto.py` (nuovo): `test_ca71_foto_possibili_del_gruppo_idonee_e_libere_sul_canale`, `test_ca71_foto_senza_analisi_in_cima`, `test_ca71_foto_non_idonea_o_di_un_altro_gruppo_esclusa`, `test_ca71_foto_gia_in_un_post_vivo_dello_stesso_canale_esclusa`, `test_ca71_foto_di_un_post_scartato_torna_libera`, `test_ca71_nasce_la_versione_cambio_foto_con_lo_stesso_testo`, `test_ca71_foto_fuori_elenco_422`, `test_ca71_immagine_ai_409`.
- `tests/moduli/revisione/test_interventi.py`: `test_ca71_cambia_foto_in_revisione_via_api`, `test_ca71_cambia_foto_dopo_l_approvazione_ha_la_riga_approvazione`, `test_ca71_cambia_foto_entro_15_minuti_409`.
- Le foto della fabbrica non hanno analisi: nei test che vogliono una foto idonea si mette `analisi_ai=dict(ANALISI_IDONEA)`.

**Fatto quando**: CA-71 verde; comandi del backend verdi.

---

## T3-63 · Richiesta all'artigiano, backend

**Leggi**: spec R-46, R-13, R-41, §4 (artigiano); plan §2 (`decisione_campagna`), §3 (righe di `campagne` della richiesta, `GET /campagne`, `GET /campagne/{id}`, `GET /da-approvare`); questo brief §1.3, §1.4.

**File da toccare**: `campagne/service.py`, `campagne/schemas.py`, `campagne/router.py`, `campagne/viste.py`; `revisione/letture.py`, `revisione/schemas.py` (solo `CampagnaDaApprovare`); `tests/moduli/campagne/fabbrica.py` (fabbrica `richiesta`), test in `tests/moduli/campagne/` e `tests/moduli/revisione/`.
**Da non toccare**: `contenuti/`, `revisione/interventi.py`, `revisione/router.py`, i `domain.py`, l'archivio (congelato).

**Passi**
1. `campagne/schemas.py`: `RichiestaCrea`, `RichiestaInvia`, `FotoDaSostituire`, `RichiestaArtigiano`; campi nuovi `CampagnaDettaglio.richiesta` e `CampagnaElencoItem.richiesta` (§1.4).
2. `campagne/service.py`:
   - `richiesta_di(db, campagna_id) -> RichiestaArtigiano | None`. L'ultima decisione `integrazione` (per id) è la richiesta; nessuna → `None`. Le decisioni `integrazione_foto` con id maggiore danno le foto nuove (`foto_segnate = [segnata, nuova]`); la prima `integrazione_risposta` con id maggiore dà risposta e `inviata_il`. Stato: `inviata` se c'è la risposta; altrimenti `aperta` se la campagna è `in_revisione`, `decaduta` se no.
   - `apri_richiesta(db, campagna_id, utente_id, domanda, foto_ids) -> RichiestaArtigiano`, in quest'ordine:
     1. campagna (404 com'è oggi); non `in_revisione` → `StatoNonValido("Si chiede all'artigiano solo con la campagna in revisione.")`;
     2. domanda vuota dopo `strip()` → `DatiNonValidi("Scrivi la domanda per l'artigiano.")`;
     3. id ripetuti tolti, nell'ordine; più di `MAX_FOTO_RICHIESTA` → `DatiNonValidi("Si chiedono al massimo 3 foto.")`;
     4. ogni foto deve essere della campagna, `caricata` e in un gruppo → altrimenti `DatiNonValidi("Si possono segnare solo le foto caricate dall'artigiano per questa campagna.")`;
     5. decisione `integrazione` (§1.3). Una richiesta già aperta non blocca: la nuova la sostituisce.
   - `_salva_foto_caricata(db, campagna, gruppo, contenuto) -> Foto`: la parte di oggi di `carica_foto()` che controlla il file (`analizza_e_valida_immagine()`), lo salva nell'archivio con la pulizia al rollback (`_al_termine_transazione()`) e crea la `Foto` (`origine="caricata"`, senza analisi). `carica_foto()` la usa: il suo comportamento non cambia (CA-13 verde).
   - `carica_foto_richiesta(db, utente_id, campagna_id, foto_id, contenuto, dichiarazione) -> Foto`, in quest'ordine:
     1. campagna dell'artigiano (`profilo_di()`), altrimenti `NonTrovato("Campagna non trovata.")`;
     2. richiesta non `aperta` (o assente) → `StatoNonValido("Non c'è una richiesta del consorzio aperta.")`;
     3. `foto_id` non tra le foto segnate → `DatiNonValidi("Questa foto non è tra quelle chieste dal consorzio.")`;
     4. foto segnata già sostituita → `StatoNonValido("Per questa foto hai già caricato quella nuova.")`;
     5. `dichiarazione` non vera → `DatiNonValidi("Confermare la dichiarazione sulle foto prima di caricarle.")`;
     6. gruppo della foto segnata, con `with_for_update()`; già con 20 foto → lo stesso messaggio di `carica_foto()`;
     7. `_salva_foto_caricata()`, poi decisione `integrazione_foto` con l'artigiano e `[foto_id, nuova.id]`.
   - `invia_risposta(db, utente_id, campagna_id, risposta) -> RichiestaArtigiano`: campagna dell'artigiano (404); richiesta non `aperta` → 409 come sopra; foto segnate senza la nuova → `StatoNonValido("Mancano {n} foto da caricare.")`; nessuna foto segnata e risposta vuota → `DatiNonValidi("Scrivi la risposta per il consorzio.")`; poi decisione `integrazione_risposta` (risposta dopo `strip()`, vuota → `None`; `foto_segnate` = le foto nuove).
   - `dettaglio_campagna()`: `richiesta=richiesta_di(db, campagna_id)` per artigiano e operatore.
3. `campagne/viste.py`: in `campagne_artigiano()`, per ogni campagna `in_revisione` `item.richiesta = richiesta_di(…).stato` (o `None`); in `_priorita()` una campagna con la richiesta `aperta` vale `-1` (prima di tutto, anche della bozza).
4. `campagne/router.py`:
   - porta la lettura a blocchi del file di `carica_foto()` in una funzione privata `_leggi_file(file) -> bytes`, con gli stessi messaggi, e usala in `carica_foto()` e nella rotta nuova;
   - rotte nuove, in un blocco in fondo con il commento `# Corsia 6 (ADR-116): richiesta all'artigiano (spec R-46).`:
     - `POST /campagne/{id}/richiesta` (operatore, `RichiestaCrea`) → 201 `RichiestaArtigiano`;
     - `POST /campagne/{id}/richiesta/foto` (artigiano; multipart: `file`, `foto_id` come `Form`, `dichiarazione: bool` come `Form`, falso se manca) → 201 `FotoDettaglio`;
     - `POST /campagne/{id}/richiesta/invia` (artigiano, `RichiestaInvia | None = None`) → 200 `RichiestaArtigiano`.
5. `revisione/letture.da_approvare()`: `richiesta` di ogni riga = lo stato di `campagne.richiesta_di()` se è `aperta` o `inviata`, altrimenti `None`. `CampagnaDaApprovare.richiesta` in `revisione/schemas.py` (§1.4).
6. `tests/moduli/campagne/fabbrica.py`: `richiesta(db, campagna, foto=(), domanda="Puoi mandarci una foto nuova?", operatore=None) -> DecisioneCampagna`: la decisione `integrazione` (con un operatore della fabbrica di accesso se manca), `flush`, nessun `commit`.

**Test** in `tests/moduli/campagne/test_richiesta.py` (nuovo), con `utente_di_prova` e `client`:
- `test_ca86_chiedi_all_artigiano_con_domanda_e_due_foto`, `test_ca86_senza_domanda_422`, `test_ca86_quattro_foto_422`, `test_ca86_foto_di_un_altra_campagna_o_immagine_ai_422`, `test_ca86_campagna_non_in_revisione_409`, `test_ca86_artigiano_403`;
- `test_ca87_carica_la_foto_nuova_con_la_dichiarazione`, `test_ca87_senza_dichiarazione_422`, `test_ca87_foto_non_segnata_422`, `test_ca87_seconda_foto_per_la_stessa_409`, `test_ca87_file_non_valido_422`, `test_ca87_artigiano_di_un_altra_bottega_404`;
- `test_ca88_invia_la_risposta`, `test_ca88_mancano_foto_409`, `test_ca88_senza_foto_e_senza_testo_422`;
- `test_ca89_approva_e_respingi_ammessi_con_la_richiesta_aperta`, `test_ca89_dopo_l_approvazione_caricare_o_inviare_409`, `test_ca89_una_richiesta_nuova_sostituisce_quella_aperta`;
- `test_ca90_l_artigiano_vede_la_richiesta_e_nessun_post`, `test_ca90_la_campagna_con_la_richiesta_si_apre_per_prima`;
- in `tests/moduli/revisione/test_da_approvare.py`: `test_ca88_da_approvare_segna_la_richiesta`.
- I file delle foto: come nei test di `carica_foto()` di oggi (archivio finto, immagine generata con Pillow di lato corto ≥ 1080 px).

**Fatto quando**: CA-86…CA-90 verdi; CA-13, CA-31 verdi; comandi del backend verdi.

---

## T3-64 · Vedi campagna, interventi (frontend)

**Leggi**: spec R-16, R-33, R-34, R-36, §4 (operatore); plan §3 (righe di `revisione`); questo brief §1.4; pagina statica `docs/pagine/AdFlow-operatore-campagna.html` (post in attiva e sospesa, Cambia foto, Sposta, Annulla il post, Sospendi).

**File da toccare** (`frontend/src/`): `api/revisione.ts`, `api/interventi.ts`, `api/decisioni.ts` (solo `sospendi`), `api/esempi/revisione.ts`, `api/esempi/interventi.ts`, `api/esempi/decisioni.ts` (solo `sospendi`), `pages/operatore/vedi-campagna/post/AzioniPost.tsx`, file nuovi `pages/operatore/vedi-campagna/post/CambiaFoto.tsx`, `Sposta.tsx`, `AnnullaPost.tsx`, `pages/operatore/campagna/PostCard.tsx`, `pages/operatore/vedi-campagna/decisioni/AzioniCampagna.tsx`, `decisioni/Sospensione.tsx`, `decisioni/RiprogrammaPost.tsx`, `pages/operatore/VediCampagna.tsx`, `pages/operatore/campagna/Decidi.tsx` (solo il blocco `attiva`/`sospesa`).
**Da non toccare**: il blocco `in_revisione` di `Decidi.tsx` e tutto ciò che riguarda la richiesta (T3-65); `NotaInterna.tsx`, `TogliCanale.tsx`, la spunta: restano nascosti.
**Scongela**: `Sospensione.tsx`, `RiprogrammaPost.tsx`; in `AzioniCampagna.tsx` e `VediCampagna.tsx` solo sospendi, riattiva e annulla.

**Passi**
1. Tipi e funzioni:
   - `api/revisione.ts`: `Intervento`, `PostVista.interventi`, `FotoPossibile` (§1.4).
   - `api/interventi.ts`: `fotoPossibili(postId): Promise<FotoPossibile[]>` (GET `/post/{id}/foto-possibili`); `cambiaFoto(postId, fotoId)` (POST `/post/{id}/cambia-foto` `{foto_id}`); `sposta(postId, locale)` (POST `/post/{id}/sposta`, `locale` di un campo `datetime-local` convertito in ISO come fa `riprogramma()`); `annullaPost(postId, nota)` (POST `/post/{id}/annulla`).
   - `api/decisioni.ts`: `sospendi(campagnaId, nota: string | null)` manda `{nota}`.
   - Esempi: ogni post degli esempi ha `interventi` coerenti con il suo stato (in revisione i quattro; in attiva un post oltre i 15 minuti con modifica, cambia_foto, sposta, annulla; uno entro i 15 minuti senza interventi; un fallito con riprogramma); le funzioni nuove degli esempi cambiano lo stato in memoria come fanno quelle di oggi.
2. `AzioniPost.tsx`: i pulsanti nascono **solo** da `post.interventi`, non da regole sullo stato:
   - `modifica` → «Modifica a mano»; `rigenera` → «Rigenera da zero» e «Rigenera da testo proposto» con il contatore di oggi; `cambia_foto` → «Cambia foto»; `sposta` → «Sposta»; `annulla` → «Annulla il post»; `riprogramma` → «Riprogramma» (apre `RiprogrammaPost`).
   - In revisione, con rigenerazioni finite: «Le 3 rigenerazioni sono finite: resta la modifica a mano.» (come oggi).
   - Post `approvato` in campagna attiva o sospesa senza interventi: «Esce tra meno di 15 minuti: non si tocca più.» Sostituisce il testo di oggi «Il post non si modifica…».
   - Con la campagna attiva o sospesa, `ModificaMano` e `CambiaFoto` mostrano sopra il pulsante: «La campagna è approvata: la versione che salvi esce al posto di quella di prima, e la approvi tu.»
3. `CambiaFoto.tsx` (finestra «Cambia foto»): legge `fotoPossibili()`; miniature da `/api/foto/{id}/file`; su una foto non analizzata il segno «Nuova, dall'artigiano: guardala tu»; sulle altre «Punteggio n»; pulsante «Usa questa foto». Elenco vuoto: «Nel gruppo non ci sono altre foto adatte: chiedile all'artigiano, oppure respingi.» (in revisione) o «Nel gruppo non ci sono altre foto adatte.» (dopo l'approvazione).
4. `Sposta.tsx` (finestra «Sposta il post»): campo data e ora; sotto «Dentro il periodo della campagna, almeno 15 minuti da adesso.»; pulsante «Sposta».
5. `AnnullaPost.tsx` (finestra «Annulla il post»): avviso «Il post non esce più e non torna indietro.»; campo obbligatorio «Perché non deve uscire?»; pulsante rosso «Annulla il post».
6. `PostCard.tsx`: monta `RiprogrammaPost` (via `AzioniPost`) al posto del commento di congelamento; se `versione_corrente.tipo_intervento === "cambio_foto"` un avviso giallo «Foto cambiata: rileggi il testo.»
7. `AzioniCampagna.tsx` montata in `VediCampagna.tsx` sotto `Decidi`: in `attiva` «Sospendi» e «Annulla la campagna»; in `sospesa` «Riattiva» e «Annulla la campagna»; nessun pulsante in altri stati. Nota interna e togli canale restano fuori. Nella finestra Sospendi: campo «Nota interna (facoltativa)» e il testo «Nessun post esce finché non la riattivi. L'artigiano vede "Pubblicazioni ferme".»
8. `Decidi.tsx`, blocco `attiva`/`sospesa`: «Il contenuto non si modifica più.» diventa «Sui post che escono tra almeno 15 minuti puoi ancora intervenire.»
9. Dopo ogni azione la pagina rilegge Vedi campagna (`ricarica`), come oggi; gli errori mostrano il `detail` del server.

**Fatto quando**: build e lint puliti; con i dati di esempio (`VITE_USA_ESEMPI=1`) ogni pulsante compare solo dove l'esempio lo ammette; appena T3-61 e T3-62 sono su `main`, la pagina usa le API vere e il percorso a mano di `converge.md` §4 (passi 4 e 6) gira senza errori; screenshot nella PR accanto alla pagina statica.

---

## T3-65 · Richiesta all'artigiano, frontend

**Leggi**: spec R-46, R-41, §4 (artigiano e operatore); plan §3 (righe della richiesta); questo brief §1.4; pagine statiche `docs/pagine/AdFlow-operatore-campagna.html` (Chiedi all'artigiano, riquadro della richiesta) e `docs/pagine/AdFlow-campagna-stati.html` (vista «In revisione» con la richiesta).

**File da toccare** (`frontend/src/`): `api/campagne.ts`, `api/decisioni.ts` (solo `CampagnaDaApprovare.richiesta`), `api/esempi/campagne.ts`, `api/esempi/decisioni.ts` (solo i dati di `daApprovare`), `pages/operatore/campagna/Decidi.tsx` (solo il blocco `in_revisione`), file nuovi `pages/operatore/vedi-campagna/decisioni/ChiediArtigiano.tsx` e `RichiestaOperatore.tsx`, `pages/operatore/da-approvare/RigaCampagna.tsx`, `pages/artigiano/campagna/viste/VistaStato.tsx` (solo il caso `in_revisione`), file nuovo `pages/artigiano/campagna/viste/RichiestaConsorzio.tsx`, `pages/artigiano/campagna/viste/SceltaCampagna.tsx`.
**Da non toccare**: i file di T3-64; il blocco `attiva`/`sospesa` di `Decidi.tsx`.

**Passi**
1. Tipi e funzioni in `api/campagne.ts` (§1.4): `chiediArtigiano(campagnaId, domanda, foto: number[]): Promise<RichiestaArtigiano>`; `caricaFotoRichiesta(campagnaId, fotoId, file, dichiarazione): Promise<…>` (multipart `file`, `foto_id`, `dichiarazione` = `"true"`, come `caricaFoto()`); `inviaRisposta(campagnaId, risposta: string | null): Promise<RichiestaArtigiano>`. Esempi in memoria per tutte e tre, e una campagna d'esempio in revisione con una richiesta aperta.
2. **Operatore**, `Decidi.tsx`, blocco `in_revisione`: il pulsante «Chiedi all'artigiano» tra «Approva» e «Respingi»; sotto la decisione, `RichiestaOperatore` quando `campagna.richiesta` è `aperta` o `inviata`.
3. `ChiediArtigiano.tsx` (finestra «Chiedi all'artigiano», sul modello di `Respingi.tsx`): campo obbligatorio «Domanda per l'artigiano» (esempio nel segnaposto: «La foto del vaso mostra una cliente: puoi mandarne una senza persone?»); scelta delle foto caricate della campagna con `Checkbox.Card`, al massimo 3, con il contatore «n di 3»; se c'è una richiesta aperta: «Sostituisce la richiesta aperta del {data}.»; testo «La campagna resta in revisione: puoi approvare o respingere quando vuoi. Avvisa tu l'artigiano: il sistema non manda email.»; pulsante «Chiedi».
4. `RichiestaOperatore.tsx`:
   - `aperta`: titolo «Richiesta all'artigiano · in attesa», «Chiesta il {data}», la domanda, le miniature delle foto segnate con «da caricare» o «nuova arrivata»;
   - `inviata`: titolo «Risposta dell'artigiano · arrivata il {data}», la risposta, le coppie foto vecchia → foto nuova, e «Usa Cambia foto sui post che usano la foto vecchia: la nuova è in cima all'elenco.»
5. `RigaCampagna.tsx`: un segno «Richiesta aperta» (giallo) o «Risposta arrivata» (verde) dal campo `richiesta`.
6. **Artigiano**, `VistaStato.tsx`, caso `in_revisione`:
   - richiesta `aperta`: `RichiestaConsorzio` sopra l'avviso «I post sono pronti…»;
   - richiesta `inviata`: avviso «Hai risposto il {data}: il consorzio sta finendo di controllare i post.»
7. `RichiestaConsorzio.tsx` (riquadro «Il consorzio ti chiede»): la domanda; se ci sono foto, la spunta obbligatoria con il testo di R-41 («Le foto mostrano prodotti della mia bottega; le persone riconoscibili hanno dato il consenso») e, per ogni foto segnata, la miniatura, lo stato («Da sostituire» / «Caricata») e, finché manca, la scelta del file (`accept="image/jpeg,image/png,image/webp"`) con «Carica»; controllo nel browser di tipo e peso (oltre 10 MB: «La foto supera 10 MB.»); il campo «Risposta per il consorzio» (facoltativo se ci sono foto, obbligatorio se non ce ne sono); «Invia al consorzio» attivo quando ogni foto ha la sua nuova (o, senza foto, quando c'è il testo). Dopo ogni azione la pagina si rilegge.
8. `SceltaCampagna.tsx`: nella riga di scelta, il segno «Il consorzio ti chiede qualcosa» sulla campagna con `richiesta === "aperta"`.

**Fatto quando**: build e lint puliti; con i dati di esempio il percorso operatore → artigiano → operatore si fa in due finestre; appena T3-63 è su `main` la pagina usa le API vere; screenshot nella PR accanto alle pagine statiche.

---

## T3-66 · Prova della corsia 6

**Leggi**: spec CA-91; `converge.md` §4 (passi 4, 6 e 9); questo brief. **Dipende da** T3-61…T3-65 su `main`.

**File da toccare**: `backend/tests/percorsi/test_percorso_corsia6.py` (nuovo). Nessun file di `app/` né del frontend: se il percorso trova un errore, apre una PR piccola sul task che l'ha prodotto.

**Passi**
1. `test_ca91_richiesta_cambia_foto_approva_pubblica`: campagna in revisione con un post e un'altra foto idonea nel gruppo; l'operatore chiede la foto del post; l'artigiano la carica con la dichiarazione e invia; l'operatore la trova in testa a `foto-possibili`, cambia foto, approva; un tick (social e archivio finti, come in `tests/moduli/pubblicazione/test_service.py`) pubblica il post con la foto nuova.
2. `test_ca91_dopo_l_approvazione_modifica_sposta_annulla_sospendi_riattiva`: campagna attiva con tre post futuri; modifica il primo, sposta il secondo, annulla il terzo con la nota; sospendi con una nota e riattiva; un tick alla data dei post pubblica la versione nuova del primo e il secondo alla data nuova; il terzo non esce.
3. Percorso a mano in due finestre (operatore e artigiano) con `AI_PROVIDER=finto` e `SOCIAL_PROVIDER=finto`, passi 4, 6 e 9 di `converge.md` §4; screenshot nella PR.

**Fatto quando**: CA-91 verde; percorso a mano senza errori; screenshot nella PR.

---

## 2. Ordine di lavoro

La corsia 6 la fa una persona sola (Giovanni, con Claude), un task alla volta e in questo ordine, con un commit per task e i test verdi a ogni commit. Il messaggio del commit porta l'id del task.

| Ordine | Task | Perché a questo punto |
|---|---|---|
| 1 | T3-60 | prepara le regole e questo brief |
| 2 | T3-61 | interventi sul post: `interventi_ammessi()` serve a tutti gli altri |
| 3 | T3-63 | richiesta all'artigiano: dipende solo da T3-60 |
| 4 | T3-62 | cambia foto: dipende da T3-61 e usa le foto che arrivano con la richiesta di T3-63 |
| 5 | T3-64 | Vedi campagna, interventi (frontend) |
| 6 | T3-65 | richiesta all'artigiano (frontend) |
| 7 | T3-66 | prova della corsia: ultima, perché dipende da tutti |

Tutto su `main` entro il 24/10, prima di T3-08 parte 2. Ciò che non c'è resta fuori (ADR-116): per questo, se si carica un task alla volta, si carica nell'ordine della tabella. Di tanto in tanto si unisce `origin/main` al branch di lavoro, perché nel frattempo entrano gli altri task.

**File in comune.** Lavorando in sequenza non ci sono conflitti tra i task della corsia: `revisione/router.py`, `revisione/schemas.py`, `contenuti/interventi.py`, `contenuti/service.py`, `api/decisioni.ts`, `api/esempi/decisioni.ts` e `Decidi.tsx` si toccano ognuno nel proprio task, con i limiti scritti nelle sezioni T3-61…T3-65 (per `Decidi.tsx`: T3-64 il blocco `attiva`/`sospesa`, T3-65 il blocco `in_revisione`; per `api/decisioni.ts`: T3-64 solo `sospendi`, T3-65 solo `CampagnaDaApprovare`).

**Revisione delle PR**: un collega per ognuna; nessuna tocca `core/`, `alembic/` o i `domain.py`, quindi il referente dei file comuni non è obbligatorio.

## 3. Fuori da questi task (ADR-116, `docs/ROADMAP.md`)

Link a tempo per l'artigiano senza password; analisi AI della foto caricata con una richiesta; immagine AI chiesta sul singolo post; indicatore di recuperabilità della campagna; motivi codificati della sospensione; email per la richiesta (D4); controllo in pubblicazione che la versione corrente abbia la sua riga `approvazione`; sospensione automatica per un permesso scaduto (D5).
