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
| `architettura/` | Diagrammi 01–10 (sorgente `AdFlow-diagrammi.html`, PNG in `diagrammi/`, strumenti in `strumenti/`) |
| `pagine/` | Pagine statiche HTML di prova, una per ogni pagina del programma. Si parte da `pagine/index.html`: la mappa, con lo stato di ognuna (**approvata** o **bozza**). Solo le pagine approvate sono fonte di verità. Una domanda in fondo a una pagina resta aperta anche se la pagina è approvata, e la proposta di risposta vale solo quando viene confermata; quelle del 06/10 sono chiuse (ADR-89…110). Lo stile è in un solo file, `pagine/assets/adflow.css`, con le immagini di esempio in `pagine/assets/img/` (ADR-113): le pagine non hanno uno `<style>` proprio |
| `note-flusso.md` | Spiega il flusso dei diagrammi 01, 03, 04, 07, 09 e delle pagine statiche: fasi, stati, come l'AI sceglie le foto, scheda per canale, glossario, linea guida foto |
| `note-architettura.md` | Spiega i diagrammi 02, 05, 06, 08, 10: stack, ambienti, componenti, struttura a moduli del backend, corsie di lavoro |
| `lavori-aperti.md` | Tutto ciò che è da fare, decidere o verificare: analisi A-01…, domande, rischi, punti tecnici |
| `ADR.md` | Registro unico delle decisioni: una riga per decisione, con il perché e le alternative scartate; le sostituite in fondo |

**Ciò che sta solo nel canale agenti** (ADR-72): le regole R-xx e i criteri CA-xx (`spec.md` §5 e §6), tabelle, API e job (`plan.md`), l'albero delle cartelle (`constitution.md` §2), i task (`tasks.md`). Per questi il canale agenti è la fonte: le note li spiegano e rimandano lì, senza ricopiarli.

## Assorbimento: dagli appunti al canale agenti

Quando cambi qualcosa qui (una regola, un diagramma, una pagina statica, una decisione), chiedi a un agente di assorbirlo. Richiesta tipo:

> Assorbi nel canale agenti le modifiche degli appunti: *[cosa è cambiato, es. "note-flusso.md §5.1 e AdFlow-campagna.html passo 11"]*.
> Aggiorna solo i file di `docs/agenti/` coinvolti, tenendoli brevi: niente motivazioni, una sola fonte per ogni fatto, i numeri solo nelle regole R-xx di `spec.md` §5. Aggiorna i criteri CA toccati e i task. Non modificare `docs/appunti/`. Alla fine dimmi cosa hai cambiato e cosa non hai saputo tradurre.

Poi rileggi il diff del canale agenti prima di unirlo.

## Brief per i task ampi

Gli agenti leggono solo il loro canale. Per un task che richiede più contesto aggiungi al prompt un brief:

> Task *T2a-05*. Oltre al canale agenti leggi anche: `docs/appunti/pagine/AdFlow-profilo-bottega.html` (passi 1–9) e `docs/appunti/note-flusso.md` §3. Usali come riferimento per l'interfaccia; le regole restano quelle di `docs/agenti/`.

Brief corti e mirati: sezioni precise, non file interi, quando puoi.

## Regole per le persone

- **Un punto aperto che si chiude**: il risultato va nelle note o in `ADR.md`, il punto esce da `lavori-aperti.md`, poi l'assorbimento.
- **Una decisione nuova**: una riga in `ADR.md`, con il perché e le alternative scartate (quella che cambia scende tra le sostituite), poi l'assorbimento. Nelle note va solo ciò che serve a spiegare il flusso.
- **Pagine statiche**: una pagina nuova nasce in `pagine/` come bozza, con le domande aperte in fondo. Parte da una pagina esistente: stessa cornice (barra laterale, barra in alto) e componenti di `assets/adflow.css`, senza `<style>` nella pagina; le note che non fanno parte della schermata vanno in fondo, nel blocco `note-pagina`. Lo stato si scrive in due posti: nella mappa `pagine/index.html` e nel riquadro della barra in alto della pagina. Diventa approvata con una riga in `ADR.md`; solo allora si assorbe e si dà in un brief senza avvertenze. Una domanda aperta che si chiude esce dalla pagina ed entra nelle note o in `ADR.md`. Una versione superata si elimina: non c'è un archivio.
- **Diagrammi**: si modificano solo in `architettura/AdFlow-diagrammi.html`; per rigenerare i PNG vedi `architettura/strumenti/LEGGIMI.md`.
- **Git**: mai su `main`; un branch e una PR per ogni modifica; la unisce l'admin. Codice: la corsia 0 si approva tutti insieme, le corsie 1–5 si rivedono in gruppo (note-architettura.md §3.9). Documenti: li rivede un'altra persona.
- **Controllo visivo**: a fine task o sprint una persona confronta le schermate reali con le pagine statiche e mette gli screenshot nella PR.
