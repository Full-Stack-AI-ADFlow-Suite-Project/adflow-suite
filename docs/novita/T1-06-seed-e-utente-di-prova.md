# Novità · T1-06 Seed e utente di prova

2 ottobre 2026 · branch `feature/T1-06-seed-e-utente-di-prova` · corsia 0 (serve l'approvazione di tutto il team)

## In breve
C'è il seed (artigiano con profilo, operatore, admin), `core/security.py` con scrypt e token, e la fixture `utente_di_prova(ruolo)` per provare le API senza login. Il branch parte da quello di T1-04 (PR ancora aperta): va unito dopo.

## Cosa c'è adesso
- **`core/security.py`**: `hash_password()`, `verifica_password()` (scrypt, formato `scrypt$n$r$p$salt$digest`), `genera_token()`, `hash_token()` (sha256, 64 caratteri: ciò che va in `sessione.token_hash`).
- **`app/cli.py`**, da `backend/`:
  - `python -m app.cli seed`: crea `artigiano@example.com` (con il profilo completo di una bottega di ceramica), `operatore@example.com`, `admin@example.com`. Si può rilanciare: non duplica e non cambia ciò che esiste.
  - `python -m app.cli crea-utente --email … --nome … --ruolo …`: chiama `accesso.service.crea_utente()`.
- **Fixture `utente_di_prova`** in `tests/conftest.py`.
- **Test**: 275, tutti verdi (28 nuovi).

## Cosa cambia per chi lavora
1. **Nei test delle API l'utente si crea così:**
   ```python
   def test_ca04_...(client, utente_di_prova):
       artigiano = utente_di_prova("artigiano")   # ora è l'utente autenticato
       risposta = client.get("/api/campagne")
   ```
   Vale anche per `Depends(richiede_ruolo(...))`: con il ruolo sbagliato la risposta è 403. Richiamata, cambia l'utente autenticato; accetta i campi della fabbrica (`utente_di_prova("operatore", nome="…")`). Senza chiamarla, `utente_corrente` resta lo stub fino a T1-12.
2. **T1-11 e T1-13 usano `core/security.py`**: `hash_password()` per salvare, `verifica_password()` al login, `genera_token()` per il cookie e `hash_token()` per il database. Non serve altro scrypt.
3. **Dopo `alembic upgrade head` lancia il seed** per avere i tre utenti in locale.
4. **La fabbrica `utente()`** usa `hash_password()`: `PASSWORD_DI_PROVA` è la password di ogni utente di prova (utile per i test del login).

## Scelte da rivedere insieme
- **La password del seed si chiede a terminale** (due volte), come quella di `crea-utente`: niente password nel codice, negli argomenti o in una variabile nuova di `.env` (constitution §3). Se serve un seed non interattivo (E2E, demo) si aggiunge una variabile con un task della corsia 0.
- **Il seed scrive gli utenti direttamente**, senza `crea_utente()`: quella funzione è uno stub fino a T1-13 e il seed deve funzionare già ora. La docstring di `crea_utente()` dice ancora "e dal seed": si può far passare il seed dal service quando T1-13 è su `main`.
- **`crea-utente` funziona da T1-13**: fino ad allora il service solleva `NotImplementedError`. Qui è provato con un service finto.
- **`profilo_bottega.orari` resta vuoto nel seed**: plan §2 non ne fissa la forma.
- **Email del seed su `example.com`**: i domini `.test` vengono rifiutati da alcuni validatori di email.

## Documenti aggiornati
- `docs/agenti/tasks.md`: casella di T1-06 spuntata.
- `README.md`: comando del seed.
- Nessuna variabile nuova in `.env.example`.

## Come si prova
Da `backend/`, con `.venv` attivo e `.env` compilato:

```bash
alembic upgrade head && pytest && black --check .
python -m app.cli seed
```

Nessuna libreria nuova (solo libreria standard: `hashlib`, `hmac`, `secrets`, `argparse`, `getpass`), nessun segreto, nessuna chiamata ad AI, social o email.
