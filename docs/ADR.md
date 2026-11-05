# Decisioni · AdFlow Suite

Versione corta (ADR-122): le decisioni che spiegano il prodotto com'è, una frase ciascuna, con il perché. Il registro completo, con le alternative scartate, gli alias D-xx e le decisioni sostituite, è in `docs/archivio/completi/ADR.md`: lì si legge ogni ID citato qui o nel codice. Una decisione nuova è una riga nuova in fondo alla sua sezione.

## Architettura
| ID | Decisione · perché |
|---|---|
| 01, 49 | Monolite a moduli di dominio (accesso, notifiche, artigiani, campagne, contenuti, revisione, pubblicazione) più un worker, stesso codice; un modulo usa solo i precedenti e solo dal loro `service`, controllato da un test. Un deploy, cinque persone in cartelle diverse. |
| 02, 04, 10 | Python 3.11, FastAPI, SQLAlchemy 2 + Alembic, PostgreSQL 16; React + Vite + TypeScript + Mantine; un monorepo. Ecosistema AI ricco, componenti pronti, una modifica in un commit. |
| 03 | Coda e job con Procrastinate dentro PostgreSQL: nessun servizio in più, retry e lock inclusi. |
| 05 | Sessione lato server con cookie httpOnly: più semplice e sicura di JWT per una SPA sullo stesso dominio. |
| 06, 07 | AI dietro un adattatore con LiteLLM (provider finto nei test) e social dietro un adattatore: nessun vincolo a un fornitore, test senza rete. |
| 08, 09 | Un solo consorzio; prima in locale, poi Docker su un server proprio. |
| 11 | Test unitari e di API su PostgreSQL reale, un solo end-to-end. |

## Dati e principi
| ID | Decisione · perché |
|---|---|
| 12, 24 | Ogni intervento crea una versione, nulla si cancella; all'invio la campagna salva la fotografia del profilo. Tracciabilità: l'operatore vede ciò che ha ricevuto l'AI. |
| 13, 121 | Pubblicazione con il tentativo registrato prima della chiamata, e al massimo una volta: dopo un esito sconosciuto il post è `fallito` e l'operatore lo riprogramma. Un post non uscito si rimedia, uno uscito due volte no. |
| 37 | Ogni decisione sulla campagna è una riga di `decisione_campagna`: la storia non dipende dallo stato. |

## Campagna e foto
| ID | Decisione · perché |
|---|---|
| 47, 16 | Due pagine per l'artigiano, Profilo (passi 1–9) e Campagna (passi 10–12), con il Bentornato ai rientri: non si riscrive tutto ogni volta. |
| 35, 25, 119 | Inizio almeno 3 giorni dopo, durata fino a 3 mesi, una sola bozza; dall'ADR-119 campagne sovrapposte ammesse con un avviso. Tempo per generare e rivedere. |
| 57, 58 | Canali dichiarati sulla campagna, solo se collegati; frequenza per canale ("3 a settimana" su due canali sono 6 post). |
| 59, 74 | Foto a gruppi con una descrizione e una data facoltativa, che è un'indicazione per l'AI e non un vincolo. |
| 28 | Al caricamento si controllano formato, peso e lato corto; la qualità la giudica l'AI e la foto non idonea resta fuori, con il motivo. |
| 70, 73 | Avvisi all'artigiano prima dell'invio, calcolati dal server e senza blocco: può aggiungere foto prima di una respinta. |
| 81 | La frequenza è un impegno: escono sempre i post scelti, anche con poche foto. La presenza costante è lo scopo del prodotto. |

## Generazione
| ID | Decisione · perché |
|---|---|
| 29, 66 | La generazione parte da sola all'invio, a tappe salvate: un errore non fa rifare e ripagare tutto. |
| 62, 63 | Un piano editoriale dell'AI (prompt da social media manager) a uscite: un tema, un gruppo, un post per canale. L'operatore vede perché esistono i post. |
| 69, 91 | Una scheda per canale e un validatore a due livelli: il blocco ferma ciò che non può uscire, l'avviso lascia lo stile all'operatore. |
| 14, 98 | Errori dell'AI con un tipo: temporanei ritentati 3 volte, configurazione subito ferma, una foto o un testo rifiutati non fermano la campagna. L'operatore sa se riprovare serve. |
| 114 | Nell'MVP le foto che mancano diventano immagini AI quadrate, le stesse sui due canali; il codice preseleziona le foto migliori per punteggio. |

