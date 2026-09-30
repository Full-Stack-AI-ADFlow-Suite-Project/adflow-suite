# Canale umano · come funziona

La documentazione ha **due canali** (ADR-46).

| | Canale umano (`docs/umano/`) | Canale agenti (`AGENTS.md` + `docs/agenti/`) |
|---|---|---|
| Per chi | Persone del team | Agenti di coding |
| Chi lo mantiene | L'amministratore dei documenti | Un agente, su richiesta di assorbimento |
| Contenuto | Racconto, motivazioni, decisioni, diagrammi, pagine HTML, lavori di analisi | Solo ciò che serve per eseguire un task: regole, dati, API, task, verifica |
| Stile | Completo, con contesto | Breve, una sola fonte per ogni fatto |
| Se i due divergono | **Vale questo** | Si riallinea con un assorbimento |

## Cosa c'è qui

| File | Contenuto |
|---|---|
| `prodotto.md` | Cosa fa il prodotto e perché: flusso, regole, decisioni D con motivazioni, glossario, linea guida foto, storico |
| `tecnica.md` | Scelte tecniche con motivazioni, ambienti, architettura, aderenza flusso → componenti, rischi |
| `lavori.md` | Task di analisi senza codice (A-01…) |
| `ADR.md` · `ADR-archivio.md` | Indice breve delle decisioni in vigore · testo completo di tutte |
| `architettura/` | Diagrammi (sorgente `AdFlow-diagrammi.html`, strumenti in `strumenti/`) e pagine statiche HTML |

## Assorbimento: dal canale umano al canale agenti

Quando cambi qualcosa qui (una regola, un diagramma, una pagina statica, una decisione), chiedi a un agente di assorbirlo. Richiesta tipo:

> Assorbi nel canale agenti le modifiche del canale umano: *[cosa è cambiato, es. "prodotto.md §5.1 e AdFlow-scheda-bottega.html passo 11"]*.
> Aggiorna solo i file di `docs/agenti/` coinvolti, tenendoli brevi: niente motivazioni, una sola fonte per ogni fatto, i numeri solo nelle regole R-xx di `spec.md` §5. Aggiorna i criteri CA toccati e i task. Non modificare `docs/umano/`. Alla fine dimmi cosa hai cambiato e cosa non hai saputo tradurre.

Poi rileggi il diff del canale agenti prima di unirlo.

## Brief per i task ampi

Gli agenti leggono solo il canale agenti. Per un task che richiede più contesto (una schermata intera, un flusso nuovo), aggiungi al prompt un brief:

> Task *T2a-05*. Oltre ai documenti del canale agenti leggi anche: `docs/umano/architettura/AdFlow-scheda-bottega.html` (passi 1–9) e `docs/umano/prodotto.md` §3. Usali come riferimento per l'interfaccia; le regole restano quelle di `docs/agenti/`.

Brief corti e mirati: indica sezioni precise, non file interi, quando puoi.

## Regole per le persone

- **Una decisione nuova** = una riga in `ADR.md` e in `ADR-archivio.md`, poi l'aggiornamento di `prodotto.md` / `tecnica.md`, poi l'assorbimento.
- **Diagrammi**: si modificano solo in `architettura/AdFlow-diagrammi.html`; per rigenerare i PNG vedi `architettura/strumenti/LEGGIMI.md`.
- **Git**: mai su `main`; un branch e una PR per ogni modifica; la PR la rivede un'altra persona e la unisce l'admin.
- **Controllo visivo**: a fine task o sprint una persona confronta le schermate reali con le pagine statiche e mette gli screenshot nella PR.
