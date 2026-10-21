/**
 * Dati di esempio del modulo campagne, con la forma di plan §3 e le stesse
 * regole di service.py: post chiesti (post/settimana × giorni ÷ 7) e avvisi
 * di R-25 calcolati alla lettura. Seme: una campagna respinta, per la vista
 * di stato e l'avviso del Bentornato.
 */
import { ApiErrore } from "../http";
import type {
  BloccoArchivio,
  CampagnaCrea,
  CampagnaModifica,
  CampagnaDettaglio,
  CampagnaElencoItem,
  FotoArchivio,
  FotoSintetica,
  GruppoCrea,
  GruppoSintetico,
  ProfiloSnapshot,
  CalendarioCampagna,
  CalendarioSettimana,
  GiornoSettimana,
  PostSettimana,
  FotoCalendario,
  PostCalendario,
  GiornoCalendario,
  CanaleToltoCalendario,
  RichiestaArtigiano,
  StatoRichiesta,
} from "../campagne";
import {
  canaliEsempio,
  profiliEsempio,
  profiloEsempio,
  USA_ESEMPI,
} from "./artigiani";
import { sessioneEsempio } from "./accesso";
import { leggiRevisioneRecord } from "./revisione";

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
              origine: "caricata",
            },
            {
              id: 2,
              gruppo_id: 1,
              file: "laboratorio-2.jpg",
              mime: "image/jpeg",
              larghezza: 1200,
              altezza: 1200,
              origine: "caricata",
            },
            {
              id: 3,
              gruppo_id: 1,
              file: "tavolo-rovere-01.jpg",
              mime: "image/jpeg",
              larghezza: 1200,
              altezza: 1200,
              origine: "caricata",
            },
            {
              id: 4,
              gruppo_id: 1,
              file: "tavolo-rovere-02.jpg",
              mime: "image/jpeg",
              larghezza: 1200,
              altezza: 1200,
              origine: "caricata",
            },
            {
              id: 5,
              gruppo_id: 1,
              file: "sedie-01.jpg",
              mime: "image/jpeg",
              larghezza: 1200,
              altezza: 1200,
              origine: "caricata",
            },
            {
              id: 6,
              gruppo_id: 1,
              file: "sedie-02.jpg",
              mime: "image/jpeg",
              larghezza: 1200,
              altezza: 1200,
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
    ...semiArtigiano(),
    ...semiOperatore(),
  ];
}

/**
 * Le altre campagne dell'artigiano di prova (T2b-53): una in corso con un
 * canale tolto, una in revisione e due chiuse. Con la respinta del primo
 * seme la pagina Campagna ha più campagne: si apre quella in corso, la
 * respinta e le chiuse stanno in "Campagne passate".
 */
