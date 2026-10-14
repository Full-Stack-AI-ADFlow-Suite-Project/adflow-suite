/**
 * Modulo campagne (plan §3): bozza, gruppi di foto, invio.
 * I tipi rispecchiano backend/app/moduli/campagne/schemas.py e domain.py.
 */
import { ApiErrore, leggiDettaglio, richiesta } from "./http";
import { esempiCampagne, USA_ESEMPI } from "./esempi/campagne";

export type StatoCampagna =
  | "bozza"
  | "inviata"
  | "in_generazione"
  | "generazione_fallita"
  | "piano_da_rivedere"
  | "in_revisione"
  | "respinta"
  | "scaduta"
  | "attiva"
  | "sospesa"
  | "annullata"
  | "conclusa";

export interface FotoSintetica {
  id: number;
  gruppo_id: number | null;
  file: string;
  mime: string;
  larghezza: number;
  altezza: number;
  origine: string;
}

export interface GruppoSintetico {
  id: number;
  origine: string;
  descrizione: string | null;
  da_usare_il: string | null;
  n_immagini: number | null;
  foto: FotoSintetica[];
}

export interface CampagnaDettaglio {
  id: number;
  profilo_id: number;
  titolo: string;
  inizio: string;
  fine: string;
  descrizione: string | null;
  stato: StatoCampagna;
  canali: string[] | null;
  canali_tolti: string[] | null;
  frequenza: string | null;
  obiettivo: string | null;
  inviata_il: string | null;
  chiusa_il: string | null;
  gruppi: GruppoSintetico[];
  post_chiesti_per_canale: Record<string, number>;
  avvisi: string[];
  /** Visibili solo a operatore e admin (CampagnaDettaglio di schemas.py). */
  profilo_snapshot?: ProfiloSnapshot | null;
  decisioni?: DecisioneSintetica[];
  /** Esito della respinta visibile all’artigiano, (R-18). */
  esito_respinta?: {
    motivo: string;
    nota: string | null;
    foto_segnate: number[];
  } | null;
}

/**
 * La fotografia del profilo com'era all'invio (R-11): le colonne di
 * profilo_bottega (artigiani/models.py). Qui quelle che le pagine leggono.
 */
export interface ProfiloSnapshot {
  nome?: string;
  referente?: string;
  citta?: string;
  tipo_prodotto?: string;
  obiettivo?: string;
  frequenza?: string | null;
  tono?: string[] | null;
  clienti_ideali?: string;
  vincoli?: string | null;
  /** Dichiarazione dell'artigiano all'invio (R-41) e quando l'ha data. */
  dichiarazione?: boolean;
  dichiarazione_data?: string;
}

/** DecisioneSintetica di schemas.py: le decisioni dell'operatore. */
export interface DecisioneSintetica {
  id: number;
  esito: string;
  canale: string | null;
  post_id: number | null;
  motivo: string | null;
  nota: string | null;
}

export interface CampagnaElencoItem {
  id: number;
  profilo_id: number;
  titolo: string;
  inizio: string;
  fine: string;
  stato: StatoCampagna;
  canali: string[] | null;
  bottega?: string | null;
  citta?: string | null;
}

export interface CampagnaCrea {
  titolo: string;
  inizio: string;
  fine: string;
  descrizione?: string | null;
  canali: string[];
}

export interface CampagnaModifica {
  titolo?: string | null;
  inizio?: string | null;
  fine?: string | null;
  descrizione?: string | null;
  canali?: string[] | null;
}

export interface GruppoCrea {
  origine?: string;
  descrizione?: string | null;
  da_usare_il?: string | null;
  n_immagini?: number | null;
}

export function elenco(stato?: string): Promise<CampagnaElencoItem[]> {
  if (USA_ESEMPI) return esempiCampagne.elenco(stato);
  const filtro = stato ? `?stato=${encodeURIComponent(stato)}` : "";
  return richiesta<CampagnaElencoItem[]>("GET", `/campagne${filtro}`);
}

export function dettaglio(id: number): Promise<CampagnaDettaglio> {
  if (USA_ESEMPI) return esempiCampagne.dettaglio(id);
  return richiesta<CampagnaDettaglio>("GET", `/campagne/${id}`);
}

export function crea(dati: CampagnaCrea): Promise<CampagnaDettaglio> {
  if (USA_ESEMPI) return esempiCampagne.crea(dati);
  return richiesta<CampagnaDettaglio>("POST", "/campagne", dati);
}

