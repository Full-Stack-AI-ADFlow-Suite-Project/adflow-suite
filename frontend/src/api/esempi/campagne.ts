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
import {
  canaliEsempio,
  profiliEsempio,
  profiloEsempio,
  USA_ESEMPI,
} from "./artigiani";
import { sessioneEsempio } from "./accesso";

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

function postChiesti(
  inizio: string,
  fine: string,
  frequenza?: string | null,
): number {
  const giorni =
    (new Date(fine + "T00:00:00").getTime() -
      new Date(inizio + "T00:00:00").getTime()) /
      86400000 +
    1;
  const postSett = POST_A_SETTIMANA[frequenza ?? profiloEsempio.frequenza] ?? 3;
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
      decisioni: [
        {
          id: 1,
          esito: "respinta",
          canale: null,
          post_id: null,
          motivo: "foto",
          nota: "Le foto del laboratorio sono troppo buie: ricaricale con più luce e aggiungi il tavolo finito.",
        },
      ],
      esito_respinta: {
        motivo: "foto scattate male",
        nota: "Le foto del laboratorio sono troppo buie: ricaricale con più luce e aggiungi il tavolo finito.",
        foto_segnate: [1, 2],
      },
    },
    ...semiOperatore(),
  ];
}

/** Una foto caricata nel seme, compatta. */
function f(
  id: number,
  gruppoId: number,
  file: string,
  daUsare = false,
): FotoSintetica {
  return {
    id,
    gruppo_id: gruppoId,
    file,
    mime: "image/jpeg",
    larghezza: 1200,
    altezza: 1200,
    da_usare: daUsare,
    origine: "caricata",
  };
}

