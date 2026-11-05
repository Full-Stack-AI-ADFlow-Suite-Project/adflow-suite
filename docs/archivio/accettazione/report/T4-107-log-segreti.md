# T4-107 · Log, segreti e rotazione delle chiavi

Copre §5.4 punti 7 e 8 di `accettazione-post-mvp.md` e il rischio R-13.
Nessun segreto (valore) compare in questo report.

## 1. Ricerca nei log (email, password, token riconoscibili)

Prova: due richieste con valori riconoscibili — un accesso con
`email-riconoscibile@example.test` / `PasswordRiconoscibile!9` e una lettura con
`?token=TokenRiconoscibile42` — catturando tutto ciò che l'applicazione scrive
sui logger (livello INFO, formattazione reale dei log JSONL).

| Valore | Nei log dell'app | Note |
|---|---|---|
| password | **assente** | il corpo della richiesta non si logga mai |
| email | **assente** | il login logga `auth_failure` senza identità in chiaro |
| token in query | **TROVATO**, ma solo nel log di `httpx` del client di test | riga «HTTP Request: GET http://testserver/api/campagne?token=…» del logger `httpx`, non dei log JSONL dell'app: in produzione (uvicorn + client reale) quel logger non vede le richieste entranti |

Conclusione: i **log dell'applicazione non contengono dati personali né
segreti**; il test DAST `test_dast_log_dettagliato_redige_query_e_registra_esito`
e i test `test_log_jsonl.py` coprono la redazione delle query. La riga di
`httpx` è un artefatto del `TestClient` (logger del client HTTP), da tenere
presente se si cattura l'output dei test.

## 2. Storico AI

Lo storico conserva **prompt e risposte** (R-50, RL-019): contiene il profilo
della bottega e i testi. Le immagini viaggiano per id, non come byte, e le
chiavi non ci sono (prova: `test_ca109` e il formato di `chiamata_ai.richiesta`
in plan §2). È una **lacuna di conservazione e di accesso** (solo operatori),
non di segreti.

## 3. Permessi del `.env`

`stat` sul file: **600** (solo il proprietario). `.env` è fuori da git
(`gitleaks` su tutta la storia in T4-101: nessun segreto valido, solo falsi
positivi su PNG d'archivio). Le variabili nuove hanno un valore finto in
`.env.example` (costituzione §3).

## 4. `--forwarded-allow-ips`

La procedura documentata (`docs/sicurezza-accesso.md:31`) usa
`--proxy-headers --forwarded-allow-ips 127.0.0.1`: **mai `*`**. Il test locale
(`test_proxy_http_reale.py`) prova che gli header inoltrati contraffatti da un
indirizzo non fidato (`192.0.2.1`) vengono rifiutati. Resta da rifare su un
proxy di staging pubblico (RL-033).

## 5. Rotazione di `login_limite_segreto` (R-13)

**Fatto (dal codice):** la stessa chiave firma i contatori del limite di
login (`core/limite_login.py:32`) **e** gli indirizzi pubblici delle foto
(`moduli/campagne/foto_pubblica.py:29`). Cambiarla:

- azzera di fatto il conteggio dei tentativi di login (i contatori diventano
  non verificabili): effetto voluto e innocuo;
- **invalida tutte le firme degli indirizzi pubblici in corso**: una
  pubblicazione Instagram già avviata che deve scaricare una foto firmata
  prende 404 e il post diventa `fallito`.

**Conseguenza operativa:** la rotazione va fatta a pubblicazioni ferme, come
dice la §5.4 punto 8. Rilievo **RL-038** (bassa): le due funzioni dovrebbero
avere chiavi separate (una per i contatori, una per gli indirizzi pubblici).

## 6. Rilievi

- **RL-038** (Bassa): una sola chiave per login e foto pubbliche; la rotazione
  invalida le pubblicazioni in corso.
- **RL-039** (prerequisito, R-14): i permessi social non sono cifrati nel
  database; con il collegamento dei veri account serviranno cifratura,
  rotazione e revoca (fuori dall'MVP, ma è un prerequisito dello sviluppo
  completo).
