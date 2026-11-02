/**
 * Interventi dell'operatore sul singolo post (plan §3, spec §3, R-03, R-16,
 * R-30, R-31, R-36): modifica a mano, spunta "va bene", rigenera, cambia foto,
 * sposta, annulla. Gli endpoint sono di revisione (T2b-42, T3-61, T3-62);
 * con `VITE_USA_ESEMPI=1` le pagine leggono i dati di esempio. Dopo ogni intervento la pagina rilegge Vedi campagna, quindi qui
 * non si legge il corpo della risposta.
 */
import { richiesta } from "./http";
import type { FotoPossibile } from "./revisione";
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

/** POST /post/{id}/rigenera-immagine: accende l'intervento e accoda il job (R-49). */
export async function rigeneraImmagine(
  postId: number,
  nota: string | null = null,
  riscriviTesto: boolean = false,
  notaTesto: string | null = null,
): Promise<void> {
  if (USA_ESEMPI)
    return esempiInterventi.rigeneraImmagine(
      postId,
      nota,
      riscriviTesto,
      notaTesto,
    );
  await richiesta<unknown>("POST", `/post/${postId}/rigenera-immagine`, {
    nota,
    riscrivi_testo: riscriviTesto,
    nota_testo: notaTesto,
  });
}

/** GET /post/{id}/foto-possibili: le foto con cui cambiare quella del post, la migliore in cima (R-36). */
export function fotoPossibili(postId: number): Promise<FotoPossibile[]> {
  if (USA_ESEMPI) return esempiInterventi.fotoPossibili(postId);
  return richiesta<FotoPossibile[]>("GET", `/post/${postId}/foto-possibili`);
}

/** POST /post/{id}/cambia-foto: nasce una versione `cambio_foto` con lo stesso testo (R-36). */
export async function cambiaFoto(
  postId: number,
  fotoId: number,
  riscriviTesto: boolean = false,
  nota: string | null = null,
): Promise<void> {
  if (USA_ESEMPI)
    return esempiInterventi.cambiaFoto(postId, fotoId, riscriviTesto, nota);
  await richiesta<unknown>("POST", `/post/${postId}/cambia-foto`, {
    foto_id: fotoId,
    riscrivi_testo: riscriviTesto,
    nota,
  });
}

/**
 * POST /post/{id}/sposta: nuova data e ora, in revisione o dopo l'approvazione
 * (R-36). `locale` è il valore di un campo datetime-local, nell'ora del browser;
 * all'API va in UTC (constitution §4).
 */
export async function sposta(postId: number, locale: string): Promise<void> {
  const dataOra = new Date(locale).toISOString();
  if (USA_ESEMPI) return esempiInterventi.sposta(postId, dataOra);
  await richiesta<unknown>("POST", `/post/${postId}/sposta`, {
    data_ora: dataOra,
  });
}

/** POST /post/{id}/annulla: il post approvato non esce più; la nota è obbligatoria (R-36). */
export async function annullaPost(postId: number, nota: string): Promise<void> {
  if (USA_ESEMPI) return esempiInterventi.annullaPost(postId, nota);
  await richiesta<unknown>("POST", `/post/${postId}/annulla`, { nota });
}
