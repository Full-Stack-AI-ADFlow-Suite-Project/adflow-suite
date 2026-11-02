/**
 * Modulo revisione (plan §3): Vedi campagna dell'operatore, Approva e Riprova
 * (le altre decisioni sono in decisioni.ts). I tipi rispecchiano
 * backend/app/moduli/revisione/schemas.py.
 */
import type { CampagnaDettaglio } from "./campagne";
import { richiesta } from "./http";
import { esempiRevisione } from "./esempi/revisione";
import { elencoArtigianiEsempio } from "./esempi/elenco-artigiani";
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

/** Gli interventi che l'operatore può fare adesso su un post (spec R-16). */
export type Intervento =
  | "modifica"
  | "rigenera"
  | "rigenera_immagine"
  | "cambia_foto"
  | "sposta"
  | "annulla"
  | "riprogramma";

/** Una foto con cui si può cambiare quella del post (GET /post/{id}/foto-possibili, R-36). */
export interface FotoPossibile {
  foto_id: number;
  punteggio: number | null;
  /** Falso: arrivata con una richiesta all'artigiano, senza analisi (R-46). */
  analizzata: boolean;
  provenienza: "gruppo" | "campagna" | "archivio";
  soggetto: string | null;
}

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
  /** Gli interventi ammessi adesso: i pulsanti nascono da qui (R-16). */
  interventi: Intervento[];
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
  costo_ai: number;
}

/** Una riga di GET /artigiani (ArtigianoElenco di schemas.py, spec R-38). */
export interface ArtigianoElenco {
  /** L'id dell'utente artigiano. */
  id: number;
  nome: string;
  email: string;
  attivo: boolean;
  /** `null`: il profilo è da compilare. */
  bottega: string | null;
  referente: string | null;
  citta: string | null;
  canali_collegati: string[];
  n_da_approvare: number;
  n_in_corso: number;
  /** Il più vicino «entro quando» tra le campagne da approvare. */
  prossima_scadenza: string | null;
}

export function elencoArtigiani(): Promise<ArtigianoElenco[]> {
  if (USA_ESEMPI) return elencoArtigianiEsempio();
  return richiesta<ArtigianoElenco[]>("GET", "/artigiani");
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

/** Riprova da generazione_fallita: torna a inviata e riaccoda il job (T1-24). */
export function riprova(campagnaId: number): Promise<CampagnaDettaglio> {
  if (USA_ESEMPI) return esempiRevisione.riprova(campagnaId);
  return richiesta<CampagnaDettaglio>(
    "POST",
    `/campagne/${campagnaId}/riprova`,
  );
}
