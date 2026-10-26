/**
 * Passo 11 · Foto della campagna: gruppi `caricate` con descrizione e
 * data facoltativa (R-13). I gruppi `create_ai` restano nascosti
 * (spec §7). Le foto sono facoltative: quelle che mancano diventano
 * immagini AI (R-28), senza un minimo all'invio.
 */
import { useRef, useState } from "react";
import {
  Alert,
  Button,
  Divider,
  Group,
  Paper,
  Stack,
  Text,
  Textarea,
  TextInput,
  Title,
} from "@mantine/core";

import {
  aggiornaGruppo,
  caricaFoto,
  creaGruppo,
  eliminaFoto,
  eliminaGruppo,
  type CampagnaDettaglio,
  type FotoSintetica,
  type GruppoSintetico,
} from "../../../api/campagne";
import { ApiErrore } from "../../../api/http";

const MAX_MB = 10;
const MIN_LATO = 1080;
const TIPI_AMMESSI = ["image/jpeg", "image/png", "image/webp"];

function latoCorto(file: File): Promise<number> {
  return new Promise((risolvi) => {
    const img = new Image();
    img.onload = () => {
      risolvi(Math.min(img.width, img.height));
      URL.revokeObjectURL(img.src);
    };
    img.onerror = () => risolvi(0);
    img.src = URL.createObjectURL(file);
  });
}

export function Passo11({
  campagna,
  onCambiata,
  onAvanti,
  onIndietro,
}: {
  campagna: CampagnaDettaglio;
  onCambiata: (c: CampagnaDettaglio) => Promise<void>;
  onAvanti: () => void;
  onIndietro?: () => void;
}) {
  const [errore, setErrore] = useState("");
  const nFoto = campagna.gruppi.reduce((n, g) => n + g.foto.length, 0);

  const aggiungiGruppo = async () => {
    setErrore("");
    try {
      await creaGruppo(campagna.id, { origine: "caricate" });
      await onCambiata(campagna);
    } catch (e) {
      setErrore(
        e instanceof ApiErrore
          ? e.dettaglio
          : "Impossibile completare l’operazione. Riprova.",
      );
    }
  };

  return (
    <Paper withBorder radius="md" p="xl">
      {onIndietro && (
        <Text
          size="sm"
          c="verde"
          td="underline"
          mb="xs"
          component="button"
          onClick={onIndietro}
          style={{
            background: "none",
            border: "none",
            cursor: "pointer",
            padding: 0,
          }}
        >
          ← Modifica dati campagna
        </Text>
      )}
      <Text ff="monospace" size="xs" c="verde">
        11 · FOTO DELLA CAMPAGNA
      </Text>
      <Title order={2} mt={4}>
        Quali foto vuoi usare in questo periodo?
      </Title>
      <Text c="dimmed" size="sm" mt={4} mb="md">
        {campagna.titolo} · {campagna.inizio} → {campagna.fine} ·{" "}
        {(campagna.canali ?? []).join(", ")}
      </Text>
      <Alert color="verde" variant="light" mb="lg">
        Riunisci da 1 a 20 foto che vuoi raccontare insieme. Puoi anche
        proseguire senza foto: per i post mancanti creiamo un’immagine con l'AI,
        e i post che hai scelto escono sempre tutti. Se le foto sono di più,
        usiamo le migliori. JPG, PNG o WEBP, fino a {MAX_MB} MB, lato corto di
        almeno {MIN_LATO} px.
      </Alert>
      <Stack gap="lg">
        {campagna.gruppi.map((g, i) => (
          <GruppoEditor
            key={g.id}
            gruppo={g}
            numero={i + 1}
            campagna={campagna}
            onErrore={setErrore}
            onCambiata={onCambiata}
          />
        ))}
        {errore && (
          <Alert color="red" variant="light">
            {errore}
          </Alert>
        )}
        <Button variant="outline" color="verde" onClick={aggiungiGruppo}>
          + Aggiungi una serie di foto
        </Button>
        <Group gap="lg">
          <Text size="sm" c="dimmed">
            <b>{campagna.gruppi.length}</b> serie
          </Text>
          <Text size="sm" c="dimmed">
            <b>{nFoto}</b> foto in totale
          </Text>
        </Group>
        <Divider />
        <Group justify="space-between">
          {onIndietro ? (
            <Button variant="default" onClick={onIndietro}>
              ← Torna a dati e canali
            </Button>
          ) : (
            <div />
          )}
          <Button color="verde" onClick={onAvanti}>
            Vai al riepilogo →
          </Button>
        </Group>
      </Stack>
    </Paper>
  );
}

