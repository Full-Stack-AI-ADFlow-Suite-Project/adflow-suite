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
import stile from "./Passo10.module.css";

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
      setErrore(e instanceof ApiErrore ? e.dettaglio : "Errore inatteso.");
    }
  };

  return (
    <Paper radius="lg" p={{ base: "md", sm: "xl" }} className={stile.form}>
      <header className={stile.intestazione}>
        {onIndietro && (
          <Text
            size="sm"
            c="verde"
            fw={600}
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
        <Text className={stile.sopratitolo}>
          Nuova campagna · Passaggio 2 di 3
        </Text>
        <Title order={2} className={stile.titolo}>
          Materiale fotografico della campagna
        </Title>
        <Text className={stile.descrizione}>
          {campagna.titolo} · {campagna.inizio} → {campagna.fine} ·{" "}
          {(campagna.canali ?? []).join(", ")}. Carica gli scatti suddivisi per
          gruppo; le uscite scoperte verranno integrate con immagini AI.
        </Text>
        <div className={stile.avanzamento} aria-label="Passaggio 2 di 3">
          <span className={stile.attivo} />
          <span className={stile.attivo} />
          <span />
        </div>
      </header>
      <Stack gap="lg" className={stile.campi}>
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
          + Aggiungi un gruppo di foto
        </Button>
        <Group gap="lg">
          <Text size="sm" c="dimmed">
            <b>{campagna.gruppi.length}</b> gruppi
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
      onErrore(e instanceof ApiErrore ? e.dettaglio : "Errore inatteso.");
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
    <Paper
      withBorder
      radius="lg"
      p="lg"
      style={{ background: "#f8fbfb", borderColor: "rgba(16, 29, 33, 0.08)" }}
    >
      <Group justify="space-between" mb="sm">
        <Text fw={700} size="sm">
          Gruppo {numero} ·{" "}
          <Text span c="dimmed" fw={500}>
            {gruppo.foto.length} foto
          </Text>
        </Text>
        <Button
          variant="subtle"
          color="red"
          size="xs"
          onClick={() => gira(() => eliminaGruppo(campagna.id, gruppo.id))}
        >
          Rimuovi gruppo
        </Button>
      </Group>

      <div
        role="button"
        tabIndex={0}
        onClick={() => inputFile.current?.click()}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            inputFile.current?.click();
          }
        }}
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          void scegliFile(e.dataTransfer.files);
        }}
        style={{
          border: "1.5px dashed rgba(0, 121, 116, 0.38)",
          borderRadius: 14,
          padding: "16px 18px",
          background: "#ffffff",
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 12,
          marginBottom: 14,
        }}
      >
        <div>
          <Text size="sm" fw={600} c="#101d21">
            {inCarico
              ? "Caricamento foto in corso…"
              : "Tocca o trascina qui le foto di questo gruppo"}
          </Text>
          <Text size="xs" c="dimmed" mt={2}>
            JPG, PNG o WEBP · max {MAX_MB} MB · lato corto almeno {MIN_LATO} px
          </Text>
        </div>
        <Button
          variant="light"
          color="verde"
          size="xs"
          loading={inCarico}
          onClick={(e) => {
            e.stopPropagation();
            inputFile.current?.click();
          }}
        >
          + Scegli file
        </Button>
        <input
          ref={inputFile}
          type="file"
          accept={TIPI_AMMESSI.join(",")}
          multiple
          hidden
          onChange={(e) => scegliFile(e.currentTarget.files)}
        />
      </div>

      {gruppo.foto.length > 0 && (
        <Group gap="sm" mb="md" align="flex-start">
          {gruppo.foto.map((f) => (
            <Thumb
              key={f.id}
              foto={f}
              onRimuovi={() => gira(() => eliminaFoto(f.id))}
            />
          ))}
        </Group>
      )}

      <Stack gap="sm">
        <Textarea
          label="Descrizione o richieste per queste foto"
          required
          minRows={2}
          value={descrizione}
          onChange={(e) => setDescrizione(e.currentTarget.value)}
          onBlur={() => salvaCampo({ descrizione })}
          error={
            !descrizione.trim() && gruppo.foto.length > 0
              ? "La descrizione manca."
              : undefined
          }
        />
        <TextInput
          label="Da usare verso il (facoltativa)"
          type="date"
          min={campagna.inizio}
          max={campagna.fine}
          value={daUsareIl}
          onChange={(e) => {
            setDaUsareIl(e.currentTarget.value);
            salvaCampo({ da_usare_il: e.currentTarget.value || null });
          }}
          description="Solo se le foto riguardano una data precisa, dentro il periodo della campagna."
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
  const [erroreImg, setErroreImg] = useState(false);
  return (
    <Paper
      withBorder
      radius="md"
      w={104}
      h={104}
      p={0}
      style={{
        position: "relative",
        overflow: "hidden",
        background: "#ffffff",
      }}
    >
      {!erroreImg ? (
        <img
          src={`/api/foto/${foto.id}/file`}
          alt={foto.file}
          onError={() => setErroreImg(true)}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            display: "block",
          }}
        />
      ) : (
        <div
          style={{
            width: "100%",
            height: "100%",
            padding: 8,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <Text
            ff="monospace"
            size="10px"
            ta="center"
            style={{ wordBreak: "break-all", lineHeight: 1.3 }}
          >
            {foto.file}
          </Text>
        </div>
      )}
      <div
        style={{
          position: "absolute",
          inset: "auto 0 0 0",
          padding: "3px 6px",
          background: "linear-gradient(transparent, rgba(16, 29, 33, 0.72))",
        }}
      >
        <Text
          size="10px"
          c="#ffffff"
          style={{
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
          }}
        >
          {foto.file}
        </Text>
      </div>
      <Text
        component="button"
        type="button"
        aria-label="Rimuovi foto"
        onClick={onRimuovi}
        style={{
          position: "absolute",
          top: 5,
          right: 5,
          width: 22,
          height: 22,
          borderRadius: "50%",
          border: "none",
          background: "rgba(16, 29, 33, 0.68)",
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
