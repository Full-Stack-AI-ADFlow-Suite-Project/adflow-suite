/**
 * Modulo revisione (plan §3): Vedi campagna dell'operatore e le tre azioni
 * dello sprint 1 (Approva, Prosegui, Riprova). I tipi rispecchiano
 * backend/app/moduli/revisione/schemas.py.
 */
import type { CampagnaDettaglio } from "./campagne";
import { richiesta } from "./http";
import { esempiRevisione } from "./esempi/revisione";
import { USA_ESEMPI } from "./esempi/accesso";

/** Livello e regola di un esito del validatore (contenuti/validatore.py). */
export interface ErroreValidazione {
  livello: "blocco" | "avviso";
  regola: string;
  messaggio: string;
}

/** CampagnaSchema: la campagna come la legge l'operatore. */
export interface CampagnaVista {
  id: number;
  profilo_id: number;
  titolo: string;
  inizio: string;
  fine: string;
  descrizione: string | null;
  stato: string;
  canali: string[] | null;
  canali_tolti: string[] | null;
  frequenza: string | null;
  obiettivo: string | null;
  inviata_il: string | null;
  chiusa_il: string | null;
}

/** PianoSchema: strategia, esito del controllo e debolezza (R-20). */
export interface Piano {
  id: number;
  numero: number;
  strategia: string;
  esito_controllo: Record<string, unknown> | unknown[] | null;
  debole: boolean;
  creata_il: string;
}

export interface FotoLegata {
  foto_id: number;
  posizione: number;
}

/** VersionePostSchema: testo, autore, foto e risultati del validatore. */
export interface VersionePost {
  id: number;
  numero: number;
  testo: string;
  hashtag: string[];
  autore_id: number | null;
  tipo_intervento: string;
  testo_proposto: string | null;
  nota: string | null;
  provider_ai: string | null;
  modello_ai: string | null;
  versione_prompt: string | null;
  errori_validazione: ErroreValidazione[] | Record<string, unknown> | null;
  creata_il: string;
  foto: FotoLegata[];
}

export type StatoPost =
  | "da_approvare"
  | "approvato"
  | "pubblicato"
  | "fallito"
  | "scaduto"
  | "scartato"
  | "annullato";

/** PostSchema: riempitivo, versione corrente e storico. */
export interface PostVista {
  post_id: number;
  canale: string;
  formato: string;
  riempitivo: string | null;
  data_ora: string;
  stato: StatoPost;
  da_rivedere: boolean;
  controllato_da: number | null;
  controllato_il: string | null;
  intervento_in_corso: string | null;
  intervento_dal: string | null;
  versione_corrente: VersionePost | null;
  versioni: VersionePost[];
}

/** GruppoSchema: il gruppo di un'uscita o delle foto non usate. */
export interface GruppoVista {
  id: number;
  origine: string;
  descrizione: string | null;
  da_usare_il: string | null;
}

export interface Uscita {
  id: number;
  numero: number;
  tema: string;
  gruppo: GruppoVista | null;
  post: PostVista[];
}

export interface FotoNonUsata {
  foto_id: number;
  motivo: string | null;
}

export interface GruppoFotoNonUsate {
  gruppo_id: number | null;
  descrizione: string | null;
  foto: FotoNonUsata[];
}

/** ErroreSchema: l'ultimo errore della generazione (R-35). */
export interface ErroreGenerazione {
  tipo: string;
  messaggio: string;
  tappa: string;
  canale: string | null;
  creata_il: string;
}

/** VediCampagnaSchema di GET /campagne/{id}/post. */
export interface VediCampagna {
  campagna: CampagnaVista;
  piano: Piano | null;
  uscite: Uscita[];
  foto_non_usate: GruppoFotoNonUsate[];
  ultimo_errore: ErroreGenerazione | null;
}

export function vediCampagna(campagnaId: number): Promise<VediCampagna> {
  if (USA_ESEMPI) return esempiRevisione.vediCampagna(campagnaId);
  return richiesta<VediCampagna>("GET", `/campagne/${campagnaId}/post`);
}

export function approva(campagnaId: number): Promise<{ stato: string }> {
  if (USA_ESEMPI) return esempiRevisione.approva(campagnaId);
  return richiesta<{ stato: string }>(
    "POST",
    `/campagne/${campagnaId}/approva`,
  );
}

export function prosegui(campagnaId: number): Promise<{ stato: string }> {
  if (USA_ESEMPI) return esempiRevisione.prosegui(campagnaId);
  return richiesta<{ stato: string }>(
    "POST",
    `/campagne/${campagnaId}/prosegui`,
  );
}

/** Riprova da generazione_fallita: torna a inviata e riaccoda il job (T1-24). */
export function riprova(campagnaId: number): Promise<CampagnaDettaglio> {
  if (USA_ESEMPI) return esempiRevisione.riprova(campagnaId);
  return richiesta<CampagnaDettaglio>(
    "POST",
    `/campagne/${campagnaId}/riprova`,
  );
}
