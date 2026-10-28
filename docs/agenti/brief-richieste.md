# Brief · Corsia 9 · Richieste dopo la prova (T3-901…T3-927)

Per chi fa un task della corsia 9. Decisione: ADR-119. Leggi prima `constitution.md` e `perimetro-mvp.md` (blocco J), poi il §1 di questa pagina e **solo** la sezione del tuo task. Firme, rotte, messaggi d'errore e schemi di questa pagina sono il contratto tra task che lavorano in parallelo: non cambiarli senza chiedere. Dove il codice di `main` è diverso da come è descritto qui, fermati e chiedi.

**Che cosa nasce.** Dodici richieste emerse provando l'MVP: stati leggibili per l'operatore, il nome della bottega su ogni pagina dell'artigiano, la durata di una settimana con un clic, più campagne attive insieme, immagini AI senza un numero che fa fallire il piano, foto adattate alle proporzioni di Facebook e Instagram senza tagliare il soggetto, cambio d'immagine con le foto della campagna, dell'archivio o una nuova immagine AI, «Rifai il post» al posto di una campagna buttata, Rigenera immagine, una sola Rigenera testo, prompt migliori, storico delle chiamate all'AI con numeri e voto.

**Regole di lavoro per tutti i task.**
- Un branch `feature/<id>-<breve>` da `main`; fai solo il tuo task; tocca i file elencati nella sua sezione e i loro test. Se ti serve un altro file, fermati e chiedi.
- **Una sola migrazione**, `013_storico_ai.py`, in T3-907. Nessun altro task scrive migrazioni. **Nessuna libreria nuova**, né nel backend né nel frontend: le immagini si lavorano con Pillow, che c'è.
- La costituzione non cambia: in revisione un post non si toglie (§1.10–1.11), dopo l'approvazione nessuna AI (§1.5), la foto originale non si modifica (§1.3), una foto non esce due volte sullo stesso canale nella stessa campagna (§1.9).
- Il codice congelato resta congelato: `campagne/archivio.py` e le rotte `/archivio` non si toccano. T3-909 **chiama** `campagne.service.foto_di_archivio()` così com'è, senza cambiarla.
- Nessun cambio di stile: tema, palette e caratteri sono quelli della corsia 8 (`tema.ts`, `index.css`). I testi fissi di `brief-interfaccia.md` §1.4 restano, con le sole eccezioni scritte qui (§1.7).
- Messaggi in italiano, esattamente quelli di questa pagina; codici solo tra quelli di costituzione §4.
- Test su PostgreSQL con le fixture di plan §7 e le fabbriche; il nome porta il CA (`test_ca102_…`). Nessuna chiamata reale ad AI, social o email: si usa il provider finto.
- **File condivisi** (§1.8): prima di aprire la PR fai `git fetch` e il rebase su `origin/main`, poi rilancia i controlli. Un conflitto in un file condiviso si risolve tenendo le due modifiche, non scegliendone una.
- Fatto quando, per ogni task di backend: da `backend/`, `uv run alembic upgrade head`, `uv run pytest`, `uv run black --check .` verdi, `tests/test_confini.py` compreso. Per ogni task di frontend: da `frontend/`, `npm run lint` e `npm run build` puliti, screenshot nella PR. Poi la checklist di `converge.md` §1 e la casella del task in `tasks.md`.
- Frontend: finché l'endpoint del task di backend non è su `main`, la pagina usa i dati di esempio (`src/api/esempi/`) con la forma degli schemi di questa pagina; quando arriva, passa alle API vere nello stesso task o, se è già chiuso, nel task successivo dello stesso file.

---

## 1. Contratti comuni

### 1.1 Etichette degli stati (T3-901, T3-915)

Il valore che arriva dal backend non cambia: cambia solo ciò che si legge. Un solo file, `frontend/src/components/stati.ts`, esporta le tabelle qui sotto, `etichettaStato(tipo, valore, ruolo)` e i colori, che sono quelli di oggi di `coloreCampagna()` e `colorePost()` (`pages/operatore/campagna/util.ts`): le due funzioni si spostano in `stati.ts` e `util.ts` le riesporta. Un valore che non è in tabella si mostra com'è.

**Campagna, operatore**

| Valore | Etichetta | Spiegazione (al passaggio del mouse) |
|---|---|---|
| `bozza` | Bozza | L'artigiano la sta ancora preparando. |
| `inviata` | In coda | Inviata dall'artigiano: l'AI la prende tra poco. |
| `in_generazione` | L'AI la prepara | L'AI analizza le foto e scrive piano e post. |
| `generazione_fallita` | Preparazione non riuscita | L'AI si è fermata: leggi l'errore e usa Riprova. |
| `piano_da_rivedere` | Piano da rivedere | Stato delle campagne di prima dell'MVP. |
| `in_revisione` | Da rivedere | Piano e post pronti: sistemali, poi approva o respingi. |
| `respinta` | Respinta | Respinta dal consorzio: l'artigiano ne crea una nuova. |
| `scaduta` | Scaduta | Non approvata in tempo. |
| `attiva` | In pubblicazione | Approvata: i post escono alla loro data. |
| `sospesa` | Sospesa | Le pubblicazioni sono ferme finché non la riattivi. |
| `annullata` | Annullata | Chiusa dal consorzio: i post rimasti non escono. |
| `conclusa` | Conclusa | Tutti i post sono usciti o chiusi. |

**Post, operatore**

| Valore | Etichetta | Spiegazione |
|---|---|---|
| `da_approvare` | Da approvare | Esce con l'approvazione della campagna. |
| `approvato` | In programma | Approvato: esce alla sua data. |
| `pubblicato` | Pubblicato | Uscito sulla pagina. |
| `fallito` | Non pubblicato | La pubblicazione non è riuscita: riprogrammalo. |
| `annullato` | Annullato | Annullato dal consorzio: non esce. |
| `scartato` | Scartato | Tolto con il suo canale o con la campagna. |
| `scaduto` | Scaduto | La sua data è passata prima dell'approvazione. |
| `da_rivedere` vero | Da correggere | Ha un blocco: si sblocca con una versione senza blocchi. |

