/**
 * «Il consorzio ti chiede» (R-46, R-41): nella vista «In revisione» della
 * pagina Campagna l'artigiano vede la domanda del consorzio e le sue foto da
 * sostituire, carica quelle nuove (con la spunta di R-41) e invia la risposta.
 * Mai piano né post. Dopo ogni azione la richiesta si rilegge.
 */
import {
  Alert,
  Badge,
  Button,
  Checkbox,
  FileInput,
  Group,
  Image,
  Paper,
  Stack,
  Text,
  Textarea,
  Title,
} from "@mantine/core";
import { useState } from "react";

import { urlFotoFile } from "../../../../api/archivio";
import type {
  CampagnaDettaglio,
  FotoSintetica,
  RichiestaArtigiano,
} from "../../../../api/campagne";
import {
  caricaFotoRichiesta,
  dettaglio,
  inviaRisposta,
} from "../../../../api/campagne";
import { ApiErrore } from "../../../../api/http";

const TIPI_ACCETTATI = "image/jpeg,image/png,image/webp";
const MAX_BYTE = 10 * 1024 * 1024;
const DICHIARAZIONE =
  "Le foto mostrano prodotti della mia bottega; le persone riconoscibili hanno dato il consenso";

function dataIT(iso: string | null): string {
  return iso ? new Date(iso).toLocaleDateString("it-IT") : "—";
}

/** Il controllo nel browser di tipo e peso; il server rifà quello vero (R-13). */
function controllaFile(file: File): string | null {
  if (!TIPI_ACCETTATI.split(",").includes(file.type))
    return "Scegli una foto JPG, PNG o WEBP.";
  if (file.size > MAX_BYTE) return "Scegli una foto che non superi 10 MB.";
  return null;
}

function Miniatura({
  campagna,
  fotoId,
}: {
  campagna: CampagnaDettaglio;
  fotoId: number;
}) {
  const foto: FotoSintetica | undefined = campagna.gruppi
    .flatMap((g) => g.foto)
    .find((f) => f.id === fotoId);
  return (
    <Image
      src={foto ? urlFotoFile(foto.file, foto.id) : undefined}
      alt={`Foto ${fotoId}`}
      h={72}
      w={72}
      fit="cover"
      radius="sm"
      fallbackSrc="data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='72' height='72'%3E%3Crect width='72' height='72' fill='%23e9ecef'/%3E%3C/svg%3E"
    />
  );
}