/** Le campagne delle altre botteghe, per la pagina dell'operatore (T1-53). */
function semiOperatore(): CampagnaDettaglio[] {
  const snap = (profiloId: number) => ({ ...profiliEsempio[profiloId] });
  return [
    {
      id: 10,
      profilo_id: 2,
      titolo: "Natale su misura",
      inizio: "2026-11-09",
      fine: "2026-11-22",
      descrizione:
        "A novembre voglio spingere i regali su misura. Sabato 21 teniamo le porte aperte: se ne parli nella seconda settimana.",
      stato: "in_revisione",
      canali: ["facebook", "instagram"],
      canali_tolti: null,
      frequenza: "f3_4",
      obiettivo: "Vendere di più",
      inviata_il: "2026-11-03T10:12:00",
      chiusa_il: null,
      gruppi: [
        {
          id: 101,
          origine: "caricate",
          descrizione: "Piatti e vassoi della linea autunno, smalto verde.",
          da_usare_il: null,
          n_immagini: null,
          foto: [
            f(101, 101, "piatto-verde-01.jpg", true),
            f(102, 101, "vassoio-01.jpg"),
            f(103, 101, "piatto-dettaglio.jpg"),
          ],
        },
        {
          id: 102,
          origine: "caricate",
          descrizione:
            "Tazze decorate a mano e le porte aperte di sabato 21 novembre.",
          da_usare_il: "2026-11-21",
          n_immagini: null,
          foto: [
            f(104, 102, "tazze-01.jpg"),
            f(105, 102, "mani-tornio.jpg"),
            f(106, 102, "bottega-ingresso.jpg"),
            f(107, 102, "tazze-sfocate.jpg"),
          ],
        },
      ],
      post_chiesti_per_canale: {},
      avvisi: [],
      profilo_snapshot: snap(2),
      decisioni: [],
    },
    {
      id: 11,
      profilo_id: 3,
      titolo: "Borse d'inverno",
      inizio: "2026-10-12",
      fine: "2026-11-08",
      descrizione: "Presentare la nuova collezione di borse.",
      stato: "piano_da_rivedere",
      canali: ["facebook", "instagram"],
      canali_tolti: null,
      frequenza: "f1_2",
      obiettivo: "Riempire l'agenda ordini",
      inviata_il: "2026-10-08T15:40:00",
      chiusa_il: null,
      gruppi: [
        {
          id: 111,
          origine: "caricate",
          descrizione: "Le borse della collezione inverno.",
          da_usare_il: null,
          n_immagini: null,
          foto: [
            f(111, 111, "borsa-cuoio-01.jpg", true),
            f(112, 111, "borsa-nero.jpg"),
            f(113, 111, "borsa-buia.jpg"),
          ],
        },
      ],
      post_chiesti_per_canale: {},
      avvisi: [],
      profilo_snapshot: snap(3),
      decisioni: [],
    },
    {
      id: 12,
      profilo_id: 2,
      titolo: "Autunno in tavola",
      inizio: "2026-10-05",
      fine: "2026-11-01",
      descrizione: "La tavola d'autunno con i pezzi della linea.",
      stato: "generazione_fallita",
      canali: ["instagram"],
      canali_tolti: null,
      frequenza: "f3_4",
      obiettivo: "Vendere di più",
      inviata_il: "2026-09-27T09:05:00",
      chiusa_il: null,
      gruppi: [
        {
          id: 121,
          origine: "caricate",
          descrizione: "La tavola apparecchiata e i dettagli.",
          da_usare_il: null,
          n_immagini: null,
          foto: [
            f(121, 121, "tavola-01.jpg"),
            f(122, 121, "zucca-piatti.jpg"),
            f(123, 121, "tavola-dettaglio.jpg"),
            f(124, 121, "calici.jpg"),
          ],
        },
      ],
      post_chiesti_per_canale: {},
      avvisi: [],
      profilo_snapshot: snap(2),
      decisioni: [],
    },
    {
      id: 13,
      profilo_id: 4,
      titolo: "Sciarpe e plaid",
      inizio: "2026-10-15",
      fine: "2026-11-15",
      descrizione: "Sciarpe e plaid in lana per l'autunno.",
      stato: "in_revisione",
      canali: ["facebook"],
      canali_tolti: null,
      frequenza: "f1_2",
      obiettivo: "Farmi conoscere",
      inviata_il: "2026-10-06T11:20:00",
      chiusa_il: null,
      gruppi: [
        {
          id: 131,
          origine: "caricate",
          descrizione: "Sciarpe e plaid fotografati al telaio.",
          da_usare_il: null,
          n_immagini: null,
          foto: [
            f(131, 131, "sciarpa-01.jpg", true),
            f(132, 131, "plaid-piegato.jpg"),
            f(133, 131, "telaio-filo.jpg"),
            f(134, 131, "sciarpa-colori.jpg"),
          ],
        },
      ],
      post_chiesti_per_canale: {},
      avvisi: [],
      profilo_snapshot: snap(4),
      decisioni: [],
    },
    {
      id: 14,
      profilo_id: 3,
      titolo: "Collezione inverno",
      inizio: "2026-10-01",
      fine: "2026-10-31",
      descrizione: "La collezione inverno in vetrina.",
      stato: "attiva",
      canali: ["facebook"],
      canali_tolti: null,
      frequenza: "f1_2",
      obiettivo: "Riempire l'agenda ordini",
      inviata_il: "2026-09-25T14:00:00",
      chiusa_il: null,
      gruppi: [
        {
          id: 141,
          origine: "caricate",
          descrizione: "Borse e portafogli della vetrina.",
          da_usare_il: null,
          n_immagini: null,
          foto: [f(141, 141, "vetrina-01.jpg"), f(142, 141, "portafoglio.jpg")],
        },
      ],
      post_chiesti_per_canale: {},
      avvisi: [],
      profilo_snapshot: snap(3),
      decisioni: [
        {
          id: 2,
          esito: "approvata",
          canale: null,
          post_id: null,
          motivo: null,
          nota: null,
        },
      ],
    },
    {
      id: 15,
      profilo_id: 4,
      titolo: "Tende d'estate",
      inizio: "2026-08-01",
      fine: "2026-08-31",
      descrizione: null,
      stato: "conclusa",
      canali: ["facebook"],
      canali_tolti: null,
      frequenza: "f1_2",
      obiettivo: "Farmi conoscere",
      inviata_il: "2026-07-20T09:00:00",
      chiusa_il: "2026-09-01T00:05:00",
      gruppi: [
        {
          id: 151,
          origine: "caricate",
          descrizione: "Tende leggere per l'estate.",
          da_usare_il: null,
          n_immagini: null,
          foto: [f(151, 151, "tenda-01.jpg"), f(152, 151, "tenda-02.jpg")],
        },
      ],
      post_chiesti_per_canale: {},
      avvisi: [],
      profilo_snapshot: snap(4),
      decisioni: [
        {
          id: 3,
          esito: "approvata",
          canale: null,
          post_id: null,
          motivo: null,
          nota: null,
        },
      ],
    },
    {
      id: 16,
      profilo_id: 3,
      titolo: "Idee per la casa",
      inizio: "2026-09-14",
      fine: "2026-09-27",
      descrizione: "Piccoli accessori in pelle per la casa.",
      stato: "scaduta",
      canali: ["instagram"],
      canali_tolti: null,
      frequenza: "f1_2",
      obiettivo: "Riempire l'agenda ordini",
      inviata_il: "2026-09-10T16:45:00",
      chiusa_il: "2026-09-14T00:00:00",
      gruppi: [
        {
          id: 161,
          origine: "caricate",
          descrizione: "Svuotatasche e copertine.",
          da_usare_il: null,
          n_immagini: null,
          foto: [f(161, 161, "svuotatasche.jpg"), f(162, 161, "copertina.jpg")],
        },
      ],
      post_chiesti_per_canale: {},
      avvisi: [],
      profilo_snapshot: snap(3),
      decisioni: [],
    },
    {
      id: 17,
      profilo_id: 2,
      titolo: "Collezione primavera",
      inizio: "2026-10-20",
      fine: "2026-11-16",
      descrizione: "Anticipare la linea primavera.",
      stato: "in_generazione",
      canali: ["facebook", "instagram"],
      canali_tolti: null,
      frequenza: "f3_4",
      obiettivo: "Vendere di più",
      inviata_il: "2026-10-09T08:30:00",
      chiusa_il: null,
      gruppi: [
        {
          id: 171,
          origine: "caricate",
          descrizione: "Prove smalto della linea primavera.",
          da_usare_il: null,
          n_immagini: null,
          foto: [
            f(171, 171, "smalto-01.jpg"),
            f(172, 171, "smalto-02.jpg"),
            f(173, 171, "ciotole-01.jpg"),
            f(174, 171, "ciotole-02.jpg"),
          ],
        },
      ],
      post_chiesti_per_canale: {},
      avvisi: [],
      profilo_snapshot: snap(2),
      decisioni: [],
    },
  ];
}

