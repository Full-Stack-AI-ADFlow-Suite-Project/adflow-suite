# T4-101 · Scansioni di sicurezza e qualità

Tutte le scansioni della §5.3 di `accettazione-post-mvp.md`, lanciate in locale
il 30/10/2026 dal branch della simulazione, con i report grezzi accanto
(`T4-101-grezzo-*.json|txt|md`). Nessun segreto, token o dato personale è
riportato in questo documento o nei grezzi.

## Riepilogo

| Controllo | Strumento | Esito | Rilievo |
|---|---|---|---|
| Dipendenze Python | `uvx pip-audit -r backend/requirements.txt` | **57 vulnerabilità in 3 pacchetti** | RL-004, RL-005, RL-006 |
| Dipendenze frontend | `npm --prefix frontend audit --omit=dev` | 0 vulnerabilità (30 dipendenze di produzione) | — |
| Analisi statica | `uvx bandit -r backend/app -ll` | 0 risultati a media o alta gravità | — |
| Analisi statica | `uvx semgrep` con `p/python`, `p/owasp-top-ten`, `p/react`, `p/typescript` su `backend/app` e `frontend/src` | 0 risultati | — |
| Segreti in tutta la storia | `gitleaks` (versione installata, sottocomando `detect`) con `--log-opts=--all` | 2 rilevamenti, **entrambi falsi positivi** | RL-007 |
| Tipi Python | `uvx mypy` su `domain.py` e `service.py` (con i file importati) | **83 errori** | RL-008 |
| Componenti e licenze | `pip-licenses` | 124 pacchetti; nessuna licenza copyleft forte nel runtime | nota sotto |

## pip-audit: 57 vulnerabilità, 3 pacchetti (RL-004, RL-005, RL-006)

