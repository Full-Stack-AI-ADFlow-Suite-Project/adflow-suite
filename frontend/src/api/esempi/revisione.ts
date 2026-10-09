/**
 * Dati di esempio del modulo revisione (plan §3): Vedi campagna dell'operatore
 * con piano, uscite, post dei canali, foto non usate e ultimo errore, più le
 * tre azioni dello sprint 1 (approva, prosegui, riprova). Le mutazioni tengono
 * il passo con il magazzino campagne (stessa fonte di verità locale).
 */
import { ApiErrore } from "../http";
import type { CampagnaDettaglio } from "../campagne";
import type {
  ErroreGenerazione,
  GruppoFotoNonUsate,
  Piano,
  PostVista,
  StatoPost,
  Uscita,
  VediCampagna,
  VersionePost,
} from "../revisione";
import { leggiCampagna, salvaCampagna } from "./campagne";
import { sessioneEsempio } from "./accesso";

interface RevisioneRecord {
  piano: Piano | null;
  uscite: Uscita[];
  foto_non_usate: GruppoFotoNonUsate[];
  ultimo_errore: ErroreGenerazione | null;
}

const CHIAVE = "adflow_esempi_revisione";

function carica(): Record<number, RevisioneRecord> {
  const grezzo = localStorage.getItem(CHIAVE);
  if (grezzo) {
    try {
      return JSON.parse(grezzo) as Record<number, RevisioneRecord>;
    } catch {
      /* riseme sotto */
    }
  }
  const seme = seed();
  localStorage.setItem(CHIAVE, JSON.stringify(seme));
  return seme;
}

function salva(dati: Record<number, RevisioneRecord>): void {
  localStorage.setItem(CHIAVE, JSON.stringify(dati));
}

/* ---------- Costruttori compatti del seme ---------- */

let _vid = 1;
function ver(
  testo: string,
  hashtag: string[],
  extra: Partial<VersionePost> = {},
): VersionePost {
  return {
    id: _vid++,
    numero: extra.numero ?? 1,
    testo,
    hashtag,
    autore_id: null,
    tipo_intervento: "generazione",
    testo_proposto: null,
    nota: null,
    provider_ai: "esempio",
    modello_ai: "esempio-1",
    versione_prompt: "1",
    errori_validazione: extra.errori_validazione ?? [],
    creata_il: extra.creata_il ?? "2026-11-03T11:00:00",
    foto: extra.foto ?? [],
    ...extra,
  };
}

function pst(
  postId: number,
  canale: string,
  dataOra: string,
  corrente: VersionePost | null,
  extra: Partial<PostVista> = {},
): PostVista {
  return {
    post_id: postId,
    canale,
    formato: "post",
    riempitivo: extra.riempitivo ?? null,
    data_ora: dataOra,
    stato: extra.stato ?? "da_approvare",
    da_rivedere: extra.da_rivedere ?? false,
    controllato_da: null,
    controllato_il: null,
    intervento_in_corso: null,
    intervento_dal: null,
    versione_corrente: corrente,
    versioni: corrente ? [corrente] : [],
    ...extra,
  };
}

function usc(
  numero: number,
  tema: string,
  gruppo: Uscita["gruppo"],
  post: PostVista[],
): Uscita {
  return { id: numero, numero, tema, gruppo, post };
}

/* ---------- Seme ---------- */

