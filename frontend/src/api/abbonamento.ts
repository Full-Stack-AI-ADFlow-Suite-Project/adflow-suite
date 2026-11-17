/**
 * L'abbonamento della bottega: quanti post a settimana per ogni social
 * (plan §2, spec R-05). Un solo posto per la tabella e per il conto dei post,
 * così profilo, bozza e riepilogo dicono gli stessi numeri del server
 * (`post_chiesti`: post a settimana × giorni ÷ 7, per difetto).
 */

export interface Abbonamento {
  value: string;
  postSett: number;
  titolo: string;
  nota: string;
}

export const ABBONAMENTI: Abbonamento[] = [
  {
    value: "f1_2",
    postSett: 2,
    titolo: "2 post a settimana",
    nota: "per ogni social",
  },
  {
    value: "f3_4",
    postSett: 3,
    titolo: "3 post a settimana",
    nota: "per ogni social",
  },
  {
    value: "f5_piu",
    postSett: 5,
    titolo: "5 post a settimana",
    nota: "per ogni social",
  },
  {
    value: "decidete_voi",
    postSett: 3,
    titolo: "Lo decide il consorzio",
    nota: "conta come 3 post a settimana per ogni social",
  },
];

/** Post a settimana per social di una frequenza; 3 se non è tra quelle note. */
export function postASettimana(frequenza: string | null | undefined): number {
  return ABBONAMENTI.find((a) => a.value === frequenza)?.postSett ?? 3;
}

export function giorniTra(inizio: string, fine: string): number {
  return (
    Math.round(
      (new Date(fine + "T00:00:00").getTime() -
        new Date(inizio + "T00:00:00").getTime()) /
        86400000,
    ) + 1
  );
}

export interface ContoPost {
  giorni: number;
  settimane: number;
  giorniInPiu: number;
  /** Post per social nel periodo. */
  perSocial: number;
  /** Post di tutti i social scelti. */
  totale: number;
}

/** Il conto del server: post/settimana × giorni ÷ 7, per difetto, per ogni social. */
export function contaPost(
  postSett: number,
  inizio: string,
  fine: string,
  nSocial: number,
): ContoPost {
  const giorni = Math.max(0, giorniTra(inizio, fine));
  const perSocial = Math.floor((postSett * giorni) / 7);
  return {
    giorni,
    settimane: Math.floor(giorni / 7),
    giorniInPiu: giorni % 7,
    perSocial,
    totale: perSocial * nSocial,
  };
}

/** «4 settimane e 2 giorni», «1 settimana», «5 giorni». */
export function durataInSettimane(c: ContoPost): string {
  const sett =
    c.settimane === 0
      ? ""
      : `${c.settimane} ${c.settimane === 1 ? "settimana" : "settimane"}`;
  const gg =
    c.giorniInPiu === 0
      ? ""
      : `${c.giorniInPiu} ${c.giorniInPiu === 1 ? "giorno" : "giorni"}`;
  return [sett, gg].filter(Boolean).join(" e ") || "0 giorni";
}
