import layout from "../../../components/Layout.module.css";
import { Alert, Button, Group, Paper, Stack, Text, Title } from "@mantine/core";
import { useNavigate } from "react-router-dom";

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
  const navigate = useNavigate();

  return (
    <Paper withBorder radius="md" p={{ base: "md", sm: "xl" }}>
      <Title order={2}>Bentornato, {utente?.nome.split(" ")[0] ?? ""}</Title>
      <Text c="dimmed" size="sm" mt="xs" mb="lg">
        Ritrovi qui il riepilogo della pagina Profilo bottega. Controlla che sia
        aggiornato prima di preparare la campagna.
      </Text>
      {respinta?.esito_respinta && (
        <Alert color="orange" variant="light" mb="md">
          <b>L’ultima campagna è stata respinta.</b> Il consorzio non ha
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
      <Group className={layout.azioni} mt="xl">
        <Button color="verde" onClick={onAvanti}>
          Va bene così, vai alla campagna →
        </Button>
        <Button variant="light" onClick={() => navigate("/profilo")}>
          Modifica il profilo
        </Button>
      </Group>
    </Paper>
  );
}
