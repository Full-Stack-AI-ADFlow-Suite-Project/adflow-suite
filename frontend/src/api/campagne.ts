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
  /** La richiesta del consorzio all'artigiano, se c'è (R-46). */
  richiesta?: RichiestaArtigiano | null;
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

/** Stato della richiesta del consorzio all'artigiano (R-46), ricavato dalle decisioni. */
export type StatoRichiesta = "aperta" | "inviata" | "decaduta";

/** Una foto segnata da sostituire e, se l'artigiano l'ha caricata, la nuova. */
export interface FotoDaSostituire {
  foto_id: number;
  gruppo_id: number | null;
  nuova_foto_id: number | null;
}

/** RichiestaArtigiano di schemas.py: la domanda dell'operatore e la risposta. */
export interface RichiestaArtigiano {
  stato: StatoRichiesta;
  domanda: string;
  creata_il: string;
  foto: FotoDaSostituire[];
  risposta: string | null;
  inviata_il: string | null;
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
  /** Stato della richiesta del consorzio, solo nell'elenco dell'artigiano (R-46). */
  richiesta?: StatoRichiesta | null;
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

/**
 * GET /campagne. `artigiano` (l'id dell'utente) è per l'operatore: solo le
 * campagne di quell'artigiano (R-38, CA-94); per l'artigiano non conta.
 */
export function elenco(
  stato?: string,
  artigiano?: number,
): Promise<CampagnaElencoItem[]> {
  if (USA_ESEMPI) return esempiCampagne.elenco(stato, artigiano);
  const filtri = new URLSearchParams();
  if (stato) filtri.set("stato", stato);
  if (artigiano !== undefined) filtri.set("artigiano", String(artigiano));
  const query = filtri.toString();
  return richiesta<CampagnaElencoItem[]>(
    "GET",
    `/campagne${query ? `?${query}` : ""}`,
  );
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

/** POST /campagne/{id}/richiesta: l'operatore chiede una risposta e fino a 3 foto da sostituire (R-46). */
export function chiediArtigiano(
  campagnaId: number,
  domanda: string,
  foto: number[],
): Promise<RichiestaArtigiano> {
  if (USA_ESEMPI)
    return esempiCampagne.chiediArtigiano(campagnaId, domanda, foto);
  return richiesta<RichiestaArtigiano>(
    "POST",
    `/campagne/${campagnaId}/richiesta`,
    { domanda, foto },
  );
}

/**
 * POST /campagne/{id}/richiesta/foto (multipart): l'artigiano carica la foto
 * nuova al posto di una segnata, con la dichiarazione di R-41.
 */
export async function caricaFotoRichiesta(
  campagnaId: number,
  fotoId: number,
  file: File,
  dichiarazione: boolean,
): Promise<FotoSintetica> {
  if (USA_ESEMPI)
    return esempiCampagne.caricaFotoRichiesta(
      campagnaId,
      fotoId,
      file,
      dichiarazione,
    );
  const corpo = new FormData();
  corpo.append("file", file);
  corpo.append("foto_id", String(fotoId));
  corpo.append("dichiarazione", dichiarazione ? "true" : "false");
  const risposta = await fetch(`/api/campagne/${campagnaId}/richiesta/foto`, {
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

/** POST /campagne/{id}/richiesta/invia: l'artigiano risponde; il testo è facoltativo se ci sono foto. */
export function inviaRisposta(
  campagnaId: number,
  risposta: string | null,
): Promise<RichiestaArtigiano> {
  if (USA_ESEMPI) return esempiCampagne.inviaRisposta(campagnaId, risposta);
  return richiesta<RichiestaArtigiano>(
    "POST",
    `/campagne/${campagnaId}/richiesta/invia`,
    { risposta },
  );
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
