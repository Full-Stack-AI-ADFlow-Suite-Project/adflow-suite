/**
 * Elenco degli artigiani (docs/pagine/AdFlow-operatore-elenco.html, spec R-38,
 * ADR-117, H3): una tabella in un riquadro con altezza fissa e scorrimento
 * proprio, intestazione ferma, ricerca nel browser. La riga apre la pagina
 * dell'artigiano.
 */
import {
  Alert,
  Anchor,
  Badge,
  Box,
  Button,
  Card,
  Center,
  Group,
  Loader,
  Table,
  Text,
  TextInput,
} from "@mantine/core";
import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { elencoArtigiani, type ArtigianoElenco } from "../../api/revisione";
import { Guscio } from "../../components/Guscio";
import { NOME_CANALE } from "./campagna/util";

/** La scadenza come nella pagina statica: «22/10 ore 00:00». */
function scadenza(iso: string): string {
  const d = new Date(iso);
  const due = (n: number) => String(n).padStart(2, "0");
  return `${due(d.getDate())}/${due(d.getMonth() + 1)} ore ${due(
    d.getHours(),
  )}:${due(d.getMinutes())}`;
}

function cerca(a: ArtigianoElenco, testo: string): boolean {
  const ago = testo.trim().toLowerCase();
  if (!ago) return true;
  return [a.bottega, a.referente, a.citta, a.email].some((campo) =>
    (campo ?? "").toLowerCase().includes(ago),
  );
}

export function Artigiani() {
  const naviga = useNavigate();
  const [lista, setLista] = useState<ArtigianoElenco[] | null>(null);
  const [errore, setErrore] = useState<string | null>(null);
  const [testo, setTesto] = useState("");

  useEffect(() => {
    elencoArtigiani()
      .then(setLista)
      .catch(() =>
        setErrore("Impossibile caricare l’elenco degli artigiani. Riprova."),
      );
  }, []);

  const visibili = useMemo(
    () => (lista ?? []).filter((a) => cerca(a, testo)),
    [lista, testo],
  );

  return (
    <Guscio titolo="Artigiani" largo={1100}>
      <Group justify="space-between" mb="md" wrap="wrap">
        <Text c="dimmed">
          Tutte le botteghe del consorzio, dalla scadenza più vicina. La riga
          apre la pagina dell&apos;artigiano.
        </Text>
        <Button component={Link} to="/nuovo-artigiano">
          + Nuovo artigiano
        </Button>
      </Group>

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
        <Card withBorder radius="md" p={0}>
          <Group justify="space-between" p="md">
            <TextInput
              type="search"
              aria-label="Cerca"
              placeholder="Cerca per bottega, referente, città o email"
              value={testo}
              onChange={(e) => setTesto(e.currentTarget.value)}
              w={420}
              maw="100%"
            />
            <Text size="sm" c="dimmed">
              {visibili.length} di {lista.length}
            </Text>
          </Group>
          <Box style={{ maxHeight: "60vh", overflow: "auto" }}>
            <Table stickyHeader highlightOnHover verticalSpacing="xs">
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Bottega</Table.Th>
                  <Table.Th>Referente</Table.Th>
                  <Table.Th>Città</Table.Th>
                  <Table.Th>Canali collegati</Table.Th>
                  <Table.Th>Da approvare</Table.Th>
                  <Table.Th>In corso</Table.Th>
                  <Table.Th>Prossima scadenza</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {visibili.map((a) => (
                  <Table.Tr
                    key={a.id}
                    style={{ cursor: "pointer" }}
                    onClick={() => naviga(`/artigiani/${a.id}`)}
                  >
                    <Table.Td>
                      <Anchor
                        component={Link}
                        to={`/artigiani/${a.id}`}
                        fw={600}
                        c="inherit"
                        // Il clic sul nome apre già la pagina: la riga non lo ripete.
                        onClick={(e) => e.stopPropagation()}
                      >
                        {a.bottega ?? a.nome}
                      </Anchor>
                      {a.bottega === null && (
                        <Text size="xs" c="dimmed">
                          Profilo da compilare
                        </Text>
                      )}
                      {!a.attivo && (
                        <Badge color="gray" variant="light" size="xs" ml={6}>
                          account non attivo
                        </Badge>
                      )}
                    </Table.Td>
                    <Table.Td>{a.referente ?? "—"}</Table.Td>
                    <Table.Td>{a.citta ?? "—"}</Table.Td>
                    <Table.Td>
                      {a.canali_collegati.length ? (
                        <Group gap={4}>
                          {a.canali_collegati.map((c) => (
                            <Badge
                              key={c}
                              color="green"
                              variant="light"
                              size="sm"
                            >
                              {NOME_CANALE[c] ?? c}
                            </Badge>
                          ))}
                        </Group>
                      ) : (
                        <Text size="xs" c="dimmed">
                          nessuno
                        </Text>
                      )}
                    </Table.Td>
                    <Table.Td>
                      {a.n_da_approvare > 0 ? (
                        <Badge color="yellow" variant="light">
                          {a.n_da_approvare}
                        </Badge>
                      ) : (
                        0
                      )}
                    </Table.Td>
                    <Table.Td>{a.n_in_corso}</Table.Td>
                    <Table.Td>
                      {a.prossima_scadenza ? (
                        <b>{scadenza(a.prossima_scadenza)}</b>
                      ) : (
                        <Text c="dimmed">—</Text>
                      )}
                    </Table.Td>
                  </Table.Tr>
                ))}
                {visibili.length === 0 && (
                  <Table.Tr>
                    <Table.Td colSpan={7}>
                      <Text c="dimmed" size="sm" ta="center" py="md">
                        Nessun artigiano corrisponde alla ricerca.
                      </Text>
                    </Table.Td>
                  </Table.Tr>
                )}
              </Table.Tbody>
            </Table>
          </Box>
        </Card>
      )}
    </Guscio>
  );
}
