/**
 * Date del calendario settimanale (spec R-48). Si lavora in UTC sulla sola
 * data AAAA-MM-GG: nel browser non c'è nessun fuso da calcolare.
 */

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

/** Somma giorni a una data AAAA-MM-GG lavorando in UTC sulla sola data: nessun fuso nel browser. */
export function sommaGiorni(data: string, giorni: number): string {
  const [anno, mese, giorno] = data.split("-").map(Number);
  return new Date(Date.UTC(anno, mese - 1, giorno + giorni))
    .toISOString()
    .slice(0, 10);
}

/** «19 – 25 ottobre 2026»; «28 settembre – 4 ottobre 2026» e «29 dicembre 2026 – 4 gennaio 2027» a cavallo. */
export function etichettaSettimana(dal: string, al: string): string {
  const [a1, m1, g1] = dal.split("-").map(Number);
  const [a2, m2, g2] = al.split("-").map(Number);
  const inizio =
    a1 !== a2
      ? `${g1} ${MESI[m1 - 1]} ${a1}`
      : m1 === m2
      ? `${g1}`
      : `${g1} ${MESI[m1 - 1]}`;
  return `${inizio} – ${g2} ${MESI[m2 - 1]} ${a2}`;
}
