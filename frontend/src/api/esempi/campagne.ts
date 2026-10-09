/**
 * Dati di esempio del modulo campagne, con la forma di plan §3 e le stesse
 * regole di service.py: post chiesti (post/settimana × giorni ÷ 7) e avvisi
 * di R-25 calcolati alla lettura. Seme: una campagna respinta, per la vista
 * di stato e l'avviso del Bentornato.
 */
import { ApiErrore } from "../http";
import type {
  CampagnaCrea,
  CampagnaDettaglio,
  CampagnaElencoItem,
  FotoSintetica,
  GruppoCrea,
  GruppoSintetico,
} from "../campagne";
import { canaliEsempio, profiloEsempio, USA_ESEMPI } from "./artigiani";

export { USA_ESEMPI };

// artigiani/domain.py
const POST_A_SETTIMANA: Record<string, number> = {
  f1_2: 2,
  f3_4: 3,
  f5_piu: 5,
  decidete_voi: 3,
};
// campagne/service.py · R-25
const LIMITI_POLICY_FOTO: Record<string, number> = {
  meno_5: 4,
  da5_a12: 12,
  da12_a20: 20,
};

const CHIAVE = "adflow_esempi_campagne";

function postChiesti(inizio: string, fine: string): number {
  const giorni =
    (new Date(fine + "T00:00:00").getTime() -
      new Date(inizio + "T00:00:00").getTime()) /
      86400000 +
    1;
  const postSett = POST_A_SETTIMANA[profiloEsempio.frequenza] ?? 3;
  return Math.max(0, Math.floor((postSett * giorni) / 7));
}

function carica(): CampagnaDettaglio[] {
  const grezzo = localStorage.getItem(CHIAVE);
  if (grezzo) {
    try {
      return JSON.parse(grezzo) as CampagnaDettaglio[];
    } catch {
      /* riseme sotto */
    }
  }
  const seme = seed();
  localStorage.setItem(CHIAVE, JSON.stringify(seme));
  return seme;
}

function salva(campagne: CampagnaDettaglio[]): void {
  localStorage.setItem(CHIAVE, JSON.stringify(campagne));
}

function seed(): CampagnaDettaglio[] {
  return [
    {
      id: 1,
      profilo_id: 1,
      titolo: "Campagna Luglio 2026",
      inizio: "2026-07-01",
      fine: "2026-07-31",
      descrizione: null,
      stato: "respinta",
      canali: ["facebook", "instagram"],
      canali_tolti: null,
      frequenza: "f3_4",
      obiettivo: "Farmi conoscere",
      inviata_il: "2026-06-18T10:12:00",
      chiusa_il: "2026-06-22T09:30:00",
      gruppi: [
        {
          id: 1,
          origine: "caricate",
          descrizione: "Il laboratorio e il tavolo in lavorazione.",
          da_usare_il: null,
          n_immagini: null,
          foto: [
            {
              id: 1,
              gruppo_id: 1,
              file: "laboratorio-1.jpg",
              mime: "image/jpeg",
              larghezza: 1200,
              altezza: 1200,
              da_usare: false,
              origine: "caricata",
            },
            {
              id: 2,
              gruppo_id: 1,
              file: "laboratorio-2.jpg",
              mime: "image/jpeg",
              larghezza: 1200,
              altezza: 1200,
              da_usare: false,
              origine: "caricata",
            },
            {
              id: 3,
              gruppo_id: 1,
              file: "tavolo-rovere-01.jpg",
              mime: "image/jpeg",
              larghezza: 1200,
              altezza: 1200,
              da_usare: false,
              origine: "caricata",
            },
            {
              id: 4,
              gruppo_id: 1,
              file: "tavolo-rovere-02.jpg",
              mime: "image/jpeg",
              larghezza: 1200,
              altezza: 1200,
              da_usare: false,
              origine: "caricata",
            },
            {
              id: 5,
              gruppo_id: 1,
              file: "sedie-01.jpg",
              mime: "image/jpeg",
              larghezza: 1200,
              altezza: 1200,
              da_usare: false,
              origine: "caricata",
            },
            {
              id: 6,
              gruppo_id: 1,
              file: "sedie-02.jpg",
              mime: "image/jpeg",
              larghezza: 1200,
              altezza: 1200,
              da_usare: false,
              origine: "caricata",
            },
          ],
        },
      ],
      post_chiesti_per_canale: { facebook: 13, instagram: 13 },
      avvisi: [],
      esito_respinta: {
        motivo: "foto scattate male",
        nota: "Le foto del laboratorio sono troppo buie: ricaricale con più luce e aggiungi il tavolo finito.",
        foto_segnate: [1, 2],
      },
    },
  ];
}