| Pacchetto | Versione | Ruolo | Vulnerabilità | Gravità NVD (dove c'è il CVE) | Correzione |
|---|---|---|---|---|---|
| `pillow` | 12.3.0 | **runtime**: sistemazione e ritaglio delle foto caricate dagli artigiani (R-42) | 39 | **3 CRITICAL (CVSS 9.8/9.2), 9 HIGH, 6 MEDIUM**, 21 senza record NVD (solo PYSEC/GHSA) | 13.0.0 |
| `filelock` | 3.32.7 | **runtime transitiva**: `litellm` → `huggingface-hub` → `filelock` | 13 | nessun record NVD | 4.0.9 / 4.2.1 |
| `black` | 23.3.0 | solo sviluppo (formattazione) | 5 | nessun record NVD | 24.3.0+ |

Le vulnerabilità di Pillow sono quasi tutte nella decodifica delle immagini
(letture oltre il buffer, use-after-free con libtiff, dereferenziazioni in
filtri e font): è esattamente la superficie esposta da AdFlow, che apre file
JPEG/PNG/WEBP caricati dagli utenti. Le tre CRITICAL sono
`CVE-2026-112398` e `CVE-2026-112403` (CVSS v3 9.8, v4 9.2) e
`CVE-2026-96639` (CVSS v3 9.8). Correzione disponibile con `pillow==13.0.0`:
non applicata (T4-101 non corregge: è un rilievo).

`filelock` è una dipendenza che il runtime si trascina dietro `litellm`
(→ `huggingface-hub` → `filelock`): con R-06 (nessun lockfile) la versione
installata può cambiare a ogni risoluzione.

Report grezzo: `T4-101-grezzo-pip-audit.json` (estratto senza le descrizioni
intere); gravità NVD recuperate una a una dall'API NVD per i 22 CVE con alias.

## gitleaks: 2 falsi positivi, nessun segreto valido (RL-007)

`gitleaks detect --source . --log-opts=--all --redact` (versione locale, senza
il sottocomando `git` delle 8.19+): **2 rilevamenti**, entrambi con le regole
`easypost-test-api-token` ed `easypost-api-token`, nel file
`docs/archivio/appunti/architettura/AdFlow-diagrammi.html` (righe 334 e 555
delle versioni storiche dei commit del 30/09).

Verifica a mano (mai riportando i valori): le stringhe trovate sono frammenti
**casuali di base64 dentro PNG incorporati** nel diagramma (`data:image/png;
base64,…`): 154 frammenti con prefisso `EZ**` di lunghezza variabile (24–270
caratteri) tutti diversi tra loro, dentro dati binari, non in codice. Nessuna
chiave reale di EasyPost (servizio, peraltro, non usato da AdFlow): **nessun
blocco assoluto**. Resta il rilievo RL-007: chi mette gitleaks in CI avrà
questi due falsi positivi e dovrà configurare una baseline o un'esclusione per
i diagrammi d'archivio. Report grezzo redatto (senza valori):
`T4-101-grezzo-gitleaks-redatto.json`.

## mypy: 83 errori di tipo (RL-008)

Comando: `uv run --with mypy mypy <tutti i domain.py e service.py> …
--ignore-missing-imports`. Il controllo segue gli import: 83 errori in tutto,
di cui 16 nei file `domain.py`/`service.py` richiesti dalla §5.3. Distribuzione:
30 accessi ad attributi su optional (`union-attr`), 17 tipi di argomento,
11 indici, 7 operatori, il resto tra assegnazioni, ritorni e annotazioni
mancanti. I file più colpiti: `contenuti/interventi.py` (27),
`contenuti/generazione.py` (12), `campagne/service.py` (5).

Nessun errore porta a un comportamento sbagliato dimostrato (la suite è
verde), ma il controllo dei tipi oggi non è utilizzabile come barriera:
RL-008. Report grezzo: `T4-101-grezzo-mypy.txt`. Nessuna correzione applicata
(§5.3: «report degli errori, senza correzioni»).

## Licenze (pip-licenses)

124 pacchetti nell'ambiente. Nessuna GPL/AGPL/SSPL tra le dipendenze (le
librerie chiave: fastapi BSD, SQLAlchemy MIT, litellm MIT, pillow HPND,
procrastinate MIT, psycopg **LGPL-3.0-only**). Nota: `psycopg` è LGPL-3.0-only;
usata come libreria non modificata via import è la modalità d'uso prevista
dalla licenza, ma va tenuta presente se un giorno si distribuisce il prodotto:
nessun rilievo, solo una nota da confermare con chi firma la licenza d'uso.
Report grezzo: `T4-101-grezzo-pip-licenses.md`.

## Conclusioni

- **R-05 confermato** (RL-001): `httpx` è importato dal runtime
  (`app/adapters/social/meta.py:25`) e non è dichiarato in
  `requirements.txt`; arriva per via di litellm. Se litellm cambia le sue
  dipendenze, l'adattatore Meta si rompe all'import.
- **R-06 confermato** (RL-002): nessun lockfile Python (solo `requirements.txt`
  con pin del primo livello) e runtime e strumenti di test nello stesso file
  (`pytest`, `httpx2`, `black`, `pre-commit`, `cryptography` accanto a fastapi
  e litellm): le vulnerabilità di `black` finiscono nell'ambiente di
  produzione e le versioni transitive (come `filelock`) non sono fissate.
- **R-07 confermato** (RL-003): la CI (`backend.yml`, `frontend.yml`) fa
  migrazioni, probe SAST/DAST locale, pytest e black, più lint e build del
  frontend. Mancano: analisi delle dipendenze, analisi statica indipendente,
  ricerca segreti nella storia, controllo tipi, copertura, E2E.
- **RL-004 (Alta in produzione)**: pillow 12.3.0 con 39 vulnerabilità note,
  3 CRITICAL e 9 HIGH, nel percorso che apre le immagini caricate dagli
  utenti; correzione disponibile (13.0.0) non applicata.
- Nessun segreto valido nella storia di git: il blocco assoluto ipotizzato
  dalla §8 non si materializza (RL-007, smentito).
