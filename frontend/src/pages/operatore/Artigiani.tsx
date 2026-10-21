/**
 * Elenco degli artigiani del consorzio (GET /artigiani, plan §3).
 *
 * Prima pagina dell'operatore: KPI sulle botteghe, ricerca e la tabella
 * in una finestra scrollabile. Il nome della bottega — o tutta la riga —
 * apre la scheda dell'artigiano.
 */
import { Alert, Button, Center, Loader, Text, TextInput } from "@mantine/core";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Link, useNavigate } from "react-router-dom";

import { elencoArtigiani, type ArtigianoElenco } from "../../api/artigiani";
import { BadgeCanale } from "../../components/IconaCanale";
import { Guscio } from "../../components/Guscio";
import { dataOra } from "./campagna/util";
import stile from "./Artigiani.module.css";

const ICONE_KPI = {
  botteghe: (
    <>
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </>
  ),
  daApprovare: (
    <>
      <path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2" />
      <rect x="9" y="3" width="6" height="4" rx="1" />
      <path d="m9 14 2 2 4-4" />
    </>
  ),
  inCorso: (
    <>
      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
    </>
  ),
  daCompilare: (
    <>
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="12" y1="18" x2="12" y2="12" />
      <line x1="9" y1="15" x2="15" y2="15" />
    </>
  ),
};

function Kpi({
  label,
  valore,
  icona,
  avviso,
}: {
  label: string;
  valore: number;
  icona: ReactNode;
  avviso?: boolean;
}) {
  return (
    <div className={stile.kpiCard}>
      <div className={`${stile.kpiIcona} ${avviso ? stile.avviso : ""}`}>
        <svg viewBox="0 0 24 24" aria-hidden="true">
          {icona}
        </svg>
      </div>
      <div className={stile.kpiTesto}>
        <div className={stile.kpiLabel}>{label}</div>
        <div className={`${stile.kpiNumero} ${avviso ? stile.avviso : ""}`}>
          {valore}
        </div>
      </div>
    </div>
  );
}

function RigaArtigiano({ r }: { r: ArtigianoElenco }) {
  const naviga = useNavigate();
  const scheda = `/artigiani/${r.id}`;
  const canali = ["facebook", "instagram"];
  return (
    <tr
      tabIndex={0}
      onClick={() => naviga(scheda)}
      onKeyDown={(e) => {
        if (e.key === "Enter") naviga(scheda);
      }}
    >
      <td>
        <Link
          to={scheda}
          className={stile.bottega}
          onClick={(e) => e.stopPropagation()}
        >
          {r.bottega ?? r.nome}
        </Link>
        <div className={stile.referente}>
          {r.bottega ? r.nome : r.email}
          {r.citta ? ` · ${r.citta}` : ""}
        </div>
      </td>
      <td>
        {r.bottega ? (
          <span className={`${stile.badge} ${stile.badgeNeutro}`}>
            Profilo compilato
          </span>
        ) : (
          <span className={`${stile.badge} ${stile.badgeAttesa}`}>
            Profilo da compilare
          </span>
        )}
        {!r.attivo && (
          <span className={`${stile.badge} ${stile.badgeSpento}`}>Sospeso</span>
        )}
      </td>
      <td>
        <div className={stile.canali}>
          {canali.map((canale) =>
            r.canali_collegati.includes(canale) ? (
              <BadgeCanale key={canale} canale={canale} size="xs" />
            ) : (
              <span
                key={canale}
                className={`${stile.badge} ${stile.badgeSpento}`}
              >
                {canale === "facebook" ? "Fb" : "Ig"}
              </span>
            ),
          )}
        </div>
      </td>
      <td>
        <span
          className={`${stile.contatore} ${
            r.n_da_approvare > 0 ? stile.contatoreAttesa : stile.contatoreNeutro
          }`}
        >
          {r.n_da_approvare}
        </span>
      </td>
      <td>
        <span
          className={`${stile.contatore} ${
            r.n_in_corso > 0 ? stile.contatoreVerde : stile.contatoreNeutro
          }`}
        >
          {r.n_in_corso}
        </span>
      </td>
      <td>
        {r.prossima_scadenza ? (
          <Link
            to={`/campagne/${r.prossima_campagna_id}`}
            className={stile.scadenza}
            onClick={(e) => e.stopPropagation()}
          >
            {dataOra(r.prossima_scadenza)}
          </Link>
        ) : (
          <span className={stile.vuoto}>
            {r.bottega ? "—" : "— · profilo da compilare"}
          </span>
        )}
      </td>
    </tr>
  );
}

