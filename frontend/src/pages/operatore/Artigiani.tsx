/**
 * Elenco degli artigiani del consorzio (GET /artigiani, plan §3).
 *
 * Prima pagina dell'operatore: tutte le botteghe con la loro situazione.
 * Il nome della bottega apre la scheda dell'artigiano; la tabella resta in
 * una finestra scrollabile così l'elenco cresce senza perdere la testata.
 */
import {
  Alert,
  Badge,
  Button,
  Card,
  Center,
  Group,
  Loader,
  Paper,
  ScrollArea,
  Stack,
  Table,
  Text,
  TextInput,
} from "@mantine/core";
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { elencoArtigiani, type ArtigianoElenco } from "../../api/artigiani";
import { BadgeCanale } from "../../components/IconaCanale";
import { Guscio } from "../../components/Guscio";
import { dataOra } from "./campagna/util";

function Kpi({
  label,
  valore,
  colore,
}: {
  label: string;
  valore: number;
  colore?: string;
}) {
  return (
    <Paper withBorder radius="md" p="md" bg="#ffffff">
      <Text size="xs" c="dimmed" fw={600} tt="uppercase" lts={0.5}>
        {label}
      </Text>
      <Text size="xl" fw={800} c={colore} mt={4}>
        {valore}
      </Text>
    </Paper>
  );
}

function RigaArtigiano({ r }: { r: ArtigianoElenco }) {
  const canali = ["facebook", "instagram"];
  return (
    <Table.Tr>
      <Table.Td>
        <Text
          component={Link}
          to={`/artigiani/${r.id}`}
          fw={700}
          size="sm"
          c="dark"
          style={{ textDecoration: "none" }}
        >
          {r.bottega ?? r.nome}
        </Text>
        <Text size="xs" c="dimmed">
          {r.bottega ? r.nome : r.email}
          {r.citta ? ` · ${r.citta}` : ""}
        </Text>
      </Table.Td>
      <Table.Td>
        {r.bottega ? (
          <Badge color="verde" variant="light">
            profilo compilato
          </Badge>
        ) : (
          <Badge color="yellow" variant="light">
            profilo da compilare
          </Badge>
        )}
        {!r.attivo && (
          <Badge color="gray" variant="light" ml={6}>
            sospeso
          </Badge>
        )}
      </Table.Td>
      <Table.Td>
        <Group gap={4} wrap="nowrap">
          {canali.map((canale) =>
            r.canali_collegati.includes(canale) ? (
              <BadgeCanale key={canale} canale={canale} size="xs" />
            ) : (
              <Badge key={canale} color="gray" variant="outline" size="sm">
                {canale === "facebook" ? "Fb" : "Ig"}
              </Badge>
            ),
          )}
        </Group>
      </Table.Td>
      <Table.Td>
        {r.n_da_approvare > 0 ? (
          <Badge color="yellow" variant="light">
            {r.n_da_approvare}
          </Badge>
        ) : (
          <Text size="sm" c="dimmed">
            0
          </Text>
        )}
      </Table.Td>
      <Table.Td>
        <Text size="sm">{r.n_in_corso}</Text>
      </Table.Td>
      <Table.Td>
        {r.prossima_scadenza ? (
          <Text
            size="sm"
            fw={600}
            component={Link}
            to={`/campagne/${r.prossima_campagna_id}`}
            c="dark"
            style={{ textDecoration: "none" }}
          >
            {dataOra(r.prossima_scadenza)}
          </Text>
        ) : (
          <Text size="sm" c="dimmed">
            {r.bottega ? "—" : "— · profilo da compilare"}
          </Text>
        )}
      </Table.Td>
    </Table.Tr>
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
        <Group grow mb="lg" preventGrowOverflow={false} wrap="wrap">
          <Kpi label="Botteghe iscritte" valore={lista.length} />
          <Kpi
            label="Con campagne da approvare"
            valore={nDaApprovare}
            colore={
              nDaApprovare > 0 ? "var(--mantine-color-yellow-8)" : undefined
            }
          />
          <Kpi label="Con campagne in corso" valore={nInCorso} />
          <Kpi
            label="Profilo da compilare"
            valore={nSenzaProfilo}
            colore={
              nSenzaProfilo > 0 ? "var(--mantine-color-yellow-8)" : undefined
            }
          />
        </Group>
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
        <Stack gap="md">
          <Group justify="space-between" align="center" wrap="wrap">
            <TextInput
              aria-label="Cerca artigiano"
              placeholder="Cerca per bottega, referente, città o email"
              value={cerca}
              onChange={(e) => setCerca(e.currentTarget.value)}
              w={380}
            />
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
          </Group>

          <Card withBorder radius="md" p={0} style={{ overflow: "hidden" }}>
            <ScrollArea.Autosize mah={560} type="auto">
              <Table highlightOnHover verticalSpacing="sm" miw={760}>
                <Table.Thead
                  style={{
                    position: "sticky",
                    top: 0,
                    background: "#ffffff",
                    zIndex: 1,
                  }}
                >
                  <Table.Tr>
                    <Table.Th>Bottega</Table.Th>
                    <Table.Th>Stato</Table.Th>
                    <Table.Th>Canali collegati</Table.Th>
                    <Table.Th>Da approvare</Table.Th>
                    <Table.Th>In corso</Table.Th>
                    <Table.Th>Prossima scadenza</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {visibili.map((r) => (
                    <RigaArtigiano key={r.id} r={r} />
                  ))}
                </Table.Tbody>
              </Table>
              {!visibili.length && (
                <Text c="dimmed" size="sm" p="lg" ta="center">
                  {cerca
                    ? "Nessun artigiano corrisponde alla ricerca."
                    : "Nessun artigiano ancora iscritto. Crealo da «Nuovo artigiano»."}
                </Text>
              )}
            </ScrollArea.Autosize>
          </Card>
          <Text size="xs" c="dimmed">
            Il nome della bottega apre la sua pagina con profilo e campagne.
            Mostrati {visibili.length} su {lista.length} artigiani.
          </Text>
        </Stack>
      )}
    </Guscio>
  );
}
