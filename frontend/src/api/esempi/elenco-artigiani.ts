/**
 * Dati di esempio delle pagine degli artigiani dell'operatore (spec R-38,
 * CA-92, CA-93): elenco e pagina dell'artigiano. Gli artigiani 1–4 sono le
 * botteghe di `profiliEsempio` (l'id dell'utente è quello della bottega); il
 * quinto non ha ancora compilato il profilo. Conteggi e scadenze si ricavano
 * dalle campagne di esempio, come fa il backend.
 */
import type { ProfiloPubblico, SchedaArtigiano } from "../artigiani";
import { SCELTE } from "../artigiani";
import { ApiErrore } from "../http";
import type { ArtigianoElenco } from "../revisione";
import { sessioneEsempio } from "./accesso";
import { profiliEsempio, type BottegaEsempio } from "./artigiani";
import { esempiCampagne } from "./campagne";
import { esempiDecisioni } from "./decisioni";

interface ArtigianoEsempio {
  id: number;
  nome: string;
  email: string;
  attivo: boolean;
  /** Collegati (facebook, instagram); vuoto senza profilo. */
  canali: string[];
}

const ARTIGIANI: ArtigianoEsempio[] = [
  {
    id: 1,
    nome: "Mario Bianchi",
    email: "mario@falegnameriabianchi.it",
    attivo: true,
    canali: ["facebook", "instagram"],
  },
  {
    id: 2,
    nome: "Anna Olivero",
    email: "anna@ceramicheolivero.it",
    attivo: true,
    canali: ["instagram"],
  },
  {
    id: 3,
    nome: "Giulia Ferrero",
    email: "giulia@pelletteriaferrero.it",
    attivo: true,
    canali: ["facebook", "instagram"],
  },
  {
    id: 4,
    nome: "Paolo Gallo",
    email: "paolo@tessituragallo.it",
    attivo: true,
    canali: ["facebook"],
  },
  {
    id: 5,
    nome: "Paolo Costa",
    email: "paolo.costa@example.it",
    attivo: true,
    canali: [],
  },
];

function operatore(): void {
  const utente = sessioneEsempio();
  if (!utente || (utente.ruolo !== "operatore" && utente.ruolo !== "admin"))
    throw new ApiErrore(403, "Non hai i permessi per questa operazione.");
}

export async function elencoArtigianiEsempio(): Promise<ArtigianoElenco[]> {
  operatore();
  const tutte = await esempiCampagne.elenco();
  const daApprovare = await esempiDecisioni.daApprovare();
  const righe = ARTIGIANI.map((a): ArtigianoElenco => {
    const bottega = profiliEsempio[a.id];
    const sue = daApprovare.filter((c) => c.profilo_id === a.id);
    const scadenze = sue
      .map((c) => c.entro_quando)
      .filter((s): s is string => s !== null)
      .sort();
    return {
      id: a.id,
      nome: a.nome,
      email: a.email,
      attivo: a.attivo,
      bottega: bottega?.bottega ?? null,
      referente: bottega?.referente ?? null,
      citta: bottega?.citta ?? null,
      canali_collegati: a.canali,
      n_da_approvare: sue.length,
      n_in_corso: tutte.filter(
        (c) =>
          c.profilo_id === a.id &&
          (c.stato === "attiva" || c.stato === "sospesa"),
      ).length,
      prossima_scadenza: scadenze[0] ?? null,
    };
  });
  // Prima la scadenza più vicina, in fondo chi non ce l'ha; poi la bottega.
  return righe.sort(
    (a, b) =>
      (a.prossima_scadenza ?? "9").localeCompare(b.prossima_scadenza ?? "9") ||
      (a.bottega ?? a.nome)
        .toLowerCase()
        .localeCompare((b.bottega ?? b.nome).toLowerCase()),
  );
}

/** Il valore di una scelta (`SCELTE`) dalla sua etichetta; se non c'è, il primo. */
function valore(campo: keyof typeof SCELTE, etichetta: string): string {
  const scelte = SCELTE[campo];
  return (scelte.find((s) => s.label === etichetta) ?? scelte[0]).value;
}

function profiloDi(id: number, b: BottegaEsempio): ProfiloPubblico {
  return {
    id,
    nome: b.bottega,
    referente: b.referente,
    citta: b.citta,
    tipo_prodotto: valore("tipo_prodotto", b.tipo_prodotto),
    clienti_ideali: b.clienti,
    obiettivo: valore("obiettivo", b.obiettivo),
    canali: ARTIGIANI.find((a) => a.id === id)?.canali ?? [],
    anni_attivita: 20,
    sito: null,
    storia: `${b.bottega}: ${b.tipo_prodotto.toLowerCase()} fatti a mano.`,
    origine: null,
    valori: ["artigianalita", "territorio"],
    gamma: null,
    fascia_prezzo: "media",
    stagionalita: null,
    zona: null,
    tono: ["caldo"],
    cortesia: "tu",
    vincoli: b.da_non_dire,
    frequenza: b.frequenza,
    orari: null,
    social_esistenti: null,
    foto_policy: { quantita_mese: "da5_a12" },
    eventi_ricorrenti: null,
    chiusure: null,
    aggiornato_il: "2026-10-10T00:00:00Z",
  };
}

export async function schedaArtigianoEsempio(
  id: number,
): Promise<SchedaArtigiano> {
  operatore();
  const a = ARTIGIANI.find((x) => x.id === id);
  if (!a) throw new ApiErrore(404, "Artigiano non trovato.");
  const bottega = profiliEsempio[id];
  return {
    id: a.id,
    nome: a.nome,
    email: a.email,
    attivo: a.attivo,
    profilo: bottega ? profiloDi(id, bottega) : null,
    canali_collegati: a.canali,
  };
}
