import { Alert, Button, Group, Paper, Stack, Text, Title } from "@mantine/core";
import { useNavigate } from "react-router-dom";

import type { CampagnaDettaglio } from "../../../api/campagne";
import type { ProfiloBottega } from "../../../api/artigiani";
import { BadgeCanale } from "../../../components/IconaCanale";
import { useAuth } from "../../../contesto-auth";
import stile from "./Passo10.module.css";
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
    <div className={stile.layout}>
      <aside className={stile.indice} aria-label="Stato del profilo">
        <div className={stile.indiceTitolo}>Prima di iniziare</div>
        <Text size="xs" c="dimmed" px={8} lh={1.55}>
          Controlla i dati principali della bottega prima di aprire i 3 passi
          della nuova campagna.
        </Text>
      </aside>

      <Paper radius="lg" p={{ base: "md", sm: "xl" }} className={stile.form}>
        <header className={stile.intestazione}>
          <Text className={stile.sopratitolo}>Riepilogo rapido</Text>
          <Title order={2} className={stile.titolo}>
            Bentornato, {utente?.nome.split(" ")[0] ?? ""}
          </Title>
          <Text className={stile.descrizione}>
            Il riepilogo del profilo già salvato. Chi non ha un profilo viene
            portato prima alla pagina Profilo bottega.
          </Text>
        </header>
        {respinta?.esito_respinta && (
          <Alert color="orange" variant="light" mt="lg">
            <b>Solo se l'ultima campagna è stata respinta.</b> Il consorzio non
            ha approvato "{respinta.titolo}".{" "}
            <b>Motivo: {respinta.esito_respinta.motivo}.</b>
            {respinta.esito_respinta.nota && (
              <> Richiesta di modifica: "{respinta.esito_respinta.nota}"</>
            )}{" "}
            Tienine conto nella nuova campagna: foto e testi vanno inseriti di
            nuovo.
          </Alert>
        )}
        <Stack gap={4} className={stile.campi}>
          <Riga nome="Bottega" valore={profilo.bottega} />
          <Riga nome="Referente" valore={profilo.referente} />
          <Riga nome="Tipo di prodotto" valore={profilo.tipo_prodotto} />
          <Riga nome="Obiettivo" valore={profilo.obiettivo} />
          <Riga
            nome="Canali preferiti"
            valore={
              <Group gap={6} wrap="wrap">
                {profilo.canali_preferiti.map((c) => (
                  <BadgeCanale key={c} canale={c} size="xs" />
                ))}
              </Group>
            }
          />
        </Stack>
        <Group mt="xl" justify="space-between" wrap="wrap">
          <Button variant="default" onClick={() => navigate("/profilo")}>
            Modifica il profilo
          </Button>
          <Button color="verde" onClick={onAvanti}>
            Va bene così, vai alla campagna →
          </Button>
        </Group>
      </Paper>
    </div>
  );
}
