/**
 * Scheda di un artigiano (GET /artigiani/{utente_id}, plan §3).
 *
 * Anagrafica, canali collegati e campagne separate per stato — da approvare
 * e in corso in cima, ultime chiuse sotto — più il profilo della bottega
 * in sola lettura. Le campagne portano alla vista di dettaglio.
 */
import {
  Alert,
  Anchor,
  Card,
  Center,
  Divider,
  Group,
  Loader,
  Stack,
  Text,
} from "@mantine/core";
import { useEffect, useState, type ReactNode } from "react";
import { Link, useParams } from "react-router-dom";

import {
  schedaArtigiano,
  type CampagnaSezione,
  type SchedaArtigiano,
} from "../../api/artigiani";
import type { CampagnaDaApprovare } from "../../api/decisioni";
import { BadgeCanale } from "../../components/IconaCanale";
import { Guscio } from "../../components/Guscio";
import { coloreCampagna, data, dataOra } from "./campagna/util";
import stile from "./Artigiani.module.css";

function periodo(inizio: string, fine: string): string {
  return `${data(inizio)} – ${data(fine)}`;
}

/** Classe del badge per lo stato della campagna (colori di coloreCampagna). */
const CLASSE_STATO: Record<string, string> = {
  verde: stile.badgeVerde,
  red: stile.badgeRosso,
  yellow: stile.badgeAttesa,
  orange: stile.badgeArancio,
  dark: stile.badgeScuro,
  gray: stile.badgeNeutro,
};

function BadgeStato({ stato }: { stato: string }) {
  return (
    <span
      className={`${stile.badge} ${
        CLASSE_STATO[coloreCampagna(stato)] ?? stile.badgeNeutro
      }`}
    >
      {stato.replaceAll("_", " ")}
    </span>
  );
}

function Voce({
  label,
  valore,
}: {
  label: string;
  valore: string | number | null | undefined;
}) {
  if (valore === null || valore === undefined || valore === "") return null;
  return (
    <div>
      <Text size="xs" c="dimmed" fw={600} tt="uppercase" lts={0.4}>
        {label}
      </Text>
      <Text size="sm" mt={2} style={{ whiteSpace: "pre-wrap" }}>
        {valore}
      </Text>
    </div>
  );
}

function RigaSezione({ c, extra }: { c: CampagnaSezione; extra?: ReactNode }) {
  return (
    <tr>
      <td>
        <Link to={`/campagne/${c.id}`} className={stile.bottega}>
          {c.titolo}
        </Link>
      </td>
      <td>
        <BadgeStato stato={c.stato} />
      </td>
      <td>
        <Text size="sm">{periodo(c.inizio, c.fine)}</Text>
      </td>
      <td>
        <Text size="sm">
          {c.n_post} post
          {c.n_falliti > 0 && (
            <Text span c="red" fw={600}>
              {" "}
              · {c.n_falliti} falliti
            </Text>
          )}
        </Text>
      </td>
      {extra}
    </tr>
  );
}

