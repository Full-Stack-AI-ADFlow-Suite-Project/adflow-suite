/** Dati di esempio del modulo artigiani: canali e profilo (2a). */
import type { CanaleCollegato, ProfiloBottega } from "../artigiani";

export { USA_ESEMPI } from "./accesso";

export const canaliEsempio: CanaleCollegato[] = [
  { canale: "facebook", collegato: true },
  { canale: "instagram", collegato: true },
];

export const profiloEsempio: ProfiloBottega = {
  bottega: "Falegnameria Bianchi",
  referente: "Mario Bianchi",
  citta: "Bra (CN)",
  tipo_prodotto: "Legno e mobili",
  obiettivo: "Farmi conoscere",
  canali_preferiti: ["facebook", "instagram"],
  frequenza: "f3_4",
  foto_policy: { quantita_mese: "da5_a12" },
};
