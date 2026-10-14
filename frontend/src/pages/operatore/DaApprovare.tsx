/**
 * Campagne da approvare (T1-53): tutti gli artigiani, da GET /campagne con lo
 * stato ripetuto. Ordinata per urgenza; la decisione si prende in Vedi campagna.
 */
import {
  Alert,
  Card,
  Center,
  Loader,
  Select,
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

  return (
    <Guscio titolo="Campagne da approvare" largo={1100}>
      <Text c="dimmed" size="sm" mb="md">
        Dalla più urgente: per "entro quando", cioè la data del primo post da
        approvare o le 00:00 del giorno di inizio se il piano non c'è. Si decide
        sempre in Vedi campagna.
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
