/**
 * Campagne da approvare (T1-53): tutti gli artigiani, da GET /campagne con lo
 * stato ripetuto. Ordinata per urgenza; la decisione si prende in Vedi campagna.
 */
import {
  Alert,
  Badge,
  Box,
  Button,
  Card,
  Center,
  Group,
  Loader,
  Select,
  Stack,
  Text,
} from "@mantine/core";
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import type { CampagnaElencoItem } from "../../api/campagne";
import { elenco } from "../../api/campagne";
import { Guscio } from "../../components/Guscio";
import { coloreCampagna, data } from "./campagna/util";

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

const BORDO: Record<string, string | undefined> = {
  in_revisione: "var(--mantine-color-yellow-6)",
  piano_da_rivedere: "var(--mantine-color-yellow-6)",
  generazione_fallita: "var(--mantine-color-red-6)",
};

export function DaApprovare() {
  const [lista, setLista] = useState<CampagnaElencoItem[] | null>(null);
  const [errore, setErrore] = useState<string | null>(null);
  const [stato, setStato] = useState<string | null>(null);

  useEffect(() => {
    elenco()
      .then((tutte) =>
        setLista(
          tutte
            .filter((c) => STATI_DA_APPROVARE.includes(c.stato))
            .sort(
              (a, b) =>
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

  return (
    <Guscio titolo="Campagne da approvare" largo={1100}>
      <Text c="dimmed" size="sm" mb="md">
        Dalla più urgente. Si decide sempre in Vedi campagna.
      </Text>
      <Alert color="verde" variant="light" mb="lg">
        Stati mostrati:{" "}
        {STATI_DA_APPROVARE.map((s, i) => (
          <span key={s}>
            {i > 0 && ", "}
            <Text span ff="monospace" size="sm">
              {s}
            </Text>
          </span>
        ))}
        . Da ogni riga si va in <b>Vedi campagna</b> per decidere.
      </Alert>

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
          <Select
            aria-label="Filtra per stato"
            data={filtri}
            value={stato}
            onChange={setStato}
            w={280}
            mb="md"
          />
          <Stack gap="sm">
            {visibili.map((c) => (
              <Card
                key={c.id}
                withBorder
                radius="md"
                p="lg"
                style={
                  BORDO[c.stato]
                    ? { borderLeft: `4px solid ${BORDO[c.stato]}` }
                    : undefined
                }
              >
                <Group justify="space-between" align="flex-start" wrap="wrap">
                  <Box>
                    <Text size="sm" c="dimmed">
                      {c.bottega}
                      {c.citta ? ` · ${c.citta}` : ""}
                    </Text>
                    <Group gap="sm" mt={4}>
                      <Text fw={600} size="lg">
                        {c.titolo}
                      </Text>
                      <Badge
                        color={coloreCampagna(c.stato)}
                        variant="light"
                        ff="monospace"
                      >
                        {c.stato}
                      </Badge>
                    </Group>
                    <Text size="sm" c="dimmed" mt={6}>
                      {data(c.inizio)} → {data(c.fine)} ·{" "}
                      {(c.canali ?? []).join(", ")}
                    </Text>
                  </Box>
                  <Button
                    color="verde"
                    component={Link}
                    to={`/campagne/${c.id}`}
                  >
                    Vedi campagna →
                  </Button>
                </Group>
              </Card>
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
      <Text size="xs" c="dimmed" mt="lg">
        Conteggi dei post, "entro quando" e nota interna arrivano con la 2b; lo
        storico della bottega con lo sprint 3.
      </Text>
    </Guscio>
  );
}
