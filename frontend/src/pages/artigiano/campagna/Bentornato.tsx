/** Bentornato: riepilogo del profilo salvato prima del passo 10. */
import { Alert, Button, Group, Paper, Stack, Text, Title } from "@mantine/core";

import type { CampagnaDettaglio } from "../../../api/campagne";
import type { ProfiloBottega } from "../../../api/artigiani";
import { useAuth } from "../../../contesto-auth";
import { Riga } from "./Riga";

export function Bentornato({
  profilo,
  respinta,
  onAvanti,
}: {
  profilo: ProfiloBottega;
  respinta: CampagnaDettaglio | null;
  onAvanti: () => void;
}) {
  const { utente } = useAuth();
  return (
    <Paper withBorder radius="md" p="xl">
      <Title order={2}>Bentornato, {utente?.nome.split(" ")[0] ?? ""}</Title>
      <Text c="dimmed" size="sm" mt="xs" mb="lg">
        Il riepilogo del profilo già salvato. Chi non ha un profilo viene
        portato prima alla pagina Profilo bottega.
      </Text>
      {respinta?.esito_respinta && (
        <Alert color="orange" variant="light" mb="md">
          <b>Solo se l'ultima campagna è stata respinta.</b> Il consorzio non ha
          approvato "{respinta.titolo}".{" "}
          <b>Motivo: {respinta.esito_respinta.motivo}.</b>
          {respinta.esito_respinta.nota && (
            <> Richiesta di modifica: "{respinta.esito_respinta.nota}"</>
          )}{" "}
          Tienine conto nella nuova campagna: foto e testi vanno inseriti di
          nuovo.
        </Alert>
      )}
      <Stack gap={4}>
        <Riga nome="Bottega" valore={profilo.bottega} />
        <Riga nome="Referente" valore={profilo.referente} />
        <Riga nome="Tipo di prodotto" valore={profilo.tipo_prodotto} />
        <Riga nome="Obiettivo" valore={profilo.obiettivo} />
        <Riga
          nome="Canali preferiti"
          valore={profilo.canali_preferiti.join(", ")}
        />
      </Stack>
      <Group mt="xl">
        <Button color="verde" onClick={onAvanti}>
          Va bene così, vai alla campagna →
        </Button>
        <Button variant="default" disabled>
          Voglio modificare il profilo
        </Button>
      </Group>
      <Text size="xs" c="dimmed" mt="sm">
        Il profilo si modifica dalla pagina Profilo bottega, che arriva con lo
        sprint 2a.
      </Text>
    </Paper>
  );
}
