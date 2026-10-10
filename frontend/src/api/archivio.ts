/**
 * Modulo archivio e logo della bottega (plan §3, spec R-13, R-27, R-40).
 * Gestisce il caricamento del logo e la gestione dell'archivio permanente della bottega.
 */
import { ApiErrore, leggiDettaglio, richiesta } from "./http";
import type { FotoSintetica, GruppoSintetico } from "./campagne";
import type { ProfiloPubblico } from "./artigiani";
import { esempiArchivio, USA_ESEMPI } from "./esempi/archivio";

export type { FotoSintetica, GruppoSintetico };

export interface FotoDettaglio {
  id: number;
  profilo_id: number;
  campagna_id: number | null;
  gruppo_id: number | null;
  origine: string;
  file: string;
  mime: string;
  larghezza: number;
  altezza: number;
  da_usare: boolean;
  n_utilizzi: number;
}

export interface GruppoArchivioCrea {
  descrizione: string;
}

export function urlLogo(logo?: string | null): string | null {
  if (!logo) return null;
  if (
    logo.startsWith("data:") ||
    logo.startsWith("blob:") ||
    logo.startsWith("http")
  ) {
    return logo;
  }
  if (USA_ESEMPI) {
    return `/assets/img/${logo}`;
  }
  return `/api/profilo/logo`;
}

export function urlFotoFile(file: string, id?: number): string {
  if (
    file.startsWith("data:") ||
    file.startsWith("blob:") ||
    file.startsWith("http")
  ) {
    return file;
  }
  if (USA_ESEMPI) {
    return `/assets/img/${file}`;
  }
  return id ? `/api/foto/${id}/file` : file;
}

export async function elencoArchivio(): Promise<GruppoSintetico[]> {
  if (USA_ESEMPI) return esempiArchivio.elenco();
  return richiesta<GruppoSintetico[]>("GET", "/archivio");
}

export async function creaGruppoArchivio(
  dati: GruppoArchivioCrea,
): Promise<GruppoSintetico> {
  if (USA_ESEMPI) return esempiArchivio.creaGruppo(dati);
  return richiesta<GruppoSintetico>("POST", "/archivio/gruppi", dati);
}

export async function eliminaGruppoArchivio(gruppoId: number): Promise<void> {
  if (USA_ESEMPI) return esempiArchivio.eliminaGruppo(gruppoId);
  return richiesta<void>("DELETE", `/archivio/gruppi/${gruppoId}`);
}

export async function caricaFotoArchivio(
  gruppoId: number,
  file: File,
): Promise<FotoSintetica> {
  if (USA_ESEMPI) return esempiArchivio.caricaFoto(gruppoId, file);
  const corpo = new FormData();
  corpo.append("file", file);
  corpo.append("gruppo_id", String(gruppoId));
  const risposta = await fetch("/api/archivio/foto", {
    method: "POST",
    body: corpo,
  });
  if (risposta.status === 401) throw new ApiErrore(401, "Sessione scaduta.");
  if (!risposta.ok) {
    const dati: unknown = await risposta.json().catch(() => null);
    throw new ApiErrore(risposta.status, leggiDettaglio(dati));
  }
  return (await risposta.json()) as FotoSintetica;
}

export async function eliminaFotoArchivio(fotoId: number): Promise<void> {
  if (USA_ESEMPI) return esempiArchivio.eliminaFoto(fotoId);
  return richiesta<void>("DELETE", `/archivio/foto/${fotoId}`);
}

export async function caricaLogo(file: File): Promise<ProfiloPubblico> {
  if (USA_ESEMPI) return esempiArchivio.salvaLogo(file);
  const corpo = new FormData();
  corpo.append("file", file);
  const risposta = await fetch("/api/profilo/logo", {
    method: "PUT",
    body: corpo,
  });
  if (risposta.status === 401) throw new ApiErrore(401, "Sessione scaduta.");
  if (!risposta.ok) {
    const dati: unknown = await risposta.json().catch(() => null);
    throw new ApiErrore(risposta.status, leggiDettaglio(dati));
  }
  return (await risposta.json()) as ProfiloPubblico;
}

export async function eliminaLogo(): Promise<void> {
  if (USA_ESEMPI) return esempiArchivio.eliminaLogo();
  return richiesta<void>("DELETE", "/profilo/logo");
}
