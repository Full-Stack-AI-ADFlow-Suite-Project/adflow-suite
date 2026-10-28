/**
 * Storico delle chiamate all'AI (brief-richieste §1.3, spec R-50).
 * I tipi rispecchiano backend/app/moduli/contenuti/schemas.py. Finché
 * `GET /storico-ai` (T3-917) non è su `main` la pagina legge i dati di esempio:
 * quando arriva basta portare `ENDPOINT_PRONTO` a `true`.
 */
import { richiesta } from "./http";
import { esempiStorico } from "./esempi/storico";

const ENDPOINT_PRONTO = false;

export type TipoChiamata = "analisi" | "piano" | "testo" | "immagine";

export interface ChiamataAIRiga {
  id: number;
  creata_il: string;
  campagna_id: number;
  campagna_titolo: string;
  bottega: string | null;
  post_id: number | null;
  foto_id: number | null;
  tipo: TipoChiamata;
  modello_ai: string;
  versione_prompt: string | null;
  /** "ok" o il tipo dell'errore (ESITI_CHIAMATA_AI). */
  esito: string;
  durata_ms: number | null;
  /** Decimal: arriva come stringa. */
  costo_usd: string;
  token_ingresso: number | null;
  token_uscita: number | null;
  voto_medio: number | null;
}

export interface ValutazioneAI {
  id: number;
  utente_nome: string;
  voto: number;
  nota: string | null;
  creata_il: string;
}

export interface ChiamataAIDettaglio extends ChiamataAIRiga {
  richiesta: Record<string, unknown> | null;
  risposta: string | null;
  errore: string | null;
  tentativo: number | null;
  valutazioni: ValutazioneAI[];
}

export interface PaginaChiamateAI {
  voci: ChiamataAIRiga[];
  totale: number;
  pagina: number;
  per_pagina: number;
}

export interface FiltriStorico {
  campagna_id?: number;
  tipo?: string;
  modello?: string;
  versione_prompt?: string;
  esito?: string;
  /** AAAA-MM-GG, compreso. */
  dal?: string;
  al?: string;
}

function querystring(filtri: FiltriStorico, pagina?: number): string {
  const q = new URLSearchParams();
  for (const [chiave, valore] of Object.entries(filtri))
    if (valore !== undefined && valore !== "") q.set(chiave, String(valore));
  if (pagina !== undefined) q.set("pagina", String(pagina));
  const testo = q.toString();
  return testo ? `?${testo}` : "";
}

export function elencoChiamate(
  filtri: FiltriStorico,
  pagina: number,
): Promise<PaginaChiamateAI> {
  if (!ENDPOINT_PRONTO) return esempiStorico.elenco(filtri, pagina);
  return richiesta("GET", `/storico-ai${querystring(filtri, pagina)}`);
}

export function dettaglioChiamata(id: number): Promise<ChiamataAIDettaglio> {
  if (!ENDPOINT_PRONTO) return esempiStorico.dettaglio(id);
  return richiesta("GET", `/storico-ai/${id}`);
}

/** Valori ammessi dai filtri di esito (domain.ESITI_CHIAMATA_AI). */
export const ESITI = [
  "ok",
  "temporaneo",
  "richiesta",
  "rifiuto",
  "risposta",
  "configurazione",
] as const;

export const TIPI: { value: TipoChiamata; label: string }[] = [
  { value: "analisi", label: "Analisi delle foto" },
  { value: "piano", label: "Piano della campagna" },
  { value: "testo", label: "Testo di un post" },
  { value: "immagine", label: "Immagine AI" },
];

const ETICHETTA_ESITO: Record<string, string> = {
  ok: "Riuscita",
  temporaneo: "Errore temporaneo",
  richiesta: "Richiesta non valida",
  rifiuto: "Rifiutata dall'AI",
  risposta: "Risposta fuori schema",
  configurazione: "Configurazione",
};

export function etichettaEsito(esito: string): string {
  return ETICHETTA_ESITO[esito] ?? esito;
}

export function etichettaTipo(tipo: string): string {
  return TIPI.find((t) => t.value === tipo)?.label ?? tipo;
}
