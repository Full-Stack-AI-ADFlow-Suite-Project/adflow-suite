# Converge

## 1. Prima della PR

Si parte allineati: dalla radice `uv run python allinea.py` (aggiorna `main`, dipendenze e database, e dice se il tuo branch è indietro). Se `main` è andato avanti, portalo nel branch prima dei controlli: `git merge origin/main`.

```bash
# backend/ (PostgreSQL acceso, backend/.env compilato), un comando alla volta
uv run alembic upgrade head
uv run pytest
uv run black --check .
# frontend/
npm run lint
npm run build
```

GitHub rilancia i comandi del backend a ogni PR (`.github/workflows/backend.yml`): il controllo deve essere verde.

- [ ] "Fatto quando" del task vero; ogni CA citato ha un test `test_caNN_...` verde.
- [ ] Nessuna regola di `constitution.md` violata; `tests/test_confini.py` verde.
- [ ] La PR tocca solo ciò che è della corsia del task (`tasks.md`) e, dallo sprint 2a, solo i file della colonna "Tocca" del task, con i loro test. Tabelle, stati, funzioni di plan §6, `core/` e composizione solo nei task della corsia 0.
- [ ] Dopo aver portato `main` nel branch, le funzioni della corsia 0 sono identiche a `main`: `git diff origin/main -- <file>` non mostra righe tolte o cambiate dentro quelle funzioni.
- [ ] Nessuna libreria nuova fuori da `requirements.txt` su `main`; nessun SQL scritto a mano sulle tabelle di un altro modulo e nessuna copia delle sue costanti (plan §6).
- [ ] Se tocchi il database (solo corsia 0): `alembic downgrade -1` e di nuovo `upgrade head` funzionano.
- [ ] `.env.example` e README aggiornati se serve; casella del task spuntata.
- [ ] Nella PR: cosa fa, quali CA copre, come si prova.
- [ ] Revisione: corsia 0 approvata da tutto il team; corsie 1–5 riviste in gruppo. Unisce l'admin.

## 2. Test

- `tests/moduli/<modulo>/`: unitari, service e API del modulo. I dati degli altri moduli si creano con le loro fabbriche (plan §6); l'utente con `utente_di_prova(ruolo)`.
- `tests/adapters/`: senza rete.
- `tests/percorsi/`: più moduli insieme (corsia 0).
- `tests/test_confini.py`: regole di import di constitution §2.

Database pulito a ogni test con le fixture `db` e `client` di `tests/conftest.py` (plan §7); ora iniettata. `pytest` svuota `adflow_test` a ogni esecuzione. Copertura dei CA: `grep -r "test_ca" backend/tests`.

## 3. Chiusura dello sprint 1 (T1-07)

Su `main` pulito, da database vuoto: comandi del §1 verdi, tutti i CA con S = 1 coperti, frontend sulle API vere, poi a mano:

1. seed → avvio di API, worker, frontend;
2. artigiano: bozza di 7 giorni che inizia tra 4 giorni, su Facebook e Instagram, 4 foto in 2 gruppi con descrizione e una stella, invio;
3. la campagna passa a in_revisione (AI finta);
4. operatore: Vedi campagna, controlla il piano, le uscite con un post per canale, il numero di post per canale, uguale a quelli chiesti (R-05), nessuna foto due volte sullo stesso canale, la foto con la stella presente; un post con soli avvisi non blocca; approva;
5. data di test avanti (`OROLOGIO_GIORNI_AVANTI=12` in `backend/.env`, poi API e worker riavviati): i post si pubblicano (simulato), campagna conclusa;
6. prove negative: inizio tra 1 giorno, durata di 3 giorni, un PDF come foto, invio con 3 foto, canale non collegato, artigiano su pagina operatore (l'admin invece entra), errore di configurazione dell'AI (con `AI_PROVIDER=litellm`, finché il provider vero non c'è): generazione fallita subito, con il motivo accanto a Riprova;
7. piano debole: 4 settimane con 4 foto → `piano_da_rivedere`; Prosegui → in_revisione, con 12 post per canale: 4 con le foto e 8 cartoline (R-28).

Il controllo visivo contro le pagine statiche lo fa una persona (vedi gli appunti).

## 4. Chiusura degli sprint successivi (T2a-07, T2b-07, T3-07)

Come al §3: su `main` pulito, da database vuoto, comandi del §1 verdi, tutti i CA dello sprint coperti (`S` dello sprint in spec §6), frontend sulle API vere al posto dei dati di esempio, poi il percorso a mano.

Il percorso a mano di ogni sprint lo scrive qui il suo task di apertura (T2a-01, T2b-01, T3-01), insieme alle firme: così chi lavora sa fin dall'inizio che cosa verrà provato alla fine. Ogni percorso riparte da quello dello sprint prima e aggiunge le cose nuove e le loro prove negative.

Ciò che la chiusura trova rotto torna alla corsia proprietaria come una PR piccola: la chiusura non corregge il codice degli altri.

### Sprint 2a (T2a-07)

Da database vuoto, con AI e social finti:

1. seed → avvio di API, worker, frontend. Un artigiano nuovo (`crea-utente`, senza profilo) entra e arriva alla pagina Profilo, passo 1 (CA-05); al passo 9 con un obbligatorio vuoto non salva e lo indica (CA-07); completato, salva e arriva alla pagina Campagna. Non ha canali collegati (il collegamento è dello sprint 3): il resto si fa con l'artigiano del seed;
2. artigiano del seed: entra → Bentornato; "Va bene così" porta al passo 10 senza salvare il profilo, "Modifica" apre la pagina Profilo (CA-06);
3. passo 7 del profilo: carica il logo, lo sostituisce, lo rivede; archivio: un gruppo con la descrizione e 2 foto. Prove negative: logo che è un PDF, logo oltre 2 MB, logo con il lato corto sotto 300 px → rifiutati con il motivo (CA-78); foto d'archivio con il lato corto sotto 1080 px e gruppo senza descrizione → rifiutati;
4. campagna A, come al §3 passo 2 (7 giorni, inizio tra 4 giorni, Facebook e Instagram, 4 foto in 2 gruppi): esce e rientra → passo 10 con dati, canali, gruppi e foto (CA-08); cambia titolo e fine; una data di gruppo fuori dal nuovo periodo → rifiutata; invio → in_revisione; l'operatore approva; data di test avanti di 12 giorni → pubblicata e conclusa. Nel database ogni foto uscita porta canale e istante (`select id, pubblicata_su from foto`), le cartoline no (CA-76);
5. campagna B, 4 settimane con 4 foto nuove, inviata con l'errore di configurazione dell'AI del §3 passo 6 → generazione fallita; l'artigiano cambia il nome della bottega e il logo; torna l'AI finta, Riprova → in_revisione. Vedi campagna: 12 post per canale, con le foto nuove, le foto d'archivio mai uscite su quel canale (quelle del passo 3 e quelle di A che lì non sono uscite) e, per i post che mancano, cartoline con il logo e il nome di prima dell'invio (CA-16, CA-77); nessuna foto di A sul canale dove è appena uscita; nessuna foto due volte sullo stesso canale. L'operatore approva;
6. data di test avanti di 110 giorni: B si conclude. Campagna C, 4 settimane con 4 foto nuove → tra i riempitivi ci sono post `archivio` con le foto di A, uscite da più di 90 giorni, prima delle cartoline, e Vedi campagna li mostra come tali; una foto uscita su un canale da meno di 90 giorni lì non compare (CA-76);
7. prove negative: quelle del §3 passo 6, e in più modifica di una campagna non in bozza, archivio di un altro artigiano, eliminazione di una foto d'archivio già usata in un post → rifiutate.
