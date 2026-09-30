# Converge

## 1. Prima della PR
```bash
# backend/ (venv attivo, PostgreSQL acceso)
alembic upgrade head && pytest && black --check .
# frontend/
npm run lint && npm run build
```
- [ ] "Fatto quando" del task vero; ogni CA citato ha un test `test_caNN_...` verde.
- [ ] Nessuna regola di `constitution.md` violata.
- [ ] Se tocchi il database: `alembic downgrade -1` e di nuovo `upgrade head` funzionano.
- [ ] `.env.example` e README aggiornati se serve; casella del task spuntata.
- [ ] Nella PR: cosa fa, quali CA copre, come si prova.

## 2. Test
Livelli: `tests/unit` (domain, slot, validatore), `tests/services` (generazione, pubblicazione, scadenze, cicli), `tests/api` (permessi, 422 / 409, percorsi), `tests/adapters` (senza rete). Database pulito a ogni test; ora iniettata. Copertura dei CA: `grep -r "test_ca" backend/tests`.

## 3. Chiusura dello sprint 1
Su `main` pulito, da database vuoto: comandi del §1 verdi, tutti i CA con S = 1 coperti, poi a mano:
1. seed → avvio di API, worker, frontend;
2. artigiano: bozza che inizia tra 4 giorni, 3 foto in 2 gruppi con descrizione, invio;
3. la campagna passa a in_revisione (AI finta);
4. operatore: Vedi campagna, controlla numero di post, canali alternati, foto ≤ 2 usi; approva;
5. data di test avanti: i post si pubblicano (simulato), campagna conclusa;
6. prove negative: inizio tra 1 giorno, un PDF come foto, artigiano su pagina operatore.

Il controllo visivo contro le pagine statiche lo fa una persona, nel canale umano.
