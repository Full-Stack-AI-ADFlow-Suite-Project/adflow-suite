# T4-101 · Copertura dei rami

Comando (da `backend/`, T4-101 della corsia 10):

```bash
uv run --with pytest-cov pytest --cov=app --cov-branch --cov-report=term-missing
```

Esito: **1 failed, 1999 passed** in circa 2 minuti e 20 secondi; copertura totale
**94 %** (7038 righe, 326 non eseguite; 1946 rami, 195 non presi).

Il test che fallisce è `tests/test_sast_security.py::test_instagram_meta_in_produzione_richiede_url_foto_https`
e **fallisce solo quando la suite gira con `--cov`** (tre esecuzioni su tre, senza
`--cov` la suite è verde). Non è un problema della copertura in sé: è il difetto
RL-009 del registro, qui scoperto per la prima volta.

## Perché la corsa con --cov fallisce (RL-009)

Catena accertata con un plugin diagnostico che intercetta le scritture in
`os.environ` e con un canarino temporaneo nel test (poi rimosso):

1. `litellm`, appena importato, chiama `load_dotenv()`
   (`litellm/__init__.py:30`): python-dotenv cerca un file `.env`;
2. in un processo avviato **senza** `__main__.__file__` (per esempio `python -c`,
   oppure pytest sotto `pytest-cov`) la ricerca parte dalla directory di lavoro
   (`backend/`) e **trova `backend/.env`: tutte le sue variabili finiscono in
   `os.environ`**, `FOTO_URL_PUBBLICO` compreso (valore `https://…` valido);
3. `Impostazioni(_env_file=None, …)` del test non legge il `.env` ma legge
   **le variabili d'ambiente**: il validatore di produzione, che deve rifiutare
   Instagram senza `FOTO_URL_PUBBLICO` HTTPS, trova l'URL valido e non solleva
   più `ValidationError` → «DID NOT RAISE».

La prova contraria: `pytest tests/adapters/ai/test_litellm.py
tests/test_sast_security.py…` (senza `--cov`, import di litellm compreso) passa,
perché in quel layout python-dotenv risale il percorso del pacchetto litellm e
non trova nessun `.env`. Il difetto è documentato dal test
`tests/accettazione/test_linea_base.py::test_importare_litellm_non_esporta_il_file_env_nell_ambiente`
in `xfail(strict=True)` (RL-009).

## Copertura per file, confrontata con le soglie di §6

Soglie di `accettazione-post-mvp.md` §6: sotto l'85 % su `service.py` e
`domain.py` è un rilievo; sotto il 100 % su transizioni e `interventi_ammessi()`
è un rilievo.

| File | Copertura rami | Soglia | Esito |
|---|---|---|---|
| `core/transizioni.py` | **100 %** | 100 % | verde |
| `contenuti/domain.py` (`INTERVENTI_AMMESSI`) | **100 %** | 100 % | verde |
| `contenuti/interventi.py` · `interventi_ammessi()` (righe 60–81) | **100 %** | 100 % | verde |
| `moduli/accesso/service.py` | 95 % | 85 % | verde |
| `moduli/artigiani/service.py` | 100 % | 85 % | verde |
| `moduli/campagne/service.py` | 90 % | 85 % | verde |
| `moduli/contenuti/service.py` | 99 % | 85 % | verde |
| `moduli/notifiche/service.py` | 97 % | 85 % | verde |
| `moduli/pubblicazione/service.py` | 94 % | 85 % | verde |
| `moduli/revisione/service.py` | 100 % | 85 % | verde |
| `domain.py` di tutti i moduli | 100 % | 85 % | verde |

Nessuna soglia violata: la copertura dei file a soglia è tutta verde. Le righe
non coperte restano quasi tutte nei rami d'errore raro degli adattatori veri
(litellm, meta, disco) e nei percorsi di ripiego di `campagne/service.py`.

## Copertura per area (estratto)

| Area | Copertura |
|---|---|
| `adapters/ai` (finto, litellm, immagini) | 95–100 % |
| `adapters/social` | 96–97 % |
| `adapters/archivio` | 89–96 % |
| `core` | 93–100 % |
| `moduli` (media) | 90–100 % |

Il report completo riga per riga è nell'output del comando, che si rifà con la
riga qui sopra; i numeri di questo documento sono dell'esecuzione del 30/10/2026
sul branch della simulazione.

## Conclusioni

- Copertura dei rami alta e sopra ogni soglia di §6: **nessun rilievo**.
- La corsa con `--cov` perde un test per colpa di RL-009 (litellm esporta
  `backend/.env` nell'ambiente): **rilievo RL-009**, con test `xfail` che lo
  riproduce alla radice, in un processo separato, senza dipendere da `--cov`.
- La copertura **non entra in CI** (domanda 3 della §12: strumenti solo in
  locale): R-07 resta valido come rilievo.
