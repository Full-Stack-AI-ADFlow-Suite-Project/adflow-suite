/** Durata e costo come si leggono nello storico dell'AI. */

export function durata(ms: number | null): string {
  if (ms === null) return "—";
  return ms < 1000
    ? `${ms} ms`
    : `${(ms / 1000).toFixed(1).replace(".", ",")} s`;
}

/** Il costo arriva come stringa (Decimal); sotto il centesimo si vedono 4 cifre. */
export function costo(usd: string): string {
  const valore = Number(usd);
  if (!valore) return "0 $";
  return `${valore.toFixed(valore < 0.01 ? 4 : 2).replace(".", ",")} $`;
}