export function modifica(
  id: number,
  dati: CampagnaModifica,
): Promise<CampagnaDettaglio> {
  if (USA_ESEMPI) return esempiCampagne.modifica(id, dati);
  return richiesta<CampagnaDettaglio>("PATCH", `/campagne/${id}`, dati);
}

export function creaGruppo(
  campagnaId: number,
  dati: GruppoCrea,
): Promise<GruppoSintetico> {
  if (USA_ESEMPI) return esempiCampagne.creaGruppo(campagnaId, dati);
  return richiesta<GruppoSintetico>(
    "POST",
    `/campagne/${campagnaId}/gruppi`,
    dati,
  );
}

export function aggiornaGruppo(
  campagnaId: number,
  gruppoId: number,
  dati: GruppoCrea,
): Promise<GruppoSintetico> {
  if (USA_ESEMPI)
    return esempiCampagne.aggiornaGruppo(campagnaId, gruppoId, dati);
  return richiesta<GruppoSintetico>(
    "PUT",
    `/campagne/${campagnaId}/gruppi/${gruppoId}`,
    dati,
  );
}

export function eliminaGruppo(
  campagnaId: number,
  gruppoId: number,
): Promise<void> {
  if (USA_ESEMPI) return esempiCampagne.eliminaGruppo(campagnaId, gruppoId);
  return richiesta<void>(
    "DELETE",
    `/campagne/${campagnaId}/gruppi/${gruppoId}`,
  );
}

/** Upload multipart: file e gruppo_id, entrambi obbligatori (plan §3). */
export async function caricaFoto(
  campagnaId: number,
  gruppoId: number,
  file: File,
): Promise<FotoSintetica> {
  if (USA_ESEMPI) return esempiCampagne.caricaFoto(campagnaId, gruppoId, file);
  const corpo = new FormData();
  corpo.append("file", file);
  corpo.append("gruppo_id", String(gruppoId));
  const risposta = await fetch(`/api/campagne/${campagnaId}/foto`, {
    method: "POST",
    body: corpo,
  });
  if (risposta.status === 401) throw new ApiErrore(401, "Sessione scaduta.");
  if (!risposta.ok) {
    const dati: unknown = await risposta.json().catch(() => null);
    throw new ApiErrore(risposta.status, leggiDettaglio(dati));
  }
  return (await risposta.json()) as FotoSintetica;
}

export function eliminaFoto(fotoId: number): Promise<void> {
  if (USA_ESEMPI) return esempiCampagne.eliminaFoto(fotoId);
  return richiesta<void>("DELETE", `/foto/${fotoId}`);
}

/** `dichiarazione` è la spunta obbligatoria dell'artigiano (R-41, CampagnaInvia). */
export function invia(
  campagnaId: number,
  dichiarazione: boolean,
): Promise<CampagnaDettaglio> {
  if (USA_ESEMPI) return esempiCampagne.invia(campagnaId, dichiarazione);
  return richiesta<CampagnaDettaglio>("POST", `/campagne/${campagnaId}/invia`, {
    dichiarazione,
  });
}

/** Dati di una foto nel calendario approvato (contenuti/schemas.py). */
export interface FotoCalendario {
  id: number;
  url: string;
  mime: string;
  larghezza: number;
  altezza: number;
  origine: string;
}

/** PostCalendario di contenuti/schemas.py: post approvato o successivo. */
export interface PostCalendario {
  id: number;
  data_ora: string;
  ora: string;
  canale: string;
  stato: string;
  testo: string;
  hashtag: string[];
  foto: FotoCalendario[];
}

/** GiornoCalendario: elenco dei post in una data. */
export interface GiornoCalendario {
  data: string;
  post: PostCalendario[];
}

/** CanaleToltoCalendario: note dei canali tolti, visibili all'artigiano. */
export interface CanaleToltoCalendario {
  canale: string;
  nota: string | null;
}

/** CalendarioCampagna: GET /campagne/{id}/calendario (R-45, CA-56). */
export interface CalendarioCampagna {
  campagna_id: number;
  strategia: string | null;
  giorni: GiornoCalendario[];
  canali_tolti: CanaleToltoCalendario[];
  n_post_scaduti: number;
}

export function calendario(campagnaId: number): Promise<CalendarioCampagna> {
  if (USA_ESEMPI) return esempiCampagne.calendario(campagnaId);
  return richiesta<CalendarioCampagna>(
    "GET",
    `/campagne/${campagnaId}/calendario`,
  );
}
