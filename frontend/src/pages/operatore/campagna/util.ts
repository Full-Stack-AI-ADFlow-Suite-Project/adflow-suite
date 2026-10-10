/** Formattazione date e etichette dei mockup operatore. */

const GG = ["dom", "lun", "mar", "mer", "gio", "ven", "sab"];
const MESI = [
  "gennaio",
  "febbraio",
  "marzo",
  "aprile",
  "maggio",
  "giugno",
  "luglio",
  "agosto",
  "settembre",
  "ottobre",
  "novembre",
  "dicembre",
];

const p2 = (n: number) => String(n).padStart(2, "0");
const D = (s: string) => new Date(s.length === 10 ? s + "T00:00" : s);

export const NOME_CANALE: Record<string, string> = {
  facebook: "Facebook",
  instagram: "Instagram",
};

/** I valori di artigiani/domain.py, come li legge una persona. */
export const NOME_OBIETTIVO: Record<string, string> = {
  vendere: "Vendere di più",
  negozio: "Portare persone in bottega",
  notorieta: "Farmi conoscere",
  fidelizzare: "Mantenere il rapporto con i clienti",
};

export const NOME_TIPO_PRODOTTO: Record<string, string> = {
  legno_mobili: "Legno e mobili",
  ceramica_vetro: "Ceramica e vetro",
  gioielli_metalli: "Gioielli e metalli",
  tessile_pelle: "Tessuti e pelle",
  alimentare: "Alimentare",
  altro: "Altro",
};

/** Il nome di un codice; il codice stesso se non è tra quelli noti. */
export function nomeDi(
  nomi: Record<string, string>,
  codice: string | null | undefined,
): string {
  return codice ? nomi[codice] ?? codice : "—";
}

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

export function dataLunga(s: string): string {
  const x = D(s);
  return `${x.getDate()} ${MESI[x.getMonth()]} alle ore ${p2(
    x.getHours(),
  )}:${p2(x.getMinutes())}`;
}

export function giorni(inizio: string, fine: string): number {
  return Math.round((D(fine).getTime() - D(inizio).getTime()) / 86400000) + 1;
}

/** Colore del badge per lo stato della campagna (badge dei mockup). */
export function coloreCampagna(stato: string): string {
  if (
    stato === "in_revisione" ||
    stato === "piano_da_rivedere" ||
    stato === "sospesa"
  )
    return "yellow";
  if (
    stato === "generazione_fallita" ||
    stato === "respinta" ||
    stato === "scaduta" ||
    stato === "annullata"
  )
    return "red";
  if (stato === "attiva" || stato === "conclusa") return "verde";
  return "gray";
}

/** Colore del badge per lo stato del post. */
export function colorePost(stato: string): string {
  if (stato === "approvato" || stato === "pubblicato") return "verde";
  if (
    stato === "fallito" ||
    stato === "scaduto" ||
    stato === "scartato" ||
    stato === "annullato"
  )
    return "red";
  return "yellow";
}

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
