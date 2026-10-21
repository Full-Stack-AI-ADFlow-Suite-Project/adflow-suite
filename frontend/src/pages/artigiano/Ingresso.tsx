/**
 * L'ingresso dell'artigiano (docs/pagine/AdFlow-ingresso.html, spec R-29,
 * ADR-117, H1): ciò che gli chiede il consorzio, gli avvisi sulle sue
 * campagne, "Nuova campagna" e le campagne in corso. Gli avvisi dicono solo lo
 * stato: piano e post si vedono dopo l'approvazione (spec §4).
 */
import {
  Alert,
  Button,
  Card,
  Center,
  Group,
  Loader,
  Stack,
  Text,
  Title,
} from "@mantine/core";
import { useEffect, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";

import { elenco, type CampagnaElencoItem } from "../../api/campagne";
import { ElencoCampagne } from "../../components/campagne/ElencoCampagne";
import { sezioniDi } from "../../components/campagne/sezioni";
import { Guscio } from "../../components/Guscio";
import { useAuth } from "../../contesto-auth";
import { scegli } from "./campagna/viste/scelta";

const IN_LAVORAZIONE = [
  "inviata",
  "in_generazione",
  "generazione_fallita",
  "piano_da_rivedere",
  "in_revisione",
];

const aprila = (c: CampagnaElencoItem) => `/campagna?id=${c.id}`;

/** Un avviso con un link: la campagna che lo causa e dove si apre. */
function Avviso({
  colore,
  link,
  vai,
  children,
}: {
  colore: string;
  link: string;
  vai: string;
  children: ReactNode;
}) {
  return (
    <Alert color={colore} variant="light">
      {children}{" "}
      <Text component={Link} to={link} fw={600} c="inherit">
        {vai}
      </Text>
    </Alert>
  );
}

/** Gli avvisi di bozza, lavorazione, respinta e scaduta (le stesse di `scegli`). */
function avvisi(lista: CampagnaElencoItem[]): ReactNode[] {
  const { visibili } = scegli(lista);
  return visibili.flatMap((c): ReactNode[] => {
    // La richiesta aperta ha già il suo riquadro in evidenza.
    if (c.richiesta === "aperta") return [];
    if (c.stato === "bozza")
      return [
        <Avviso key={c.id} colore="gray" link={aprila(c)} vai="Continua">
          Hai una campagna in bozza: <b>{c.titolo}</b>.
        </Avviso>,
      ];
    if (IN_LAVORAZIONE.includes(c.stato))
      return [
        <Avviso key={c.id} colore="blue" link={aprila(c)} vai="Vedi">
          Il consorzio sta preparando la campagna <b>{c.titolo}</b>.
        </Avviso>,
      ];
    if (c.stato === "respinta")
      return [
        <Avviso
          key={c.id}
          colore="red"
          link={aprila(c)}
          vai="Vedi motivo e nota"
        >
          La campagna <b>{c.titolo}</b> è stata respinta.
        </Avviso>,
      ];
    if (c.stato === "scaduta")
      return [
        <Avviso key={c.id} colore="red" link={aprila(c)} vai="Vedi">
          La campagna <b>{c.titolo}</b> è scaduta senza essere approvata.
        </Avviso>,
      ];
    return [];
  });
}

export function Ingresso() {
  const { utente } = useAuth();
  const [lista, setLista] = useState<CampagnaElencoItem[] | null>(null);
  const [errore, setErrore] = useState<string | null>(null);

  useEffect(() => {
    elenco()
      .then(setLista)
      .catch(() => setErrore("Non sono riuscita a leggere le campagne."));
  }, []);

  const nome = utente?.nome.split(" ")[0] ?? "";
  const richieste = (lista ?? []).filter(
    (c) => c.stato === "in_revisione" && c.richiesta === "aperta",
  );
  const elencoAvvisi = lista ? avvisi(lista) : [];
  const haBozza = (lista ?? []).some((c) => c.stato === "bozza");
  const inCorso = sezioniDi("artigiano", lista ?? []).filter(
    (s) => s.chiave === "in_corso",
  );

  return (
    <Guscio titolo={nome ? `Buongiorno, ${nome}` : "Buongiorno"} largo={900}>
      <Text c="dimmed" mb="lg">
        Qui trovi che cosa ti chiede il consorzio e a che punto sono le tue
        campagne.
      </Text>
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
        <Stack gap="xl">
          {richieste.map((c) => (
            <Card
              key={c.id}
              withBorder
              radius="md"
              p="lg"
              style={{ borderLeft: "4px solid var(--mantine-color-yellow-6)" }}
            >
              <Title order={2} size="h4">
                Il consorzio ti chiede…
              </Title>
              <Text mt={6}>
                Campagna <b>{c.titolo}</b>: apri la campagna per leggere la
                richiesta e rispondere.
              </Text>
              <Group mt="md">
                <Button component={Link} to={aprila(c)} size="xs">
                  Rispondi →
                </Button>
              </Group>
            </Card>
          ))}

          {elencoAvvisi.length > 0 && (
            <section aria-label="Avvisi">
              <Title order={2} size="h4" mb="xs">
                Avvisi
              </Title>
              <Text c="dimmed" size="sm" mb="sm">
                Solo lo stato: piano e post li vedi quando il consorzio approva.
              </Text>
              <Stack gap="sm">{elencoAvvisi}</Stack>
            </section>
          )}

          {!haBozza && (
            <Group>
              <Button component={Link} to="/campagna">
                + Nuova campagna
              </Button>
            </Group>
          )}

          <ElencoCampagne
            sezioni={inCorso}
            lato="artigiano"
            link={aprila}
            vuoto="Nessuna campagna in corso."
          />
          {/* Questa settimana: il calendario settimanale arriva con T3-77. */}
        </Stack>
      )}
    </Guscio>
  );
}