**Post, artigiano** (spec §4): `approvato` → «In programma», `pubblicato` → «Pubblicato», `fallito` e `annullato` → «Non pubblicato». Le etichette delle campagne dell'artigiano restano quelle di oggi (`STATO_ARTIGIANO` in `ElencoCampagne.tsx`, «Pubblicazioni ferme» compreso).

**Barra di avanzamento** (T3-915): Inviata → Preparazione → Revisione → Pubblicazione → Conclusa. `inviata` accende il passo 1, `in_generazione` il 2, `in_revisione` il 3, `attiva` il 4, `conclusa` il 5. `generazione_fallita` mostra il passo 2 in errore; `sospesa` il passo 4 in pausa; `respinta`, `scaduta` e `annullata` fermano la barra al passo raggiunto, con l'etichetta della tabella.

### 1.2 Interventi sul post (T3-904, T3-908, T3-909, T3-919, T3-923)

`contenuti/domain.py` (lo cambia T3-908):

```python
RIGENERA_IMMAGINE = "rigenera_immagine"
INTERVENTI = (MODIFICA, RIGENERA, RIGENERA_IMMAGINE, CAMBIA_FOTO, SPOSTA, ANNULLA, RIPROGRAMMA)
# ("in_revisione", DA_APPROVARE): {MODIFICA, RIGENERA, RIGENERA_IMMAGINE, CAMBIA_FOTO, SPOSTA}
# attiva e sospesa: come oggi (nessuna AI dopo l'approvazione)
MAX_RIGENERAZIONI_IMMAGINE = 3
# TIPI_INTERVENTO e TIPI_INTERVENTO_IN_CORSO: in più "rigenera_immagine"
```

`interventi_ammessi()` toglie `rigenera_immagine` quando il post ha già **3** versioni `rigenera_immagine`; `cambia_foto` è ammesso anche sui post con un'immagine AI (T3-909).

**Rotte** (`revisione/router.py`, operatore; rispondono come `/rigenera`):

```python
# revisione/schemas.py → frontend/src/api/interventi.ts
class PostRigeneraImmagine(BaseModel):          # POST /post/{id}/rigenera-immagine (T3-908)
    model_config = ConfigDict(extra="forbid")
    nota: str | None = Field(None, max_length=500)        # indicazione per l'immagine
    riscrivi_testo: bool = False                          # dopo l'immagine, riscrive anche il testo
    nota_testo: str | None = Field(None, max_length=500)  # indicazione per il testo

class PostCambiaFoto(BaseModel):                # POST /post/{id}/cambia-foto (T3-909)
    model_config = ConfigDict(extra="forbid")
    foto_id: int
    riscrivi_testo: bool = False                          # solo in revisione
    nota: str | None = Field(None, max_length=500)        # indicazione per il testo

class FotoPossibile(BaseModel):                 # GET /post/{id}/foto-possibili (T3-909)
    foto_id: int
    punteggio: float | None
    analizzata: bool
    provenienza: Literal["gruppo", "campagna", "archivio"]
    soggetto: str | None          # dall'analisi, se c'è
```

**Messaggi** (409 se non diversamente detto):

| Caso | Messaggio |
|---|---|
| Quarta rigenerazione dell'immagine | «Questa immagine è già stata rigenerata 3 volte: scegli una foto con Cambia immagine.» |
| `riscrivi_testo` senza rigenerazioni del testo rimaste | «Il testo di questo post non si può più rigenerare: modificalo a mano.» |
| `riscrivi_testo` dopo l'approvazione (422) | «Dopo l'approvazione il testo non si riscrive con l'AI: modificalo a mano.» |
| Foto non tra le possibili (422) | come oggi in `cambia_foto()` |
| Intervento non ammesso, intervento in corso | come oggi (`verifica_intervento()`, R-31) |

I controlli si fanno **prima** di cambiare qualcosa: un 409 lascia il post com'è.

**Versioni.** Rigenera immagine crea su ogni post toccato una versione `rigenera_immagine` con lo stesso testo e la nuova foto; con `riscrivi_testo` segue, nello stesso job, una versione `rigenera_totale` con `nota_testo`, che conta un ciclo di R-03. Cambia foto con `riscrivi_testo` crea la versione `cambio_foto`, accende l'intervento `rigenera_totale` e accoda `rigenera_post(post_id, None, nota)`: conta un ciclo. «Rifai il post» nell'interfaccia (T3-923) è una di queste due chiamate con `riscrivi_testo` vero: nessuna rotta in più.

**Dicitura.** Quando un post passa da un'immagine AI a una foto vera il testo perde «Immagine creata con AI» in fondo e `post.riempitivo` diventa `None`; quando passa da una foto vera a un'immagine AI la guadagna (`con_dicitura()`) e `post.riempitivo` diventa `immagine_ai`. La dicitura è un testo fisso.

**Prompt dell'immagine sulla foto.** Ogni foto `creata_ai` nuova porta in `foto.analisi_ai` il prompt con cui è nata: `{"prompt": str, "versione_prompt": str, "nota": str | None}` (con `campagne.service.aggiorna_foto()`). Rigenera immagine passa all'AI, come «da non ripetere», i prompt delle immagini che l'uscita ha già avuto.

### 1.3 Storico dell'AI (T3-907, T3-916, T3-917, T3-918, T3-914, T3-924)

**Migrazione 013** (T3-907), schema per esteso come le altre:

| Tabella | Colonne nuove |
|---|---|
| `chiamata_ai` | `versione_prompt` text null · `richiesta` jsonb null · `risposta` text null · `esito` text not null default `'ok'` · `errore` text null · `durata_ms` integer null · `tentativo` integer null · `foto_id` integer null FK `foto.id` · indice su `creata_il` |
| `valutazione_ai` (nuova) | `id` · `chiamata_ai_id` FK not null, indice · `utente_id` FK `utente.id` not null · `voto` smallint not null, check 1–5 · `nota` text null · `creata_il` timestamptz default now |

`contenuti/domain.py`: `ESITI_CHIAMATA_AI = ("ok",) + TIPI_ERRORE_GENERAZIONE`. Una chiamata fallita ha `costo_usd` 0 se il provider non dice altro.

