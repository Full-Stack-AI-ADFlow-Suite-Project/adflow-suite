# Appunti · come funzionano

La documentazione ha **due canali** (ADR-46).

| | Appunti (`docs/appunti/`) | Agenti (`AGENTS.md` + `docs/agenti/`) |
|---|---|---|
| Cosa sono | Riflessioni personali, discussioni con i colleghi, lavoro con l'AI: materiale in continua rimodulazione | Solo ciò che serve per eseguire un task: regole, dati, API, task, verifica |
| Chi li mantiene | L'amministratore dei documenti | Un agente, su richiesta di assorbimento |
| Stile | Completo, con il perché | Breve, una sola fonte per ogni fatto |
| Se divergono | **Valgono gli appunti** | Si riallineano con un assorbimento |

## Cosa c'è qui

| File | Contenuto |
|---|---|
| `architettura/` | Diagrammi 01–10 (sorgente `AdFlow-diagrammi.html`, PNG in `diagrammi/`, strumenti in `strumenti/`) e pagine statiche HTML (profilo bottega, campagna, pagina operatore) |
| `note-flusso.md` | Spiega il flusso dei diagrammi 01, 03, 04, 07, 09 e delle pagine statiche: fasi, regole, decisioni D con il perché, glossario, linea guida foto |
| `note-architettura.md` | Spiega i diagrammi 02, 05, 06, 08, 10: stack, ambienti, componenti, struttura a moduli del backend, corsie di lavoro, scelte tecniche con il perché |
| `lavori-aperti.md` | Tutto ciò che è da fare, decidere o verificare: analisi A-01…, domande, rischi, punti tecnici |
| `ADR.md` | Indice delle decisioni in vigore, con le sostituite in fondo |

## Assorbimento: dagli appunti al canale agenti

Quando cambi qualcosa qui (una regola, un diagramma, una pagina statica, una decisione), chiedi a un agente di assorbirlo. Richiesta tipo:

> Assorbi nel canale agenti le modifiche degli appunti: *[cosa è cambiato, es. "note-flusso.md §5.1 e AdFlow-campagna.html passo 11"]*.
> Aggiorna solo i file di `docs/agenti/` coinvolti, tenendoli brevi: niente motivazioni, una sola fonte per ogni fatto, i numeri solo nelle regole R-xx di `spec.md` §5. Aggiorna i criteri CA toccati e i task. Non modificare `docs/appunti/`. Alla fine dimmi cosa hai cambiato e cosa non hai saputo tradurre.

Poi rileggi il diff del canale agenti prima di unirlo.

## Brief per i task ampi

Gli agenti leggono solo il loro canale. Per un task che richiede più contesto aggiungi al prompt un brief:

> Task *T2a-05*. Oltre al canale agenti leggi anche: `docs/appunti/architettura/AdFlow-profilo-bottega.html` (passi 1–9) e `docs/appunti/note-flusso.md` §3. Usali come riferimento per l'interfaccia; le regole restano quelle di `docs/agenti/`.

Brief corti e mirati: sezioni precise, non file interi, quando puoi.

## Regole per le persone

- **Un punto aperto che si chiude**: il risultato va nelle note o in `ADR.md`, il punto esce da `lavori-aperti.md`, poi l'assorbimento.
- **Una decisione nuova**: una riga in `ADR.md` (quella che cambia scende tra le sostituite), il perché nelle note, poi l'assorbimento.
- **Diagrammi**: si modificano solo in `architettura/AdFlow-diagrammi.html`; per rigenerare i PNG vedi `architettura/strumenti/LEGGIMI.md`.
- **Git**: mai su `main`; un branch e una PR per ogni modifica; la unisce l'admin. Codice: la corsia 0 si approva tutti insieme, le corsie 1–5 si rivedono in gruppo (note-architettura.md §3.9). Documenti: li rivede un'altra persona.
- **Controllo visivo**: a fine task o sprint una persona confronta le schermate reali con le pagine statiche e mette gli screenshot nella PR.
