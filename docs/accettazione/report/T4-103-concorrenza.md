# T4-103 · Concorrenza

Copre §7.3 di `accettazione-post-mvp.md` e la costituzione §1. Prove in
`backend/tests/accettazione/concorrenza/`: una sessione e una connessione
PostgreSQL per thread, `threading.Barrier` per partire insieme, commit veri
(le prove poi si puliscono da sole). Comando: da `backend/`,
`uv run pytest tests/accettazione/concorrenza -q`. Esito: **9 passed, 4 xfailed**.

Le staccionate:
- **verdi** → ripetute 50 volte senza fallire (le due prove di invio 20 volte);
- **rosse deterministiche** (50/50) → `xfail(strict=True)`;
- **rosse intermittenti** → `xfail(strict=False)` con la percentuale su 50
  ripetizioni (regola del brief T4-103).

## 1. Riepilogo degli scenari

| Scenario | Ripetizioni | Esito | Rilievo |
|---|---|---|---|
| Due operatori approvano la stessa campagna (R-03) | 50 | **entrambe passano 49/50** | RL-021 |
| Approva e respingi in parallelo | 50 | **entrambe passano 49/50** | RL-022 |
| Approva e richiesta all'artigiano in parallelo | 50 | verde: l'approvazione non è mai fermata | — |
| La stessa foto su due post dello stesso canale (§1.9) | 50 | **entrambe passano 50/50** | RL-023 |
| Due rigenerazioni dello stesso post insieme (R-04, R-31) | 50 | **entrambe partono 49/50** | RL-024 |
| Invio della stessa bozza da due schede | 50 | verde: un solo invio | — |
| Campagne sovrapposte: invio della bozza mentre si sposta un post dell'altra | 20 | verde: nessuno dei due si blocca | — |
| Due botteghe diverse inviano insieme | 20 | verde: entrambe passano | — |
| Due operatori votano la stessa chiamata AI | 50 | verde: due righe, nessun voto perso | — |
| Lo stesso operatore vota due volte insieme | 50 | verde: due righe (§1.2) | — |
| Due worker (tick) pubblicano lo stesso post | 50 | verde: **una sola chiamata al social** (§1.7) | — |
| Annulla un post dovuto mentre il tick lo pubblica | 50 | verde: annulla 409, il post esce una volta | — |
| Annulla un post che esce tra 20 minuti, tick in parallelo | 50 | verde: annulla passa, il tick non tocca nulla | — |

## 2. R-03 confermato: approvazione doppia (RL-021)

`test_approvazione.py::test_due_operatori_approvano_insieme` — due operatori
chiamano `revisione.service.approva()` sulla stessa campagna `in_revisione`,
ognuno nella sua transazione, sbloccati insieme. In **49 ripetizioni su 50
passano entrambe**: la campagna prende due decisioni `approvata`, i post due
righe di `approvazione`, e lo stato finale è scritto due volte.

Causa: `approva()` legge la campagna **senza bloccarla** (`db.get(Campagna)`),
controlla `stato == "in_revisione"` in Python, poi scrive; con READ COMMITTED
entrambe le transazioni leggono lo stato vecchio. `Approvazione` non ha
vincoli unici. Correzione proposta, **non applicata**: `SELECT … FOR UPDATE`
sulla campagna all'inizio di `approva()` (oppure
`UPDATE campagna SET stato = 'attiva' WHERE id = :id AND stato = 'in_revisione'`
e 409 se non aggiorna righe). Test in `xfail(strict=False)` (1 caso su 50 passa
per caso: è intermittente, come da regola).

## 3. Approva e respingi insieme (RL-022)

`test_interventi.py::test_approva_e_respingi_insieme` — 49/50 volte passano
entrambe: la campagna finisce con una decisione `approvata` **e** una
`respinta`, e con i post in parte `approvato` e in parte `scartato`. Stessa
radice di RL-021 (nessun blocco della riga in `approva()`/`respingi()`).
Correzione proposta: la stessa di RL-021, estesa a `respingi()`. Test in
`xfail(strict=False)`.