function seed(): Record<number, RevisioneRecord> {
  const g101 = {
    id: 101,
    origine: "caricate",
    descrizione: "Piatti e vassoi della linea autunno, smalto verde.",
    da_usare_il: null,
  };
  const g102 = {
    id: 102,
    origine: "caricate",
    descrizione:
      "Tazze decorate a mano e le porte aperte di sabato 21 novembre.",
    da_usare_il: "2026-11-21",
  };
  const g111 = {
    id: 111,
    origine: "caricate",
    descrizione: "Le borse della collezione inverno.",
    da_usare_il: null,
  };
  const g121 = {
    id: 121,
    origine: "caricate",
    descrizione: "La tavola apparecchiata e i dettagli.",
    da_usare_il: null,
  };
  const g131 = {
    id: 131,
    origine: "caricate",
    descrizione: "Sciarpe e plaid fotografati al telaio.",
    da_usare_il: null,
  };
  const g141 = {
    id: 141,
    origine: "caricate",
    descrizione: "Borse e portafogli della vetrina.",
    da_usare_il: null,
  };
  const g151 = {
    id: 151,
    origine: "caricate",
    descrizione: "Tende leggere per l'estate.",
    da_usare_il: null,
  };
  const g161 = {
    id: 161,
    origine: "caricate",
    descrizione: "Svuotatasche e copertine.",
    da_usare_il: null,
  };

  const strategiaOlivero =
    "Sei temi in due settimane: prima i piatti verdi, intero e da vicino, poi le tazze decorate e il lavoro al tornio; nella seconda settimana le porte aperte di sabato 21 e, per chiudere, gli ordini di Natale. Ogni tema esce su Facebook la sera e su Instagram la mattina dopo.";

  return {
    // Ceramiche Olivero · in_revisione: il banco di prova completo
    10: {
      piano: {
        id: 1,
        numero: 1,
        strategia: strategiaOlivero,
        esito_controllo: [
          "Post per canale uguali a quelli chiesti",
          "Riempitivi solo dove le foto non bastano",
          "Nessuna foto due volte sullo stesso canale",
          "La foto con la stella c'è",
          "Date dentro il periodo",
        ],
        debole: false,
        creata_il: "2026-11-03T11:02:00",
      },
      uscite: [
        usc(1, "I piatti verdi appena usciti dal forno", g101, [
          pst(
            1001,
            "facebook",
            "2026-11-09T18:30",
            ver(
              "I piatti che vedete qui sono usciti dal forno ieri. Smalto verde bosco, lo stesso che usava mio padre trent'anni fa.\n\nSe vi piace una tavola che racconta qualcosa, passate in bottega a Mondovì: li trovate tutti esposti.",
              ["#ceramica", "#fattoamano", "#mondovi"],
              { foto: [{ foto_id: 101, posizione: 0 }] },
            ),
          ),
          pst(
            1002,
            "instagram",
            "2026-11-10T10:00",
            ver(
              "Smalto verde bosco, appena sfornato. Ogni piatto è unico: le piccole differenze sono la firma del fatto a mano.",
              ["#ceramica", "#tavola", "#fattoamano", "#mondovi"],
              { foto: [{ foto_id: 101, posizione: 0 }] },
            ),
          ),
        ]),
        usc(2, "Da vicino: smalto e pennellate", g101, [
          pst(
            1003,
            "facebook",
            "2026-11-11T18:30",
            ver(
              "Lo smalto si riconosce da come prende la luce. Qui ogni pennellata si vede: niente stencil, niente decalcomanie.",
              ["#ceramica", "#dettagli", "#artigianato"],
              { foto: [{ foto_id: 103, posizione: 0 }] },
            ),
          ),
          pst(
            1004,
            "instagram",
            "2026-11-12T10:00",
            ver(
              "Da vicino si vede tutto: la pennellata, la mano, il tempo che ci vuole.",
              [
                "#ceramica",
                "#smalto",
                "#fattoamano",
                "#dettagli",
                "#mondovi",
                "#artigianato",
                "#handmade",
                "#piatti",
                "#tableware",
              ],
              {
                foto: [{ foto_id: 103, posizione: 0 }],
                errori_validazione: [
                  {
                    livello: "avviso",
                    regola: "max_hashtag",
                    messaggio:
                      "Gli hashtag sono 9: su instagram conviene restare entro 5.",
                  },
                ],
              },
            ),
          ),
        ]),
        usc(3, "Le tazze decorate per Natale", g102, [
          pst(
            1005,
            "facebook",
            "2026-11-13T18:30",
            ver(
              "Le tazze della linea invernale, decorate una a una. Ne abbiamo fatte poche, per chi cerca un regalo che non si trova altrove.",
              ["#tazze", "#regalidinatale", "#ceramica"],
              { foto: [{ foto_id: 104, posizione: 0 }] },
            ),
          ),
          pst(
            1006,
            "instagram",
            "2026-11-14T10:00",
            ver(
              "Tazze decorate a mano, pronte per Natale. A partire da 24 €.",
              ["#tazze", "#natale", "#ceramica", "#fattoamano"],
              {
                foto: [{ foto_id: 104, posizione: 0 }],
                errori_validazione: [
                  {
                    livello: "blocco",
                    regola: "prezzi_o_premi",
                    messaggio:
                      "Prezzo che non è nei dati della bottega (24 €).",
                  },
                ],
              },
            ),
            { da_rivedere: true },
          ),
        ]),
        usc(4, "Le mani al tornio", g102, [
          pst(
            1007,
            "facebook",
            "2026-11-16T18:30",
            ver(
              "Il tornio non perdona: una distrazione e il pezzo si piega. Ma è anche il momento più bello del mestiere.",
              ["#tornio", "#ceramica", "#mestiere"],
              { foto: [{ foto_id: 105, posizione: 0 }] },
            ),
          ),
          pst(
            1008,
            "instagram",
            "2026-11-17T10:00",
            ver(
              "Dodici anni al tornio, e il momento più bello resta questo.",
              ["#tornio", "#artigianato", "#ceramica"],
              { foto: [{ foto_id: 105, posizione: 0 }] },
            ),
          ),
        ]),
        usc(5, "Porte aperte in bottega, sabato 21 novembre", g102, [
          pst(
            1009,
            "facebook",
            "2026-11-18T18:30",
            ver(
              "Sabato 21 novembre la bottega è aperta a tutti, dalle 10 alle 18: venite a vedere come nasce un piatto, dal tornio al forno.",
              ["#porteaperte", "#mondovi", "#ceramica"],
              { foto: [{ foto_id: 106, posizione: 0 }] },
            ),
          ),
          pst(
            1010,
            "instagram",
            "2026-11-19T10:00",
            ver(
              "Sabato 21 porte aperte: dalle 10 alle 18 si entra, si guarda, si chiede.",
              ["#porteaperte", "#mondovi", "#ceramica", "#fattoamano"],
              { foto: [{ foto_id: 106, posizione: 0 }] },
            ),
          ),
        ]),
        usc(6, "Ordini su misura per Natale", null, [
          pst(
            1011,
            "facebook",
            "2026-11-20T18:30",
            ver(
              "Un servizio di piatti, un set di tazze con il nome inciso: per averli sotto l'albero gli ordini chiudono il 30 novembre.",
              ["#sumisura", "#natale", "#ceramica"],
              { foto: [{ foto_id: 906, posizione: 0 }] },
            ),
            { riempitivo: "cartolina" },
          ),
          pst(
            1012,
            "instagram",
            "2026-11-21T10:00",
            ver(
              "Per Natale, su misura: gli ordini chiudono il 30 novembre.",
              ["#natale", "#sumisura", "#ceramica"],
              { foto: [{ foto_id: 906, posizione: 0 }] },
            ),
            { riempitivo: "cartolina" },
          ),
        ]),
      ],
      foto_non_usate: [
        {
          gruppo_id: 102,
          descrizione:
            "Tazze decorate a mano e le porte aperte di sabato 21 novembre.",
          foto: [
            {
              foto_id: 102,
              motivo: "Non servita: i temi del piano erano già coperti.",
            },
            { foto_id: 107, motivo: "Sfocata: la decorazione non si legge." },
          ],
        },
      ],
      ultimo_errore: null,
    },

    // Pelletteria Ferrero · piano_da_rivedere: piano debole (R-20)
    11: {
      piano: {
        id: 2,
        numero: 1,
        strategia:
          "Quattro temi in quattro settimane: la borsa in cuoio, il laboratorio, la vetrina e gli ordini. Su ogni canale 2 foto disponibili su 8 post chiesti: il piano copre con cartoline.",
        esito_controllo: [
          "Post per canale uguali a quelli chiesti",
          "Riempitivi oltre uno ogni due foto nuove",
        ],
        debole: true,
        creata_il: "2026-10-08T15:52:00",
      },
      uscite: [
        usc(1, "La borsa in cuoio, il pezzo forte", g111, [
          pst(1101, "facebook", "2026-10-13T18:30", null),
          pst(1102, "instagram", "2026-10-14T10:00", null),
        ]),
        usc(2, "Il laboratorio e le cuciture a mano", g111, [
          pst(1103, "facebook", "2026-10-20T18:30", null, {
            riempitivo: "cartolina",
          }),
          pst(1104, "instagram", "2026-10-21T10:00", null, {
            riempitivo: "cartolina",
          }),
        ]),
        usc(3, "La vetrina d'inverno", g111, [
          pst(1105, "facebook", "2026-10-27T18:30", null),
          pst(1106, "instagram", "2026-10-28T10:00", null, {
            riempitivo: "cartolina",
          }),
        ]),
        usc(4, "Ordini e riparazioni", null, [
          pst(1107, "facebook", "2026-11-03T18:30", null, {
            riempitivo: "cartolina",
          }),
          pst(1108, "instagram", "2026-11-04T10:00", null, {
            riempitivo: "cartolina",
          }),
        ]),
      ],
      foto_non_usate: [
        {
          gruppo_id: 111,
          descrizione: "Le borse della collezione inverno.",
          foto: [
            {
              foto_id: 112,
              motivo: "Troppo scura: la pelle non si distingue dallo sfondo.",
            },
            { foto_id: 113, motivo: "Sottoesposta: non idonea." },
          ],
        },
      ],
      ultimo_errore: null,
    },

    // Ceramiche Olivero · generazione_fallita: errore accanto a Riprova
    12: {
      piano: {
        id: 3,
        numero: 1,
        strategia:
          "Tre temi in quattro settimane: la tavola apparecchiata, la zucca e i piatti, i dettagli.",
        esito_controllo: null,
        debole: false,
        creata_il: "2026-09-27T09:20:00",
      },
      uscite: [
        usc(1, "La tavola d'autunno apparecchiata", g121, [
          pst(1201, "instagram", "2026-10-06T10:00", null),
        ]),
        usc(2, "Zucca e piatti: la tavola di stagione", g121, [
          pst(1202, "instagram", "2026-10-13T10:00", null),
        ]),
        usc(3, "Dettagli: calici e decori", g121, [
          pst(1203, "instagram", "2026-10-20T10:00", null),
        ]),
      ],
      foto_non_usate: [],
      ultimo_errore: {
        tipo: "temporaneo",
        messaggio: "Il servizio AI non ha risposto in tempo.",
        tappa: "testi dei post",
        canale: "instagram",
        creata_il: "2026-09-27T09:48:00",
      },
    },

    // Tessitura Gallo · in_revisione pulita: Approva funziona
    13: {
      piano: {
        id: 4,
        numero: 1,
        strategia:
          "Quattro temi in un mese: la sciarpa in lana, il plaid, il telaio al lavoro, i colori d'autunno.",
        esito_controllo: [
          "Post per canale uguali a quelli chiesti",
          "La foto con la stella c'è",
          "Date dentro il periodo",
        ],
        debole: false,
        creata_il: "2026-10-06T11:30:00",
      },
      uscite: [
        usc(1, "La sciarpa in lana cardata", g131, [
          pst(
            1301,
            "facebook",
            "2026-10-15T18:30",
            ver(
              "La lana cardata a mano, come una volta: questa sciarpa nasce dal filato del Lanificio di Biella e passa sul nostro telaio un filo alla volta.",
              ["#tessitura", "#lana", "#fattoamano"],
              { foto: [{ foto_id: 131, posizione: 0 }] },
            ),
          ),
        ]),
        usc(2, "Il plaid che dura una vita", g131, [
          pst(
            1302,
            "facebook",
            "2026-10-22T18:30",
            ver(
              "Un plaid comprato oggi e tramandato domani: lana piena, bordi rifiniti a mano, nessun filo sintetico.",
              ["#plaid", "#lana", "#casa"],
              { foto: [{ foto_id: 132, posizione: 0 }] },
            ),
          ),
        ]),
        usc(3, "Al telaio: un filo alla volta", g131, [
          pst(
            1303,
            "facebook",
            "2026-10-29T18:30",
            ver(
              "Il telaio scandisce le giornate in bottega: qui nasce la stoffa delle vostre sciarpe, un filo alla volta.",
              ["#telaio", "#tessitura", "#artigianato"],
              { foto: [{ foto_id: 133, posizione: 0 }] },
            ),
          ),
        ]),
        usc(4, "I colori dell'autunno in lana", g131, [
          pst(
            1304,
            "facebook",
            "2026-11-05T18:30",
            ver(
              "Ruggine, verde bosco, grigio perla: la palette dell'autunno sulle nostre sciarpe.",
              ["#sciarpe", "#autunno", "#lana"],
              { foto: [{ foto_id: 134, posizione: 0 }] },
            ),
          ),
        ]),
      ],
      foto_non_usate: [],
      ultimo_errore: null,
    },

    // Pelletteria Ferrero · attiva
    14: {
      piano: {
        id: 5,
        numero: 1,
        strategia: "La vetrina d'inverno e i pezzi più richiesti.",
        esito_controllo: null,
        debole: false,
        creata_il: "2026-09-25T14:10:00",
      },
      uscite: [
        usc(1, "La vetrina d'inverno", g141, [
          pst(
            1401,
            "facebook",
            "2026-10-02T18:30",
            ver(
              "La vetrina è cambiata: dentro c'è tutta la collezione inverno.",
              ["#vetrina", "#pelletteria", "#alba"],
              { foto: [{ foto_id: 141, posizione: 0 }] },
            ),
            { stato: "pubblicato" },
          ),
        ]),
        usc(2, "Il portafoglio che non si consuma", g141, [
          pst(
            1402,
            "facebook",
            "2026-10-12T18:30",
            ver(
              "Cucito a mano, bordi levigati: un portafoglio che invecchia bene.",
              ["#portafoglio", "#pelle", "#fattoamano"],
              { foto: [{ foto_id: 142, posizione: 0 }] },
            ),
            { stato: "approvato" },
          ),
        ]),
      ],
      foto_non_usate: [],
      ultimo_errore: null,
    },

    // Tessitura Gallo · conclusa
    15: {
      piano: {
        id: 6,
        numero: 1,
        strategia: "Tende leggere per l'estate.",
        esito_controllo: null,
        debole: false,
        creata_il: "2026-07-20T09:12:00",
      },
      uscite: [
        usc(1, "Tende leggere per l'estate", g151, [
          pst(
            1501,
            "facebook",
            "2026-08-04T18:30",
            ver(
              "Lino leggero, trama aperta: le tende che lasciano passare la luce.",
              ["#tende", "#lino", "#estate"],
              { foto: [{ foto_id: 151, posizione: 0 }] },
            ),
            { stato: "pubblicato" },
          ),
        ]),
        usc(2, "Il bianco che non stanca", g151, [
          pst(
            1502,
            "facebook",
            "2026-08-11T18:30",
            ver(
              "Il bianco del lino lava via solo il sole.",
              ["#lino", "#casa", "#tende"],
              { foto: [{ foto_id: 152, posizione: 0 }] },
            ),
            { stato: "fallito" },
          ),
        ]),
      ],
      foto_non_usate: [],
      ultimo_errore: null,
    },

    // Pelletteria Ferrero · scaduta
    16: {
      piano: {
        id: 7,
        numero: 1,
        strategia: "Svuotatasche e copertine per la casa.",
        esito_controllo: null,
        debole: false,
        creata_il: "2026-09-10T17:00:00",
      },
      uscite: [
        usc(1, "Lo svuotatasche in pelle", g161, [
          pst(1601, "instagram", "2026-09-15T10:00", null, {
            stato: "scaduto" as StatoPost,
          }),
        ]),
        usc(2, "La copertina fatta a mano", g161, [
          pst(1602, "instagram", "2026-09-22T10:00", null, {
            stato: "scaduto" as StatoPost,
          }),
        ]),
      ],
      foto_non_usate: [],
      ultimo_errore: null,
    },
  };
}

