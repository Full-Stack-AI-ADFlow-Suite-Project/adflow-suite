/**
 * Passo 7 · Foto e contenuti: solo le tre preferenze sulle foto. Nell'MVP
 * non ci sono né l'archivio della bottega (A10, congelato: SezioneArchivio
 * resta nel codice, nascosta) né il logo (A7, tolto: è una foto come le
 * altre). Le foto si caricano in ogni campagna.
 */
import { Alert, Select, SimpleGrid, Stack } from "@mantine/core";

import type {
  DatiProfilo,
  SCELTE as ScelteTipo,
} from "../../../../api/artigiani";

export function Passo7({
  dati,
  cambia,
  scelte,
}: {
  dati: DatiProfilo;
  cambia: <K extends keyof DatiProfilo>(
    campo: K,
    valore: DatiProfilo[K],
  ) => void;
  scelte: typeof ScelteTipo;
}) {
  const policy = (
    campo: "quantita_mese" | "chi_scatta" | "persone",
    label: string,
  ) => (
    <Select
      label={label}
      data={scelte[campo]}
      clearable
      value={
        typeof dati?.foto_policy?.[campo] === "string"
          ? (dati.foto_policy[campo] as string)
          : null
      }
      onChange={(v) => {
        const p = { ...dati?.foto_policy };
        if (v) p[campo] = v;
        else delete p[campo];
        cambia("foto_policy", Object.keys(p).length ? p : null);
      }}
    />
  );

  return (
    <Stack gap="lg">
      <SimpleGrid
        cols={{ base: 1, sm: 3 }}
        spacing="md"
        style={{ alignItems: "end" }}
      >
        {policy("quantita_mese", "Disponibilità mensile scatti")}
        {policy("chi_scatta", "Produzione fotografica")}
        {policy("persone", "Persone ritratte")}
      </SimpleGrid>

      <Alert color="verde" variant="light">
        Il materiale fotografico viene caricato all'interno di ciascuna
        campagna. Quando il numero di scatti è inferiore alle uscite previste,
        il piano integra immagini editoriali generate con AI (ambientazioni,
        materiali e lavorazioni, senza riprodurre prodotti non appartenenti
        all'impresa).
      </Alert>
    </Stack>
  );
}