## 4. Costituzione §1.9 violata: la stessa foto su due post (RL-023)

`test_interventi.py::test_cambia_foto_insieme_sulla_stessa_foto` — due
operatori cambiano foto su due post **instagram** della stessa campagna
scegliendo **la stessa foto libera**. Entrambi i cambi passano in **50
ripetizioni su 50**: la stessa foto finisce nella versione corrente di due
post dello stesso canale, che è esattamente ciò che la costituzione §1.9
vieta (e R-36 ripete: «non è nella versione corrente di un altro post della
campagna sullo stesso canale»).

Causa: `contenuti.cambia_foto()` controlla l'elenco delle foto possibili
leggendo le versioni correnti, senza bloccare nulla; le due transazioni non
vedono la scrittura dell'altra. Correzione proposta, **non applicata**: blocco
della foto scelta (`SELECT … FOR UPDATE` sulla riga `foto`) oppure un vincolo
che escluda la stessa foto in due versioni correnti dello stesso canale, con
409 al secondo. Test in `xfail(strict=True)` (50/50 è deterministico).

## 5. R-04 e R-31: due rigenerazioni insieme (RL-024)

`test_interventi.py::test_rigenerazioni_insieme_col_limite_a_tre` — un post
con 2 rigenerazioni già fatte (limite 3, R-04) riceve due accensioni in
parallelo. In **49/50** partono entrambe: l'intervento «in corso» di R-31 non
ferma la seconda, e due job di rigenerazione vengono accodati sullo stesso
post. Il contatore resta sotto il limite solo perché in questa prova i job non
girano: in produzione le due esecuzioni scriverebbero due versioni e il
contatore arriverebbe a 4 su un massimo di 3.

Correzione proposta, **non applicata**: blocco della riga del post
all'accensione (`with_for_update` in `accendi_intervento`) e controllo del
contatore dentro la stessa transazione. R-04 è **confermato** come rischio:
il limite non è atomico. Test in `xfail(strict=False)`.

## 6. Scenari verdi (nessun rilievo)

- **Invio da due schede** (`test_invio.py`): un solo invio passa; l'altro trova
  la campagna non più in bozza (StatoNonValido). 50/50 verde.
- **Campagne sovrapposte** (`test_sovrapposte.py`): l'invio della bozza e lo
  spostamento di un post della campagna attiva non si bloccano; due botteghe
  inviano insieme senza interferenze. Il rispetto degli **orari occupati**
  (R-25, CA-115) si gioca nel pianificatore con l'AI e la coda: **non provato**
  a questo livello (il provider finto non pianifica), vedi §7.
- **Voti** (`test_voto.py`): due voti in parallelo sulla stessa chiamata → due
  righe `valutazione_ai`, nessun voto perso, nemmeno per lo stesso operatore
  (R-50, §1.2).
- **Pubblicazione** (`test_pubblicazione.py`):
  - **due worker sullo stesso post**: il social finto riceve **una sola
    chiamata** in 50/50 — la difesa è l'indice unico `(post_id, n_tentativo)`
    sulla riga del tentativo, che fa fallire il secondo `INSERT` **prima** della
    chiamata al social. Il secondo tick prende un `IntegrityError` (non un 409
    ordinato: è un guasto del job, non un doppio post);
  - **annulla mentre il tick pubblica** un post dovuto: annulla prende 409
    (esce entro 15 minuti, R-16), il post esce una volta sola;
  - **annulla un post che esce tra 20 minuti**: annulla passa, il tick non lo
    tocca.
  Nessun doppio post: il blocco assoluto della §8 («lo stesso post pubblicato
  due volte») **non si materializza** in questa prova.

## 7. Che cosa non si è potuto provare

- **Orari occupati con il piano in concorrenza** (R-25, CA-115): servirebbe il
  job di generazione con il provider finto e la coda reale, non solo il
  service. Nel report è `non provato` con il motivo; CA-115 resta coperto dal
  test funzionale.
- **Cambio d'ora** (28/03/2027): fuori portata qui, come dichiarato nella §2
  del documento di accettazione.
