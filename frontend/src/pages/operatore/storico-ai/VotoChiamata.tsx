/**
 * Il voto da 1 a 5 su una chiamata all'AI (R-50), con la nota, e i voti già dati.
 * Un voto nuovo si aggiunge: quelli di prima restano.
 */
import {
  Alert,
  Button,
  Group,
  Paper,
  Rating,
  Stack,
  Text,
  Textarea,
} from "@mantine/core";
import { useState } from "react";

import { votaChiamata, type ValutazioneAI } from "../../../api/storico";
import { dataOra } from "../campagna/util";

export function VotoChiamata({
  id,
  valutazioni,
  onVotato,
}: {
  id: number;
  valutazioni: ValutazioneAI[];
  onVotato: (nuova: ValutazioneAI) => void;
}) {
  const [voto, setVoto] = useState(0);
  const [nota, setNota] = useState("");
  const [invio, setInvio] = useState(false);
  const [errore, setErrore] = useState<string | null>(null);

  const salva = () => {
    setInvio(true);
    setErrore(null);
    votaChiamata(id, { voto, nota: nota.trim() || null })
      .then((nuova) => {
        onVotato(nuova);
        setVoto(0);
        setNota("");
      })
      .catch(() => setErrore("Impossibile salvare il voto. Riprova."))
      .finally(() => setInvio(false));
  };

  return (
    <Paper withBorder radius="md" p="md">
      <Text fw={600} size="sm" mb="xs">
        Il tuo voto
      </Text>
      <Stack gap="xs">
        <Rating
          value={voto}
          onChange={setVoto}
          size="lg"
          aria-label="Voto da 1 a 5"
        />
        <Textarea
          label="Nota (facoltativa)"
          value={nota}
          onChange={(e) => setNota(e.currentTarget.value)}
          maxLength={1000}
          autosize
          minRows={2}
        />
        {errore && (
          <Alert color="red" variant="light">
            {errore}
          </Alert>
        )}
        <Group>
          <Button
            color="verde"
            onClick={salva}
            disabled={voto < 1}
            loading={invio}
          >
            Salva il voto
          </Button>
        </Group>
      </Stack>

      <Text fw={600} size="sm" mt="md" mb="xs">
        Voti dati
      </Text>
      {valutazioni.length ? (
        <Stack gap="xs">
          {valutazioni.map((v) => (
            <div key={v.id}>
              <Group gap="xs">
                <Rating value={v.voto} readOnly size="xs" />
                <Text size="sm">
                  {v.utente_nome} · {dataOra(v.creata_il)}
                </Text>
              </Group>
              {v.nota && (
                <Text size="sm" c="dimmed">
                  {v.nota}
                </Text>
              )}
            </div>
          ))}
        </Stack>
      ) : (
        <Text size="sm" c="dimmed">
          Nessuno ha ancora votato questa risposta.
        </Text>
      )}
    </Paper>
  );
}
