/**
 * Vedi campagna (T1-53): la schermata dell'operatore su ogni stato dopo
 * l'invio. In cima la decisione e il piano, poi le uscite con i post dei
 * canali affiancati, e il pannello Foto e profilo.
 */
import {
  Alert,
  Anchor,
  Badge,
  Card,
  Center,
  Group,
  Loader,
  Paper,
  SimpleGrid,
  Stack,
  Tabs,
  Text,
  Title,
} from "@mantine/core";
import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import type { CampagnaDettaglio } from "../../api/campagne";
import { dettaglio } from "../../api/campagne";
import { ApiErrore } from "../../api/http";
import type { VediCampagna as Vista } from "../../api/revisione";
import { vediCampagna } from "../../api/revisione";
import { Guscio } from "../../components/Guscio";
import { BadgeCanale } from "../../components/IconaCanale";
import { Decidi } from "./campagna/Decidi";
import { Materiali } from "./campagna/Materiali";
import { PianoCard } from "./campagna/PianoCard";
import { UscitaCard } from "./campagna/UscitaCard";
import { AzioniCampagna } from "./vedi-campagna/decisioni/AzioniCampagna";
import { CalendarioCampagnaView } from "../../components/CalendarioCampagnaView";
import { coloreCampagna, data, giorni } from "./campagna/util";

const BOTTEGA_SCONOSCIUTA = "Bottega";

