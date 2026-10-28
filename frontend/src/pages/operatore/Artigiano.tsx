/**
 * La pagina dell'artigiano (docs/pagine/AdFlow-operatore-artigiano.html, spec
 * R-38, ADR-117, H3): account, canali collegati e profilo della bottega in
 * sola lettura, con i pulsanti per le sue campagne e il suo archivio foto.
 */
import {
  Alert,
  Anchor,
  Badge,
  Button,
  Card,
  Center,
  Group,
  Loader,
  SimpleGrid,
  Text,
  Title,
} from "@mantine/core";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { schedaArtigiano, type SchedaArtigiano } from "../../api/artigiani";
import { ApiErrore } from "../../api/http";
import { Guscio } from "../../components/Guscio";
import { NOME_CANALE } from "./campagna/util";
import { ProfiloInSolaLettura } from "./artigiano/ProfiloInSolaLettura";

export function Artigiano() {
  const id = Number(useParams().id);
  const [scheda, setScheda] = useState<SchedaArtigiano | null>(null);
  const [errore, setErrore] = useState<string | null>(null);

  useEffect(() => {
    schedaArtigiano(id)
      .then(setScheda)
      .catch((e: unknown) =>
        setErrore(
          e instanceof ApiErrore && e.stato === 404
            ? "Artigiano non trovato."
            : "Impossibile caricare la scheda dell’artigiano. Riprova.",
        ),
      );
  }, [id]);

  return (
    <Guscio
      titolo={scheda?.profilo?.nome ?? scheda?.nome ?? "Artigiano"}
      largo={1000}
    >
      <Anchor component={Link} to="/artigiani" size="sm">
        ← Artigiani
      </Anchor>

      {errore && (
        <Alert color="red" variant="light" mt="md">
          {errore}
        </Alert>
      )}
      {!scheda && !errore && (
        <Center py="xl">
          <Loader color="verde" />
        </Center>
      )}

      {scheda && (
        <>
          <Group justify="space-between" mt="sm" mb="md" wrap="wrap">
            <Badge
              color={scheda.attivo ? "green" : "gray"}
              variant="light"
              size="lg"
            >
              {scheda.attivo ? "account attivo" : "account non attivo"}
            </Badge>
            <Group>
              <Button component={Link} to={`/artigiani/${scheda.id}/campagne`}>
                Campagne
              </Button>
              <Button
                component={Link}
                to={`/artigiani/${scheda.id}/archivio`}
                variant="default"
              >
                Archivio foto
              </Button>
            </Group>
          </Group>
          <Text c="dimmed" mb="lg">
            Account, canali e profilo della bottega, in sola lettura: il profilo
            lo compila e lo cambia l&apos;artigiano.
          </Text>

          <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="md" mb="xl">
            <Card withBorder radius="md" p="md">
              <Text fw={600} mb="xs">
                Account
              </Text>
              <Text>
                <b>{scheda.nome}</b> · {scheda.email}
              </Text>
            </Card>
            <Card withBorder radius="md" p="md">
              <Text fw={600} mb="xs">
                Canali collegati
              </Text>
              {scheda.canali_collegati.length ? (
                <Group gap={6}>
                  {scheda.canali_collegati.map((c) => (
                    <Badge key={c} color="green" variant="light">
                      {NOME_CANALE[c] ?? c}
                    </Badge>
                  ))}
                </Group>
              ) : (
                <Text size="sm" c="dimmed">
                  nessuno
                </Text>
              )}
              <Text size="xs" c="dimmed" mt={8}>
                Nell&apos;MVP tutti pubblicano sulla pagina di prova del team.
              </Text>
            </Card>
          </SimpleGrid>

          <Title order={2} size="h3" mb="sm">
            Profilo bottega
          </Title>
          {scheda.profilo ? (
            <ProfiloInSolaLettura profilo={scheda.profilo} />
          ) : (
            <Alert color="gray" variant="light">
              Profilo da compilare: l&apos;artigiano non l&apos;ha ancora
              scritto.
            </Alert>
          )}
        </>
      )}
    </Guscio>
  );
}
