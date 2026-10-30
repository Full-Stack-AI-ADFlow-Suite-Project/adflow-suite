# T4-101 · Ricostruzione da zero

Prova di §4.1 di `accettazione-post-mvp.md`: clone in una cartella pulita
(`/tmp/opencode/adflow-ricostruzione`), `allinea.py`, migrazioni da database
vuoto, seed, test e build, con ogni passo cronometrato. La prova è del
30/10/2026, dal branch della simulazione `integrazione-166-167`.

## Che cosa è stato fatto, passo per passo

| Passo | Comando | Esito | Tempo |
|---|---|---|---|
| Clone del repository (branch della simulazione) | `git clone --branch integrazione-166-167 …` | ok | < 1 s (da disco; da GitHub dipende dalla rete) |
| Prima esecuzione di allinea | `uv run python allinea.py 10` | ok: crea `.venv`, installa le dipendenze, installa `pre-commit`, copia `backend/.env.example` in `backend/.env` e si ferma chiedendo le credenziali | 5 s con cache di uv calda (minuti a cache fredda: la prima corsa ha installato 124 pacchetti) |
| Credenziali | riempire `DATABASE_URL` e `DATABASE_URL_TEST` in `backend/.env` | ok | — |
| Database vuoto | `CREATE DATABASE` via psycopg | ok: `adflow_ricostruzione` creato vuoto (e `adflow_test` già presente) | 1 s |
| Migrazioni da database vuoto | `uv run python allinea.py 10` (seconda volta: `alembic upgrade head`) | ok: 001 → 013 senza errori | 1 s |
| Seed | `uv run python -m app.cli seed` (password chiesta a terminale) | ok: artigiano, operatore e admin creati, con gli account social finti collegati | 1 s |
| Test | `uv run pytest -q` | **2000 passed** | 106 s |
| Frontend | `npm install` → `npm run build` → `npm run lint` | ok tutti (build `tsc -b && vite build` pulita, lint 0 errori) | 0 s (cache npm calda) / 6 s / 0 s |
| Avvio | `uv run uvicorn app.main:app` e `GET /api/health` | ok: `{"stato":"ok"}` | 1 s |

Totale circa 2 minuti di lavoro effettivo oltre l'installazione (con le cache
calde). La documentazione (`README.md` §Setup, `AGENTS.md`, `converge.md` §1)
guida tutti i passi principali: la ricostruzione riesce.

## Correzioni applicate durante la prova (resi ripetibili)

- Alla prima esecuzione della suite nella copia pulita, con un database dei
  test chiamato in modo diverso da `adflow_test`, la suite perdeva 23 test per
  errore e 5 per fallimento: alcune fixture **verificano per nome** che il
  database corrente sia `adflow_test` (per esempio
  `tests/moduli/accesso/test_auth_transazioni.py:30`,
  `tests/moduli/accesso/test_sessioni_transazioni.py:60`, e il subprocesso di
  `test_limite_condiviso_tra_processi_indipendenti` che asserisce
  `(u.database, u.port) == ('adflow_test', 5432)`). Con `DATABASE_URL_TEST`
  su `adflow_test`, come dice il README, la suite è verde: 2000 passed.
  Rilievo RL-012: il vincolo esiste ma lo si scopre solo sbagliando.
- Tre fallimenti della prima corsa (`test_proxy_http_reale`,
  `test_auth_http_reale`, `test_migrazione_downgrade_upgrade_solo_test`) sono
  nati dall'avvio contemporaneo di due suite sullo stesso PostgreSQL (porte e
  schema condivisi): rilanciando senza concorrenza tutto è verde. Nota per le
  prove dei task seguenti: le suite non vanno mai lanciate in parallelo.

## Passi che richiedono una conoscenza non scritta

1. **Creare i database.** Il README dice «Servono … PostgreSQL 16 con i
   database `adflow` e `adflow_test`» ma non dice come si creano (nessun
   `createdb`, nessuna SQL). Per chi parte da una macchina nuova è un passo
   implicito. (RL-013)
2. **Il nome del database dei test è un vincolo forte, sepolto nei test**
   (vedi sopra). Il README lo dichiara come informazione, non come vincolo:
   con un nome diverso la suite non gira. (RL-012)
3. **La demo con le foto vere non si ricostruisce dal repository.**
   `python -m app.cli demo --foto CARTELLA` prende le foto da una cartella che
   non sta in git («le foto restano fuori da git», `backend/README.md`) e la
   sua posizione non è scritta da nessuna parte (cercata in tutto il disco:
   nessun `demo.json`, nessuna cartella delle foto della demo). Il percorso
   della demo di `converge.md` §4, quello del pitch, non è riproducibile da un
   clone pulito senza chiedere a chi l'ha preparata. (RL-014)
4. **Il seed chiede la password a terminale due volte** (`getpass`): per
   automatizzare la preparazione serve knowing how to pipe stdin —
   minuzia, documentata a metà (il README dice che la chiede, non che la
   chiede due volte né come renderla non interattiva). Non è rilievo.

## Che cosa la prova ha verificato di positivo

- `allinea.py` funziona davvero da zero: crea l'ambiente, copia il `.env` di
  esempio e si ferma nel punto giusto; alla seconda esecuzione migra.
- Le migrazioni 001 → 013 girano su un database vuoto senza errori.
- La suite completa (2000 test) è verde in una copia pulita.
- Build e lint del frontend sono ripetibili.
- L'API parte e risponde al controllo di salute.
