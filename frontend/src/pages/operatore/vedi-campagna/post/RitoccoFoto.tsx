/**
 * Ritocco della foto del post (ADR-124, RT-30): le tre varianti (Originale, Standard, Spinta),
 * l'interruttore delle zone di privacy e gli avvisi sulla foto. Ogni scelta chiama
 * `ritocca-foto` (senza AI) e poi la vista si ricarica: l'anteprima è il render nuovo.
 * Una variante che non c'è è spenta; una che esce uguale all'Originale lo dice.
 */
import { Alert, SegmentedControl, Stack, Switch, Text } from "@mantine/core";
import { useState } from "react";

import { ApiErrore } from "../../../../api/http";
import { ritoccaFoto } from "../../../../api/interventi";
import type { PostVista, VarianteFoto } from "../../../../api/revisione";

const NOME_VARIANTE: Record<VarianteFoto, string> = {
  originale: "Originale",
  standard: "Standard",
  spinta: "Spinta",
};
const ORDINE: VarianteFoto[] = ["originale", "standard", "spinta"];

/** Gli avvisi della foto (codici del backend) in parole. */
const TESTO_AVVISO: Record<string, string> = {
  privacy_da_decidere:
    "Ci sono zone da proteggere (dati personali visibili): decidi se oscurarle.",
  volto_minore: "Nella foto c'è un volto che sembra di un minore.",
  riflessi_ai_bordi: "Riflessi ai bordi della foto.",
  riflessi_sul_soggetto: "Riflessi sul soggetto.",
  foto_mossa_lieve: "La foto è leggermente mossa.",
  foto_mossa_forte: "La foto è molto mossa.",
  foto_di_foto: "È la fotografia di una fotografia.",
  screenshot: "Sembra uno screenshot.",
  grafica: "Sembra una grafica, non una foto.",
  marchi_di_altre_aziende: "Si vedono loghi o marchi di altre aziende.",
  compressione_forte: "La foto è molto compressa.",
};

export function RitoccoFoto({
  post,
  ricarica,
}: {
  post: PostVista;
  ricarica: () => void;
}) {
  const foto = post.foto;
  const [occupata, setOccupata] = useState(false);
  const [errore, setErrore] = useState<string | null>(null);
  const [esteso, setEsteso] = useState<string | null>(null);
  if (!foto) return null;

  const { varianti, zone_privacy: zone } = foto;
  const uguale = varianti.uguali.includes(varianti.scelta);

  const invia = async (
    variante: VarianteFoto | null,
    privacy: boolean | null,
  ) => {
    setOccupata(true);
    setErrore(null);
    setEsteso(null);
    try {
      const esito = await ritoccaFoto(post.post_id, variante, privacy);
      const altri = esito.post_aggiornati.filter((id) => id !== post.post_id);
      if (altri.length > 0)
        setEsteso("Vale anche per l'altro post con questa foto.");
      if (esito.post_non_aggiornati.length > 0)
        setEsteso(
          `Un altro post con questa foto non si è potuto aggiornare: ${esito.post_non_aggiornati[0].motivo}`,
        );
      ricarica();
    } catch (e) {
      setErrore(
        e instanceof ApiErrore ? e.message : "Qualcosa non ha funzionato.",
      );
    } finally {
      setOccupata(false);
    }
  };

  return (
    <Stack gap="xs" aria-label="Ritocco della foto">
      <SegmentedControl
        size="xs"
        aria-label="Variante della foto"
        value={varianti.scelta}
        disabled={occupata}
        data={ORDINE.map((v) => ({
          value: v,
          label: NOME_VARIANTE[v],
          disabled: !varianti.disponibili.includes(v),
        }))}
        onChange={(v) => void invia(v as VarianteFoto, null)}
      />
      {uguale && (
        <Text size="xs" c="dimmed">
          Nessuna modifica necessaria: esce uguale all'Originale.
        </Text>
      )}
      {!varianti.disponibili.includes("spinta") && (
        <Text size="xs" c="dimmed">
          La variante Spinta non è disponibile per questa foto.
        </Text>
      )}
      {zone.numero > 0 && (
        <Switch
          size="sm"
          label={`Oscura ${zone.numero} ${zone.numero === 1 ? "zona" : "zone"}`}
          checked={!!zone.oscurate}
          disabled={occupata}
          onChange={(e) => void invia(null, e.currentTarget.checked)}
        />
      )}
      {foto.avvisi.map((a) => (
        <Alert key={a} color="yellow" variant="light" py="xs">
          {TESTO_AVVISO[a] ?? a} Se non va, usa «Cambia immagine» o «Chiedi
          all'artigiano».
        </Alert>
      ))}
      {esteso && (
        <Text size="xs" c="dimmed" role="status">
          {esteso}
        </Text>
      )}
      {errore && (
        <Alert color="red" variant="light" py="xs">
          {errore}
        </Alert>
      )}
    </Stack>
  );
}
