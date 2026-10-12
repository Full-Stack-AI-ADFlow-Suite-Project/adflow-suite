/**
 * Interventi dell'operatore sul singolo post (plan §3, spec §3, R-03, R-30,
 * R-31): modifica a mano, spunta "va bene", rigenera. Gli endpoint sono di
 * revisione (T2b-42); finché non sono su main le pagine leggono i dati di
 * esempio. Dopo ogni intervento la pagina rilegge Vedi campagna, quindi qui
 * non si legge il corpo della risposta.
 */
import { richiesta } from "./http";
import { esempiInterventi } from "./esempi/interventi";
import { USA_ESEMPI } from "./esempi/accesso";

/** `totale` riscrive da zero; `da_proposta` parte dal testo scritto dall'operatore. */
export type ModalitaRigenerazione = "totale" | "da_proposta";

/** POST /post/{id}/modifica: testo e hashtag (senza #) come nuova versione. */
export async function modificaPost(
  postId: number,
  testo: string,
  hashtag: string[],
): Promise<void> {
  if (USA_ESEMPI) return esempiInterventi.modifica(postId, testo, hashtag);
  await richiesta<unknown>("POST", `/post/${postId}/modifica`, {
    testo,
    hashtag,
  });
}

/** POST /post/{id}/controllato: mette o toglie la spunta "va bene" (R-30). */
export async function segnaControllato(
  postId: number,
  valore: boolean,
): Promise<void> {
  if (USA_ESEMPI) return esempiInterventi.controllato(postId, valore);
  await richiesta<unknown>("POST", `/post/${postId}/controllato`, { valore });
}

/** POST /post/{id}/rigenera: accende l'intervento in corso e accoda il job (R-31). */
export async function rigeneraPost(
  postId: number,
  modalita: ModalitaRigenerazione,
  testoProposto: string | null,
  nota: string | null,
): Promise<void> {
  if (USA_ESEMPI)
    return esempiInterventi.rigenera(postId, modalita, testoProposto, nota);
  await richiesta<unknown>("POST", `/post/${postId}/rigenera`, {
    modalita,
    testo_proposto: testoProposto,
    nota,
  });
}