function semiArtigiano(): CampagnaDettaglio[] {
  const base = {
    profilo_id: 1,
    descrizione: null,
    canali: ["facebook", "instagram"],
    canali_tolti: null,
    frequenza: "f3_4",
    obiettivo: "Farmi conoscere",
    post_chiesti_per_canale: {},
    avvisi: [],
    profilo_snapshot: fotografia(1),
    decisioni: [],
  };
  const gruppo = (id: number, nomi: string[]) => ({
    id,
    origine: "caricate",
    descrizione: "Il laboratorio e i pezzi finiti.",
    da_usare_il: null,
    n_immagini: null,
    foto: nomi.map((nome, i) => f(id * 10 + i, id, nome)),
  });
  return [
    {
      ...base,
      id: 2,
      titolo: "Primavera in bottega",
      inizio: "2026-04-06",
      fine: "2026-05-03",
      stato: "conclusa",
      inviata_il: "2026-03-28T09:40:00",
      chiusa_il: "2026-05-04T00:05:00",
      gruppi: [
        gruppo(181, [
          "sedia-01.jpg",
          "sedia-02.jpg",
          "sedia-03.jpg",
          "sedia-04.jpg",
        ]),
      ],
    },
    {
      ...base,
      id: 3,
      titolo: "Idee per l'estate",
      inizio: "2026-08-17",
      fine: "2026-09-06",
      stato: "scaduta",
      inviata_il: "2026-08-10T16:20:00",
      chiusa_il: "2026-08-17T00:00:00",
      gruppi: [
        gruppo(182, [
          "panca-01.jpg",
          "panca-02.jpg",
          "panca-03.jpg",
          "panca-04.jpg",
        ]),
      ],
    },
    {
      ...base,
      id: 18,
      titolo: "Autunno in bottega",
      inizio: "2026-10-05",
      fine: "2026-11-08",
      stato: "attiva",
      canali_tolti: ["instagram"],
      inviata_il: "2026-09-28T11:05:00",
      chiusa_il: null,
      gruppi: [
        gruppo(191, [
          "tavolo-01.jpg",
          "tavolo-02.jpg",
          "mensola-01.jpg",
          "mensola-02.jpg",
        ]),
      ],
      decisioni: [
        {
          id: 1,
          esito: "canale_tolto",
          canale: "instagram",
          post_id: null,
          motivo: null,
          nota: "Le foto non sono adatte al formato di Instagram: usciamo solo su Facebook.",
        },
        {
          id: 2,
          esito: "nota",
          canale: null,
          post_id: null,
          motivo: null,
          nota: "Mario risponde sempre tardi: chiamare di mattina.",
        },
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
      ...base,
      id: 19,
      titolo: "Natale in falegnameria",
      inizio: "2026-11-23",
      fine: "2026-12-20",
      stato: "in_revisione",
      // Il consorzio chiede due foto nuove (R-46): la richiesta è aperta.
      richiesta: {
        stato: "aperta",
        domanda:
          "La foto dell'albero mostra una cliente: puoi mandarne una senza persone? Mandane anche una dei giochi su una superficie chiara.",
        creata_il: "2026-10-12T09:30:00",
        foto: [
          { foto_id: 1920, gruppo_id: 192, nuova_foto_id: null },
          { foto_id: 1922, gruppo_id: 192, nuova_foto_id: null },
        ],
        risposta: null,
        inviata_il: null,
      },
      inviata_il: "2026-10-09T15:30:00",
      chiusa_il: null,
      gruppi: [
        gruppo(192, [
          "albero-01.jpg",
          "albero-02.jpg",
          "giochi-01.jpg",
          "giochi-02.jpg",
        ]),
      ],
    },
  ];
}

/** Una foto caricata nel seme, compatta. */
function f(id: number, gruppoId: number, file: string): FotoSintetica {
  return {
    id,
    gruppo_id: gruppoId,
    file,
    mime: "image/jpeg",
    larghezza: 1200,
    altezza: 1200,
    origine: "caricata",
  };
}

/** La fotografia come la salva l'invio: i nomi delle colonne del profilo. */
function fotografia(profiloId: number): ProfiloSnapshot {
  const b = profiliEsempio[profiloId];
  return {
    nome: b.bottega,
    referente: b.referente,
    citta: b.citta,
    tipo_prodotto: b.tipo_prodotto,
    obiettivo: b.obiettivo,
    frequenza: b.frequenza,
    tono: [b.tono],
    clienti_ideali: b.clienti,
    vincoli: b.da_non_dire,
  };
}

/** Le campagne delle altre botteghe, per la pagina dell'operatore (T1-53). */
function semiOperatore(): CampagnaDettaglio[] {
  const snap = fotografia;
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
            f(101, 101, "piatto-verde-01.jpg"),
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
            f(111, 111, "borsa-cuoio-01.jpg"),
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
            f(131, 131, "sciarpa-01.jpg"),
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

/** La richiesta decade quando la campagna esce da `in_revisione` senza risposta (R-46). */
function conRichiesta(c: CampagnaDettaglio): CampagnaDettaglio {
  if (!c.richiesta) return c;
  const stato: StatoRichiesta =
    c.richiesta.stato === "inviata"
      ? "inviata"
      : c.stato === "in_revisione"
      ? "aperta"
      : "decaduta";
  return { ...c, richiesta: { ...c.richiesta, stato } };
}

function statoRichiesta(c: CampagnaDettaglio): StatoRichiesta | null {
  return conRichiesta(c).richiesta?.stato ?? null;
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

/** Le campagne dopo l'approvazione: l'artigiano ne vede le immagini AI (R-47). */
const STATI_APPROVATA = ["attiva", "sospesa", "conclusa", "annullata"];

/** Un quadrato colorato con il nome della foto: negli esempi non ci sono file. */
function segnaposto(etichetta: string, ai: boolean, seme: number): string {
  const colore = `hsl(${(seme * 47) % 360} 35% ${ai ? 62 : 72}%)`;
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400"><rect width="400" height="400" fill="${colore}"/><text x="200" y="210" font-family="sans-serif" font-size="26" text-anchor="middle" fill="white">${etichetta}</text></svg>`;
  return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`;
}

export const esempiCampagne = {
  async elenco(
    stato?: string,
    artigiano?: number,
  ): Promise<CampagnaElencoItem[]> {
    const utente = sessioneEsempio();
    const operatore =
      utente?.ruolo === "operatore" || utente?.ruolo === "admin";
    // `artigiano` è l'id dell'utente; negli esempi coincide con la bottega (1–4).
    return carica()
      .filter((c) => (operatore ? true : c.profilo_id === 1))
      .filter((c) => !operatore || !artigiano || c.profilo_id === artigiano)
      .filter((c) => !stato || c.stato === stato)
      .map((c) => ({
        id: c.id,
        profilo_id: c.profilo_id,
        titolo: c.titolo,
        inizio: c.inizio,
        fine: c.fine,
        stato: c.stato,
        canali: c.canali,
        // Lo stato della richiesta si legge solo nell'elenco dell'artigiano (R-46).
        ...(!operatore && c.stato === "in_revisione"
          ? { richiesta: statoRichiesta(c) }
          : {}),
        ...(operatore
          ? {
              bottega: profiliEsempio[c.profilo_id]?.bottega ?? null,
              citta: profiliEsempio[c.profilo_id]?.citta ?? null,
            }
          : {}),
      }));
  },

  async dettaglio(id: number): Promise<CampagnaDettaglio> {
    const c = conAvvisi(conRichiesta(trova(carica(), id)));
    const utente = sessioneEsempio();
    if (utente?.ruolo === "operatore" || utente?.ruolo === "admin") return c;
    // L'artigiano non legge snapshot, note interne né le altre decisioni: solo
    // il canale tolto, con la nota (spec §4, R-32).
    return {
      ...c,
      profilo_snapshot: undefined,
      decisioni: (c.decisioni ?? []).filter((d) => d.esito === "canale_tolto"),
    };
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

  async modifica(
    id: number,
    dati: CampagnaModifica,
  ): Promise<CampagnaDettaglio> {
    const campagne = carica();
    const c = trova(campagne, id);
    soloBozza(c);

    const nuovoTitolo =
      dati.titolo !== undefined && dati.titolo !== null
        ? dati.titolo.trim()
        : c.titolo;
    const nuovaDescrizione =
      dati.descrizione !== undefined
        ? dati.descrizione?.trim() || null
        : c.descrizione;
    const nuovoInizio =
      dati.inizio !== undefined && dati.inizio !== null
        ? dati.inizio
        : c.inizio;
    const nuovoFine =
      dati.fine !== undefined && dati.fine !== null ? dati.fine : c.fine;
    const nuoviCanali =
      dati.canali !== undefined && dati.canali !== null
        ? dati.canali
        : c.canali ?? [];

    if (!nuovoTitolo) {
      throw new ApiErrore(422, "Il titolo non può essere vuoto.");
    }
    if (!nuoviCanali.length) {
      throw new ApiErrore(422, "Selezionare almeno un canale.");
    }

    // R-22, CA-48: solo canali con account collegato
    const collegati = canaliEsempio
      .filter((k) => k.collegato)
      .map((k) => k.canale);
    const nonCollegati = nuoviCanali.filter((ch) => !collegati.includes(ch));
    if (nonCollegati.length > 0) {
      throw new ApiErrore(
        422,
        `I seguenti canali non sono collegati: ${nonCollegati.join(", ")}.`,
      );
    }

    // R-08, CA-09: inizio >= oggi + 3 giorni
    const oggi = new Date();
    oggi.setHours(0, 0, 0, 0);
    const anticipoMinimo = 3;
    const dataMinima = new Date(oggi);
    dataMinima.setDate(dataMinima.getDate() + anticipoMinimo);
    const inizioData = new Date(nuovoInizio + "T00:00:00");
    if (inizioData < dataMinima) {
      throw new ApiErrore(
        422,
        `La data di inizio deve essere ad almeno ${anticipoMinimo} giorni da oggi.`,
      );
    }

    // R-08, CA-10: fine > inizio e durata tra 7 e 92 giorni
    const fineData = new Date(nuovoFine + "T00:00:00");
    if (fineData <= inizioData) {
      throw new ApiErrore(
        422,
        "La data di fine deve essere successiva alla data di inizio.",
      );
    }
    const durata =
      Math.round((fineData.getTime() - inizioData.getTime()) / 86400000) + 1;
    if (durata < 7) {
      throw new ApiErrore(
        422,
        "La durata della campagna deve essere di almeno 7 giorni.",
      );
    }
    if (durata > 92) {
      throw new ApiErrore(
        422,
        "La durata della campagna non può superare 92 giorni.",
      );
    }

    // R-12, CA-12: campagne non chiuse non sovrapposte
    const STATI_CHIUSI = ["annullata", "conclusa", "respinta", "scaduta"];
    const sovrapposta = campagne.find(
      (altra) =>
        altra.id !== c.id &&
        altra.profilo_id === c.profilo_id &&
        !STATI_CHIUSI.includes(altra.stato) &&
        altra.inizio <= nuovoFine &&
        altra.fine >= nuovoInizio,
    );
    if (sovrapposta) {
      throw new ApiErrore(
        409,
        "Il periodo si sovrappone a una campagna già esistente.",
      );
    }

    // R-13, T2a-21: se la data di un gruppo esce dal nuovo periodo -> 422
    for (const g of c.gruppi) {
      if (g.da_usare_il) {
        if (g.da_usare_il < nuovoInizio || g.da_usare_il > nuovoFine) {
          throw new ApiErrore(
            422,
            `La data di utilizzo del gruppo (${g.da_usare_il}) esce dal nuovo periodo della campagna.`,
          );
        }
      }
    }

    c.titolo = nuovoTitolo;
    c.descrizione = nuovaDescrizione;
    c.inizio = nuovoInizio;
    c.fine = nuovoFine;
    c.canali = nuoviCanali;

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

  async invia(
    campagnaId: number,
    dichiarazione: boolean,
  ): Promise<CampagnaDettaglio> {
    const campagne = carica();
    const c = trova(campagne, campagnaId);
    soloBozza(c);
    if (!dichiarazione)
      throw new ApiErrore(
        422,
        "Confermare la dichiarazione sulle foto prima dell'invio.",
      );
    if (c.gruppi.some((g) => !g.descrizione?.trim()))
      throw new ApiErrore(422, "Ogni gruppo vuole la sua descrizione.");
    const collegati = canaliEsempio
      .filter((k) => k.collegato)
      .map((k) => k.canale);
    if (!(c.canali ?? []).every((k) => collegati.includes(k)))
      throw new ApiErrore(409, "Un canale della campagna non è collegato.");
    c.stato = "inviata";
    c.inviata_il = new Date().toISOString();
    c.profilo_snapshot = {
      ...fotografia(1),
      dichiarazione: true,
      dichiarazione_data: new Date().toISOString(),
    };
    salva(campagne);
    return conAvvisi(c);
  },

  /** CA-86: l'operatore chiede una risposta e fino a 3 foto caricate della campagna. */
  async chiediArtigiano(
    campagnaId: number,
    domanda: string,
    foto: number[],
  ): Promise<RichiestaArtigiano> {
    const utente = sessioneEsempio();
    if (utente?.ruolo !== "operatore" && utente?.ruolo !== "admin")
      throw new ApiErrore(403, "Non hai i permessi per questa operazione.");
    const campagne = carica();
    const c = trova(campagne, campagnaId);
    if (c.stato !== "in_revisione")
      throw new ApiErrore(
        409,
        "Si chiede all'artigiano solo con la campagna in revisione.",
      );
    const testo = domanda.trim();
    if (!testo) throw new ApiErrore(422, "Scrivi la domanda per l'artigiano.");
    const ids = [...new Set(foto)];
    if (ids.length > 3)
      throw new ApiErrore(422, "Si chiedono al massimo 3 foto.");
    const mappa = new Map(
      c.gruppi.flatMap((g) => g.foto.map((f) => [f.id, f] as const)),
    );
    if (ids.some((id) => mappa.get(id)?.origine !== "caricata"))
      throw new ApiErrore(
        422,
        "Si possono segnare solo le foto caricate dall'artigiano per questa campagna.",
      );
    c.richiesta = {
      stato: "aperta",
      domanda: testo,
      creata_il: new Date().toISOString(),
      foto: ids.map((id) => ({
        foto_id: id,
        gruppo_id: mappa.get(id)?.gruppo_id ?? null,
        nuova_foto_id: null,
      })),
      risposta: null,
      inviata_il: null,
    };
    (c.decisioni ??= []).push({
      id: (c.decisioni ?? []).reduce((m, d) => Math.max(m, d.id), 0) + 1,
      esito: "integrazione",
      canale: null,
      post_id: null,
      motivo: null,
      nota: testo,
    });
    salva(campagne);
    return c.richiesta;
  },

  /** CA-87: la foto nuova entra nello stesso gruppo, senza analisi; serve la dichiarazione. */
  async caricaFotoRichiesta(
    campagnaId: number,
    fotoId: number,
    file: File,
    dichiarazione: boolean,
  ): Promise<FotoSintetica> {
    const campagne = carica();
    const c = trova(campagne, campagnaId);
    const aperta = conRichiesta(c).richiesta;
    if (aperta?.stato !== "aperta")
      throw new ApiErrore(409, "Non c'è una richiesta del consorzio aperta.");
    const segnata = aperta.foto.find((f) => f.foto_id === fotoId);
    if (!segnata)
      throw new ApiErrore(
        422,
        "Questa foto non è tra quelle chieste dal consorzio.",
      );
    if (segnata.nuova_foto_id !== null)
      throw new ApiErrore(
        409,
        "Per questa foto hai già caricato quella nuova.",
      );
    if (!dichiarazione)
      throw new ApiErrore(
        422,
        "Confermare la dichiarazione sulle foto prima di caricarle.",
      );
    const gruppo = c.gruppi.find((g) => g.id === segnata.gruppo_id);
    if (!gruppo) throw new ApiErrore(404, "Gruppo non trovato.");
    const nuova: FotoSintetica = {
      id: nuovoId(campagne),
      gruppo_id: gruppo.id,
      file: file.name,
      mime: file.type || "image/jpeg",
      larghezza: 1200,
      altezza: 1200,
      origine: "caricata",
    };
    gruppo.foto.push(nuova);
    const richiesta = c.richiesta as RichiestaArtigiano;
    const voce = richiesta.foto.find((f) => f.foto_id === fotoId);
    if (voce) voce.nuova_foto_id = nuova.id;
    (c.decisioni ??= []).push({
      id: (c.decisioni ?? []).reduce((m, d) => Math.max(m, d.id), 0) + 1,
      esito: "integrazione_foto",
      canale: null,
      post_id: null,
      motivo: null,
      nota: null,
    });
    salva(campagne);
    return nuova;
  },

  /** CA-88: con tutte le foto caricate la risposta parte; senza foto serve il testo. */
  async inviaRisposta(
    campagnaId: number,
    risposta: string | null,
  ): Promise<RichiestaArtigiano> {
    const campagne = carica();
    const c = trova(campagne, campagnaId);
    const aperta = conRichiesta(c).richiesta;
    if (aperta?.stato !== "aperta")
      throw new ApiErrore(409, "Non c'è una richiesta del consorzio aperta.");
    const mancanti = aperta.foto.filter((f) => f.nuova_foto_id === null).length;
    if (mancanti)
      throw new ApiErrore(409, `Mancano ${mancanti} foto da caricare.`);
    const testo = (risposta ?? "").trim() || null;
    if (!aperta.foto.length && testo === null)
      throw new ApiErrore(422, "Scrivi la risposta per il consorzio.");
    const richiesta = c.richiesta as RichiestaArtigiano;
    richiesta.stato = "inviata";
    richiesta.risposta = testo;
    richiesta.inviata_il = new Date().toISOString();
    (c.decisioni ??= []).push({
      id: (c.decisioni ?? []).reduce((m, d) => Math.max(m, d.id), 0) + 1,
      esito: "integrazione_risposta",
      canale: null,
      post_id: null,
      motivo: null,
      nota: testo,
    });
    salva(campagne);
    return richiesta;
  },

  /**
   * GET /archivio-foto (R-47): le foto dei gruppi di ogni campagna, più
   * un'immagine AI per le campagne approvate, che l'artigiano vede solo da
   * lì (CA-95). Negli esempi `artigiano` coincide con la bottega (1–4).
   */
  async archivioFoto(artigiano?: number): Promise<BloccoArchivio[]> {
    const utente = sessioneEsempio();
    const operatore =
      utente?.ruolo === "operatore" || utente?.ruolo === "admin";
    if (operatore && artigiano === undefined)
      throw new ApiErrore(422, "Indica l'artigiano di cui vedere le foto.");
    const profilo = operatore ? artigiano : 1;
    return carica()
      .filter((c) => c.profilo_id === profilo)
      .sort((a, b) => b.id - a.id)
      .map((c): BloccoArchivio => {
        const approvata = STATI_APPROVATA.includes(c.stato);
        const caricate = c.gruppi.flatMap((g) => g.foto);
        const foto = caricate.map(
          (f, i): FotoArchivio => ({
            id: f.id,
            url: segnaposto(f.file.replace(/\.\w+$/, ""), false, f.id),
            origine: "caricata",
            mime: f.mime,
            larghezza: f.larghezza,
            altezza: f.altezza,
            // Le prime foto di una campagna approvata sono già uscite.
            pubblicata_su:
              approvata && i < 2
                ? { facebook: `${c.inizio}T09:00:00+00:00` }
                : {},
          }),
        );
        if (operatore || approvata)
          foto.push({
            id: 100000 + c.id,
            url: segnaposto("immagine creata dall'AI", true, c.id),
            origine: "creata_ai",
            mime: "image/png",
            larghezza: 1024,
            altezza: 1024,
            pubblicata_su: approvata
              ? { instagram: `${c.inizio}T17:00:00+00:00` }
              : {},
          });
        return {
          campagna: {
            id: c.id,
            titolo: c.titolo,
            stato: c.stato,
            inizio: c.inizio,
            fine: c.fine,
          },
          foto,
        };
      })
      .filter((b) => b.foto.length > 0);
  },

  /**
   * GET /calendario (R-48): i post di un'agenda tipo (Facebook lunedì,
   * mercoledì e sabato; Instagram martedì, giovedì e sabato) delle campagne
   * approvate che coprono ogni giorno della settimana. Quelli già passati
   * risultano pubblicati, uno ogni tanto non pubblicato; gli altri in programma.
   */
  async calendarioSettimana(dal?: string): Promise<CalendarioSettimana> {
    const utente = sessioneEsempio();
    const operatore =
      utente?.ruolo === "operatore" || utente?.ruolo === "admin";
    const adesso = new Date();
    const due = (n: number) => String(n).padStart(2, "0");
    const oggi = `${adesso.getFullYear()}-${due(adesso.getMonth() + 1)}-${due(
      adesso.getDate(),
    )}`;
    const giornoSett = (data: string) =>
      (new Date(`${data}T00:00:00Z`).getUTCDay() + 6) % 7; // 0 = lunedì
    const piu = (data: string, n: number) =>
      new Date(Date.parse(`${data}T00:00:00Z`) + n * 86400000)
        .toISOString()
        .slice(0, 10);
    if (dal && giornoSett(dal) !== 0)
      throw new ApiErrore(422, "La settimana comincia di lunedì.");
    const lunedi = dal ?? piu(oggi, -giornoSett(oggi));

    const campagne = carica().filter(
      (c) =>
        STATI_APPROVATA.includes(c.stato) && (operatore || c.profilo_id === 1),
    );
    const giorni: GiornoSettimana[] = [];
    for (let i = 0; i < 7; i++) {
      const data = piu(lunedi, i);
      const post: PostSettimana[] = [];
      for (const c of campagne) {
        if (data < c.inizio || data > c.fine) continue;
        const canali = (c.canali ?? []).filter(
          (x) => !(c.canali_tolti ?? []).includes(x),
        );
        const agenda: [string, number, string][] = [
          ["facebook", 0, "09:00"],
          ["instagram", 1, "18:30"],
          ["facebook", 2, "09:00"],
          ["instagram", 3, "18:30"],
          ["facebook", 5, "10:00"],
          ["instagram", 5, "10:30"],
        ];
        const foto = c.gruppi.flatMap((g) => g.foto);
        agenda
          .filter(([canale, g]) => g === i && canali.includes(canale))
          .forEach(([canale, , ora], k) => {
            const quando = `${data}T${ora}:00`;
            const passato = new Date(quando) < adesso;
            const immagine = foto[(i + k) % Math.max(foto.length, 1)];
            post.push({
              id: Number(data.replaceAll("-", "")) * 100 + c.id * 2 + k,
              data_ora: quando,
              ora,
              canale,
              stato: !passato
                ? "approvato"
                : i === 2 && canale === "facebook" && c.id % 2 === 0
                ? "fallito"
                : "pubblicato",
              testo: `Post di esempio di ${c.titolo}`,
              hashtag: [],
              foto: immagine
                ? [
                    {
                      id: immagine.id,
                      url: segnaposto(
                        immagine.file.replace(/\.\w+$/, ""),
                        false,
                        immagine.id,
                      ),
                      mime: immagine.mime,
                      larghezza: immagine.larghezza,
                      altezza: immagine.altezza,
                      origine: immagine.origine,
                    },
                  ]
                : [],
              campagna_id: c.id,
              campagna_titolo: c.titolo,
              bottega: profiliEsempio[c.profilo_id]?.bottega ?? null,
            });
          });
      }
      post.sort((a, b) => a.data_ora.localeCompare(b.data_ora) || a.id - b.id);
      giorni.push({ data, post });
    }
    return { dal: lunedi, al: piu(lunedi, 6), giorni };
  },

  async calendario(campagnaId: number): Promise<CalendarioCampagna> {
    const campagne = carica();
    const c = trova(campagne, campagnaId);
    const u = sessioneEsempio();
    if (u && u.ruolo === "artigiano") {
      // Un artigiano legge solo le proprie campagne (spec R-45, CA-56)
      if (c.profilo_id !== 1) {
        throw new ApiErrore(404, "Campagna non trovata.");
      }
    }
    if (!["attiva", "sospesa", "conclusa", "annullata"].includes(c.stato)) {
      throw new ApiErrore(
        409,
        "Il calendario è disponibile dopo l'approvazione.",
      );
    }
    const rev = leggiRevisioneRecord(campagnaId);
    const tuttiPost = (rev?.uscite ?? []).flatMap((uscita) => uscita.post);
    const visibili = tuttiPost.filter((p) =>
      ["approvato", "pubblicato", "fallito", "annullato"].includes(p.stato),
    );
    const nScaduti = tuttiPost.filter((p) => p.stato === "scaduto").length;

    const giorniMap = new Map<string, PostCalendario[]>();
    for (const p of visibili) {
      const dataIso = p.data_ora.slice(0, 10);
      const ora = p.data_ora.includes("T")
        ? p.data_ora.split("T")[1].slice(0, 5)
        : "12:00";
      const v = p.versione_corrente;
      const foto: FotoCalendario[] = (v?.foto ?? []).map((f) => ({
        id: f.foto_id,
        url: `/api/foto/${f.foto_id}/file`,
        mime: "image/jpeg",
        larghezza: 1080,
        altezza: 1080,
        origine: p.riempitivo === "immagine_ai" ? "ai" : "originale",
      }));
      const postCal: PostCalendario = {
        id: p.post_id,
        data_ora: p.data_ora,
        ora,
        canale: p.canale,
        stato: p.stato,
        testo: v?.testo ?? "",
        hashtag: v?.hashtag ?? [],
        foto,
      };
      const arr = giorniMap.get(dataIso) ?? [];
      arr.push(postCal);
      giorniMap.set(dataIso, arr);
    }

    const giorni: GiornoCalendario[] = Array.from(giorniMap.entries())
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([data, post]) => ({
        data,
        post: post.sort((a, b) => a.data_ora.localeCompare(b.data_ora)),
      }));

    const noteCanaliTolti: Record<string, string> = {};
    for (const d of c.decisioni ?? []) {
      if (d.esito === "canale_tolto" && d.canale && d.nota) {
        noteCanaliTolti[d.canale] = d.nota;
      }
    }
    const canaliTolti: CanaleToltoCalendario[] = (c.canali_tolti ?? []).map(
      (canale) => ({
        canale,
        nota: noteCanaliTolti[canale] ?? null,
      }),
    );

    return {
      campagna_id: campagnaId,
      strategia: rev?.piano?.strategia ?? null,
      giorni,
      canali_tolti: canaliTolti,
      n_post_scaduti: nScaduti,
    };
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
