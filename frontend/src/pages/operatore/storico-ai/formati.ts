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

/** Un rapporto 0–1 come percentuale: «12%», e «<1%» se non è zero ma quasi. */
export function percentuale(rapporto: number): string {
  if (!rapporto) return "0%";
  const valore = rapporto * 100;
  return valore < 1 ? "<1%" : `${Math.round(valore)}%`;
}

/** Il voto medio con una cifra, «4,2 / 5»; «—» se nessuno ha votato. */
export function votoMedio(voto: number | null): string {
  return voto === null ? "—" : `${voto.toFixed(1).replace(".", ",")} / 5`;
}
