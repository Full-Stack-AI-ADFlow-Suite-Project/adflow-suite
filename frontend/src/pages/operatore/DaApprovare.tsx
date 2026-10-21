/**
 * Campagne da approvare (T1-53): tutti gli artigiani, da GET /campagne con lo
 * stato ripetuto. Ordinata per urgenza; la decisione si prende in Vedi campagna.
 */
import {
  Alert,
  Card,
  Center,
  Group,
  Loader,
  Paper,
  Select,
  SimpleGrid,
  Stack,
  Text,
} from "@mantine/core";
import { useEffect, useMemo, useState } from "react";

import type { CampagnaDaApprovare } from "../../api/decisioni";
import { daApprovare } from "../../api/decisioni";
import { Guscio } from "../../components/Guscio";
import { RigaCampagna } from "./da-approvare/RigaCampagna";

const STATI_DA_APPROVARE = [
  "inviata",
  "in_generazione",
  "piano_da_rivedere",
  "generazione_fallita",
  "in_revisione",
];

const URGENZA: Record<string, number> = {
  in_revisione: 0,
  piano_da_rivedere: 1,
  generazione_fallita: 2,
  in_generazione: 3,
  inviata: 4,
};

export function DaApprovare() {
  const [lista, setLista] = useState<CampagnaDaApprovare[] | null>(null);
  const [errore, setErrore] = useState<string | null>(null);
  const [stato, setStato] = useState<string | null>(null);

  useEffect(() => {
    daApprovare()
      .then((tutte) =>
        setLista(
          [...tutte].sort(
            (a, b) =>
              (a.entro_quando ?? "9").localeCompare(b.entro_quando ?? "9") ||
              (URGENZA[a.stato] ?? 9) - (URGENZA[b.stato] ?? 9) ||
              a.inizio.localeCompare(b.inizio),
          ),
        ),
      )
      .catch(() => setErrore("Non sono riuscita a leggere le campagne."));
  }, []);

  const filtri = useMemo(() => {
    const conti = new Map<string, number>();
    for (const c of lista ?? [])
      conti.set(c.stato, (conti.get(c.stato) ?? 0) + 1);
    return [
      { value: "", label: `Stato: tutti (${lista?.length ?? 0})` },
      ...STATI_DA_APPROVARE.map((s) => ({
        value: s,
        label: `${s} (${conti.get(s) ?? 0})`,
      })),
    ];
  }, [lista]);

  const visibili = (lista ?? []).filter((c) => !stato || c.stato === stato);
  const nInRevisione = (lista ?? []).filter(
    (c) => c.stato === "in_revisione",
  ).length;
  const nDaRivedere = (lista ?? []).filter(
    (c) =>
      c.stato === "piano_da_rivedere" ||
      c.stato === "generazione_fallita" ||
      (c.conteggi?.da_rivedere ?? 0) > 0,
  ).length;
  const nInGenerazione = (lista ?? []).filter(
    (c) => c.stato === "inviata" || c.stato === "in_generazione",
  ).length;

  return (
    <Guscio titolo="Campagne da approvare">
      {lista && (
        <SimpleGrid cols={{ base: 2, sm: 4 }} spacing="sm" mb="lg">
          <Paper withBorder radius="md" p="md" bg="#ffffff">
            <Text size="xs" c="dimmed" fw={600} tt="uppercase" lts={0.5}>
              In coda totali
            </Text>
            <Text size="xl" fw={800} mt={4}>
              {lista.length}
            </Text>
          </Paper>
          <Paper withBorder radius="md" p="md" bg="#ffffff">
            <Text size="xs" c="dimmed" fw={600} tt="uppercase" lts={0.5}>
              Pronte in revisione
            </Text>
            <Text size="xl" fw={800} c="verde" mt={4}>
              {nInRevisione}
            </Text>
          </Paper>
          <Paper withBorder radius="md" p="md" bg="#ffffff">
            <Text size="xs" c="dimmed" fw={600} tt="uppercase" lts={0.5}>
              Richiedono attenzione
            </Text>
            <Text
              size="xl"
              fw={800}
              c={nDaRivedere > 0 ? "red" : undefined}
              mt={4}
            >
              {nDaRivedere}
            </Text>
          </Paper>
          <Paper withBorder radius="md" p="md" bg="#ffffff">
            <Text size="xs" c="dimmed" fw={600} tt="uppercase" lts={0.5}>
              In elaborazione AI
            </Text>
            <Text size="xl" fw={800} mt={4}>
              {nInGenerazione}
            </Text>
          </Paper>
        </SimpleGrid>
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
        <>
          <Group justify="space-between" align="center" mb="md" wrap="wrap">
            <Select
              aria-label="Filtra per stato"
              data={filtri}
              value={stato}
              onChange={setStato}
              w={280}
            />
            <Text size="xs" c="dimmed">
              Mostrate {visibili.length} su {lista.length} campagne
            </Text>
          </Group>
          <Stack gap="sm">
            {visibili.map((c) => (
              <RigaCampagna key={c.id} c={c} />
            ))}
            {!visibili.length && (
              <Card
                withBorder
                radius="md"
                p="lg"
                style={{ borderStyle: "dashed" }}
              >
                <Text c="dimmed" size="sm">
                  Nessuna campagna da approvare. Le campagne arrivano qui appena
                  un artigiano le invia.
                </Text>
              </Card>
            )}
          </Stack>
        </>
      )}
    </Guscio>
  );
}
