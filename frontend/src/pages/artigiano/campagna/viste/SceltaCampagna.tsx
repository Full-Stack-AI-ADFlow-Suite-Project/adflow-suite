/**
 * La riga di scelta in cima alla pagina Campagna, quando l'artigiano ha più
 * campagne (spec §4): una alla volta, quella che chiede qualcosa si apre da
 * sola. "Nuova campagna" sta nella stessa riga, se non c'è già una bozza.
 */
import { Button, Group } from "@mantine/core";

import type { CampagnaElencoItem } from "../../../../api/campagne";

const STATO: Record<string, string> = {
  bozza: "bozza",
  inviata: "inviata",
  in_generazione: "in preparazione",
  generazione_fallita: "in preparazione",
  piano_da_rivedere: "in revisione",
  in_revisione: "in revisione",
  attiva: "in corso",
  sospesa: "sospesa",
  respinta: "respinta",
  scaduta: "scaduta",
};

export function SceltaCampagna({
  visibili,
  apertaId,
  onApri,
  onNuova,
}: {
  visibili: CampagnaElencoItem[];
  /** La campagna mostrata; null se si sta guardando una campagna passata. */
  apertaId: number | null;
  onApri: (c: CampagnaElencoItem) => void;
  onNuova: () => void;
}) {
  const haBozza = visibili.some((c) => c.stato === "bozza");
  return (
    <Group gap="xs" mb="lg" wrap="wrap" aria-label="Scelta della campagna">
      {visibili.map((c) => (
        <Button
          key={c.id}
          size="xs"
          radius="xl"
          color="verde"
          variant={c.id === apertaId ? "filled" : "default"}
          onClick={() => onApri(c)}
        >
          {c.titolo} · {STATO[c.stato] ?? c.stato}
        </Button>
      ))}
      {!haBozza && (
        <Button
          size="xs"
          radius="xl"
          variant="subtle"
          color="verde"
          onClick={onNuova}
        >
          + Nuova campagna
        </Button>
      )}
    </Group>
  );
}
