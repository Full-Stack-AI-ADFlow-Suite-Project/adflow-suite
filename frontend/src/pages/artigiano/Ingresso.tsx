import layout from "../../components/Layout.module.css";
/**
 * L'ingresso dell'artigiano (docs/pagine/AdFlow-ingresso.html, spec R-29,
 * ADR-117, H1): ciò che gli chiede il consorzio, gli avvisi sulle sue
 * campagne, "Nuova campagna" e le campagne in corso. Gli avvisi dicono solo lo
 * stato: piano e post si vedono dopo l'approvazione (spec §4).
 */
import {
  Alert,
  Anchor,
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

import {
  calendarioSettimana,
  elenco,
  type CalendarioSettimana as Settimana,
  type CampagnaElencoItem,
} from "../../api/campagne";
import { CalendarioSettimana } from "../../components/CalendarioSettimana";
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
    <Alert className={layout.avvisoAzione} color={colore} variant="light">
      {children}{" "}
      <Text
        component={Link}
        to={link}
        fw={600}
        c="inherit"
        style={{ display: "inline-flex", alignItems: "center", minHeight: 44 }}
      >
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

/** La settimana in corso del calendario (H5): lo stesso componente della pagina Calendario. */
function QuestaSettimana() {
  const [settimana, setSettimana] = useState<Settimana | null>(null);
  const [errore, setErrore] = useState(false);

  useEffect(() => {
    calendarioSettimana()
      .then(setSettimana)
      .catch(() => setErrore(true));
  }, []);

  return (
    <section aria-label="Questa settimana">
      <Title order={2} size="h4" mb="xs">
        Questa settimana
      </Title>
      <Text c="dimmed" size="sm" mb="sm">
        I tuoi post da lunedì a domenica.{" "}
        <Anchor component={Link} to="/calendario">
          Apri il calendario
        </Anchor>
      </Text>
      {errore && (
        <Alert color="red" variant="light">
          Impossibile caricare il calendario. Riprova.
        </Alert>
      )}
      {settimana && (
        <CalendarioSettimana
          calendario={settimana}
          lato="artigiano"
          link={(p) => `/campagna?id=${p.campagna_id}`}
        />
      )}
    </section>
  );
}

export function Ingresso() {
  const { utente } = useAuth();
  const [lista, setLista] = useState<CampagnaElencoItem[] | null>(null);
  const [errore, setErrore] = useState<string | null>(null);

  useEffect(() => {
    elenco()
      .then(setLista)
      .catch(() => setErrore("Impossibile caricare le campagne. Riprova."));
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
        <Stack className={layout.ingresso} gap="xl">
          {richieste.map((c) => (
            <Card
              key={c.id}
              className={layout.richiesta}
              withBorder
              radius="md"
              p={{ base: "md", sm: "lg" }}
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
                <Button
                  className={layout.principale}
                  component={Link}
                  to={aprila(c)}
                  size="sm"
                >
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
              <Button className={layout.nuova} component={Link} to="/campagna">
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
          <QuestaSettimana />
        </Stack>
      )}
    </Guscio>
  );
}
