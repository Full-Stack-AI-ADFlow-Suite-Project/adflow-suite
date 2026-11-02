/** Formattazione date e etichette dei mockup operatore. */

const GG = ["dom", "lun", "mar", "mer", "gio", "ven", "sab"];
const p2 = (n: number) => String(n).padStart(2, "0");
const D = (s: string) => new Date(s.length === 10 ? s + "T00:00" : s);

export const NOME_CANALE: Record<string, string> = {
  facebook: "Facebook",
  instagram: "Instagram",
};

export function data(s: string): string {
  const x = D(s);
  return `${p2(x.getDate())}/${p2(x.getMonth() + 1)}/${x.getFullYear()}`;
}

export function dataOra(s: string): string {
  const x = D(s);
  return `${GG[x.getDay()]} ${p2(x.getDate())}/${p2(x.getMonth() + 1)} · ${p2(
    x.getHours(),
  )}:${p2(x.getMinutes())}`;
}

export function giorni(inizio: string, fine: string): number {
  return Math.round((D(fine).getTime() - D(inizio).getTime()) / 86400000) + 1;
}

export { coloreCampagna, colorePost } from "../../../components/stati";

/** Esiti del validatore sulla versione corrente di un post. */
export function erroriDi(p: {
  versione_corrente?: {
    errori_validazione?:
      | { livello: string; regola: string; messaggio: string }[]
      | Record<string, unknown>
      | null;
  } | null;
}) {
  const err = p.versione_corrente?.errori_validazione;
  return Array.isArray(err) ? err : [];
}