**Adattatore** (`adapters/ai/base.py`, T3-916): `UsoAI` guadagna `versione_prompt: str | None = None`, `richiesta: dict | None = None`, `risposta: str | None = None`, `durata_ms: int | None = None`, `esito: str = "ok"`, `errore: str | None = None`. L'adattatore scrive `ultimo_uso` anche quando la chiamata fallisce, **prima** di sollevare `ErroreAI` (esito = tipo dell'errore). Nella `richiesta` le immagini sono `"<foto {id}>"`, mai i byte; mai chiavi o intestazioni. `registra_chiamata_ai(db, campagna_id, uso, *, post_id=None, foto_id=None, tentativo=None)`.

**Rotte** (`contenuti/router.py`, operatore; admin passa):

```python
# contenuti/schemas.py → frontend/src/api/storico.ts
class ChiamataAIRiga(BaseModel):
    id: int
    creata_il: datetime
    campagna_id: int
    campagna_titolo: str
    bottega: str | None
    post_id: int | None
    foto_id: int | None
    tipo: str                    # analisi · piano · testo · immagine
    modello_ai: str
    versione_prompt: str | None
    esito: str                   # ESITI_CHIAMATA_AI
    durata_ms: int | None
    costo_usd: Decimal
    token_ingresso: int | None
    token_uscita: int | None
    voto_medio: float | None

class ValutazioneAISchema(BaseModel):
    id: int
    utente_nome: str
    voto: int
    nota: str | None
    creata_il: datetime

class ChiamataAIDettaglio(ChiamataAIRiga):
    richiesta: dict | None
    risposta: str | None
    errore: str | None
    tentativo: int | None
    valutazioni: list[ValutazioneAISchema]

class PaginaChiamateAI(BaseModel):
    voci: list[ChiamataAIRiga]   # dalla più recente
    totale: int
    pagina: int
    per_pagina: int              # 50

class NumeriVersione(BaseModel):
    tipo: str
    versione_prompt: str | None
    chiamate: int
    tasso_errore: float          # 0–1
    durata_media_ms: int | None
    costo_usd: Decimal
    voto_medio: float | None

class NumeriAI(BaseModel):
    chiamate: int
    costo_usd: Decimal
    durata_media_ms: int | None
    durata_p95_ms: int | None
    tasso_errore: float
    voto_medio: float | None
    testi_approvati: int                  # post approvati, pubblicati, falliti o annullati
    testi_approvati_come_ai: int          # di questi, con la versione corrente scritta dall'AI
    modifiche_a_mano: int                 # versioni modifica_operatore
    rigenerazioni_testo: int              # versioni rigenera_totale e rigenera_da_proposta
    immagini_create: int
    immagini_non_create: int              # versioni con il blocco immagine_non_creata
    immagini_rigenerate: int              # versioni rigenera_immagine
    per_versione: list[NumeriVersione]

class VotoAI(BaseModel):                  # POST /storico-ai/{id}/voto
    model_config = ConfigDict(extra="forbid")
    voto: int = Field(ge=1, le=5)
    nota: str | None = Field(None, max_length=1000)
```

| Rotta | Task | Risposta |
|---|---|---|
| `GET /storico-ai?campagna_id=&tipo=&modello=&versione_prompt=&esito=&dal=&al=&pagina=` | T3-917 | `PaginaChiamateAI`; `dal` e `al` sono date (Europe/Rome), compresi |
| `GET /storico-ai/numeri` con gli stessi filtri, senza `pagina` | T3-917 | `NumeriAI` |
| `GET /storico-ai/{id}` | T3-917 | `ChiamataAIDettaglio` · 404 «Chiamata non trovata.» |
| `POST /storico-ai/{id}/voto` | T3-918 | `ValutazioneAISchema` · 404 come sopra · 422 voto fuori da 1–5 |

Le chiamate all'AI non contengono dati personali oltre a quelli della bottega; restano nel database e **mai nei log** (costituzione §3).

### 1.4 Prompt v3 (T3-910, T3-911, T3-913, T3-920, T3-922, T3-925)

I prompt sono versionati (`brief-ai.md`): ogni task crea il file `_v3.md` del suo prompt, porta la costante della versione a `v3` e toglie il `_v2.md` del suo prompt.

**Scena di un'uscita con immagine AI** (piano v3, T3-910). Ogni uscita del piano con almeno un post `immagine_ai` ha `scena`; le altre `scena: null`.

```python
# adapters/ai/schemi.py
INQUADRATURE = ("dettaglio_materia", "banco_dall_alto", "attrezzi_still_life",
                "bottega_campo_largo", "materie_prime", "atmosfera_stagione")
class Scena(BaseModel):
    soggetto: str = Field(max_length=200)     # che cosa si vede, concreto e fotografabile
    inquadratura: Literal[INQUADRATURE]       # le stesse sei
    luce: str = Field(max_length=100)
    colori: str = Field(max_length=100)
```

