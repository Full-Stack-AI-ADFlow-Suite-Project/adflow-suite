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
- [ ] La PR fa solo il suo task e non costruisce né estende ciò che `perimetro-mvp.md` segna *Togli*, *Congela* o *Roadmap*.
- [ ] Se la PR cambia composizione, `core/`, `alembic/`, `backend/requirements.txt` o un `domain.py`, lo dice nella descrizione.
- [ ] Ogni libreria nuova è in `requirements.txt`, con nome, motivo e licenza nella PR; nessun SQL scritto a mano sulle tabelle di un altro modulo e nessuna copia delle sue costanti (plan §6).
- [ ] Se tocchi il database: `alembic downgrade -1` e di nuovo `upgrade head` funzionano.
- [ ] `.env.example` e README aggiornati se serve; casella del task spuntata.
- [ ] Nella PR: cosa fa, quali CA copre, come si prova.
- [ ] Revisione di un collega; per i file comuni del referente. Unisce l'admin.

## 2. Test

- `tests/moduli/<modulo>/`: unitari, service e API del modulo. I dati degli altri moduli si creano con le loro fabbriche (plan §6); l'utente con `utente_di_prova(ruolo)`.
- `tests/adapters/`: senza rete.
- `tests/percorsi/`: più moduli insieme.
- `tests/test_confini.py`: regole di import di constitution §2.

Database pulito a ogni test con le fixture `db` e `client` di `tests/conftest.py` (plan §7); ora iniettata. `pytest` svuota `adflow_test` a ogni esecuzione. Copertura dei CA: `grep -r "test_ca" backend/tests`.

## 3. Prove a mano

- **Orologio di prova.** `OROLOGIO_GIORNI_AVANTI=12` in `backend/.env` manda avanti di 12 giorni l'ora di API e worker: si riavviano entrambi e si rifà l'accesso, perché le sessioni di prima risultano scadute. Le date che il database scrive da solo restano quelle vere. In produzione deve restare a 0: con un altro valore l'applicazione non parte.
- **AI e social.** `AI_PROVIDER=finto` e `SOCIAL_PROVIDER=finto` per provare senza servizi esterni; con `AI_PROVIDER=litellm` e una chiave non valida si prova l'errore `configurazione` (generazione fallita subito, con il motivo accanto a Riprova).
- **Email.** Le notifiche vanno al catcher locale (Mailpit, `SMTP_HOST` e `SMTP_PORT`).
- **Controllo visivo.** Le schermate si confrontano con le pagine statiche di `docs/pagine/`; lo fa una persona, con gli screenshot nella PR.

## 4. Chiusura dello sprint 3 (T3-07): il percorso della demo

Su `main` pulito, da database vuoto: comandi del §1 verdi, tutti i CA di spec §6 coperti, frontend sulle API vere al posto dei dati di esempio, poi il percorso qui sotto. Ciò che la chiusura trova rotto torna all'area che ci lavora come una PR piccola: la chiusura non corregge il codice degli altri.

È il percorso che si mostra nel pitch e che si registra nel video di riserva. Da database vuoto, con l'AI vera (`AI_PROVIDER=litellm`), Meta sulla pagina di prova (`SOCIAL_PROVIDER=meta`, tunnel acceso) e i dati di T3-06:

1. operatore: crea un artigiano nuovo, la password provvisoria si vede una volta (CA-79); l'artigiano entra e arriva al passo 1 del profilo;
2. artigiano della demo: Bentornato, campagna di 7 giorni su Facebook e Instagram che inizia tra 4 giorni, un gruppo di foto vere meno dei post chiesti; il passo 12 mostra quanti post avranno un'immagine AI (CA-54); invio senza dichiarazione → rifiutato; con la dichiarazione → inviata (CA-14);
3. generazione: post chiesti per canale, foto migliori per punteggio, i post scoperti con un'immagine AI e la dicitura (CA-17, CA-57, CA-80); costo della campagna in Vedi campagna (CA-82);
4. operatore, Vedi campagna: modifica un testo, ne rigenera un altro, cambia la foto di un post con un'altra del gruppo (CA-71); chiede all'artigiano la foto di un secondo post (CA-86); in una seconda finestra l'artigiano apre la pagina Campagna, vede la richiesta, carica la foto con la dichiarazione e invia (CA-87, CA-88, CA-90); l'operatore la usa con Cambia foto, approva; calendario per giorno (CA-56);
5. pubblicazione: con la data di test avanti, il worker pubblica sulla pagina di prova: il post si vede su Facebook e su Instagram, con la foto dritta, senza GPS e nel formato del canale (CA-81, CA-83). Se Instagram è rimasto simulato (D1), si mostra solo Facebook;
6. dopo l'approvazione: l'operatore modifica un post che esce tra più di 15 minuti, ne sposta un altro, ne annulla un terzo con la nota; sospende con una nota (l'artigiano vede «Pubblicazioni ferme») e riattiva (CA-84, CA-72, CA-85, CA-32);
7. controllo visivo: le schermate di login, profilo, campagna (anche con la richiesta del consorzio), Vedi campagna (in revisione e in campagna attiva) e nuovo artigiano confrontate con le pagine statiche aggiornate (T3-03, T3-60, corsia 8), con gli screenshot nella PR; le pagine dell'artigiano anche alle larghezze scelte in `brief-interfaccia.md` (S2);
8. respinta: una seconda campagna con foto non della bottega → respingi con motivo `foto`, nota e foto segnate; l'artigiano le rivede;
9. prove negative: inizio tra 1 giorno, durata di 3 giorni, un PDF come foto, canale non collegato, artigiano su una pagina dell'operatore (l'admin invece entra), rigenerazione su una campagna attiva, modifica di un post che esce entro 15 minuti, caricamento dell'artigiano dopo l'approvazione, approva con un post da rivedere, nuovo artigiano con un'email già usata → 409.

Il video di riserva si registra il giorno prima della consegna, con lo stesso percorso.
