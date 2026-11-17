/**
 * Quanti post escono in questa campagna, in base al periodo scelto, e se
 * restano dentro l'abbonamento della bottega: post a settimana per social
 * (profilo) × settimane × social. Se nello stesso periodo c'è un'altra campagna
 * sugli stessi social, i post a settimana si sommano e superano l'abbonamento:
 * è un avviso, non un blocco (R-12).
 */
import { Badge, Card, Group, SimpleGrid, Stack, Text } from "@mantine/core";

import {
  contaPost,
  durataInSettimane,
  postASettimana,
} from "../../../api/abbonamento";
import type {
  CampagnaElencoItem,
  StatoCampagna,
} from "../../../api/campagne";

/** Le campagne che hanno post in programma o in arrivo. */
const STATI_CON_POST: StatoCampagna[] = [
  "inviata",
  "in_generazione",
  "piano_da_rivedere",
  "in_revisione",
  "attiva",
  "sospesa",
];

function Numero({
  valore,
  etichetta,
}: {
  valore: string | number;
  etichetta: string;
}) {
  return (
    <div>
      <Text fw={700} size="xl" lh={1.1}>
        {valore}
      </Text>
      <Text size="xs" c="dimmed">
        {etichetta}
      </Text>
    </div>
  );
}

export function RiepilogoPost({
  frequenza,
  inizio,
  fine,
  canali,
  altre,
}: {
  frequenza: string | null | undefined;
  inizio: string;
  fine: string;
  canali: string[];
  altre: CampagnaElencoItem[];
}) {
  const postSett = postASettimana(frequenza);
  const conto = contaPost(postSett, inizio, fine, canali.length);
  const sovrapposte = altre.filter(
    (c) =>
      STATI_CON_POST.includes(c.stato) &&
      c.inizio <= fine &&
      c.fine >= inizio &&
      (c.canali ?? []).some((k) => canali.includes(k)),
  );
  const oltre = sovrapposte.length > 0;
  const aSettimanaInsieme = postSett * (sovrapposte.length + 1);

  if (conto.giorni <= 0 || canali.length === 0) {
    return (
      <Card withBorder radius="md" p="md" aria-live="polite">
        <Text size="sm" c="dimmed">
          Scegli le date e almeno un social: qui vedrai quanti post escono.
        </Text>
      </Card>
    );
  }

  return (
    <Card
      withBorder
      radius="md"
      p="md"
      aria-live="polite"
      style={{
        borderColor: oltre
          ? "var(--mantine-color-orange-6)"
          : "var(--mantine-color-green-6)",
        borderWidth: 2,
      }}
    >
      <Group justify="space-between" align="flex-start" wrap="wrap">
        <Text fw={600}>Quanti post escono con queste date</Text>
        <Badge
          size="lg"
          color={oltre ? "orange" : "green"}
          variant={oltre ? "filled" : "light"}
        >
          {oltre ? "Oltre l’abbonamento" : "Dentro l’abbonamento"}
        </Badge>
      </Group>
      <SimpleGrid cols={{ base: 2, sm: 4 }} mt="sm">
        <Numero valore={durataInSettimane(conto)} etichetta="durata" />
        <Numero valore={postSett} etichetta="post a settimana per social" />
        <Numero
          valore={conto.perSocial}
          etichetta={`post per social (${canali.length} social)`}
        />
        <Numero valore={conto.totale} etichetta="post in totale" />
      </SimpleGrid>
      <Stack gap={2} mt="sm">
        <Text size="sm">
          {postSett} post a settimana × {conto.giorni} giorni ÷ 7 ={" "}
          {conto.perSocial} post per social (per difetto) × {canali.length}{" "}
          social ={" "}
          <b>{conto.totale} post</b>.
        </Text>
        {oltre ? (
          <Text size="sm" c="orange.8">
            Nello stesso periodo hai già {sovrapposte.length}{" "}
            {sovrapposte.length === 1 ? "altra campagna" : "altre campagne"} (
            {sovrapposte.map((c) => c.titolo).join(", ")}): insieme escono{" "}
            {aSettimanaInsieme} post a settimana per social, più dei{" "}
            {postSett} del tuo abbonamento. Puoi inviare lo stesso.
          </Text>
        ) : (
          <Text size="sm" c="dimmed">
            Il tuo abbonamento prevede {postSett} post a settimana per social:
            questa campagna ci sta dentro.
          </Text>
        )}
      </Stack>
    </Card>
  );
}
