/**
 * I numeri in cima allo storico dell'AI (R-50): costo, tempi, errori, voti e che
 * fine fanno i testi e le immagini, con gli stessi filtri dell'elenco. Sotto,
 * la tabella per versione del prompt, per confrontare v2 e v3.
 */
import {
  Alert,
  Loader,
  Paper,
  SimpleGrid,
  Stack,
  Table,
  Text,
  Title,
} from "@mantine/core";
import { useEffect, useState } from "react";

import {
  etichettaTipo,
  numeriChiamate,
  type FiltriStorico,
  type NumeriAI,
} from "../../../api/storico";
import { costo, durata, percentuale, votoMedio } from "./formati";

function Numero({
  nome,
  valore,
  nota,
}: {
  nome: string;
  valore: string;
  nota?: string;
}) {
  return (
    <Paper withBorder radius="md" p="sm">
      <Text size="xs" c="dimmed">
        {nome}
      </Text>
      <Text fw={600} size="lg">
        {valore}
      </Text>
      {nota && (
        <Text size="xs" c="dimmed">
          {nota}
        </Text>
      )}
    </Paper>
  );
}

export function NumeriStorico({ filtri }: { filtri: FiltriStorico }) {
  const [n, setN] = useState<NumeriAI | null>(null);
  const [errore, setErrore] = useState(false);

  useEffect(() => {
    let attivo = true;
    numeriChiamate(filtri)
      .then((dati) => {
        if (!attivo) return;
        setErrore(false);
        setN(dati);
      })
      .catch(() => attivo && setErrore(true));
    return () => {
      attivo = false;
    };
  }, [filtri]);

  if (errore)
    return (
      <Alert color="red" variant="light" mb="md">
        Impossibile caricare i numeri. Riprova.
      </Alert>
    );
  if (!n) return <Loader color="verde" size="sm" mb="md" />;

  const comeAI =
    n.testi_approvati > 0
      ? `${n.testi_approvati_come_ai} su ${n.testi_approvati}`
      : "—";

  return (
    <Stack gap="sm" mb="lg">
      <SimpleGrid cols={{ base: 2, sm: 3, md: 4 }} spacing="sm">
        <Numero nome="Chiamate" valore={String(n.chiamate)} />
        <Numero nome="Costo" valore={costo(n.costo_usd)} />
        <Numero
          nome="Tempo medio"
          valore={durata(n.durata_media_ms)}
          nota={`p95 ${durata(n.durata_p95_ms)}`}
        />
        <Numero nome="Tasso d'errore" valore={percentuale(n.tasso_errore)} />
        <Numero nome="Voto medio" valore={votoMedio(n.voto_medio)} />
        <Numero
          nome="Testi approvati come scritti dall'AI"
          valore={comeAI}
          nota={
            n.testi_approvati > 0
              ? percentuale(n.testi_approvati_come_ai / n.testi_approvati)
              : undefined
          }
        />
        <Numero nome="Modifiche a mano" valore={String(n.modifiche_a_mano)} />
        <Numero
          nome="Rigenerazioni del testo"
          valore={String(n.rigenerazioni_testo)}
        />
        <Numero nome="Immagini create" valore={String(n.immagini_create)} />
        <Numero
          nome="Immagini non create"
          valore={String(n.immagini_non_create)}
        />
        <Numero
          nome="Immagini rigenerate"
          valore={String(n.immagini_rigenerate)}
        />
      </SimpleGrid>

      <Title order={2} size="h5" mt="xs">
        Per versione del prompt
      </Title>
      {n.per_versione.length ? (
        <Paper withBorder radius="md" p="xs">
          <Table.ScrollContainer minWidth={560}>
            <Table verticalSpacing="xs" fz="sm">
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Tipo</Table.Th>
                  <Table.Th>Versione</Table.Th>
                  <Table.Th ta="right">Chiamate</Table.Th>
                  <Table.Th ta="right">Errori</Table.Th>
                  <Table.Th ta="right">Tempo medio</Table.Th>
                  <Table.Th ta="right">Costo</Table.Th>
                  <Table.Th ta="right">Voto medio</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {n.per_versione.map((v) => (
                  <Table.Tr key={`${v.tipo}|${v.versione_prompt}`}>
                    <Table.Td>{etichettaTipo(v.tipo)}</Table.Td>
                    <Table.Td>{v.versione_prompt ?? "—"}</Table.Td>
                    <Table.Td ta="right">{v.chiamate}</Table.Td>
                    <Table.Td ta="right">
                      {percentuale(v.tasso_errore)}
                    </Table.Td>
                    <Table.Td ta="right">{durata(v.durata_media_ms)}</Table.Td>
                    <Table.Td ta="right">{costo(v.costo_usd)}</Table.Td>
                    <Table.Td ta="right">{votoMedio(v.voto_medio)}</Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </Table.ScrollContainer>
        </Paper>
      ) : (
        <Text size="sm" c="dimmed">
          Nessuna chiamata con questi filtri.
        </Text>
      )}
    </Stack>
  );
}
