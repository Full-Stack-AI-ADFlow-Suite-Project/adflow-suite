/**
 * L'archivio foto in sola lettura (docs/pagine/AdFlow-archivio-foto.html, spec
 * R-47, ADR-117, H4), lo stesso componente per l'artigiano e per l'operatore:
 * un blocco per campagna, le miniature e, sulle immagini AI, l'etichetta
 * "Immagine AI". Un clic apre la foto grande. Nessun pulsante per caricare,
 * cambiare o eliminare.
 */
import {
  Badge,
  Card,
  Group,
  Image,
  Modal,
  Paper,
  SimpleGrid,
  Text,
  Title,
  UnstyledButton,
} from "@mantine/core";
import { useState } from "react";

import { StatoBadge } from "./StatoBadge";

import type {
  BloccoArchivio,
  CampagnaDelBlocco,
  FotoArchivio,
} from "../api/campagne";

const CANALE: Record<string, string> = {
  facebook: "Facebook",
  instagram: "Instagram",
};

/** Lo stato come lo legge l'artigiano; l'operatore usa `StatoBadge`. */
const STATO_ARTIGIANO: Record<string, string> = {
  bozza: "Bozza",
  inviata: "In lavorazione",
  in_generazione: "In lavorazione",
  generazione_fallita: "In lavorazione",
  piano_da_rivedere: "In lavorazione",
  in_revisione: "In lavorazione",
  attiva: "In corso",
  sospesa: "Pubblicazioni ferme",
  conclusa: "Conclusa",
  annullata: "Annullata",
  scaduta: "Scaduta",
  respinta: "Respinta",
};

/** "2026-10-01" → "01/10". */
const giornoMese = (iso: string) =>
  iso.split("-").reverse().slice(0, 2).join("/");

function periodo(c: CampagnaDelBlocco): string {
  return `${giornoMese(c.inizio)} – ${giornoMese(c.fine)}`;
}

/** «Pubblicata su Facebook, Instagram», o niente se la foto non è mai uscita. */
function doveECUscita(foto: FotoArchivio): string {
  const canali = Object.keys(foto.pubblicata_su).map((c) => CANALE[c] ?? c);
  return canali.length ? `Pubblicata su ${canali.join(", ")}` : "";
}

function Miniatura({
  foto,
  onApri,
}: {
  foto: FotoArchivio;
  onApri: () => void;
}) {
  const ai = foto.origine === "creata_ai";
  return (
    <div>
      <UnstyledButton
        onClick={onApri}
        aria-label={ai ? "Apri l'immagine AI" : "Apri la foto"}
        style={{ position: "relative", display: "block", width: "100%" }}
      >
        <Image
          src={foto.url}
          alt={ai ? "Immagine creata con AI" : "Foto della bottega"}
          radius="md"
          fit="cover"
          style={{ aspectRatio: "1 / 1" }}
          loading="lazy"
        />
        {ai && (
          <Badge
            size="xs"
            color="dark"
            style={{ position: "absolute", left: 6, bottom: 6 }}
          >
            Immagine AI
          </Badge>
        )}
      </UnstyledButton>
      <Text size="xs" c="dimmed" mt={4} mih={16}>
        {doveECUscita(foto)}
      </Text>
    </div>
  );
}

export function ArchivioFoto({
  blocchi,
  lato,
  vuoto = "Non ci sono ancora foto.",
}: {
  blocchi: BloccoArchivio[];
  lato: "artigiano" | "operatore";
  vuoto?: string;
}) {
  const [aperta, setAperta] = useState<FotoArchivio | null>(null);

  if (blocchi.length === 0) {
    return (
      <Paper withBorder radius="md" p="lg" style={{ borderStyle: "dashed" }}>
        <Text c="dimmed" size="sm">
          {vuoto}
        </Text>
      </Paper>
    );
  }

  return (
    <>
      {blocchi.map((blocco) => {
        const c = blocco.campagna;
        return (
          <Card
            key={c?.id ?? "senza-campagna"}
            withBorder
            radius="md"
            p={{ base: "md", sm: "lg" }}
            mb="lg"
          >
            <Group justify="space-between" mb="md" wrap="wrap" gap="xs">
              <Group gap="sm">
                <Title order={2} size="h4">
                  {c ? c.titolo : "Foto senza campagna"}
                </Title>
                {c &&
                  (lato === "artigiano" ? (
                    <Badge variant="light" color="gray">
                      {STATO_ARTIGIANO[c.stato] ?? c.stato}
                    </Badge>
                  ) : (
                    <StatoBadge tipo="campagna" stato={c.stato} />
                  ))}
              </Group>
              {c && (
                <Text size="sm" c="dimmed">
                  {periodo(c)}
                </Text>
              )}
            </Group>
            <SimpleGrid cols={{ base: 2, sm: 3, md: 5 }} spacing="md">
              {blocco.foto.map((foto) => (
                <Miniatura
                  key={foto.id}
                  foto={foto}
                  onApri={() => setAperta(foto)}
                />
              ))}
            </SimpleGrid>
          </Card>
        );
      })}

      <Modal
        opened={aperta !== null}
        onClose={() => setAperta(null)}
        title={aperta?.origine === "creata_ai" ? "Immagine AI" : "Foto"}
        size="lg"
        centered
      >
        {aperta && (
          <>
            <Image
              src={aperta.url}
              alt={
                aperta.origine === "creata_ai"
                  ? "Immagine creata con AI"
                  : "Foto della bottega"
              }
              fit="contain"
              mah="70vh"
            />
            <Text size="sm" c="dimmed" mt="sm">
              {doveECUscita(aperta) || "Non è ancora stata pubblicata."}
            </Text>
          </>
        )}
      </Modal>
    </>
  );
}
