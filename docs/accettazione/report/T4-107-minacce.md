# T4-107 · Modello delle minacce (STRIDE)

Flusso dei dati con i confini di fiducia e l'analisi STRIDE per ognuno
(§5.2 di `accettazione-post-mvp.md`). Per ogni minaccia: la difesa che esiste
(con il file o il test) oppure il rilievo del registro.

## Flusso e confini di fiducia

```
Browser (artigiano | operatore) → [confine 1] → API FastAPI → PostgreSQL
                                                   │
                          ┌────────────────────────┼─────────────────────────┐
                          ▼                        ▼                         ▼
                 disco locale (foto)          LLM (OpenRouter)          Meta Graph API
                          │                        │                         │
                   [confine 3]              [confine 4]                [confine 5]
```

Confini: **1** browser → API; **2** artigiano ↔ operatore (ruoli e dati);
**3** upload → disco; **4** profilo/foto → LLM e risposta → database;
**5** backend → Meta; **6** worker ↔ database; **7** segreti e log.

## STRIDE per confine

| Confine | Minaccia (STRIDE) | Difesa che esiste | Rilievo |
|---|---|---|---|
| 1 Browser → API | **S**poofing della sessione (furto del cookie) | cookie `httpOnly`, `SameSite=Lax`, `Secure` in produzione; token nel database solo come hash; scadenza per inattività (R-29) | — |
| 1 | **T**ampering tramite CSRF | `ProtezioneCSRF` in produzione (Origin), `SameSite=Lax`; test `test_origine.py` | RL-016 (in produzione c'è; in sviluppo è spenta) |
| 1 | **R**ipudio delle azioni | `decisione_campagna` e `approvazione` con autore e ora; eventi di sicurezza | — |
| 1 | **I**nformazioni: header assenti | — | **RL-015** (CSP/HSTS/nosniff/Referrer-Policy mancanti) |
| 1 | **D**oS: richieste enormi | limite di 12 MB per richiesta; 10 MB per foto | — |
| 1 | **E**levazione: ruolo sbagliato | matrice 57 × 5 tutta conforme (`test_matrice.py`); admin = operatore | — |
| 2 Artigiano ↔ operatore | **I** letture trasversali (BOLA) | 404 per risorse di un'altra bottega in tutte le operazioni con id; archivio/calendario/campagne ignorano il parametro altrui; `test_bola_nuovi_endpoint.py` | RL-020 (smentito) |
| 2 | **E** aumento dei privilegi | `richiede_ruolo` su ogni rotta; l'admin non passa le rotte dell'artigiano | — |
| 3 Upload → disco | **T** file poliglotti, bombe di decompressione | magic bytes sul contenuto, limiti di peso e lato corto, nome generato dal server, `nosniff`; `test_upload_ostili.py` | — |
| 3 | **D** disco pieno | — | **RL-029** (500 generico) |
| 3 | **I** EXIF/GPS nelle foto pubblicate | la copia sistemata non ha EXIF né GPS; l'originale resta (§1.3); test `invarianti/test_03` | — |
| 4 Profilo/foto → LLM | **T** prompt injection dal profilo o dal testo | validatore (§1.6) e approvazione umana (§1.1) fermano ogni uscita; nessun percorso salta l'approvazione; `test_prompt_injection.py` | — |
| 4 | **I** dati personali nello storico AI | — | **RL-019** (prompt e risposte conservati senza regola di conservazione) |
| 4 | **D** risposta enorme o malformata | i cinque tipi d'errore (R-35); campagna mai a metà | — |
| 4 | **E** istruzioni ostili che pubblicano | il testo non può pubblicare: serve l'approvazione; la pubblicazione è idempotente | — |
| 5 Backend → Meta | **I** fuga del token | token solo in `.env` (600), mai nei log, mai in git (gitleaks nella storia: `T4-101`); il token viaggia nel corpo della richiesta, non nell'URL | — |
| 5 | **T** pagina sbagliata | una sola pagina di prova da configurazione (D1) | — |
| 5 | **D** limiti di Meta | errori temporanei ritentati fino a `TENTATIVI_MAX`, poi `fallito`; codici Graph mappati (5xx, 190, 368, 4/17/32/613) | — |
| 5 | **T/R** doppia pubblicazione | indice unico `ok` e tentativo riusato; ma il timeout dopo la pubblicazione ripete il post | **RL-025** (D-07, blocco assoluto) |
| 6 Worker ↔ DB | **T** job ripetuti o a metà | tick serializzato dal lock di Procrastinate; idempotenza per tentativo; due worker non raddoppiano (`test_pubblicazione.py`) | RL-025 (crash prima del commit) |
| 6 | **D** coda intasata | — | **RL-031** (nessuna misura della coda) |
| 7 Segreti e log | **I** dati personali nei log | eventi JSONL senza dati; prova con email/password/token riconoscibili in `T4-107-log-segreti.md` | — |
| 7 | **T** permessi del `.env` | `600`; `.env` fuori da git | — |
| 7 | **I** credenziali social in chiaro | R-14: i permessi social cifrati sono un prerequisito dello sviluppo completo | **RL-039** (R-14) |

## Sintesi

- Le minacce **T/I/E dei confini 1–4** hanno una difesa provata da test (matrice
  dei permessi, upload ostili, prompt injection, invarianti).
- Le lacune gravi stanno nei confini **5–7**: intestazioni (RL-015), doppia
  pubblicazione dopo un crash (RL-025, blocco assoluto), osservabilità
  (RL-031), segreti social in chiaro (RL-039), dati personali nello storico
  (RL-019).
- Nessuna minaccia «aumento dei privilegi» tra artigiani è aperta: la matrice e
  i test BOLA sono verdi.