function TabellaCampagne({
  titolo,
  campagne,
  intestazioneExtra,
  rigaExtra,
}: {
  titolo: string;
  campagne: CampagnaSezione[];
  intestazioneExtra?: ReactNode;
  rigaExtra?: (c: CampagnaSezione) => ReactNode;
}) {
  if (!campagne.length) return null;
  return (
    <Card withBorder radius="lg" p="lg">
      <Text fw={700} mb="sm">
        {titolo}
      </Text>
      <div className={stile.tabella}>
        <table>
          <thead>
            <tr>
              <th>Campagna</th>
              <th>Stato</th>
              <th>Periodo</th>
              <th>Post</th>
              {intestazioneExtra}
            </tr>
          </thead>
          <tbody>
            {campagne.map((c) => (
              <RigaSezione key={c.id} c={c} extra={rigaExtra?.(c)} />
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

function RigaDaApprovare({ c }: { c: CampagnaDaApprovare }) {
  return (
    <tr>
      <td>
        <Link to={`/campagne/${c.id}`} className={stile.bottega}>
          {c.titolo}
        </Link>
      </td>
      <td>
        <BadgeStato stato={c.stato} />
      </td>
      <td>
        <Text size="sm">{periodo(c.inizio, c.fine)}</Text>
      </td>
      <td>
        <span
          className={`${stile.contatore} ${
            (c.conteggi?.da_approvare ?? 0) > 0
              ? stile.contatoreAttesa
              : stile.contatoreNeutro
          }`}
        >
          {c.conteggi?.da_approvare ?? 0}
        </span>
      </td>
      <td>
        {c.entro_quando ? (
          <Text size="sm" fw={600}>
            {dataOra(c.entro_quando)}
          </Text>
        ) : (
          <Text size="sm" c="dimmed">
            —
          </Text>
        )}
      </td>
    </tr>
  );
}

export function Artigiano() {
  const { id } = useParams();
  const [scheda, setScheda] = useState<SchedaArtigiano | null>(null);
  const [errore, setErrore] = useState<string | null>(null);

  useEffect(() => {
    schedaArtigiano(Number(id))
      .then(setScheda)
      .catch((e) =>
        setErrore(
          e instanceof Error && e.message.includes("404")
            ? "Artigiano non trovato."
            : "Non sono riuscita a leggere la scheda dell'artigiano.",
        ),
      );
  }, [id]);

  if (!scheda) {
    return (
      <Guscio titolo="Artigiano">
        {errore ? (
          <Alert color="red" variant="light">
            {errore}
          </Alert>
        ) : (
          <Center py="xl">
            <Loader color="verde" />
          </Center>
        )}
      </Guscio>
    );
  }

  const { artigiano: a, profilo: p } = scheda;
  const titolo = p?.nome ?? a.nome;

  return (
    <Guscio titolo="Artigiani">
      <Anchor component={Link} to="/artigiani" c="dimmed" size="sm" mb="xs">
        ← Tutti gli artigiani
      </Anchor>

      <Card withBorder radius="lg" p="lg" mb="lg" mt="xs">
        <Group justify="space-between" align="flex-start" wrap="wrap">
          <div>
            <Text size="xl" fw={800} lh={1.2}>
              {titolo}
            </Text>
            <Text c="dimmed" size="sm" mt={4}>
              {p?.referente ?? a.nome}
              {p?.citta ? ` · ${p.citta}` : ""}
            </Text>
          </div>
          <Group gap={6} justify="flex-end">
            {p ? (
              <span className={`${stile.badge} ${stile.badgeNeutro}`}>
                Profilo compilato
              </span>
            ) : (
              <span className={`${stile.badge} ${stile.badgeAttesa}`}>
                Profilo da compilare
              </span>
            )}
            {!a.attivo && (
              <span className={`${stile.badge} ${stile.badgeSpento}`}>
                Account sospeso
              </span>
            )}
            {scheda.bozza && (
              <span className={`${stile.badge} ${stile.badgeSpento}`}>
                Bozza in corso
              </span>
            )}
          </Group>
        </Group>
        <Divider my="md" />
        <Group gap="xl" align="flex-start" wrap="wrap">
          <Voce label="Email account" valore={a.email} />
          <Voce label="Sito web" valore={p?.sito} />
          <Voce
            label="Attività"
            valore={p?.anni_attivita ? `${p.anni_attivita} anni` : null}
          />
          <div>
            <Text size="xs" c="dimmed" fw={600} tt="uppercase" lts={0.4}>
              Canali collegati
            </Text>
            <Group gap={6} mt={4}>
              {scheda.canali_collegati.length ? (
                scheda.canali_collegati.map((c) => (
                  <BadgeCanale key={c} canale={c} size="sm" />
                ))
              ) : (
                <Text size="sm" c="dimmed">
                  Nessun canale collegato
                </Text>
              )}
            </Group>
          </div>
        </Group>
      </Card>

      {scheda.da_approvare.length > 0 && (
        <Card withBorder radius="lg" p="lg" mb="lg">
          <Text fw={700} mb="sm">
            Da approvare · {scheda.da_approvare.length}
          </Text>
          <div className={stile.tabella}>
            <table>
              <thead>
                <tr>
                  <th>Campagna</th>
                  <th>Stato</th>
                  <th>Periodo</th>
                  <th>Post da approvare</th>
                  <th>Entro</th>
                </tr>
              </thead>
              <tbody>
                {scheda.da_approvare.map((c) => (
                  <RigaDaApprovare key={c.id} c={c} />
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      <Stack gap="lg">
        <TabellaCampagne titolo="In corso" campagne={scheda.in_corso} />
        <TabellaCampagne
          titolo={
            scheda.totale_chiuse > scheda.chiuse.length
              ? `Ultime campagne chiuse · ${scheda.chiuse.length} di ${scheda.totale_chiuse}`
              : "Campagne chiuse"
          }
          campagne={scheda.chiuse}
          intestazioneExtra={<th>Chiusa il</th>}
          rigaExtra={(c) => (
            <td>
              <Text size="sm" c="dimmed">
                {c.chiusa_il ? data(c.chiusa_il) : "—"}
              </Text>
            </td>
          )}
        />
        {!scheda.da_approvare.length &&
          !scheda.in_corso.length &&
          !scheda.chiuse.length && (
            <Text c="dimmed" size="sm">
              {p
                ? "Nessuna campagna ancora."
                : "Il profilo non è ancora compilato: l'artigiano deve finirlo prima di poter creare campagne."}
            </Text>
          )}
      </Stack>

      {p && (
        <Card withBorder radius="lg" p="lg" mt="lg">
          <Group justify="space-between" align="center" mb="sm">
            <Text fw={700}>Profilo della bottega</Text>
            <Text size="xs" c="dimmed">
              Aggiornato il {p.aggiornato_il ? data(p.aggiornato_il) : "—"}
            </Text>
          </Group>
          <Stack gap="sm">
            <Group grow align="flex-start" wrap="wrap">
              <Voce
                label="Cosa fa"
                valore={
                  [
                    p.tipo_prodotto,
                    p.gamma,
                    p.fascia_prezzo && `fascia ${p.fascia_prezzo}`,
                  ]
                    .filter(Boolean)
                    .join(" · ") || null
                }
              />
              <Voce
                label="Storia e origine"
                valore={[p.storia, p.origine].filter(Boolean).join(" ") || null}
              />
            </Group>
            <Group grow align="flex-start" wrap="wrap">
              <Voce
                label="Clienti e zona"
                valore={
                  [p.clienti_ideali, p.zona].filter(Boolean).join(" · ") || null
                }
              />
              <Voce label="Obiettivo" valore={p.obiettivo} />
            </Group>
            <Group grow align="flex-start" wrap="wrap">
              <Voce
                label="Tono e cortesia"
                valore={
                  [p.tono?.join(", ") || null, p.cortesia]
                    .filter(Boolean)
                    .join(" · ") || null
                }
              />
              <Voce
                label="Valori e stagionalità"
                valore={
                  [p.valori?.join(", ") || null, p.stagionalita]
                    .filter(Boolean)
                    .join(" · ") || null
                }
              />
            </Group>
            <Voce label="Vincoli" valore={p.vincoli} />
            <Voce
              label="Canali e frequenza"
              valore={
                [p.canali?.join(", ") || null, p.frequenza]
                  .filter(Boolean)
                  .join(" · ") || null
              }
            />
            <Voce
              label="Orari di lavoro"
              valore={
                p.orari && !Array.isArray(p.orari)
                  ? Object.entries(p.orari)
                      .map(([k, v]) => `${k}: ${v}`)
                      .join(" · ")
                  : null
              }
            />
            <Voce
              label="Eventi ricorrenti"
              valore={
                p.eventi_ricorrenti
                  ?.map((e) => [e.nome, e.periodo].filter(Boolean).join(" — "))
                  .filter(Boolean)
                  .join(" · ") || null
              }
            />
            <Voce
              label="Social e foto"
              valore={
                [
                  p.social_esistenti
                    ? Object.entries(p.social_esistenti)
                        .map(([k, v]) => `${k}: ${v}`)
                        .join(" · ")
                    : null,
                  p.foto_policy
                    ? Object.entries(p.foto_policy)
                        .map(([k, v]) => `${k}: ${v}`)
                        .join(" · ")
                    : null,
                ]
                  .filter(Boolean)
                  .join(" — ") || null
              }
            />
            <Voce label="Chiusure" valore={p.chiusure} />
          </Stack>
        </Card>
      )}
    </Guscio>
  );
}
