/**
 * La griglia del calendario settimanale (docs/pagine/AdFlow-calendario.html,
 * spec R-48, ADR-117, H5): sette colonne da lunedì a domenica, il giorno e la
 * data in testa, oggi evidenziato; in ogni colonna i post in ordine d'ora.
 * Fatta a mano, senza librerie. Sotto i 768 px diventa un elenco per giorno.
 * Serve l'artigiano e l'operatore: cambiano i dati e dove porta un clic.
 */
import { Badge } from "@mantine/core";
import { Link } from "react-router-dom";

import type {
  CalendarioSettimana as Settimana,
  PostSettimana,
} from "../api/campagne";
import stile from "./CalendarioSettimana.module.css";

const GIORNI = ["Dom", "Lun", "Mar", "Mer", "Gio", "Ven", "Sab"];

const CANALE: Record<string, [string, string]> = {
  facebook: ["Facebook", "blue"],
  instagram: ["Instagram", "grape"],
};

/** Lo stato del post come lo legge chi guarda il calendario. */
const STATO: Record<string, [string, string]> = {
  approvato: ["In programma", "blue"],
  pubblicato: ["Pubblicato", "green"],
  fallito: ["Non pubblicato", "red"],
  annullato: ["Non pubblicato", "red"],
};

/** Oggi nel browser, come AAAA-MM-GG. */
function oggi(): string {
  const adesso = new Date();
  const due = (n: number) => String(n).padStart(2, "0");
  return `${adesso.getFullYear()}-${due(adesso.getMonth() + 1)}-${due(
    adesso.getDate(),
  )}`;
}

function Scheda({
  post,
  lato,
  link,
}: {
  post: PostSettimana;
  lato: "artigiano" | "operatore";
  link: string;
}) {
  const [canale, coloreCanale] = CANALE[post.canale] ?? [post.canale, "gray"];
  const [stato, coloreStato] = STATO[post.stato] ?? [post.stato, "gray"];
  const foto = post.foto[0];
  return (
    <Link className={stile.post} to={link}>
      <span className={stile.riga}>
        <span className={stile.ora}>{post.ora}</span>
        <Badge size="xs" variant="light" color={coloreCanale}>
          {canale}
        </Badge>
      </span>
      {foto && (
        <img className={stile.foto} src={foto.url} alt="" loading="lazy" />
      )}
      <b>{post.campagna_titolo}</b>
      {lato === "operatore" && post.bottega && <span>{post.bottega}</span>}
      <Badge size="xs" variant="light" color={coloreStato}>
        {stato}
      </Badge>
    </Link>
  );
}

export function CalendarioSettimana({
  calendario,
  lato,
  link,
  bottega = null,
}: {
  calendario: Settimana;
  lato: "artigiano" | "operatore";
  /** Dove porta un clic su un post (brief-pagine.md §1.2). */
  link: (post: PostSettimana) => string;
  /** Solo i post di questa bottega; `null`: tutti. */
  bottega?: string | null;
}) {
  const adesso = oggi();
  return (
    <section
      className={stile.settimana}
      aria-label="Calendario della settimana"
    >
      {calendario.giorni.map((giorno) => {
        const [anno, mese, g] = giorno.data.split("-").map(Number);
        const nome = GIORNI[new Date(Date.UTC(anno, mese - 1, g)).getUTCDay()];
        const post = giorno.post.filter(
          (p) => !bottega || p.bottega === bottega,
        );
        return (
          <div
            key={giorno.data}
            className={
              giorno.data === adesso
                ? `${stile.giorno} ${stile.oggi}`
                : stile.giorno
            }
            aria-current={giorno.data === adesso ? "date" : undefined}
          >
            <div className={stile.testa}>
              <b>{nome}</b> {String(g).padStart(2, "0")}/
              {String(mese).padStart(2, "0")}
            </div>
            {post.length === 0 ? (
              <span className={stile.vuoto}>Nessun post</span>
            ) : (
              post.map((p) => (
                <Scheda key={p.id} post={p} lato={lato} link={link(p)} />
              ))
            )}
          </div>
        );
      })}
    </section>
  );
}
