/**
 * Storico delle chiamate all'AI (brief-richieste §1.3, spec R-50).
 * I tipi rispecchiano backend/app/moduli/contenuti/schemas.py. Con
 * `ENDPOINT_PRONTO` a `false` la pagina legge i dati di esempio.
 */
import { richiesta } from "./http";
import { esempiStorico } from "./esempi/storico";

const ENDPOINT_PRONTO = true;

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

export interface NumeriVersione {
  tipo: TipoChiamata;
  versione_prompt: string | null;
  chiamate: number;
  /** 0–1. */
  tasso_errore: number;
  durata_media_ms: number | null;
  /** Decimal: arriva come stringa. */
  costo_usd: string;
  voto_medio: number | null;
}

export interface NumeriAI {
  chiamate: number;
  costo_usd: string;
  durata_media_ms: number | null;
  durata_p95_ms: number | null;
  /** 0–1. */
  tasso_errore: number;
  voto_medio: number | null;
  testi_approvati: number;
  testi_approvati_come_ai: number;
  modifiche_a_mano: number;
  rigenerazioni_testo: number;
  immagini_create: number;
  immagini_non_create: number;
  immagini_rigenerate: number;
  per_versione: NumeriVersione[];
}

export interface VotoAI {
  /** Da 1 a 5. */
  voto: number;
  nota?: string | null;
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

/** I numeri con gli stessi filtri dell'elenco, senza la pagina. */
export function numeriChiamate(filtri: FiltriStorico): Promise<NumeriAI> {
  if (!ENDPOINT_PRONTO) return esempiStorico.numeri(filtri);
  return richiesta("GET", `/storico-ai/numeri${querystring(filtri)}`);
}

/** Aggiunge un voto: quelli di prima restano. */
export function votaChiamata(id: number, voto: VotoAI): Promise<ValutazioneAI> {
  if (!ENDPOINT_PRONTO) return esempiStorico.vota(id, voto);
  return richiesta("POST", `/storico-ai/${id}/voto`, voto);
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
