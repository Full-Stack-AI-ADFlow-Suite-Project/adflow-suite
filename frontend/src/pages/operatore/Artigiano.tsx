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
  Badge,
  Card,
  Center,
  Divider,
  Group,
  Loader,
  Stack,
  Table,
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

function periodo(inizio: string, fine: string): string {
  return `${data(inizio)} – ${data(fine)}`;
}

function BadgeStato({ stato }: { stato: string }) {
  return (
    <Badge color={coloreCampagna(stato)} variant="light">
      {stato.replaceAll("_", " ")}
    </Badge>
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

function RigaCampagna({ c, extra }: { c: CampagnaSezione; extra?: ReactNode }) {
  return (
    <Table.Tr>
      <Table.Td>
        <Anchor
          component={Link}
          to={`/campagne/${c.id}`}
          fw={600}
          size="sm"
          c="dark"
        >
          {c.titolo}
        </Anchor>
      </Table.Td>
      <Table.Td>
        <BadgeStato stato={c.stato} />
      </Table.Td>
      <Table.Td>
        <Text size="sm">{periodo(c.inizio, c.fine)}</Text>
      </Table.Td>
      <Table.Td>
        <Text size="sm">
          {c.n_post} post
          {c.n_falliti > 0 && (
            <Text span c="red" fw={600}>
              {" "}
              · {c.n_falliti} falliti
            </Text>
          )}
        </Text>
      </Table.Td>
      {extra}
    </Table.Tr>
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
    <Card withBorder radius="md" p="lg">
      <Text fw={700} mb="sm">
        {titolo}
      </Text>
      <Table verticalSpacing="sm">
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Campagna</Table.Th>
            <Table.Th>Stato</Table.Th>
            <Table.Th>Periodo</Table.Th>
            <Table.Th>Post</Table.Th>
            {intestazioneExtra}
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {campagne.map((c) => (
            <RigaCampagna key={c.id} c={c} extra={rigaExtra?.(c)} />
          ))}
        </Table.Tbody>
      </Table>
    </Card>
  );
}

function RigaDaApprovare({ c }: { c: CampagnaDaApprovare }) {
  return (
    <Table.Tr>
      <Table.Td>
        <Anchor
          component={Link}
          to={`/campagne/${c.id}`}
          fw={600}
          size="sm"
          c="dark"
        >
          {c.titolo}
        </Anchor>
      </Table.Td>
      <Table.Td>
        <BadgeStato stato={c.stato} />
      </Table.Td>
      <Table.Td>
        <Text size="sm">{periodo(c.inizio, c.fine)}</Text>
      </Table.Td>
      <Table.Td>
        <Text size="sm">{c.conteggi?.da_approvare ?? "—"} da approvare</Text>
      </Table.Td>
      <Table.Td>
        {c.entro_quando ? (
          <Text size="sm" fw={600}>
            {dataOra(c.entro_quando)}
          </Text>
        ) : (
          <Text size="sm" c="dimmed">
            —
          </Text>
        )}
      </Table.Td>
    </Table.Tr>
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
    <Guscio titolo="Artigiani" largo={1100}>
      <Anchor component={Link} to="/artigiani" c="dimmed" size="sm" mb="xs">
        ← Tutti gli artigiani
      </Anchor>

      <Card withBorder radius="md" p="lg" mb="lg">
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
              <Badge color="verde" variant="light">
                profilo compilato
              </Badge>
            ) : (
              <Badge color="yellow" variant="light">
                profilo da compilare
              </Badge>
            )}
            {!a.attivo && (
              <Badge color="gray" variant="light">
                account sospeso
              </Badge>
            )}
            {scheda.bozza && (
              <Badge color="gray" variant="outline">
                bozza in corso
              </Badge>
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
        <Card withBorder radius="md" p="lg" mb="lg">
          <Text fw={700} mb="sm">
            Da approvare · {scheda.da_approvare.length}
          </Text>
          <Table verticalSpacing="sm">
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Campagna</Table.Th>
                <Table.Th>Stato</Table.Th>
                <Table.Th>Periodo</Table.Th>
                <Table.Th>Post</Table.Th>
                <Table.Th>Entro</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {scheda.da_approvare.map((c) => (
                <RigaDaApprovare key={c.id} c={c} />
              ))}
            </Table.Tbody>
          </Table>
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
          intestazioneExtra={<Table.Th>Chiusa il</Table.Th>}
          rigaExtra={(c) => (
            <Table.Td>
              <Text size="sm" c="dimmed">
                {c.chiusa_il ? data(c.chiusa_il) : "—"}
              </Text>
            </Table.Td>
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
        <Card withBorder radius="md" p="lg" mt="lg">
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
