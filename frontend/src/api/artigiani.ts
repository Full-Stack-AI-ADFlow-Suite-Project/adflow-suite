/**
 * Modulo artigiani (plan §3): GET /canali per gli account collegati.
 * Il profilo (GET /profilo) è della 2a: fino ad allora solo dati di esempio.
 */
import { richiesta } from "./http";
import { canaliEsempio, profiloEsempio, USA_ESEMPI } from "./esempi/artigiani";

/** CanaleCollegato di artigiani/schemas.py. */
export interface CanaleCollegato {
  canale: string;
  collegato: boolean;
}

/** Riassunto del profilo per il Bentornato e il riepilogo (2a: GET /profilo). */
export interface ProfiloBottega {
  bottega: string;
  referente: string;
  citta: string;
  tipo_prodotto: string;
  obiettivo: string;
  canali_preferiti: string[];
  frequenza: string;
  foto_policy: { quantita_mese?: string };
}

export function canali(): Promise<CanaleCollegato[]> {
  if (USA_ESEMPI) return Promise.resolve(canaliEsempio);
  return richiesta<CanaleCollegato[]>("GET", "/canali");
}

export function profilo(): Promise<ProfiloBottega> {
  if (USA_ESEMPI) return Promise.resolve(profiloEsempio);
  return richiesta<ProfiloBottega>("GET", "/profilo");
}