function RigaFoto({
  campagna,
  daSostituire,
  possoCaricare,
  fotoId,
  nuovaId,
  rileggi,
}: {
  campagna: CampagnaDettaglio;
  daSostituire: number;
  possoCaricare: boolean;
  fotoId: number;
  nuovaId: number | null;
  rileggi: () => Promise<void>;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [occupato, setOccupato] = useState(false);
  const [errore, setErrore] = useState<string | null>(null);

  const scegli = (nuovo: File | null) => {
    setFile(nuovo);
    setErrore(nuovo ? controllaFile(nuovo) : null);
  };

  const carica = async () => {
    if (!file) return;
    setOccupato(true);
    setErrore(null);
    try {
      await caricaFotoRichiesta(campagna.id, fotoId, file, true);
      setFile(null);
      await rileggi();
    } catch (e) {
      setErrore(
        e instanceof ApiErrore
          ? e.message
          : "Impossibile caricare la foto. Riprova.",
      );
    } finally {
      setOccupato(false);
    }
  };

  return (
    <Paper withBorder radius="md" p="sm" data-sostituisci={daSostituire}>
      <Group align="flex-start" wrap="nowrap" gap="md">
        <Miniatura campagna={campagna} fotoId={nuovaId ?? fotoId} />
        <Stack gap={6} style={{ flex: 1 }}>
          <Group gap="xs">
            <Text size="sm" fw={500}>
              Foto {fotoId}
            </Text>
            <Badge
              variant="light"
              color={nuovaId !== null ? "verde" : "yellow"}
            >
              {nuovaId !== null ? "Caricata" : "Da sostituire"}
            </Badge>
          </Group>
          {nuovaId === null && (
            <Group gap="xs" align="flex-end" wrap="wrap">
              <FileInput
                size="xs"
                placeholder="Scegli la foto nuova"
                accept={TIPI_ACCETTATI}
                value={file}
                onChange={scegli}
                clearable
                aria-label={`Foto nuova al posto della foto ${fotoId}`}
                error={errore}
                style={{ flex: "1 1 220px" }}
              />
              <Button
                size="xs"
                color="verde"
                loading={occupato}
                disabled={!file || errore !== null || !possoCaricare}
                onClick={() => void carica()}
              >
                Carica
              </Button>
            </Group>
          )}
          {nuovaId === null && !possoCaricare && (
            <Text size="xs" c="dimmed">
              Spunta la dichiarazione qui sopra per caricare le foto.
            </Text>
          )}
        </Stack>
      </Group>
    </Paper>
  );
}

export function RichiestaConsorzio({
  campagna: iniziale,
  onRisposta,
}: {
  campagna: CampagnaDettaglio;
  onRisposta?: () => void;
}) {
  const [campagna, setCampagna] = useState(iniziale);
  const [dichiarazione, setDichiarazione] = useState(false);
  const [risposta, setRisposta] = useState("");
  const [occupato, setOccupato] = useState(false);
  const [errore, setErrore] = useState<string | null>(null);

  const richiesta: RichiestaArtigiano | null | undefined = campagna.richiesta;
  if (!richiesta || richiesta.stato === "decaduta") return null;

  const rileggi = async () => setCampagna(await dettaglio(campagna.id));

  if (richiesta.stato === "inviata")
    return (
      <Alert color="verde" variant="light" mb="md">
        Hai risposto il {dataIT(richiesta.inviata_il)}: il consorzio sta finendo
        di controllare i post.
      </Alert>
    );

  const conFoto = richiesta.foto.length > 0;
  const tutteCaricate = richiesta.foto.every((f) => f.nuova_foto_id !== null);
  const puoInviare = conFoto ? tutteCaricate : risposta.trim().length > 0;

  const invia = async () => {
    setOccupato(true);
    setErrore(null);
    try {
      await inviaRisposta(campagna.id, risposta.trim() || null);
      await rileggi();
      onRisposta?.();
    } catch (e) {
      setErrore(
        e instanceof ApiErrore
          ? e.message
          : "Impossibile inviare la risposta. Riprova.",
      );
    } finally {
      setOccupato(false);
    }
  };

  return (
    <Paper
      withBorder
      radius="md"
      p="lg"
      mb="md"
      aria-label="Il consorzio ti chiede"
    >
      <Stack gap="sm">
        <Title order={3} size="h4">
          Il consorzio ti chiede
        </Title>
        <Text size="sm" c="dimmed">
          Chiesto il {dataIT(richiesta.creata_il)}
        </Text>
        <Text style={{ whiteSpace: "pre-line" }}>{richiesta.domanda}</Text>

        {conFoto && (
          <>
            <Checkbox
              checked={dichiarazione}
              onChange={(e) => setDichiarazione(e.currentTarget.checked)}
              label={DICHIARAZIONE}
              required
            />
            <Stack gap="xs">
              {richiesta.foto.map((f, i) => (
                <RigaFoto
                  key={f.foto_id}
                  campagna={campagna}
                  daSostituire={i + 1}
                  possoCaricare={dichiarazione}
                  fotoId={f.foto_id}
                  nuovaId={f.nuova_foto_id}
                  rileggi={rileggi}
                />
              ))}
            </Stack>
          </>
        )}

        <Textarea
          label="Cosa vuoi rispondere al consorzio?"
          description={
            conFoto ? "Facoltativa se hai caricato le foto." : "Obbligatoria."
          }
          value={risposta}
          onChange={(e) => setRisposta(e.currentTarget.value)}
          autosize
          minRows={3}
          maxRows={8}
          withAsterisk={!conFoto}
        />
        {errore && (
          <Alert color="red" variant="light" py="xs">
            {errore}
          </Alert>
        )}
        <Group justify="flex-end">
          <Button
            color="verde"
            loading={occupato}
            disabled={!puoInviare}
            onClick={() => void invia()}
          >
            Invia al consorzio
          </Button>
        </Group>
      </Stack>
    </Paper>
  );
}
