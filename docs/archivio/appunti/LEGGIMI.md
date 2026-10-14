> **Archiviato il 14/10/2026 (ADR-115).** Questa cartella era `docs/appunti/`: `pagine/` oggi è `docs/pagine/` e `ADR.md` è `docs/ADR.md`; il resto è qui. Il testo sotto descrive la cartella com'era.

# Appunti · archivio

Dal 13/10/2026 gli appunti sono un **archivio** (ADR-114, decisione F4): non fanno più testo e non si assorbono più nel canale agenti. Fanno eccezione le pagine statiche, che T3-03 aggiorna all'MVP e che tornano il riferimento per l'interfaccia. Vale soltanto `docs/agenti/`, e lì vale prima di tutto `perimetro-mvp.md`. Ciò che non entra nell'MVP è in `docs/ROADMAP.md`.

Gli appunti restano utili come materiale per i deliverable della traccia (analisi, architettura, pitch): diagrammi, pagine statiche e motivazioni delle decisioni.

## Cosa c'è qui

| File | Contenuto | Nell'MVP |
|---|---|---|
| `ADR.md` | Registro delle decisioni, con il perché e le alternative scartate | Resta il registro: una riga nuova solo se cambia il perimetro dell'MVP |
| `architettura/` | Diagrammi 01–10 (sorgente `AdFlow-diagrammi.html`, PNG in `diagrammi/`, strumenti in `strumenti/`) | Materiale per G2 e per il pitch; dove non tornano con `perimetro-mvp.md` vale quella |
| `pagine/` | Pagine statiche di prova, mappa in `pagine/index.html` | Aggiornate all'MVP con T3-03 (cosa cambia: `docs/agenti/perimetro-mvp.md`, sezione Pagine statiche); riferimento per l'interfaccia. Le pagine fuori MVP restano, segnate come roadmap; la pagina delle metriche va nel pitch come anteprima |
| `note-flusso.md`, `note-architettura.md` | Il perché del flusso e dell'architettura | Materiale per G1 e G2 |
| `lavori-aperti.md` | Punti aperti fino al 12/10 | Chiuso: i punti sono diventati task dello sprint MVP o voci della roadmap |

## Regole

- Gli appunti non si modificano, salvo `ADR.md` per una decisione che cambia il perimetro dell'MVP e le pagine statiche con T3-03.
- Una decisione nuova: una riga in `ADR.md` con il perché e le alternative scartate, poi lo stesso cambiamento in `docs/agenti/` nella stessa PR.
- Git: mai su `main`; un branch e una PR per ogni modifica, rivista da un collega; la unisce l'admin.