La scena si salva dentro `piano.contenuto` (il piano com'è uscito dal controllo), nessuna colonna nuova. La legge `scena_dell_uscita(db, uscita) -> dict | None` in `contenuti/immagini_ai.py` (la scrive T3-910). Una scena mancante o malformata non è una violazione del piano: l'immagine parte dal tema, come oggi.

**Firma del prompt dell'immagine** (`adapters/ai/immagini.py`), a fine corsia:

```python
def prompt_immagine(snapshot, tema, giorno, *, semplice=False,
                    nota=None, da_evitare=(),              # T3-908
                    campagna=None, scena=None, stile=None  # T3-920
                    ) -> str
```

`campagna` = `{"titolo", "descrizione", "obiettivo"}`; `stile` = `stile_delle_foto(db, campagna_id) -> str | None` in `contenuti/immagini_ai.py` (T3-920): ciò che le descrizioni delle foto vere dicono di luce, sfondi e colori, al massimo 400 caratteri.

**Riquadro del soggetto** (analisi v3, T3-913): ogni foto analizzata guadagna `soggetto_box: {"x": float, "y": float, "larghezza": float, "altezza": float} | None`, valori tra 0 e 1, origine in alto a sinistra, misurati sulla foto **già raddrizzata** secondo i metadati (come la vede `sistemazione_foto`). Si salva in `foto.analisi_ai["soggetto_box"]`. Un riquadro fuori da 0–1 o malformato vale `None`, senza errore.

**Attacchi degli altri post** (post v3, T3-911): il JSON del post guadagna `altri_post: list[str]`, la prima frase (al massimo 120 caratteri) dei testi già scritti degli altri post della campagna sullo stesso canale, al massimo 10.

**Orari occupati** (T3-922): il JSON del piano guadagna `orari_occupati: list[{"canale": str, "data_ora": str}]`, i post `da_approvare` e `approvato` delle altre campagne non chiuse della stessa bottega che cadono nel periodo.

### 1.5 Foto nelle proporzioni dei canali (T3-912, T3-921)

`campagne/sistemazione_foto.py`: la proporzione ammessa è un intervallo, da **4:5** (0,8) a **1,91:1**, uguale per Facebook e Instagram. Una foto dentro l'intervallo (tolleranza 0,01) non si taglia; una fuori va al bordo più vicino (0,8 per le verticali, 1,91 per le panoramiche). `proporzione="1:1"` o `"4:5"` forzata resta ammessa. In `contenuti/domain.py` `SCHEDE_CANALE[canale]["proporzioni"]` diventa `("4:5", "1.91:1")`, gli estremi dell'intervallo.

Firma a fine corsia: `sistema_foto_buffer(dati_foto, canale="instagram", proporzione=None, soggetto_box=None) -> bytes`; `foto_sistemata()` passa `foto.analisi_ai.get("soggetto_box")`. Quando serve un taglio (T3-921, valori di prova):

| Caso | Che cosa fa |
|---|---|
| Con il riquadro, che entra nella finestra e il taglio toglie al più il **35%** dell'area | Ritaglio: la finestra più grande della proporzione, che contiene il riquadro, centrata sul suo centro e tenuta dentro la foto |
| Senza riquadro e il taglio toglie al più il **10%** | Ritaglio al centro, come oggi |
| Altrimenti | Bordi sfocati: tela della proporzione, sotto la foto stessa ingrandita a coprire, sfocata (`GaussianBlur` 30) e scurita del 15%, sopra la foto intera centrata |

Deformare non si fa mai. L'originale non cambia (costituzione §1.3).

### 1.6 Campagne sovrapposte (T3-905, T3-922)

R-12 diventa «una sola bozza per artigiano»: due campagne della stessa bottega possono avere periodi sovrapposti. Il dettaglio della campagna guadagna l'avviso `campagne_sovrapposte` quando un'altra campagna della stessa bottega, non in bozza e non in `STATI_CHIUSI`, ha un periodo che si sovrappone. Testo al passo 12: «Nello stesso periodo hai già un'altra campagna: i post delle due campagne usciranno insieme sulla tua pagina.»

### 1.7 Interfaccia

- **Barra dell'operatore**: dopo Calendario la voce **Storico AI** (`/storico-ai`, accesa anche su `/storico-ai/…`), prima di Nuovo artigiano (T3-914). È l'unica voce nuova; le altre e quelle dell'artigiano restano (`brief-pagine.md` §1.3).
- **Nome nelle pagine dell'artigiano** (T3-902): in `Guscio`, per il ruolo artigiano, una riga sempre visibile sopra il titolo, anche a 375 px e con il menu chiuso: «{nome della bottega} · {referente}». Senza profilo, o finché si carica, solo `utente.nome`.
- **Pulsanti dei post** (T3-904, T3-919, T3-923): «Modifica a mano», «Rigenera testo» (al posto di «Rigenera da zero» e «Rigenera da testo proposto»), «Rigenera immagine» (solo sui post con un'immagine AI o con il blocco `immagine_non_creata`), «Cambia immagine» (al posto di «Cambia foto»), «Sposta», «Annulla».
- **Durata rapida** (T3-903): accanto alla data di fine «1 settimana», «2 settimane», «1 mese».

### 1.8 File condivisi

Più task toccano gli stessi file in punti diversi. Prima della PR: rebase su `origin/main` e controlli rilanciati (regole di lavoro).

| File | Task |
|---|---|
| `backend/app/moduli/contenuti/domain.py` | T3-907 (esiti), T3-908 (interventi), T3-912 (schede) |
| `backend/app/adapters/ai/litellm.py`, `finto.py` | T3-910, T3-911, T3-913, T3-916, T3-920 |
| `backend/app/adapters/ai/schemi.py` | T3-910, T3-913 |
| `backend/app/adapters/ai/immagini.py` | T3-908, poi T3-920 |
| `backend/app/moduli/contenuti/immagini_ai.py` | T3-908, T3-910, T3-916, T3-920 |
| `backend/app/moduli/contenuti/generazione.py` | T3-910, T3-911, T3-916, T3-920, T3-922 |
| `backend/app/moduli/revisione/schemas.py`, `router.py`, `interventi.py` | T3-908, T3-909 |
| `backend/app/moduli/campagne/sistemazione_foto.py` | T3-912, poi T3-921 |
| `frontend/src/pages/operatore/vedi-campagna/post/AzioniPost.tsx` | T3-904, poi T3-919, poi T3-923 |
| `frontend/src/components/Guscio.tsx` | T3-902, T3-914 |
| `frontend/src/api/interventi.ts` | T3-919, poi T3-923 |

---

## T3-901 · Stati leggibili (frontend)

- **File**: `frontend/src/components/stati.ts` (nuovo), `frontend/src/components/StatoBadge.tsx` (nuovo), `pages/operatore/campagna/util.ts` (riesporta i colori), e i punti che oggi mostrano il valore grezzo: `components/campagne/ElencoCampagne.tsx` (ramo operatore), `pages/operatore/da-approvare/RigaCampagna.tsx`, `pages/operatore/VediCampagna.tsx` (il badge della testata, senza carattere monospace), `pages/operatore/campagna/PostCard.tsx`, `components/CalendarioCampagnaView.tsx`, `components/CalendarioSettimana.tsx`, `components/ArchivioFoto.tsx` (ramo operatore), il filtro di `pages/operatore/DaApprovare.tsx` (si legge l'etichetta, si filtra sul valore).
- **Cosa**: le tabelle del §1.1, `etichettaStato()`, `<StatoBadge tipo="campagna" | "post" stato={…} ruolo={…} daRivedere?={…} />`: pallino del colore, etichetta, spiegazione in un `Tooltip`. Calendari: per l'artigiano le etichette dell'artigiano.
- **Fatto quando**: in nessuna pagina dell'operatore compare un valore con il trattino basso (cerca `\.stato}` e `{stato}` nei `.tsx`: ogni uscita passa da `StatoBadge` o `etichettaStato`); build e lint puliti; screenshot di Da approvare, Vedi campagna, campagne dell'artigiano, calendario.

## T3-902 · Nome della bottega sulle pagine dell'artigiano (frontend)

- **File**: `frontend/src/components/Guscio.tsx`, `Guscio.module.css`; se serve, il punto dove `RichiedeProfilo` legge il profilo (`pages/artigiano/profilo/Profilo.tsx`), per riusarne la lettura.
- **Cosa**: la riga del §1.7. Il profilo si legge una volta per pagina con la stessa chiamata di `RichiedeProfilo` (`api/artigiani.ts`); nessuno stato globale (costituzione §4).
- **Fatto quando**: a 375 px e a 1280 px, con il menu chiuso, Ingresso, Campagne, Campagna, Calendario, Archivio foto e Profilo bottega mostrano la riga; build e lint puliti; screenshot.

## T3-903 · Durata rapida al passo 10 (frontend)

- **File**: `frontend/src/pages/artigiano/campagna/Passo10.tsx`.
- **Cosa**: tre pulsanti (§1.7) che mettono la fine a inizio + 6, + 13, + 29 giorni (durata 7, 14, 30 giorni, R-08). Cambiano solo la data di fine; i controlli di oggi restano. Il pulsante che corrisponde alla durata scelta è acceso.
- **Fatto quando**: «1 settimana» porta a una durata di 7 giorni accettata dal server; build e lint puliti; screenshot.

## T3-904 · Una sola Rigenera testo (frontend)

- **File**: `pages/operatore/vedi-campagna/post/AzioniPost.tsx`, `Rigenera.tsx`, `regole.ts`.
- **Cosa**: un pulsante «Rigenera testo»; una finestra con «Indicazioni per l'AI» (facoltativa) e «Parti da questo testo» (facoltativa, chiusa di base, si apre con un clic e propone il testo attuale). Vuota → `modalita: "totale"`; piena → `"da_proposta"` con quel testo. Il backend non cambia; il conteggio delle 3 rigenerazioni resta. L'avviso dell'intervento in corso dice «Rigenerazione del testo in corso».
- **Fatto quando**: le due modalità partono dalla stessa finestra (rete del browser nella PR); build e lint puliti; screenshot.

## T3-905 · Campagne sovrapposte (backend e testo dell'avviso)

- **File**: `backend/app/moduli/campagne/service.py`, `bozza.py`, i loro test; `frontend/src/pages/artigiano/campagna/Passo12.tsx` (solo il testo dell'avviso).
- **Cosa**: via il controllo di sovrapposizione in creazione, modifica e invio (oggi 409 «Il periodo si sovrappone a una campagna già esistente.»); resta «una sola bozza» (CA-11). L'avviso del §1.6 nel dettaglio, calcolato con le campagne della stessa bottega.
- **Test**: CA-12 (riscritto), CA-100.
- **Fatto quando**: comandi del backend verdi; build e lint puliti.

## T3-906 · Immagini AI senza tetto: prova e DataError (backend)

- **File**: `backend/tests/percorsi/` (un test nuovo), `backend/tests/moduli/contenuti/test_piano.py`; il codice solo se la prova trova un difetto.
- **Cosa**: (1) il controllo del piano non conta più le immagini AI (commit 13731cd): un test che un piano con un'immagine AI in più di «post chiesti − foto disponibili» passa il controllo. (2) Percorso con il provider finto: campagna senza foto, 30 post per canale su Facebook e Instagram → `in_revisione`, 30 immagini AI, nessun errore. (3) Il `DataError` nella tappa testi della campagna «autunno» del database di sviluppo (errore 4 di `errore_generazione`, 28/10): riprodurlo con un test; se è un difetto, correggerlo qui; se non si riproduce, scriverlo nella PR.
- **Test**: CA-101.
- **Fatto quando**: comandi del backend verdi; nella PR l'esito sul `DataError`.

## T3-907 · Migrazione 013: storico dell'AI (backend)

- **File**: `backend/alembic/versions/013_storico_ai.py`, `backend/app/moduli/contenuti/models.py` (`ChiamataAI` estesa, `ValutazioneAI` nuova), `backend/app/tabelle.py` se serve, `contenuti/domain.py` (`ESITI_CHIAMATA_AI`), `tests/moduli/contenuti/fabbrica.py` (`chiamata_ai(campagna, **campi)`, `valutazione_ai(chiamata, utente, voto)`).
- **Cosa**: lo schema del §1.3, con `downgrade()`. Nessuna lettura né scrittura nuova: le fanno T3-916, T3-917, T3-918.
- **Test**: upgrade e downgrade su `adflow_test`; il check del voto (0 e 6 rifiutati dal database).
- **Fatto quando**: comandi del backend verdi; la PR lo dice al referente (migrazione, `domain.py`).

## T3-908 · Rigenera immagine (backend)

- **File**: `contenuti/domain.py`, `contenuti/interventi.py`, `contenuti/immagini_ai.py`, `contenuti/jobs.py`, `contenuti/service.py`, `adapters/ai/immagini.py` (`nota`, `da_evitare` e le loro righe nel prompt v2), `core/coda.py` (job `rigenera_immagine`), `revisione/interventi.py`, `revisione/router.py`, `revisione/schemas.py`, i test.
- **Cosa**: il §1.2. Rotta `POST /post/{id}/rigenera-immagine`: controlli, intervento in corso `rigenera_immagine` su ogni post toccato, job `rigenera_immagine(post_id, nota, riscrivi_testo, nota_testo)` con 3 esecuzioni, come `rigenera_post`.
  - **Quali post**: se la foto della versione corrente è `creata_ai`, tutti i post `da_approvare` della stessa uscita che usano quella foto (l'immagine è dell'uscita, R-28); se è una foto vera, solo quel post.
  - **Il job**: prompt con la scena o il tema dell'uscita, la `nota` e, in `da_evitare`, i prompt delle immagini già avute dall'uscita (§1.2); nuova foto `creata_ai` con il prompt in `analisi_ai`; nuova versione `rigenera_immagine` su ogni post toccato, stesso testo (con la dicitura), errori del validatore ricalcolati, senza il blocco `immagine_non_creata`; costo e chiamata registrati (R-44). Con `riscrivi_testo` riscrive il testo di ogni post toccato (versione `rigenera_totale`). La foto vecchia resta (costituzione §1.2).
  - **Rifiuto del provider due volte**: nessuna versione, intervento spento, post com'era.
- **Test**: CA-102, CA-103; CA-71 ancora verde.
- **Fatto quando**: comandi del backend verdi; la PR lo dice al referente (`core/coda.py`, `domain.py`).

## T3-909 · Cambia foto da gruppo, campagna e archivio (backend)

- **File**: `contenuti/interventi.py`, `revisione/interventi.py`, `revisione/router.py`, `revisione/schemas.py`, i test.
- **Cosa**: il §1.2.
  - `foto_possibili()` restituisce, in quest'ordine, (1) le foto del gruppo dell'uscita (com'è oggi), (2) le altre foto `caricata` della campagna, idonee o senza analisi, (3) le foto di `campagne.foto_di_archivio(db, profilo_id, canale, adesso)`, con `provenienza` e `soggetto`. Dentro ogni gruppo l'ordine di oggi. Nessuna foto già nella versione corrente di un altro post vivo della campagna sullo stesso canale (costituzione §1.9), nessun doppione tra le fonti.
  - Ammesso anche sui post con un'immagine AI e senza gruppo (via il 409 di oggi): si propongono le fonti (2) e (3).
  - Dicitura e `riempitivo` come nel §1.2.
  - `riscrivi_testo` e `nota` come nel §1.2; dopo l'approvazione tutte le fonti restano ammesse, `riscrivi_testo` no.
- **Test**: CA-71 (rivisto), CA-104, CA-105.
- **Fatto quando**: comandi del backend verdi.

## T3-910 · Prompt del piano v3: la scena delle immagini AI (backend)

- **File**: `adapters/ai/prompts/piano_v3.md` (al posto di `piano_v2.md`), `adapters/ai/schemi.py`, `adapters/ai/litellm.py`, `adapters/ai/finto.py`, `contenuti/generazione.py` (la scena resta in `piano.contenuto`), `contenuti/immagini_ai.py` (`scena_dell_uscita()`), `contenuti/piano.py` (la scena non è controllata), i test.
- **Cosa**: lo schema `Scena` del §1.4. Nel prompt: via «Usa tutte le `foto_disponibili`» e «i post `immagine_ai` sono `riempitivi`» (il numero delle immagini AI non è una regola, R-28); la scena è concreta e fotografabile, con ambiente e colori ripresi dalle `descrizione` delle foto vere, e due uscite con immagine AI vicine non hanno la stessa inquadratura. Il finto dà una scena per ogni uscita con immagine AI, girando sulle sei inquadrature.
- **Test**: CA-106.
- **Fatto quando**: comandi del backend verdi.

## T3-911 · Prompt dei testi v3: attacchi diversi (backend)

- **File**: `adapters/ai/prompts/post_v3.md` (al posto di `post_v2.md`), `adapters/ai/litellm.py`, `adapters/ai/finto.py`, `contenuti/generazione.py`, `contenuti/interventi.py` (la rigenerazione passa anche lei `altri_post`), i test.
- **Cosa**: `altri_post` del §1.4 e una regola nel prompt: «Non cominciare come uno degli `altri_post` e non ripeterne le immagini o le chiamate all'azione».
- **Test**: CA-107.
- **Fatto quando**: comandi del backend verdi.

## T3-912 · Proporzioni vere: da 4:5 a 1,91:1 (backend)

- **File**: `campagne/sistemazione_foto.py`, `campagne/service.py` (la docstring di `sistema_foto`), `contenuti/domain.py` (`SCHEDE_CANALE`), i test.
- **Cosa**: il primo paragrafo del §1.5, senza riquadro né bordi.
- **Test**: CA-81 (rivisto).
- **Fatto quando**: comandi del backend verdi; la PR lo dice al referente (`domain.py`).

## T3-913 · Analisi v3: il riquadro del soggetto (backend)

- **File**: `adapters/ai/prompts/analisi_v3.md` (al posto di `analisi_v2.md`), `adapters/ai/schemi.py`, `adapters/ai/litellm.py` (la foto che va all'AI è già raddrizzata secondo i metadati), `adapters/ai/finto.py` (un riquadro al centro, metà della foto), `contenuti/generazione.py` se serve per salvarlo, i test.
- **Cosa**: `soggetto_box` del §1.4, nel prompt: «il rettangolo più piccolo che contiene il soggetto principale per intero».
- **Test**: CA-108.
- **Fatto quando**: comandi del backend verdi.

## T3-914 · Storico AI, la pagina (frontend)

- **File**: `frontend/src/pages/operatore/StoricoAI.tsx` (nuovo, con i componenti che servono in `pages/operatore/storico-ai/`), `frontend/src/api/storico.ts` (nuovo), `frontend/src/api/esempi/storico.ts` (nuovo), `frontend/src/App.tsx` (rotte `/storico-ai` e `/storico-ai/:id`, operatore e admin), `frontend/src/components/Guscio.tsx` (voce e icona).
- **Cosa**: elenco paginato con i filtri del §1.3 (campagna, tipo, modello, versione del prompt, esito, periodo) e, per ogni riga, data, campagna e bottega, tipo, modello, versione, esito (`StatoBadge` se T3-901 è su `main`, altrimenti un `Badge`), durata, costo; un clic apre il dettaglio: richiesta (JSON leggibile, ripiegabile), risposta, errore, e l'immagine se `foto_id` c'è. Dati di esempio finché T3-917 non è su `main`.
- **Fatto quando**: build e lint puliti; screenshot di elenco e dettaglio.

## T3-915 · Barra di avanzamento della campagna (frontend)

- **File**: `pages/operatore/VediCampagna.tsx` (testata), un componente nuovo `components/AvanzamentoCampagna.tsx`.
- **Cosa**: la barra del §1.1 sotto il titolo di Vedi campagna, con `Stepper` di Mantine o fatta a mano; a 375 px resta leggibile (passi su due righe o solo il passo corrente con «3 di 5»).
- **Fatto quando**: build e lint puliti; screenshot di una campagna per ogni stato del §1.1.

## T3-916 · Storico AI: ogni chiamata registrata (backend)

- **File**: `adapters/ai/base.py`, `adapters/ai/litellm.py`, `adapters/ai/finto.py`, `contenuti/service.py` (`registra_chiamata_ai`), `contenuti/generazione.py`, `contenuti/immagini_ai.py`, `contenuti/interventi.py`, `contenuti/jobs.py`, i test.
- **Cosa**: il blocco «Adattatore» del §1.3 e la registrazione di **ogni** chiamata, riuscita o no, con `tentativo` (l'esecuzione del job o la riscrittura del piano e del testo). Una chiamata fallita deve restare anche quando la tappa si annulla: si registra come si registra oggi `errore_generazione`, nella transazione che sopravvive. Il `DataError` di T3-906 insegna che il messaggio vero serve: `errore` porta il tipo e il messaggio dell'eccezione, senza segreti.
- **Test**: CA-109; CA-82 ancora verde.
- **Fatto quando**: comandi del backend verdi.

## T3-917 · Storico AI: elenco, dettaglio e numeri (backend)

- **File**: `contenuti/storico_ai.py` (nuovo), `contenuti/service.py` (le espone), `contenuti/router.py`, `contenuti/schemas.py`, i test.
- **Cosa**: le tre rotte di lettura del §1.3. `campagna_titolo` con `campagne.campagna()`, `bottega` con `artigiani.profilo()`; `utente_nome` delle valutazioni con `accesso.utente()`. Numeri: medie e p95 su `durata_ms` non nulli; `testi_approvati_come_ai` conta i post la cui versione corrente ha `tipo_intervento` in `generazione`, `rigenera_totale`, `rigenera_da_proposta`, `rigenera_immagine`.
- **Test**: CA-110, CA-111.
- **Fatto quando**: comandi del backend verdi.

## T3-918 · Voto sulle risposte dell'AI (backend)

- **File**: `contenuti/storico_ai.py` (se T3-917 non c'è ancora, lo crea e T3-917 lo estende), `contenuti/router.py`, `contenuti/schemas.py`, i test.
- **Cosa**: `POST /storico-ai/{id}/voto` del §1.3: una riga `valutazione_ai` per voto, con l'utente; un voto nuovo non cancella i precedenti (costituzione §1.2).
- **Test**: CA-112.
- **Fatto quando**: comandi del backend verdi.

## T3-919 · Cambia immagine: le fonti (frontend)

- **File**: `pages/operatore/vedi-campagna/post/CambiaFoto.tsx`, `AzioniPost.tsx`, `frontend/src/api/interventi.ts`, `frontend/src/api/esempi/` (le foto possibili con `provenienza`).
- **Cosa**: il pulsante diventa «Cambia immagine» (§1.7), anche sui post con un'immagine AI. La finestra mostra le foto in tre sezioni: «Dello stesso gruppo», «Della campagna», «Dall'archivio della bottega», con il soggetto sotto la miniatura; una sezione vuota non si mostra. Avvisa, come oggi, di rileggere il testo. Dati di esempio finché T3-909 non è su `main`.
- **Fatto quando**: build e lint puliti; screenshot della finestra con le tre sezioni.

## T3-920 · Prompt delle immagini v3 (backend)

- **File**: `adapters/ai/prompts/immagine_v3.md` (al posto di `immagine_v2.md`), `adapters/ai/immagini.py`, `contenuti/immagini_ai.py` (`stile_delle_foto()`, passaggio di campagna, scena e stile), i test.
- **Cosa**: la firma del §1.4. Il prompt parte dalla scena (soggetto, inquadratura, luce, colori) e, senza scena, dal tema; aggiunge bottega (tipo di prodotto, città, gamma, origine, stagionalità, eventi ricorrenti del periodo dalla fotografia del profilo), campagna (titolo, descrizione, obiettivo), stagione e stile delle foto vere; via le righe fisse uguali per ogni immagine («sfondo semplice e leggermente sfocato», «colori fedeli e caldi»). Restano i vincoli di R-43 e la versione semplice dopo un rifiuto (R-35).
- **Test**: CA-113.
- **Fatto quando**: comandi del backend verdi; nella PR tre prompt d'esempio dalla campagna del seed.

## T3-921 · Ritaglio sul soggetto e bordi sfocati (backend)

- **File**: `campagne/sistemazione_foto.py`, `campagne/service.py` (`foto_sistemata` passa il riquadro), i test.
- **Cosa**: la tabella del §1.5. Le foto arrivate con una richiesta all'artigiano non hanno analisi: valgono le righe senza riquadro.
- **Test**: CA-114; CA-81 ancora verde.
- **Fatto quando**: comandi del backend verdi; nella PR prima e dopo di tre foto (orizzontale con il soggetto di lato, verticale 9:16, panoramica).

## T3-922 · Orari occupati nel piano (backend)

- **File**: `contenuti/generazione.py`, `adapters/ai/prompts/piano_v3.md` (una regola), `adapters/ai/finto.py`, `adapters/ai/litellm.py`, i test.
- **Cosa**: `orari_occupati` del §1.4, con `campagne.campagne_di()` e i post di `contenuti`. Regola nel prompt: «Non mettere un post nella stessa ora di un `orario_occupato` dello stesso canale; se puoi, evita anche lo stesso giorno». Il controllo del piano non la verifica. Il finto sposta di un giorno un post che cade in un'ora occupata.
- **Test**: CA-115.
- **Fatto quando**: comandi del backend verdi.

## T3-923 · Rifai il post e Rigenera immagine (frontend)

- **File**: `pages/operatore/vedi-campagna/post/CambiaFoto.tsx`, `AzioniPost.tsx`, `RigeneraImmagine.tsx` (nuovo, se serve), `frontend/src/api/interventi.ts`, `frontend/src/api/esempi/`.
- **Cosa**: nella finestra Cambia immagine, in revisione, una quarta scelta «Crea una nuova immagine AI» con «Indicazioni per l'immagine», e la spunta «Riscrivi anche il testo per la nuova immagine» (accesa di base, con «Indicazioni per il testo»): è «Rifai il post». Dopo l'approvazione né la quarta scelta né la spunta. Il pulsante «Rigenera immagine» (§1.7) apre la stessa finestra sulla quarta scelta. Mentre l'AI lavora, l'avviso e la rilettura di oggi. Dati di esempio finché T3-908 e T3-909 non sono su `main`.
- **Fatto quando**: build e lint puliti; screenshot della finestra in revisione e dopo l'approvazione.

## T3-924 · Storico AI: numeri e voto nella pagina (frontend)

- **File**: `pages/operatore/StoricoAI.tsx` e `pages/operatore/storico-ai/`, `frontend/src/api/storico.ts`, `frontend/src/api/esempi/storico.ts`.
- **Cosa**: in cima allo storico i numeri di `NumeriAI` con gli stessi filtri (costo, chiamate, tempi medio e p95, tasso d'errore, voto medio, testi approvati come scritti dall'AI su testi approvati, modifiche a mano, rigenerazioni, immagini create, non create e rigenerate) e la tabella `per_versione`, per confrontare v2 e v3; nel dettaglio il voto da 1 a 5 con la nota e le valutazioni già date. Grafici solo se servono e senza librerie nuove.
- **Fatto quando**: build e lint puliti; screenshot.

## T3-925 · Prova dei prompt v3 (backend e documento)

- **File**: `backend/app/cli.py` (un comando come quello di T3-32, se non basta quello), `docs/` (la tabella dei risultati nella PR, non un documento nuovo).
- **Cosa**: generazione vera di una campagna del seed con v3, sullo stesso profilo delle campagne di prova del 28/10 (31 immagini v2 nel database di sviluppo). Confronto nello Storico AI per versione del prompt: costo, tempi, errori, riscritture del piano; voto a mano di 10 immagini e 10 testi per versione con la rubrica: pertinenza alla bottega, coerenza con le foto vere, varietà tra le immagini, rispetto di R-43.
- **Fatto quando**: tabella e immagini a confronto nella PR; le correzioni ai prompt, se servono, nella stessa PR (versione `v3` invariata se il cambio è piccolo, `v4` se cambia la struttura).

## T3-926 · Pagine statiche della corsia 9

- **File**: in `docs/pagine/`, `AdFlow-operatore-campagna.html`, `AdFlow-operatore-da-approvare.html`, `AdFlow-operatore-artigiano-campagne.html`, `AdFlow-calendario.html`, le pagine dell'artigiano con la barra (`AdFlow-ingresso.html`, `AdFlow-campagne.html`, `AdFlow-campagna.html` con il passo 10, `AdFlow-campagna-stati.html`, `AdFlow-archivio-foto.html`, `AdFlow-profilo-bottega.html`), `AdFlow-operatore-storico-ai.html` (nuova), `index.html`; `assets/adflow.css` solo se serve.
- **Cosa**: le pagine statiche come l'app dopo la corsia 9: etichette e barra degli stati, nome della bottega, durata rapida, Rigenera testo, Cambia immagine con Rifai il post e Rigenera immagine, Storico AI.
- **Fatto quando**: ogni pagina toccata riletta da un collega; mappa aggiornata.

## T3-927 · Prova della corsia 9

- **File**: `backend/tests/percorsi/` (un test di percorso), nessun altro file se la prova va.
- **Cosa**: CA-116 e il percorso a mano in due finestre (operatore e artigiano): due campagne sovrapposte della stessa bottega; durata di una settimana; in revisione Rifai il post su un post con foto (foto della campagna e testo riscritto) e Rigenera immagine su un post con immagine AI; approva; Storico AI con le chiamate di tutte e due le campagne e un voto.
- **Fatto quando**: CA-116 verde; passi della demo di converge §4 senza errori; screenshot nella PR.

---

## 2. Ordine di lavoro

Tre ondate. Dentro un'ondata i task partono insieme; un task parte quando ciò che sta in «Dipende da» (`tasks.md`) è su `main`.

| Ondata | Task | Parte quando |
|---|---|---|
| 1 | T3-901, T3-902, T3-903, T3-904, T3-905, T3-906, T3-907, T3-908, T3-909, T3-910, T3-911, T3-912, T3-913, T3-914 | T3-900 su `main` |
| 2 | T3-915 · T3-916, T3-917, T3-918 · T3-919 · T3-920 · T3-921 · T3-922 | la loro dipendenza dell'ondata 1 |
| 3 | T3-923, T3-924, T3-925, T3-926, T3-927 | le loro dipendenze |

Priorità per la demo, se il tempo non basta: T3-908 (sblocca i post con l'immagine non creata), T3-901, T3-904, T3-905, T3-909, T3-919, T3-923; poi lo storico e i prompt; per ultime le foto.

Data (ADR-119): tutto su `main` entro domenica 1/11. Ciò che il 1/11 non è su `main` resta fuori e la sua parte di regole torna com'era; dal 2 al 6/11 solo correzioni, slide, video e prove (T3-07).

## 3. Fuori da questi task (`docs/ROADMAP.md`)

Espansione della foto con l'AI (outpainting); immagini AI che partono da una foto vera come riferimento di stile; scarto di un post in revisione (la costituzione resta: si rifà, non si toglie); anteprima della foto sistemata con la scelta «taglia o bordi» per post; esportazione dello storico; un ritocco dell'immagine AI dopo l'approvazione.