/* ---------- Funzioni ---------- */

function operatore(): void {
  const utente = sessioneEsempio();
  if (!utente || (utente.ruolo !== "operatore" && utente.ruolo !== "admin"))
    throw new ApiErrore(403, "Non hai i permessi per questa operazione.");
}

function record(
  dati: Record<number, RevisioneRecord>,
  id: number,
): RevisioneRecord {
  const r = dati[id] ?? {
    piano: null,
    uscite: [],
    foto_non_usate: [],
    ultimo_errore: null,
  };
  dati[id] = r;
  return r;
}

function nuovoIdDecisione(c: CampagnaDettaglio): number {
  return (c.decisioni ?? []).reduce((m, d) => Math.max(m, d.id), 0) + 1;
}

export const esempiRevisione = {
  async vediCampagna(campagnaId: number): Promise<VediCampagna> {
    operatore();
    const c = leggiCampagna(campagnaId);
    if (c.stato === "bozza")
      throw new ApiErrore(
        409,
        "La campagna è ancora una bozza: arriva qui dopo l'invio.",
      );
    const r = record(carica(), campagnaId);
    return {
      campagna: {
        id: c.id,
        profilo_id: c.profilo_id,
        titolo: c.titolo,
        inizio: c.inizio,
        fine: c.fine,
        descrizione: c.descrizione,
        stato: c.stato,
        canali: c.canali,
        canali_tolti: c.canali_tolti,
        frequenza: c.frequenza,
        obiettivo: c.obiettivo,
        inviata_il: c.inviata_il,
        chiusa_il: c.chiusa_il,
      },
      piano: r.piano,
      uscite: r.uscite,
      foto_non_usate: r.foto_non_usate,
      ultimo_errore: r.ultimo_errore,
    };
  },

  /** Approva in blocco (R-14): mai con post da rivedere, interventi o zero post. */
  async approva(campagnaId: number): Promise<{ stato: string }> {
    operatore();
    const c = leggiCampagna(campagnaId);
    if (c.stato !== "in_revisione")
      throw new ApiErrore(409, "Si approva solo una campagna in revisione.");
    const r = record(carica(), campagnaId);
    const post = r.uscite.flatMap((u) => u.post);
    const daApprovare = post.filter((p) => p.stato === "da_approvare");
    const rivedere = daApprovare.filter((p) => p.da_rivedere);
    const inCorso = daApprovare.filter((p) => p.intervento_in_corso);
    if (!daApprovare.length)
      throw new ApiErrore(409, "Non c'è nessun post da approvare.");
    if (rivedere.length)
      throw new ApiErrore(
        409,
        `Non si può approvare: ${rivedere.length} post da rivedere.`,
      );
    if (inCorso.length)
      throw new ApiErrore(409, "Non si può approvare: intervento in corso.");
    const adesso = new Date().toISOString();
    for (const p of daApprovare)
      p.stato = p.data_ora < adesso ? "scaduto" : "approvato";
    c.stato = "attiva";
    (c.decisioni ??= []).push({
      id: nuovoIdDecisione(c),
      esito: "approvata",
      canale: null,
      post_id: null,
      motivo: null,
      nota: `${daApprovare.length} post approvati`,
    });
    salvaCampagna(c);
    const dati = carica();
    dati[campagnaId] = r;
    salva(dati);
    return { stato: "attiva" };
  },

  /** Prosegui da piano_da_rivedere: riparte la generazione (R-20). */
  async prosegui(campagnaId: number): Promise<{ stato: string }> {
    operatore();
    const c = leggiCampagna(campagnaId);
    if (c.stato !== "piano_da_rivedere")
      throw new ApiErrore(409, "Si prosegue solo un piano da rivedere.");
    const r = record(carica(), campagnaId);
    if (!r.piano) throw new ApiErrore(409, "Il piano non c'è ancora.");
    c.stato = "in_generazione";
    (c.decisioni ??= []).push({
      id: nuovoIdDecisione(c),
      esito: "proseguita",
      canale: null,
      post_id: null,
      motivo: null,
      nota: null,
    });
    salvaCampagna(c);
    salva(carica());
    return { stato: "in_generazione" };
  },

  /** Riprova da generazione_fallita: torna a inviata e riaccoda il job. */
  async riprova(campagnaId: number): Promise<CampagnaDettaglio> {
    operatore();
    const c = leggiCampagna(campagnaId);
    if (c.stato !== "generazione_fallita")
      throw new ApiErrore(
        409,
        "Si possono riprovare solo campagne con generazione fallita.",
      );
    c.stato = "inviata";
    salvaCampagna(c);
    return c;
  },
};
