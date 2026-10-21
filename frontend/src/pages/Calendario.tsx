/**
 * Il calendario settimanale (docs/pagine/AdFlow-calendario.html, spec R-48,
 * ADR-117, H5), uguale per i tre ruoli: l'artigiano vede i suoi post,
 * l'operatore quelli di tutti, con il filtro per bottega. Si naviga una
 * settimana alla volta; senza data il server dà quella di oggi.
 */
import { Alert, Badge, Button, Group, Select, Text } from "@mantine/core";
import { useEffect, useMemo, useState } from "react";

import {
  calendarioSettimana,
  type CalendarioSettimana as Settimana,
  type PostSettimana,
} from "../api/campagne";
import { CalendarioSettimana } from "../components/CalendarioSettimana";
import { etichettaSettimana, sommaGiorni } from "../components/calendario-date";
import { Guscio } from "../components/Guscio";
import { useAuth } from "../contesto-auth";

export function Calendario() {
  const { utente } = useAuth();
  const lato = utente?.ruolo === "artigiano" ? "artigiano" : "operatore";
  /** Il lunedì mostrato; `undefined`: la settimana di oggi, scelta dal server. */
  const [dal, setDal] = useState<string | undefined>(undefined);
  const [settimana, setSettimana] = useState<Settimana | null>(null);
  const [errore, setErrore] = useState<string | null>(null);
  const [bottega, setBottega] = useState<string | null>(null);

  useEffect(() => {
    let attuale = true;
    calendarioSettimana(dal)
      .then((s) => {
        if (!attuale) return;
        setSettimana(s);
        setErrore(null);
      })
      .catch(() => {
        if (attuale) setErrore("Non sono riuscita a leggere il calendario.");
      });
    return () => {
      attuale = false;
    };
  }, [dal]);

  const botteghe = useMemo(
    () =>
      [
        ...new Set(
          (settimana?.giorni ?? [])
            .flatMap((g) => g.post)
            .map((p) => p.bottega)
            .filter((b): b is string => b !== null),
        ),
      ].sort((a, b) => a.localeCompare(b)),
    [settimana],
  );
  // Una bottega che nella settimana nuova non c'è non filtra più.
  const filtro =
    bottega !== null && botteghe.includes(bottega) ? bottega : null;
  const quanti = (settimana?.giorni ?? [])
    .flatMap((g) => g.post)
    .filter((p) => !filtro || p.bottega === filtro).length;

  const vai = (giorni: number) =>
    settimana && setDal(sommaGiorni(settimana.dal, giorni));
  const apri = (p: PostSettimana) =>
    lato === "artigiano"
      ? `/campagna?id=${p.campagna_id}`
      : `/campagne/${p.campagna_id}`;

  return (
    <Guscio titolo="Calendario" largo={1200}>
      <Group justify="space-between" mb="sm" wrap="wrap">
        <Text c="dimmed">
          {lato === "artigiano"
            ? "I tuoi post da lunedì a domenica. Un clic apre la campagna."
            : "Tutti i post approvati della settimana, di tutti gli artigiani. Un clic apre Vedi campagna."}
        </Text>
        {lato === "operatore" && (
          <Select
            aria-label="Filtra per bottega"
            placeholder="Tutte le botteghe"
            data={botteghe}
            value={filtro}
            onChange={setBottega}
            clearable
            w={240}
          />
        )}
      </Group>

      <Group gap="xs" mb="md" wrap="wrap">
        <Button size="xs" variant="default" onClick={() => vai(-7)}>
          ← Settimana prima
        </Button>
        <Button size="xs" variant="default" onClick={() => setDal(undefined)}>
          Oggi
        </Button>
        <Button size="xs" variant="default" onClick={() => vai(7)}>
          Settimana dopo →
        </Button>
        {settimana && (
          <>
            <Text fw={600} ml="xs">
              {etichettaSettimana(settimana.dal, settimana.al)}
            </Text>
            <Badge color="gray" variant="light">
              {quanti} post
            </Badge>
          </>
        )}
      </Group>

      {errore && (
        <Alert color="red" variant="light" mb="md">
          {errore}
        </Alert>
      )}
      {settimana && (
        <CalendarioSettimana
          calendario={settimana}
          lato={lato}
          link={apri}
          bottega={filtro}
        />
      )}
    </Guscio>
  );
}
