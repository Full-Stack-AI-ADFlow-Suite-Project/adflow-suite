/**
 * Dati e comportamenti di esempio per l'archivio della bottega (T2a-52).
 * Simula le operazioni di backend in localStorage rispettando i vincoli di R-13.
 */
import { ApiErrore } from "../http";
import type { FotoSintetica, GruppoSintetico } from "../campagne";
import { sessioneEsempio, USA_ESEMPI } from "./accesso";

export { USA_ESEMPI };

const CHIAVE_ARCHIVIO_PREFISSO = "adflow_archivio_esempio_";

function chiaveArchivio(): { chiave: string; utenteId: number } {
  const u = sessioneEsempio();
  if (USA_ESEMPI && !u) throw new ApiErrore(401, "Sessione assente.");
  if (u && u.ruolo !== "artigiano") {
    throw new ApiErrore(403, "Accesso riservato agli artigiani.");
  }
  const utenteId = u?.id ?? 1;
  return { chiave: `${CHIAVE_ARCHIVIO_PREFISSO}${utenteId}`, utenteId };
}

function semiArchivio(utenteId: number): GruppoSintetico[] {
  if (utenteId !== 1) return [];
  return [
    {
      id: 1,
      origine: "caricate",
      descrizione: "Laboratorio e lavorazioni classiche",
      da_usare_il: null,
      n_immagini: null,
      foto: [
        {
          id: 1001,
          gruppo_id: 1,
          file: "laboratorio-banco.jpg",
          mime: "image/jpeg",
          larghezza: 1200,
          altezza: 1200,
          origine: "caricata",
        },
        {
          id: 1002,
          gruppo_id: 1,
          file: "dettaglio-legno.jpg",
          mime: "image/jpeg",
          larghezza: 1200,
          altezza: 1200,
          origine: "caricata",
        },
      ],
    },
  ];
}

function caricaGruppi(): GruppoSintetico[] {
  const { chiave, utenteId } = chiaveArchivio();
  const grezzo = localStorage.getItem(chiave);
  if (grezzo === null) {
    const iniziali = semiArchivio(utenteId);
    salvaGruppi(iniziali);
    return iniziali;
  }
  try {
    return JSON.parse(grezzo) as GruppoSintetico[];
  } catch {
    return [];
  }
}

function salvaGruppi(gruppi: GruppoSintetico[]): void {
  const { chiave } = chiaveArchivio();
  localStorage.setItem(chiave, JSON.stringify(gruppi));
}

function validaImmagineFile(
  file: File,
): Promise<{ larghezza: number; altezza: number }> {
  return new Promise((resolve, reject) => {
    const nome = file.name.toLowerCase();
    const tipo = file.type.toLowerCase();
    const estensioneAmmessa = /\.(jpe?g|png|webp)$/i.test(nome);
    const mimeAmmesso = [
      "image/jpeg",
      "image/jpg",
      "image/png",
      "image/webp",
    ].includes(tipo);

    if (file.size > 10 * 1024 * 1024) {
      reject(
        new ApiErrore(
          422,
          "La dimensione del file supera il limite massimo di 10 MB.",
        ),
      );
      return;
    }
    if (!estensioneAmmessa && !mimeAmmesso) {
      reject(
        new ApiErrore(
          422,
          "La foto non è un'immagine valida: usare JPG, PNG o WEBP.",
        ),
      );
      return;
    }

    if (typeof Image === "undefined") {
      resolve({ larghezza: 1200, altezza: 1200 });
      return;
    }

    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      URL.revokeObjectURL(url);
      const minLato = Math.min(img.naturalWidth, img.naturalHeight);
      if (minLato < 1080) {
        reject(
          new ApiErrore(
            422,
            "Il lato corto della foto deve essere di almeno 1080 px.",
          ),
        );
        return;
      }
      resolve({ larghezza: img.naturalWidth, altezza: img.naturalHeight });
    };
    img.onerror = () => {
      URL.revokeObjectURL(url);
      reject(
        new ApiErrore(
          422,
          "La foto non è un'immagine valida: usare JPG, PNG o WEBP.",
        ),
      );
    };
    img.src = url;
  });
}

function leggiComeDataUrl(file: File): Promise<string> {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => resolve(file.name);
    reader.readAsDataURL(file);
  });
}

export const esempiArchivio = {
  async elenco(): Promise<GruppoSintetico[]> {
    return structuredClone(caricaGruppi());
  },

  async creaGruppo(dati: { descrizione: string }): Promise<GruppoSintetico> {
    const desc = dati.descrizione?.trim();
    if (!desc) {
      throw new ApiErrore(
        422,
        "La descrizione del gruppo non può essere vuota.",
      );
    }
    const gruppi = caricaGruppi();
    const nuovoId =
      gruppi.length > 0 ? Math.max(...gruppi.map((g) => g.id)) + 1 : 1;
    const nuovo: GruppoSintetico = {
      id: nuovoId,
      origine: "caricate",
      descrizione: desc,
      da_usare_il: null,
      n_immagini: null,
      foto: [],
    };
    gruppi.push(nuovo);
    salvaGruppi(gruppi);
    return structuredClone(nuovo);
  },

  async eliminaGruppo(gruppoId: number): Promise<void> {
    const gruppi = caricaGruppi();
    const indice = gruppi.findIndex((g) => g.id === gruppoId);
    if (indice === -1) {
      throw new ApiErrore(404, "Gruppo non trovato nell'archivio.");
    }
    gruppi.splice(indice, 1);
    salvaGruppi(gruppi);
  },

  async caricaFoto(gruppoId: number, file: File): Promise<FotoSintetica> {
    const { larghezza, altezza } = await validaImmagineFile(file);
    const gruppi = caricaGruppi();
    const gruppo = gruppi.find((g) => g.id === gruppoId);
    if (!gruppo) {
      throw new ApiErrore(404, "Gruppo non trovato nell'archivio.");
    }
    if (gruppo.foto.length >= 20) {
      throw new ApiErrore(422, "Il gruppo non può contenere più di 20 foto.");
    }

    const tutteLeFoto = gruppi.flatMap((g) => g.foto);
    const nuovoId =
      tutteLeFoto.length > 0
        ? Math.max(...tutteLeFoto.map((f) => f.id)) + 1
        : 1;

    const dataUrl = await leggiComeDataUrl(file);

    const foto: FotoSintetica = {
      id: nuovoId,
      gruppo_id: gruppoId,
      file: dataUrl,
      mime: file.type || "image/jpeg",
      larghezza,
      altezza,
      origine: "caricata",
    };
    gruppo.foto.push(foto);
    salvaGruppi(gruppi);
    return structuredClone(foto);
  },

  async eliminaFoto(fotoId: number): Promise<void> {
    const gruppi = caricaGruppi();
    let trovata = false;
    for (const g of gruppi) {
      const prima = g.foto.length;
      g.foto = g.foto.filter((f) => f.id !== fotoId);
      if (g.foto.length !== prima) {
        trovata = true;
        break;
      }
    }
    if (!trovata) {
      throw new ApiErrore(404, "Foto non trovata nell'archivio.");
    }
    salvaGruppi(gruppi);
  },
};