export function VediCampagna() {
  const { id } = useParams();
  const campagnaId = Number(id);
  const [vista, setVista] = useState<Vista | null>(null);
  const [campagna, setCampagna] = useState<CampagnaDettaglio | null>(null);
  const [errore, setErrore] = useState<string | null>(null);

  const carica = useCallback(() => {
    if (!campagnaId || Number.isNaN(campagnaId)) {
      setErrore("Indirizzo non valido.");
      return;
    }
    setErrore(null);
    Promise.all([vediCampagna(campagnaId), dettaglio(campagnaId)])
      .then(([v, c]) => {
        setVista(v);
        setCampagna(c);
      })
      .catch((e) => {
        setErrore(
          e instanceof ApiErrore && e.stato === 404
            ? "Campagna non trovata."
            : e instanceof ApiErrore
            ? e.message
            : "Non sono riuscita a leggere la campagna.",
        );
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [campagnaId]);

  useEffect(() => {
    // caricamento all'ingresso della pagina
    // eslint-disable-next-line react-hooks/set-state-in-effect
    carica();
  }, [carica]);

  const bottega =
    campagna?.profilo_snapshot?.nome ?? (campagna ? "" : BOTTEGA_SCONOSCIUTA);
  const citta = campagna?.profilo_snapshot?.citta ?? null;
  const postTotali = vista?.uscite.reduce((n, u) => n + u.post.length, 0) ?? 0;
  const postDaRivedere =
    vista?.uscite.reduce(
      (n, u) => n + u.post.filter((p) => p.da_rivedere).length,
      0,
    ) ?? 0;

  return (
    <Guscio titolo="Vedi campagna">
      <Text size="sm" mb="md">
        <Anchor component={Link} to="/da-approvare" c="dimmed">
          ← Campagne da approvare
        </Anchor>
        {bottega ? ` · ${bottega}` : ""}
      </Text>

      {errore && (
        <Alert color="red" variant="light">
          {errore}{" "}
          <Anchor onClick={carica} c="verde">
            Riprova
          </Anchor>
        </Alert>
      )}
      {!vista && !errore && (
        <Center py="xl">
          <Loader color="verde" />
        </Center>
      )}

      {vista && (
        <Stack gap="lg">
          <Paper withBorder radius="lg" p="lg" bg="#ffffff">
            <Group justify="space-between" align="flex-start" wrap="wrap">
              <div>
                <Text size="xs" c="verde" fw={700} tt="uppercase" lts={0.8}>
                  {bottega}
                  {citta ? ` · ${citta}` : ""}
                </Text>
                <Group gap="sm" align="center" mt={4}>
                  <Title order={1} size="h2">
                    {vista.campagna.titolo}
                  </Title>
                  <Badge
                    color={coloreCampagna(vista.campagna.stato)}
                    variant="light"
                    ff="monospace"
                    size="lg"
                  >
                    {vista.campagna.stato}
                  </Badge>
                </Group>
                <Text size="sm" c="dimmed" mt={6}>
                  {data(vista.campagna.inizio)} → {data(vista.campagna.fine)} (
                  {giorni(vista.campagna.inizio, vista.campagna.fine)} giorni)
                  {vista.campagna.inviata_il
                    ? ` · Inviata il ${data(vista.campagna.inviata_il)}`
                    : ""}
                </Text>
              </div>
              <Group gap={6} wrap="wrap">
                {(vista.campagna.canali ?? []).map((c) => (
                  <BadgeCanale key={c} canale={c} size="sm" />
                ))}
              </Group>
            </Group>

            <SimpleGrid cols={{ base: 2, sm: 4 }} spacing="sm" mt="md">
              <Paper radius="md" p="sm" bg="#f1f5f9">
                <Text size="xs" c="dimmed" fw={600}>
                  Uscite
                </Text>
                <Text size="lg" fw={700}>
                  {vista.uscite.length}
                </Text>
              </Paper>
              <Paper radius="md" p="sm" bg="#f1f5f9">
                <Text size="xs" c="dimmed" fw={600}>
                  Post totali
                </Text>
                <Text size="lg" fw={700}>
                  {postTotali}
                </Text>
              </Paper>
              <Paper radius="md" p="sm" bg="#f1f5f9">
                <Text size="xs" c="dimmed" fw={600}>
                  Post da rivedere
                </Text>
                <Text
                  size="lg"
                  fw={700}
                  c={postDaRivedere > 0 ? "red" : "verde"}
                >
                  {postDaRivedere}
                </Text>
              </Paper>
              <Paper radius="md" p="sm" bg="#f1f5f9">
                <Text size="xs" c="dimmed" fw={600}>
                  Costo AI
                </Text>
                <Text size="lg" fw={700}>
                  {vista.costo_ai != null
                    ? `${Number(vista.costo_ai).toFixed(2).replace(".", ",")} $`
                    : "—"}
                </Text>
              </Paper>
            </SimpleGrid>
          </Paper>

          <Decidi vista={vista} campagna={campagna} ricarica={carica} />
          <AzioniCampagna vista={vista} ricarica={carica} />
          {/* Congelato per l'MVP, ADR-114: nota interna e togli canale restano nascosti */}
          <PianoCard piano={vista.piano} />

          <Tabs defaultValue="uscite">
            <Tabs.List>
              <Tabs.Tab value="uscite">Uscite ({vista.uscite.length})</Tabs.Tab>
              <Tabs.Tab value="calendario">Calendario</Tabs.Tab>
              <Tabs.Tab value="materiali">Foto e profilo</Tabs.Tab>
            </Tabs.List>
            <Tabs.Panel value="uscite" pt="lg">
              {vista.uscite.length ? (
                <Stack gap="md">
                  {vista.uscite.map((u) => (
                    <UscitaCard
                      key={u.id}
                      uscita={u}
                      bottega={bottega}
                      citta={citta}
                      statoCampagna={vista.campagna.stato}
                      ricarica={carica}
                    />
                  ))}
                </Stack>
              ) : (
                <Card
                  withBorder
                  radius="md"
                  p="lg"
                  style={{ borderStyle: "dashed" }}
                >
                  <Text c="dimmed" size="sm">
                    {vista.campagna.stato === "inviata" ||
                    vista.campagna.stato === "in_generazione"
                      ? "Le uscite si vedranno qui, quando ci saranno: ogni uscita porta un tema e i post dei canali affiancati."
                      : "Nessuna uscita."}
                  </Text>
                </Card>
              )}
            </Tabs.Panel>
            <Tabs.Panel value="calendario" pt="lg">
              <CalendarioCampagnaView
                campagnaId={vista.campagna.id}
                stato={vista.campagna.stato}
                ruolo="operatore"
              />
            </Tabs.Panel>
            <Tabs.Panel value="materiali" pt="lg">
              {campagna ? (
                <Materiali campagna={campagna} vista={vista} />
              ) : (
                <Center py="xl">
                  <Loader color="verde" />
                </Center>
              )}
            </Tabs.Panel>
          </Tabs>
        </Stack>
      )}
    </Guscio>
  );
}
