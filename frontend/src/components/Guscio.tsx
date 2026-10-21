/**
 * Cornice delle pagine interne: barra laterale con marca, voci, utente
 * collegato ed Esci (docs/pagine, ADR-113).
 */
import { Avatar, Title } from "@mantine/core";
import { Link, useLocation, useNavigate } from "react-router-dom";
import type { ReactNode } from "react";

import type { Ruolo } from "../api/accesso";
import { useAuth } from "../contesto-auth";
import stile from "./Guscio.module.css";

export interface VoceNav {
  label: string;
  attivo?: boolean;
  /** Rotta della voce: senza, la voce è solo un'etichetta. */
  to?: string;
}

/**
 * Le voci del ruolo, come nelle pagine statiche. Valgono quando la pagina
 * non passa le sue.
 */
function vociDelRuolo(ruolo: Ruolo, percorso: string): VoceNav[] {
  if (ruolo === "artigiano")
    return [
      { label: "Ingresso", to: "/ingresso", attivo: percorso === "/ingresso" },
      {
        label: "Campagne",
        to: "/campagne",
        // La pagina Campagna si apre da qui: la voce resta accesa.
        attivo: percorso === "/campagne" || percorso === "/campagna",
      },
      {
        label: "Calendario",
        to: "/calendario",
        attivo: percorso === "/calendario",
      },
      {
        label: "Archivio foto",
        to: "/archivio",
        attivo: percorso === "/archivio",
      },
      {
        label: "Profilo bottega",
        to: "/profilo",
        attivo: percorso === "/profilo",
      },
    ];
  return [
    {
      label: "Da approvare",
      to: "/da-approvare",
      // Vedi campagna si apre da qui: la voce resta accesa.
      attivo: percorso === "/da-approvare" || percorso.startsWith("/campagne/"),
    },
    {
      label: "Artigiani",
      to: "/artigiani",
      // Pagina, campagne e archivio dell'artigiano si aprono da qui.
      attivo: percorso === "/artigiani" || percorso.startsWith("/artigiani/"),
    },
    {
      label: "Calendario",
      to: "/calendario",
      attivo: percorso === "/calendario",
    },
    {
      label: "Nuovo artigiano",
      to: "/nuovo-artigiano",
      attivo: percorso === "/nuovo-artigiano",
    },
  ];
}

const ICONE: Record<string, ReactNode> = {
  "Da approvare": (
    <>
      <path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2" />
      <rect x="9" y="3" width="6" height="4" rx="1" />
      <path d="m9 14 2 2 4-4" />
    </>
  ),
  Calendario: (
    <>
      <rect x="3" y="4" width="18" height="18" rx="2" />
      <line x1="16" y1="2" x2="16" y2="6" />
      <line x1="8" y1="2" x2="8" y2="6" />
      <line x1="3" y1="10" x2="21" y2="10" />
    </>
  ),
  "Archivio foto": (
    <>
      <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
      <circle cx="8.5" cy="8.5" r="1.5" />
      <polyline points="21 15 16 10 5 21" />
    </>
  ),
  Artigiani: (
    <>
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" />
    </>
  ),
  "Nuovo artigiano": (
    <>
      <circle cx="9" cy="7" r="4" />
      <path d="M3 21v-2a6 6 0 0 1 12 0v2M19 8v6M16 11h6" />
    </>
  ),
  Ingresso: (
    <>
      <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
      <polyline points="9 22 9 12 15 12 15 22" />
    </>
  ),
  Campagne: (
    <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
  ),
  "Profilo bottega": (
    <>
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
      <circle cx="12" cy="7" r="4" />
    </>
  ),
};

function Voce({ voce }: { voce: VoceNav }) {
  const icona = ICONE[voce.label];
  const contenuto = (
    <>
      {icona && (
        <svg viewBox="0 0 24 24" aria-hidden="true">
          {icona}
        </svg>
      )}
      <span>{voce.label}</span>
    </>
  );

  const classe = voce.attivo ? `${stile.voce} ${stile.attiva}` : stile.voce;
  const corrente = voce.attivo ? "page" : undefined;
  return voce.to ? (
    <Link className={classe} to={voce.to} aria-current={corrente}>
      {contenuto}
    </Link>
  ) : (
    <span className={classe} aria-current={corrente}>
      {contenuto}
    </span>
  );
}

export function Guscio({
  titolo,
  nav,
  largo = 720,
  children,
}: {
  titolo: string;
  nav?: VoceNav[];
  largo?: number;
  children: ReactNode;
}) {
  const { utente, esci } = useAuth();
  const naviga = useNavigate();
  const { pathname } = useLocation();

  const esciEVai = async () => {
    await esci();
    naviga("/accesso", { replace: true });
  };

  const artigiano = utente?.ruolo === "artigiano";
  const voci = nav ?? (utente ? vociDelRuolo(utente.ruolo, pathname) : []);

  return (
    <div className={stile.guscio}>
      <aside className={stile.barra}>
        <Link className={stile.marca} to="/">
          <span className={stile.marcaIcona}>
            <svg
              width="22"
              height="22"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <polygon points="12 2 2 7 12 12 22 7 12 2" />
              <polyline points="2 17 12 22 22 17" />
              <polyline points="2 12 12 17 22 12" />
            </svg>
          </span>
          <span className={stile.marcaTesto}>
            <b>AdFlow</b>
            <span>Suite · {artigiano ? "Artigiano" : "Operatore"}</span>
          </span>
        </Link>
        <nav
          className={stile.voci}
          aria-label={artigiano ? "Sezioni artigiano" : "Sezioni operatore"}
        >
          {voci.map((voce) => (
            <Voce key={voce.label} voce={voce} />
          ))}
        </nav>
        <div className={stile.piede}>
          {utente && (
            <div className={stile.utente}>
              <Avatar name={utente.nome} color="blu" radius="xl" size={36} />
              <div className={stile.utenteDati}>
                <div className={stile.utenteNome}>{utente.nome}</div>
                <div className={stile.utenteRuolo}>{utente.ruolo}</div>
              </div>
            </div>
          )}
          <button type="button" className={stile.esci} onClick={esciEVai}>
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
              <polyline points="16 17 21 12 16 7" />
              <line x1="21" y1="12" x2="9" y2="12" />
            </svg>
            <span>Esci</span>
          </button>
        </div>
      </aside>
      <main className={stile.contenuto}>
        <div className={stile.pagina} style={{ maxWidth: largo }}>
          <Title order={1} mb="md">
            {titolo}
          </Title>
          {children}
        </div>
      </main>
    </div>
  );
}