function conAvvisi(c: CampagnaDettaglio): CampagnaDettaglio {
  const canali = c.canali ?? [];
  const chiesti = postChiesti(c.inizio, c.fine);
  const post_chiesti_per_canale = Object.fromEntries(
    canali.map((k) => [k, chiesti]),
  );
  const nFoto = c.gruppi
    .filter((g) => g.origine === "caricate")
    .reduce((n, g) => n + g.foto.length, 0);
  const avvisi: string[] = [];
  if (chiesti > 0 && nFoto < chiesti) avvisi.push("foto_poche");
  if (chiesti > nFoto && chiesti - nFoto > nFoto / 2)
    avvisi.push("riempitivi_molti");
  const qMese = profiloEsempio.foto_policy.quantita_mese;
  const postSett = POST_A_SETTIMANA[profiloEsempio.frequenza] ?? 3;
  if (
    qMese &&
    qMese in LIMITI_POLICY_FOTO &&
    postSett * 4 > LIMITI_POLICY_FOTO[qMese]
  )
    avvisi.push("frequenza_alta");
  return { ...c, post_chiesti_per_canale, avvisi };
}

function trova(campagne: CampagnaDettaglio[], id: number): CampagnaDettaglio {
  const c = campagne.find((x) => x.id === id);
  if (!c) throw new ApiErrore(404, "Campagna non trovata.");
  return c;
}

function soloBozza(c: CampagnaDettaglio): void {
  if (c.stato !== "bozza")
    throw new ApiErrore(409, "Si può modificare solo una campagna in bozza.");
}

function nuovoId(campagne: CampagnaDettaglio[]): number {
  let massimo = 0;
  for (const c of campagne) {
    massimo = Math.max(massimo, c.id);
    for (const g of c.gruppi) {
      massimo = Math.max(massimo, g.id);
      for (const f of g.foto) massimo = Math.max(massimo, f.id);
    }
  }
  return massimo + 1;
}