export function Artigiani() {
  const [lista, setLista] = useState<ArtigianoElenco[] | null>(null);
  const [errore, setErrore] = useState<string | null>(null);
  const [cerca, setCerca] = useState("");

  useEffect(() => {
    elencoArtigiani()
      .then(setLista)
      .catch(() => setErrore("Non sono riuscita a leggere gli artigiani."));
  }, []);

  const visibili = useMemo(() => {
    const q = cerca.trim().toLowerCase();
    if (!q) return lista ?? [];
    return (lista ?? []).filter((r) =>
      [r.bottega, r.nome, r.citta, r.email].some(
        (v) => v?.toLowerCase().includes(q),
      ),
    );
  }, [lista, cerca]);

  const nDaApprovare = (lista ?? []).filter((r) => r.n_da_approvare > 0).length;
  const nInCorso = (lista ?? []).filter((r) => r.n_in_corso > 0).length;
  const nSenzaProfilo = (lista ?? []).filter((r) => r.bottega === null).length;

  return (
    <Guscio titolo="Artigiani" largo={1100}>
      {lista && (
        <div className={stile.kpi}>
          <Kpi
            label="Botteghe iscritte"
            valore={lista.length}
            icona={ICONE_KPI.botteghe}
          />
          <Kpi
            label="Con campagne da approvare"
            valore={nDaApprovare}
            icona={ICONE_KPI.daApprovare}
            avviso={nDaApprovare > 0}
          />
          <Kpi
            label="Con campagne in corso"
            valore={nInCorso}
            icona={ICONE_KPI.inCorso}
          />
          <Kpi
            label="Profilo da compilare"
            valore={nSenzaProfilo}
            icona={ICONE_KPI.daCompilare}
            avviso={nSenzaProfilo > 0}
          />
        </div>
      )}

      {errore && (
        <Alert color="red" variant="light" mb="md">
          {errore}
        </Alert>
      )}
      {!lista && !errore && (
        <Center py="xl">
          <Loader color="verde" />
        </Center>
      )}

      {lista && (
        <div className={stile.tabella}>
          <div className={stile.barra}>
            <div className={stile.barraSx}>
              <TextInput
                aria-label="Cerca artigiano"
                placeholder="Cerca per bottega, referente, città o email"
                value={cerca}
                onChange={(e) => setCerca(e.currentTarget.value)}
                w={340}
                leftSection={
                  <svg
                    width="15"
                    height="15"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    aria-hidden="true"
                  >
                    <circle cx="11" cy="11" r="7" />
                    <line x1="21" y1="21" x2="16.5" y2="16.5" />
                  </svg>
                }
              />
              <Text className={stile.conteggio} component="span">
                {visibili.length} di {lista.length} botteghe
              </Text>
            </div>
            <Button
              color="verde"
              component={Link}
              to="/nuovo-artigiano"
              leftSection={
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  aria-hidden="true"
                >
                  <line x1="12" y1="5" x2="12" y2="19" />
                  <line x1="5" y1="12" x2="19" y2="12" />
                </svg>
              }
            >
              Nuovo artigiano
            </Button>
          </div>
          <div className={stile.scorri}>
            <table>
              <thead>
                <tr>
                  <th>Bottega</th>
                  <th>Stato</th>
                  <th>Canali collegati</th>
                  <th>Da approvare</th>
                  <th>In corso</th>
                  <th>Prossima scadenza</th>
                </tr>
              </thead>
              <tbody>
                {visibili.map((r) => (
                  <RigaArtigiano key={r.id} r={r} />
                ))}
              </tbody>
            </table>
            {!visibili.length && (
              <div className={stile.vuota}>
                {cerca
                  ? "Nessun artigiano corrisponde alla ricerca."
                  : "Nessun artigiano ancora iscritto. Crealo da «Nuovo artigiano»."}
              </div>
            )}
          </div>
        </div>
      )}
    </Guscio>
  );
}
