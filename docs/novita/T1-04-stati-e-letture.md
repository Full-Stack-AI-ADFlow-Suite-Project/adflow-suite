# Novità · T1-04 Stati e letture comuni

2 ottobre 2026 · branch `feature/T1-04-stati-e-letture` · corsia 0 (serve l'approvazione di tutto il team)

## In breve
Le funzioni di plan §6 segnate T1-04 non sono più stub: stati, transizioni e letture comuni funzionano e sono provati. La stessa PR corregge alcuni punti di T1-02 e T1-03 emersi rileggendo le due PR già unite.

## Cosa c'è adesso
- **`domain.py`** in artigiani (valori ammessi del profilo, frequenza → post alla settimana), campagne (stati, transizioni, esiti e motivi della decisione, origine della foto) e contenuti (stati e transizioni del post, tipi di intervento).
- **artigiani**: `profilo_di()`.
- **campagne**: `campagna()`, `foto_della_campagna()`, `campagne_in_stato()`, `cambia_stato()`, `registra_decisione()`, `aggiorna_foto()`.
- **contenuti**: `post_della_campagna()`, `ha_blocchi()`, `approva_post()`, `post_dovuti()`, `segna_esito()`, `tutti_chiusi()`.
- **Fabbriche complete**: le campagne dall'invio in poi hanno canali, frequenza e obiettivo copiati dal profilo, la fotografia del profilo e una foto valida con descrizione; ogni post ha la sua foto.
- **Test**: 247, tutti verdi (con quelli di T1-05). Ogni transizione ammessa e vietata di campagna e post, e almeno un test per funzione.

## Cosa cambia per chi lavora
1. **Ricrea il database locale.** Le migrazioni 001–006 sono state corrette sul posto: da `backend/`, `alembic downgrade base && alembic upgrade head`. Il database dei test si ricrea da solo.
2. **`richiede_ruolo()` funziona già.** Nei router si può scrivere `Depends(richiede_ruolo("operatore"))`: prima sollevava un errore all'avvio dell'app. Il controllo passa da `utente_corrente`, che fino a T1-12 si sostituisce con la fixture `utente_di_prova` (T1-06).
3. **Nei service la sessione è `db: Session`**, senza `Depends`: la passa il router o il job.
4. **`post_della_campagna()` restituisce i `Post`**: `post.versione_corrente` è l'ultima versione, `post.versioni` lo storico in ordine.
5. **`aggiorna_foto()` riceve `analisi_ai` come JSON** (dizionario), come la colonna della tabella.
6. **Le date tornano sempre in UTC**, qualunque sia il fuso del proprio PostgreSQL.
7. **Gli stati si scrivono con le costanti del `domain.py`** dentro il modulo proprietario. Un altro modulo passa il nome dello stato al service (`cambia_stato(db, campagna, "attiva")`): i `domain.py` altrui non si importano.

## Correzioni a T1-02 e T1-03
| Cosa | Prima | Adesso |
|---|---|---|
| Fuso della connessione | quello del server: un test falliva fuori da UTC | UTC fissato in `core/db.py` (`crea_motore`) e nei test |
| `richiede_ruolo()` | `NotImplementedError` alla chiamata, cioè all'import del router | factory funzionante |
| Firme dei service | `db: Annotated[Session, Depends(get_db)]`, ritorni `Any` | `db: Session`, ritorni con i modelli del modulo |
| `aggiorna_foto(analisi_ai)` | `str` | `dict`, come la colonna JSONB |
| Docstring | `approva_post` citava pubblicazione; `tutti_chiusi` citava `scaduto` | allineate a plan §6 e spec §2.4 |
| Indici | solo chiavi primarie e vincoli unici | indici sulle chiavi esterne e su `post(stato, data_ora)` |
| `pubblicazione` | nessun vincolo sul numero di tentativo | unico su `(post_id, n_tentativo)` |
| `versione_post` | `provider_ai`, `modello_ai`, `versione_prompt` obbligatori | facoltativi (servono vuoti per `scelta_foto`, sprint 3) |
| Fabbriche | foto 800×600; post senza foto; scrypt a ogni utente | foto 1080×1350; post sempre con foto; hash calcolato una volta |

## Scelte da rivedere insieme
- **`ha_blocchi()` guarda solo `da_rivedere`.** L'"intervento in corso" di R-14 e CA-22 non ha ancora un campo: nasce con la rigenerazione (sprint 2b). Fino ad allora CA-22 è coperto per la parte `da_rivedere`.
- **`tutti_chiusi()`** è vero quando ogni post è `pubblicato` o `fallito` (spec §2.4, CA-39); una campagna senza post risulta chiusa.
- **`registra_decisione()`** controlla esito e motivo sui valori del `domain.py` e, per `respinta`, pretende motivo e nota (R-18). Non controlla che le foto segnate siano della campagna: lo fa l'endpoint della 2b.
- **`approva_post()`** rifiuta tutto se anche un solo post non è `da_approvare`: nessun post cambia stato.
- **`profilo_bottega.orari`** resta JSONB, come deciso in T1-03.
- **Relazione `Post.versioni`**: è interna al modulo contenuti (constitution §2.3) e non cambia lo schema.

## Documenti aggiornati
Poche righe, per restare allineati al codice:
- `docs/agenti/tasks.md`: caselle di T1-02 e T1-04 spuntate.
- `docs/agenti/plan.md`: §2 `orari` e `analisi_ai` sono JSON, unico su `(post_id, n_tentativo)`; §6 `richiede_ruolo` già funzionante e forma di `post_della_campagna`; §7 connessione in UTC.
- `docs/agenti/spec.md`: CA-22, l'intervento in corso vale dalla 2b.
- `AGENTS.md`, `constitution.md`, `converge.md`: nessuna modifica.

## Dopo l'unione di T1-05
Il branch include `main` con T1-05. Un test di T1-05 (`test_tick_pubblicazione_invoca_pubblica_dovuti`) falliva su `main`: usava `pytest.mark.asyncio` senza il plugin. Ora chiama il tick con `asyncio.run`, senza librerie nuove. I segnaposto delle fabbriche di notifiche, revisione e pubblicazione non rimandano più a T1-04: plan §6 non prevede fabbriche per quei moduli.

## Come si prova
Da `backend/`, con `.venv` attivo e `.env` compilato:

```bash
alembic downgrade base && alembic upgrade head && pytest && black --check .
```

Nessuna libreria nuova, nessun segreto, nessuna chiamata ad AI, social o email.
