/**
 * Quale campagna apre la pagina dell'artigiano e quali restano nell'elenco
 * "Campagne passate" (spec §4). Si apre quella che chiede qualcosa: quella
 * in revisione con una richiesta del consorzio aperta (R-46), la bozza, poi una respinta o scaduta non ancora sostituita, poi quella in corso, poi
 * quella in lavorazione.
 */
import type { CampagnaElencoItem } from "../../../../api/campagne";

const IN_CORSO = ["attiva", "sospesa"];
const IN_LAVORAZIONE = [
  "inviata",
  "in_generazione",
  "generazione_fallita",
  "piano_da_rivedere",
  "in_revisione",
];

export interface Scelta {
  /** Le campagne della riga di scelta, nell'ordine in cui si aprono. */
  visibili: CampagnaElencoItem[];
  /** Chiuse e sostituite: stanno in fondo alla pagina. */
  passate: CampagnaElencoItem[];
  /** Quella che si apre da sola, se c'è una campagna da mostrare. */
  aperta: CampagnaElencoItem | null;
}

/** Più basso = chiede prima. `null` = è una campagna passata. */
function priorita(
  c: CampagnaElencoItem,
  lista: CampagnaElencoItem[],
): number | null {
  if (c.richiesta === "aperta") return -1;
  if (c.stato === "bozza") return 0;
  if (c.stato === "respinta" || c.stato === "scaduta") {
    // Resta finché l'artigiano crea una nuova campagna: l'ordine di creazione è l'id.
    return lista.some((x) => x.id > c.id) ? null : 1;
  }
  if (IN_CORSO.includes(c.stato)) return 2;
  if (IN_LAVORAZIONE.includes(c.stato)) return 3;
  return null;
}

export function scegli(lista: CampagnaElencoItem[]): Scelta {
  const conPriorita = lista.map((c) => ({ c, p: priorita(c, lista) }));
  const visibili = conPriorita
    .filter((x): x is { c: CampagnaElencoItem; p: number } => x.p !== null)
    .sort((a, b) => a.p - b.p || b.c.id - a.c.id)
    .map((x) => x.c);
  const passate = conPriorita
    .filter((x) => x.p === null)
    .map((x) => x.c)
    .sort((a, b) => b.id - a.id);
  return { visibili, passate, aperta: visibili[0] ?? null };
}
