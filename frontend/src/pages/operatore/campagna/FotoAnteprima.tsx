/**
 * L'immagine del post come esce (anteprima reale, RT-08). Mostra un segnaposto
 * mentre carica e un messaggio se non arriva: la card non resta mai vuota.
 */
import { Box, Skeleton, Text } from "@mantine/core";
import { useState } from "react";

/** Con una `key` diversa per ogni `src` (come in PostCard) cambiare foto riparte dal caricamento. */
export function FotoAnteprima({ src, alt }: { src: string; alt: string }) {
  const [stato, setStato] = useState<"carica" | "pronta" | "errore">("carica");

  if (stato === "errore") {
    return (
      <Box
        role="alert"
        p="md"
        style={{
          background: "var(--mantine-color-gray-0)",
          border: "1px dashed var(--mantine-color-gray-5)",
          borderRadius: 8,
        }}
      >
        <Text size="xs" c="dimmed">
          Anteprima non disponibile. Riprova tra poco o ricarica la pagina.
        </Text>
      </Box>
    );
  }
  return (
    <Box pos="relative">
      {stato === "carica" && (
        <Skeleton
          h={180}
          radius={8}
          aria-label="Caricamento della foto"
          role="status"
        />
      )}
      <img
        src={src}
        alt={alt}
        onLoad={() => setStato("pronta")}
        onError={() => setStato("errore")}
        style={{
          width: "100%",
          height: "auto",
          borderRadius: 8,
          display: stato === "pronta" ? "block" : "none",
        }}
      />
    </Box>
  );
}
