# Novità · T1-22 API Bozza Campagna

7 ottobre 2026 · corsia 2 (Silvia) · branch `feature/T1-22-api-bozza`

## Funzionalità implementate

- `POST /api/campagne`: creazione bozza campagna riservata all'artigiano (`HTTP 201`).
  - Validazione rigorosa e difensiva (Defense in Depth): titolo non vuoto (max 200 car.), descrizione (max 2000 car.), codifica UTF-8, blocco preventivo dei byte NUL (`\x00`) e normalizzazione a `None` per descrizioni di soli spazi bianchi.
  - Rispetto regola **R-08**: inizio ad almeno 3 giorni da oggi calcolato sul fuso locale `Europe/Rome` (`ANTICIPO_MINIMO_GIORNI`, CA-09: `HTTP 422`), data fine successiva ad inizio e durata massima entro 92 giorni (CA-10: `HTTP 422`). Testati e garantiti con successo i valori limite esatti (esattamente 3 giorni ed esattamente 92 giorni).
  - Rispetto regola **R-12**: limite di una sola bozza aperta per artigiano (CA-11: `HTTP 409`).
  - Rispetto regola **R-12** e **R-15**: periodi non sovrapposti per lo stesso artigiano con campagne non chiuse (`HTTP 409`); sovrapposizione consentita con campagne in stato `respinta`, `scaduta`, `annullata` o `conclusa` (CA-12: `HTTP 201`). Confini temporali adiacenti collaudati millimetricamente.
  - Concorrenza atomica sicura: impiego di `pg_advisory_xact_lock` a livello di transazione sul profilo artigiano per serializzare in modo sicuro eventuali richieste simultanee ed evitare race condition (dimostrato con test multi-thread a 4 worker concorrenti).
  - Rispetto regola **R-19**: supporto al flag `crea_immagini_ai` (default `False`), salvato e restituito nel dettaglio (CA-46).
- `GET /api/campagne`: elenco delle campagne (`HTTP 200`).
  - L'artigiano visualizza esclusivamente le proprie campagne (o lista vuota se senza bottega).
  - L'operatore e l'admin visualizzano tutte le campagne del consorzio.
  - Supporto per filtro query parameter `?stato=` con validazione rigorosa su `domain.STATI` (`HTTP 422` se non valido).
- `GET /api/campagne/{id}`: dettaglio della campagna (`HTTP 200`).
  - Rispetto criterio **CA-04**: se un artigiano richiede una campagna appartenente ad un altro artigiano, il sistema solleva `HTTP 404` per prevenire information disclosure.
  - Riservatezza dei dati: per l'artigiano i campi riservati (`profilo_snapshot` e `decisioni`) non vengono mai esposti (`None` e `[]`), mentre sono visibili a operatori e admin. Ruoli non previsti ricevono `HTTP 403`.

## Test, Debug Avanzato e Robustezza

- Suite completa in `tests/moduli/campagne/test_api_bozza.py`:
  - `test_ca04_artigiano_accede_a_campagna_altrui_da_404`
  - `test_ca09_creazione_inizio_troppo_vicino_da_422`
  - `test_ca10_durata_superiore_92_giorni_o_fine_prima_inizio_da_422`
  - `test_ca11_bozza_esistente_nuova_bozza_da_409`
  - `test_ca12_periodo_sovrapposto_campagna_attiva_da_409`
  - `test_ca46_crea_immagini_ai_salvato_e_restituito`
  - `test_elenco_campagne_artigiano_e_operatore`
  - `test_creazione_richiede_ruolo_artigiano_da_403`
  - `test_debug_date_limite_esatto_3_giorni_e_92_giorni_consentite`
  - `test_debug_sovrapposizioni_limiti_precisi`
  - `test_debug_artigiano_senza_profilo_gestito_con_grazia`
  - `test_debug_validazione_difensiva_stringhe`
  - `test_debug_riservatezza_operatore_vs_artigiano_nel_dettaglio`
  - `test_debug_filtro_stato_valido_ed_errore_su_stato_sconosciuto`
  - `test_debug_descrizione_spazi_normalizzata_a_none`
  - `test_debug_ruolo_non_previsto_riceve_403`
  - `test_debug_creazione_bozza_concorrente_atomica` (con cleanup garantito in `try...finally` per prevenire test flaky)
- **173 test su 173 superati (100% VERDE)** (`tests/moduli/campagne/` e `tests/test_confini.py`).
- Codice 100% conforme a PEP 8 e formattato con `black`.
- Confini architetturali intatti: zero import vietati, nessun commit nei service.
