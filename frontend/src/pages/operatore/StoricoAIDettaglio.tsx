/**
 * Il dettaglio di una chiamata all'AI (R-50): che cosa è stato chiesto, che
 * cosa è tornato, l'errore e, se c'è, la foto analizzata.
 */
import {
  Alert,
  Anchor,
  Badge,
  Center,
  Code,
  Collapse,
  Group,
  Image,
  Loader,
  Paper,
  Stack,
  Text,
  Title,
} from "@mantine/core";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { ApiErrore } from "../../api/http";
import {
  dettaglioChiamata,
  etichettaEsito,
  etichettaTipo,
  type ChiamataAIDettaglio,
} from "../../api/storico";
import { Guscio } from "../../components/Guscio";
import { dataOra } from "./campagna/util";
import { costo, durata } from "./storico-ai/formati";

function Dato({ nome, valore }: { nome: string; valore: string }) {
  return (
    <div>
      <Text size="xs" c="dimmed">
        {nome}
      </Text>
      <Text size="sm">{valore}</Text>
    </div>
  );
}

export function StoricoAIDettaglio() {
  const { id } = useParams();
  const [c, setC] = useState<ChiamataAIDettaglio | null>(null);
  const [errore, setErrore] = useState<string | null>(null);
  const [richiestaAperta, setRichiestaAperta] = useState(false);

  useEffect(() => {
    let attivo = true;
    dettaglioChiamata(Number(id))
      .then((d) => attivo && setC(d))
      .catch(
        (e) =>
          attivo &&
          setErrore(
            e instanceof ApiErrore && e.stato === 404
              ? "Chiamata non trovata."
              : "Impossibile caricare la chiamata. Riprova.",
          ),
      );
    return () => {
      attivo = false;
    };
  }, [id]);

  return (
    <Guscio titolo="Chiamata all'AI" largo={900}>
      <Anchor component={Link} to="/storico-ai" size="sm">
        ← Storico AI
      </Anchor>
      {errore && (
        <Alert color="red" variant="light" mt="md">
          {errore}
        </Alert>
      )}
      {!c && !errore && (
        <Center py="xl">
          <Loader color="verde" />
        </Center>
      )}
      {c && (
        <Stack gap="md" mt="md">
          <Group gap="sm">
            <Title order={2} size="h3">
              {etichettaTipo(c.tipo)}
            </Title>
            <Badge variant="light" color={c.esito === "ok" ? "verde" : "red"}>
              {etichettaEsito(c.esito)}
            </Badge>
          </Group>

          <Paper withBorder radius="md" p="md">
            <Group gap="xl" wrap="wrap">
              <Dato nome="Quando" valore={dataOra(c.creata_il)} />
              <Dato
                nome="Campagna"
                valore={`${c.campagna_titolo}${
                  c.bottega ? ` · ${c.bottega}` : ""
                }`}
              />
              <Dato nome="Modello" valore={c.modello_ai} />
              <Dato
                nome="Versione del prompt"
                valore={c.versione_prompt ?? "—"}
              />
              <Dato nome="Durata" valore={durata(c.durata_ms)} />
              <Dato nome="Costo" valore={costo(c.costo_usd)} />
              <Dato
                nome="Token (ingresso / uscita)"
                valore={`${c.token_ingresso ?? "—"} / ${c.token_uscita ?? "—"}`}
              />
              {c.tentativo !== null && (
                <Dato nome="Tentativo" valore={String(c.tentativo)} />
              )}
            </Group>
          </Paper>

          {c.errore && (
            <Alert color="red" variant="light" title="Errore">
              {c.errore}
            </Alert>
          )}

          {c.foto_id && (
            <Image
              src={`/api/foto/${c.foto_id}/file`}
              alt={`Foto ${c.foto_id}`}
              maw={320}
              radius="md"
              fallbackSrc="data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='320' height='200'%3E%3Crect width='100%25' height='100%25' fill='%23e9ecef'/%3E%3C/svg%3E"
            />
          )}

          <div>
            <Anchor
              component="button"
              type="button"
              size="sm"
              onClick={() => setRichiestaAperta((a) => !a)}
            >
              {richiestaAperta
                ? "Nascondi la richiesta"
                : "Mostra la richiesta"}
            </Anchor>
            <Collapse expanded={richiestaAperta}>
              <Code block mt="xs">
                {c.richiesta
                  ? JSON.stringify(c.richiesta, null, 2)
                  : "Non registrata."}
              </Code>
            </Collapse>
          </div>

          <div>
            <Text fw={600} size="sm" mb={4}>
              Risposta
            </Text>
            <Code block>{c.risposta ?? "Nessuna risposta."}</Code>
          </div>
        </Stack>
      )}
    </Guscio>
  );
}