function conAvvisi(c: CampagnaDettaglio): CampagnaDettaglio {
  const canali = c.canali ?? [];
  const chiesti = postChiesti(c.inizio, c.fine, c.frequenza);
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
  async elenco(stato?: string): Promise<CampagnaElencoItem[]> {
    const utente = sessioneEsempio();
    const operatore =
      utente?.ruolo === "operatore" || utente?.ruolo === "admin";
    return carica()
      .filter((c) => (operatore ? true : c.profilo_id === 1))
      .filter((c) => !stato || c.stato === stato)
      .map(({ id, profilo_id, titolo, inizio, fine, stato: st, canali }) => ({
        id,
        profilo_id,
        titolo,
        inizio,
        fine,
        stato: st,
        canali,
        ...(operatore
          ? {
              bottega: profiliEsempio[profilo_id]?.bottega ?? null,
              citta: profiliEsempio[profilo_id]?.citta ?? null,
            }
          : {}),
      }));
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
    c.profilo_snapshot = { ...profiliEsempio[1] };
    salva(campagne);
    return conAvvisi(c);
  },
};

/**
 * Accesso al record interno per il modulo revisione degli esempi:
 * legge senza ricalcoli e salva dopo le mutazioni (stesso localStorage).
 */
export function leggiCampagna(id: number): CampagnaDettaglio {
  return trova(carica(), id);
}

export function salvaCampagna(campagna: CampagnaDettaglio): void {
  const campagne = carica();
  const i = campagne.findIndex((c) => c.id === campagna.id);
  if (i < 0) throw new ApiErrore(404, "Campagna non trovata.");
  campagne[i] = campagna;
  salva(campagne);
}