export const esempiCampagne = {
  async elenco(): Promise<CampagnaElencoItem[]> {
    return carica().map(
      ({ id, profilo_id, titolo, inizio, fine, stato, canali }) => ({
        id,
        profilo_id,
        titolo,
        inizio,
        fine,
        stato,
        canali,
      }),
    );
  },

  async dettaglio(id: number): Promise<CampagnaDettaglio> {
    return conAvvisi(trova(carica(), id));
  },

  async crea(dati: CampagnaCrea): Promise<CampagnaDettaglio> {
    const campagne = carica();
    const c: CampagnaDettaglio = {
      id: nuovoId(campagne),
      profilo_id: 1,
      titolo: dati.titolo.trim(),
      inizio: dati.inizio,
      fine: dati.fine,
      descrizione: dati.descrizione ?? null,
      stato: "bozza",
      canali: dati.canali,
      canali_tolti: null,
      frequenza: profiloEsempio.frequenza,
      obiettivo: profiloEsempio.obiettivo,
      inviata_il: null,
      chiusa_il: null,
      gruppi: [],
      post_chiesti_per_canale: {},
      avvisi: [],
    };
    campagne.push(c);
    salva(campagne);
    return conAvvisi(c);
  },

  async creaGruppo(
    campagnaId: number,
    dati: GruppoCrea,
  ): Promise<GruppoSintetico> {
    const campagne = carica();
    const c = trova(campagne, campagnaId);
    soloBozza(c);
    const gruppo: GruppoSintetico = {
      id: nuovoId(campagne),
      origine: dati.origine ?? "caricate",
      descrizione: dati.descrizione ?? null,
      da_usare_il: dati.da_usare_il ?? null,
      n_immagini: dati.n_immagini ?? null,
      foto: [],
    };
    c.gruppi.push(gruppo);
    salva(campagne);
    return gruppo;
  },

  async aggiornaGruppo(
    campagnaId: number,
    gruppoId: number,
    dati: GruppoCrea,
  ): Promise<GruppoSintetico> {
    const campagne = carica();
    const c = trova(campagne, campagnaId);
    soloBozza(c);
    const g = c.gruppi.find((x) => x.id === gruppoId);
    if (!g) throw new ApiErrore(404, "Gruppo non trovato.");
    if (dati.descrizione !== undefined) g.descrizione = dati.descrizione;
    if (dati.da_usare_il !== undefined) g.da_usare_il = dati.da_usare_il;
    if (dati.n_immagini !== undefined) g.n_immagini = dati.n_immagini;
    salva(campagne);
    return g;
  },

  async eliminaGruppo(campagnaId: number, gruppoId: number): Promise<void> {
    const campagne = carica();
    const c = trova(campagne, campagnaId);
    soloBozza(c);
    c.gruppi = c.gruppi.filter((g) => g.id !== gruppoId);
    salva(campagne);
  },

  async caricaFoto(
    campagnaId: number,
    gruppoId: number,
    file: File,
  ): Promise<FotoSintetica> {
    const campagne = carica();
    const c = trova(campagne, campagnaId);
    soloBozza(c);
    const g = c.gruppi.find((x) => x.id === gruppoId);
    if (!g) throw new ApiErrore(422, "Serve un gruppo di foto caricate.");
    const foto: FotoSintetica = {
      id: nuovoId(campagne),
      gruppo_id: gruppoId,
      file: file.name,
      mime: file.type || "image/jpeg",
      larghezza: 1200,
      altezza: 1200,
      da_usare: false,
      origine: "caricata",
    };
    g.foto.push(foto);
    salva(campagne);
    return foto;
  },

  async eliminaFoto(fotoId: number): Promise<void> {
    const campagne = carica();
    for (const c of campagne) {
      for (const g of c.gruppi) {
        const prima = g.foto.length;
        g.foto = g.foto.filter((f) => f.id !== fotoId);
        if (g.foto.length !== prima) {
          soloBozza(c);
          salva(campagne);
          return;
        }
      }
    }
    throw new ApiErrore(404, "Foto non trovata.");
  },

  async stellaFoto(fotoId: number, daUsare: boolean): Promise<FotoSintetica> {
    const campagne = carica();
    for (const c of campagne) {
      for (const g of c.gruppi) {
        const f = g.foto.find((x) => x.id === fotoId);
        if (f) {
          soloBozza(c);
          f.da_usare = daUsare;
          salva(campagne);
          return f;
        }
      }
    }
    throw new ApiErrore(404, "Foto non trovata.");
  },

  async invia(campagnaId: number): Promise<CampagnaDettaglio> {
    const campagne = carica();
    const c = trova(campagne, campagnaId);
    soloBozza(c);
    const nFoto = c.gruppi
      .filter((g) => g.origine === "caricate")
      .reduce((n, g) => n + g.foto.length, 0);
    if (nFoto < 4)
      throw new ApiErrore(422, "Per inviare servono almeno 4 foto caricate.");
    if (c.gruppi.some((g) => !g.descrizione?.trim()))
      throw new ApiErrore(422, "Ogni gruppo vuole la sua descrizione.");
    const collegati = canaliEsempio
      .filter((k) => k.collegato)
      .map((k) => k.canale);
    if (!(c.canali ?? []).every((k) => collegati.includes(k)))
      throw new ApiErrore(409, "Un canale della campagna non è collegato.");
    c.stato = "inviata";
    c.inviata_il = new Date().toISOString();
    salva(campagne);
    return conAvvisi(c);
  },
};