function GruppoEditor({
  gruppo,
  numero,
  campagna,
  onErrore,
  onCambiata,
}: {
  gruppo: GruppoSintetico;
  numero: number;
  campagna: CampagnaDettaglio;
  onErrore: (e: string) => void;
  onCambiata: (c: CampagnaDettaglio) => Promise<void>;
}) {
  const inputFile = useRef<HTMLInputElement>(null);
  const [descrizione, setDescrizione] = useState(gruppo.descrizione ?? "");
  const [daUsareIl, setDaUsareIl] = useState(gruppo.da_usare_il ?? "");
  const [inCarico, setInCarico] = useState(false);

  const gira = async (azione: () => Promise<unknown>) => {
    onErrore("");
    try {
      await azione();
      await onCambiata(campagna);
    } catch (e) {
      onErrore(
        e instanceof ApiErrore
          ? e.dettaglio
          : "Impossibile completare l’operazione. Riprova.",
      );
    }
  };

  const salvaCampo = (dati: Parameters<typeof aggiornaGruppo>[2]) =>
    gira(() => aggiornaGruppo(campagna.id, gruppo.id, dati));

  const scegliFile = async (lista: FileList | null) => {
    if (!lista?.length) return;
    setInCarico(true);
    for (const file of Array.from(lista)) {
      if (!TIPI_AMMESSI.includes(file.type)) {
        onErrore(`${file.name}: solo foto JPG, PNG o WEBP.`);
        continue;
      }
      if (file.size > MAX_MB * 1024 * 1024) {
        onErrore(`${file.name}: più di ${MAX_MB} MB.`);
        continue;
      }
      if ((await latoCorto(file)) < MIN_LATO) {
        onErrore(
          `${file.name}: il lato corto deve essere di almeno ${MIN_LATO} px.`,
        );
        continue;
      }
      await gira(() => caricaFoto(campagna.id, gruppo.id, file));
    }
    setInCarico(false);
    if (inputFile.current) inputFile.current.value = "";
  };

  return (
    <Paper withBorder radius="md" p="md" bg="var(--mantine-color-body)">
      <Group justify="space-between" mb="sm">
        <Text ff="monospace" size="xs" c="dimmed">
          Serie di foto {numero} · {gruppo.foto.length} foto
        </Text>
        <Text
          size="xs"
          c="dimmed"
          td="underline"
          component="button"
          onClick={() => gira(() => eliminaGruppo(campagna.id, gruppo.id))}
          style={{ background: "none", border: "none", cursor: "pointer" }}
        >
          Rimuovi queste foto
        </Text>
      </Group>
      <Group gap="xs" mb="sm" align="flex-start">
        {gruppo.foto.map((f) => (
          <Thumb
            key={f.id}
            foto={f}
            onRimuovi={() => gira(() => eliminaFoto(f.id))}
          />
        ))}
        <Button
          variant="outline"
          color="gray"
          w={84}
          h={84}
          loading={inCarico}
          onClick={() => inputFile.current?.click()}
        >
          +
        </Button>
        <input
          ref={inputFile}
          type="file"
          accept={TIPI_AMMESSI.join(",")}
          multiple
          hidden
          onChange={(e) => scegliFile(e.currentTarget.files)}
        />
      </Group>
      <Stack gap="sm">
        <Textarea
          label="Cosa mostrano queste foto e cosa vuoi raccontare?"
          required
          minRows={2}
          value={descrizione}
          onChange={(e) => setDescrizione(e.currentTarget.value)}
          onBlur={() => salvaCampo({ descrizione })}
          error={
            !descrizione.trim() && gruppo.foto.length > 0
              ? "Racconta cosa mostrano queste foto."
              : undefined
          }
        />
        <TextInput
          label="C’è un giorno in cui vuoi che escano? (facoltativo)"
          type="date"
          min={campagna.inizio}
          max={campagna.fine}
          value={daUsareIl}
          onChange={(e) => {
            setDaUsareIl(e.currentTarget.value);
            salvaCampo({ da_usare_il: e.currentTarget.value || null });
          }}
          description="Puoi indicare una data preferita nel periodo della campagna. Le date dei post le propone l’AI."
        />
      </Stack>
    </Paper>
  );
}

function Thumb({
  foto,
  onRimuovi,
}: {
  foto: FotoSintetica;
  onRimuovi: () => void;
}) {
  return (
    <Paper
      withBorder
      radius="sm"
      w={84}
      h={84}
      p={4}
      style={{ position: "relative", overflow: "hidden" }}
    >
      <Text
        ff="monospace"
        size="10px"
        ta="center"
        style={{ wordBreak: "break-all", lineHeight: 1.3 }}
      >
        {foto.file}
      </Text>
      <Text
        component="button"
        aria-label="Rimuovi foto"
        onClick={onRimuovi}
        style={{
          position: "absolute",
          top: 2,
          right: 2,
          width: 20,
          height: 20,
          borderRadius: "50%",
          border: "none",
          background: "rgba(0,0,0,.4)",
          color: "#fff",
          fontSize: 13,
          lineHeight: 1,
          cursor: "pointer",
          padding: 0,
        }}
      >
        ×
      </Text>
    </Paper>
  );
}