## Revisione e pubblicazione
| ID | Decisione · perché |
|---|---|
| 30, 67, 68 | Si approva o si respinge la campagna intera; l'artigiano vede il piano solo dopo l'approvazione. Una decisione per campagna, stato sempre chiaro. |
| 33, 40 | Respingi chiude la campagna con motivo (`foto` con le foto da rifare, o `altro`) e nota; l'artigiano ne fa una nuova. |
| 89, 90, 99 | In revisione un post non si toglie: si sistema con modifica a mano, rigenerazione, cambia foto, sposta. Il numero di post scelto resta. |
| 93 | Intervento in corso con un limite di 10 minuti: un worker fermo non blocca l'approvazione per sempre. |
| 95 | Scadenza morbida: scade il singolo post, la campagna solo sotto la metà dei post chiesti. Il ritardo dell'operatore non costa tutta la campagna. |
| 96, 97 | Sospendi, riattiva (gli arretrati si scelgono), annulla; un post fallito si riprogramma. |
| 101, 106 | Si decide solo in Vedi campagna, che si apre in ogni stato dopo l'invio; Campagne da approvare ordinate per "entro quando". |
| 77, 78 | Notifiche agli operatori per campagna pronta, generazione fallita e post fallito; il piano approvato si legge dal calendario della campagna. |
| 116 | Dopo l'approvazione l'operatore corregge il singolo post (modifica, cambia foto, sposta, annulla) senza AI; in revisione può chiedere all'artigiano una risposta e fino a 3 foto. Un errore si corregge senza buttare la campagna. |
| 119 | Rigenera immagine, Cambia immagine dalla campagna e dall'archivio, «Rifai il post», storico dell'AI con i voti, foto da 4:5 a 1,91:1 senza deformazioni. Nate provando l'MVP. |

## Accesso e pagine
| ID | Decisione · perché |
|---|---|
| 102 | Sessione che scade senza uso (7 giorni artigiano, 12 ore operatore); l'admin vale come operatore; nessun recupero password per email. |
| 103 | Nuovo artigiano con una password provvisoria mostrata una sola volta: nessuna password viaggia per email. |
| 104, 117 | Pagine dell'artigiano (Ingresso, Campagne, Calendario, Archivio foto, Profilo) e dell'operatore (Da approvare, Artigiani, Calendario, Storico AI): ognuno trova in un posto ciò che lo riguarda. |
| 113, 118 | Uno stile unico per app e pagine statiche; le scelte visive le fa chi sviluppa con una guida e criteri (WCAG AA, telefono). |

## Perimetro e processo
| ID | Decisione · perché |
|---|---|
| 114 | Perimetro MVP (`docs/archivio/perimetro-mvp.md`): consegna il 6/11/2026, codice bloccato il 30/10; AI vera, pubblicazione su una pagina di prova Meta; ciò che resta fuori va in `docs/ROADMAP.md` o è congelato. Supera, per l'MVP, le decisioni che non tornano. |
| 115, 122 | Un solo archivio, `docs/archivio/`, per ciò che non fa testo; a sprint chiusi ci vanno brief, report, QA, i testi completi di ADR, spec e plan e, dopo il pitch, pagine statiche e pitch. |
| 116…119 | Corsie 6–9: interventi e richiesta, pagine e calendario, interfaccia, richieste dopo la prova. |
| 120 | Sprint 4: simulazione di accettazione, con rilievi e non correzioni (esito in `docs/archivio/accettazione/sintesi.md`). |
| 121 | Sprint 5: corsia rapida, correzioni dei rilievi più gravi, perimetro invariato. |
| 123 | Tutto chiuso dal 5/11/2026: sprint conclusi, nessuna data di consegna, documentazione come fonte di conoscenza passiva; i lavori si aprono uno alla volta su scelta del team, e ciò che serve per presentare il progetto è nella corsia della presentazione di `tasks.md`. La consegna è stata spostata senza una data nuova. Nell'archivio vanno anche pagine statiche, perimetro, converge, sicurezza, sintesi dell'accettazione e il video di T3-07; comandi, demo e produzione stanno in `backend/README.md`. |

## Superate dal perimetro MVP
Restano nel registro completo per la storia: ritocco AI delle foto e cicli dei ritocchi (41, 43, 100), minimi di foto e capacità calcolata (60, 64, 75), immagini AI su richiesta, cartoline e riempitivi a tappe (61, 80, 82, 84, 85, 86, 88), piano debole (65, 79), archivio come rimpiazzo (83), spunta e nota interna (92, 94), togli canale (67, 76), ingresso dell'operatore, anagrafica e metriche (105, 107, 108, 109), e le decisioni sulle pagine statiche e sui documenti (53–56, 71–73, 87, 110–112). Dettagli minori e di processo: 18, 19, 21, 27, 38 (profilo e anagrafica), 44 (superata da 116), 45, 50, 51 (avvio del repository e corsie degli sprint 1–2). Le sostituite (15, 17, 20, 22, 23, 26, 31, 32, 34, 36, 39, 42, 46, 48, 52) sono in fondo al registro completo.
