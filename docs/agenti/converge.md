# Converge

## 1. Prima della PR
```bash
# backend/ (venv attivo, PostgreSQL acceso)
alembic upgrade head && pytest && black --check .
# frontend/
npm run lint && npm run build
```
- [ ] "Fatto quando" del task vero; ogni CA citato ha un test `test_caNN_...` verde.
- [ ] Nessuna regola di `constitution.md` violata; `tests/test_confini.py` verde.
- [ ] La PR tocca solo ciò che è della corsia del task (`tasks.md`). Tabelle, stati, funzioni di plan §6, `core/` e composizione solo nei task della corsia 0.
- [ ] Se tocchi il database (solo corsia 0): `alembic downgrade -1` e di nuovo `upgrade head` funzionano.
- [ ] `.env.example` e README aggiornati se serve; casella del task spuntata.
- [ ] Nella PR: cosa fa, quali CA copre, come si prova.
- [ ] Revisione: corsia 0 approvata da tutto il team; corsie 1–5 riviste in gruppo. Unisce l'admin.

## 2. Test
- `tests/moduli/<modulo>/`: unitari, service e API del modulo. I dati degli altri moduli si creano con le loro fabbriche (plan §6); l'utente con `utente_di_prova(ruolo)`.
- `tests/adapters/`: senza rete.
- `tests/percorsi/`: più moduli insieme (corsia 0).
- `tests/test_confini.py`: regole di import di constitution §2.

Database pulito a ogni test; ora iniettata. Copertura dei CA: `grep -r "test_ca" backend/tests`.

## 3. Chiusura dello sprint 1 (T1-07)
Su `main` pulito, da database vuoto: comandi del §1 verdi, tutti i CA con S = 1 coperti, frontend sulle API vere, poi a mano:
1. seed → avvio di API, worker, frontend;
2. artigiano: bozza che inizia tra 4 giorni, 3 foto in 2 gruppi con descrizione, invio;
3. la campagna passa a in_revisione (AI finta);
4. operatore: Vedi campagna, controlla numero di post, canali alternati, foto ≤ 2 usi; approva;
5. data di test avanti: i post si pubblicano (simulato), campagna conclusa;
6. prove negative: inizio tra 1 giorno, un PDF come foto, artigiano su pagina operatore.

Il controllo visivo contro le pagine statiche lo fa una persona (vedi gli appunti).
