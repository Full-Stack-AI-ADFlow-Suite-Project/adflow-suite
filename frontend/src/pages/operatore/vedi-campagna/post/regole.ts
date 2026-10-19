/** Le regole degli interventi sul post, lette dalla pagina (spec R-03, R-30, R-31). */
import type { PostVista, VersionePost } from "../../../../api/revisione";

/** Sopra il salvataggio di una modifica o di un cambio foto dopo l'approvazione (R-16). */
export const AVVISO_CAMPAGNA_APPROVATA =
  "La campagna è approvata: la versione che salvi esce al posto di quella di prima, e la approvi tu.";

/** R-03: al massimo 3 rigenerazioni del testo per post. */
export const MAX_RIGENERAZIONI = 3;

/** R-31: un intervento partito da più di 10 minuti vale come fallito. */
const SCADENZA_INTERVENTO_MS = 10 * 60 * 1000;

const TIPI_RIGENERAZIONE = ["rigenera_totale", "rigenera_da_proposta"];

const NOME_TIPO: Record<string, string> = {
  generazione: "Generazione",
  rigenera_totale: "Rigenerato da zero",
  rigenera_da_proposta: "Rigenerato da testo proposto",
  modifica_operatore: "Modifica a mano",
  ritocco_foto: "Foto ritoccata",
  scelta_foto: "Foto scelta",
  cambio_foto: "Foto cambiata",
};

export function nomeTipo(tipo: string): string {
  return NOME_TIPO[tipo] ?? tipo;
}

/** True se l'intervento è in corso e non è ancora scaduto: blocca gli altri interventi e l'approvazione. */
export function interventoAttivo(
  post: PostVista,
  adesso = Date.now(),
): boolean {
  if (!post.intervento_in_corso) return false;
  if (!post.intervento_dal) return true;
  return (
    adesso - new Date(post.intervento_dal).getTime() < SCADENZA_INTERVENTO_MS
  );
}

/** I cicli di testo già consumati: si contano quando nasce la versione (R-03). */
export function rigenerazioniFatte(post: PostVista): number {
  return post.versioni.filter((v) =>
    TIPI_RIGENERAZIONE.includes(v.tipo_intervento),
  ).length;
}

/** Gli hashtag salvati sono senza #: si mostrano e si scrivono con. */
export function conCancelletto(hashtag: string[]): string {
  return hashtag.map((h) => (h.startsWith("#") ? h : `#${h}`)).join(" ");
}

/** Dal campo di testo agli hashtag da salvare: separati da spazi o virgole, senza #. */
export function daCampoHashtag(campo: string): string[] {
  return campo
    .split(/[\s,]+/)
    .map((h) => h.replace(/^#+/, ""))
    .filter((h) => h.length > 0);
}

export function nomeAutore(
  versione: VersionePost,
  utente: { id: number; nome: string } | null | undefined,
): string {
  if (versione.autore_id == null) return "AI";
  if (utente && versione.autore_id === utente.id) return `${utente.nome} (tu)`;
  return `Operatore n. ${versione.autore_id}`;
}
