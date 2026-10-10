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
  Loader,
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
import { Decidi } from "./campagna/Decidi";
import { Materiali } from "./campagna/Materiali";
import { PianoCard } from "./campagna/PianoCard";
import { UscitaCard } from "./campagna/UscitaCard";
import { coloreCampagna, data, giorni, NOME_CANALE } from "./campagna/util";

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

  return (
    <Guscio titolo="Vedi campagna" largo={1100}>
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
          <div>
            <Text size="sm" c="dimmed">
              Campagna · {(vista.campagna.canali ?? []).length} canali ·{" "}
              {postTotali} post
            </Text>
            <Title order={1} size="h2" mt={2}>
              {vista.campagna.titolo}{" "}
              <Badge
                color={coloreCampagna(vista.campagna.stato)}
                variant="light"
                ff="monospace"
                size="lg"
              >
                {vista.campagna.stato}
              </Badge>
            </Title>
            <Text size="sm" c="dimmed" mt={6}>
              {bottega}
              {citta ? ` · ${citta}` : ""} · {data(vista.campagna.inizio)} →{" "}
              {data(vista.campagna.fine)} ·{" "}
              {giorni(vista.campagna.inizio, vista.campagna.fine)} giorni ·{" "}
              {(vista.campagna.canali ?? [])
                .map((c) => NOME_CANALE[c] ?? c)
                .join(" e ")}
              {vista.campagna.inviata_il
                ? ` · inviata il ${data(vista.campagna.inviata_il)}`
                : ""}
            </Text>
          </div>

          <Decidi vista={vista} ricarica={carica} />
          <PianoCard piano={vista.piano} uscite={vista.uscite} />

          <Tabs defaultValue="uscite">
            <Tabs.List>
              <Tabs.Tab value="uscite">Uscite ({vista.uscite.length})</Tabs.Tab>
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
