/**
 * Decisioni dell'operatore sulla campagna (plan §3, spec §2.3, R-18, R-32,
 * R-33, R-34) e pagina Campagne da approvare (R-38). Gli endpoint sono di
 * revisione (T2b-41, -43, -45); finché non sono su main le pagine leggono i
 * dati di esempio. Dopo ogni decisione la pagina rilegge Vedi campagna, quindi
 * qui non si legge il corpo delle risposte.
 */
import type { CampagnaElencoItem } from "./campagne";
import { elenco } from "./campagne";
import { richiesta } from "./http";
import { esempiDecisioni } from "./esempi/decisioni";
import { USA_ESEMPI } from "./esempi/accesso";

/**
 * GET /da-approvare arriva con T2b-45. Finché è false, con le API vere la
 * pagina legge GET /campagne e non ha conteggi, "entro quando" e nota: il
 * passaggio si fa nella chiusura dello sprint (T2b-07).
 */
const DA_APPROVARE_SU_MAIN = false;

export type MotivoRespinta = "foto" | "altro";

/** Conteggi dei post di una campagna (plan §3, GET /da-approvare). */
export interface ConteggiPost {
  totale: number;
  da_approvare: number;
  da_rivedere: number;
  /** Post riempitivo per canale. */
  riempitivi: Record<string, number>;
}

/** Una riga di Campagne da approvare: la campagna con i suoi conteggi. */
export interface CampagnaDaApprovare extends CampagnaElencoItem {
  conteggi: ConteggiPost | null;
  /** Data del primo post da approvare o 00:00 dell'inizio senza piano (R-38). */
  entro_quando: string | null;
  ultima_nota: string | null;
}

export async function daApprovare(): Promise<CampagnaDaApprovare[]> {
  if (USA_ESEMPI) return esempiDecisioni.daApprovare();
  if (DA_APPROVARE_SU_MAIN)
    return richiesta<CampagnaDaApprovare[]>("GET", "/da-approvare");
  const stati = [
    "inviata",
    "in_generazione",
    "piano_da_rivedere",
    "generazione_fallita",
    "in_revisione",
  ];
  return (await elenco())
    .filter((c) => stati.includes(c.stato))
    .map((c) => ({
      ...c,
      conteggi: null,
      entro_quando: null,
      ultima_nota: null,
    }));
}

/** POST /campagne/{id}/nota: in ogni stato dopo l'invio, nessuna email (R-32). */
export async function aggiungiNota(
  campagnaId: number,
  nota: string,
): Promise<void> {
  if (USA_ESEMPI) return esempiDecisioni.nota(campagnaId, nota);
  await richiesta<unknown>("POST", `/campagne/${campagnaId}/nota`, { nota });
}

/** POST /campagne/{id}/respingi: da in_revisione o piano_da_rivedere (R-18). */
export async function respingi(
  campagnaId: number,
  motivo: MotivoRespinta,
  nota: string,
  fotoSegnate: number[],
): Promise<void> {
  if (USA_ESEMPI)
    return esempiDecisioni.respingi(campagnaId, motivo, nota, fotoSegnate);
  await richiesta<unknown>("POST", `/campagne/${campagnaId}/respingi`, {
    motivo,
    nota,
    foto_segnate: fotoSegnate,
  });
}

/** POST /campagne/{id}/togli-canale: definitivo, mai l'ultimo canale (R-18). */
export async function togliCanale(
  campagnaId: number,
  canale: string,
  nota: string,
): Promise<void> {
  if (USA_ESEMPI) return esempiDecisioni.togliCanale(campagnaId, canale, nota);
  await richiesta<unknown>("POST", `/campagne/${campagnaId}/togli-canale`, {
    canale,
    nota,
  });
}

/** POST /campagne/{id}/sospendi: attiva → sospesa (R-33). */
export async function sospendi(campagnaId: number): Promise<void> {
  if (USA_ESEMPI) return esempiDecisioni.sospendi(campagnaId);
  await richiesta<unknown>("POST", `/campagne/${campagnaId}/sospendi`);
}

/**
 * POST /campagne/{id}/riattiva: sospesa → attiva. I post in arretrato scelti
 * escono adesso, gli altri diventano annullati (R-33).
 */
export async function riattiva(
  campagnaId: number,
  pubblicaOra: number[],
): Promise<void> {
  if (USA_ESEMPI) return esempiDecisioni.riattiva(campagnaId, pubblicaOra);
  await richiesta<unknown>("POST", `/campagne/${campagnaId}/riattiva`, {
    pubblica_ora: pubblicaOra,
  });
}

/** POST /campagne/{id}/annulla: i post approvati diventano annullati (R-33). */
export async function annulla(campagnaId: number): Promise<void> {
  if (USA_ESEMPI) return esempiDecisioni.annulla(campagnaId);
  await richiesta<unknown>("POST", `/campagne/${campagnaId}/annulla`);
}

/**
 * POST /post/{id}/riprogramma: un post fallito torna approvato con una nuova
 * data (R-34). `locale` è il valore di un campo datetime-local, nell'ora del
 * browser; all'API va in UTC (constitution §4).
 */
export async function riprogramma(
  postId: number,
  locale: string,
): Promise<void> {
  const dataOra = new Date(locale).toISOString();
  if (USA_ESEMPI) return esempiDecisioni.riprogramma(postId, dataOra);
  await richiesta<unknown>("POST", `/post/${postId}/riprogramma`, {
    data_ora: dataOra,
  });
}
