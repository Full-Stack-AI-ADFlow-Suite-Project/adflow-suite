/** Una riga etichetta-valore del riepilogo (le .rev-line dei mockup). */
import { Box, Text } from "@mantine/core";
import type { ReactNode } from "react";

export function Riga({ nome, valore }: { nome: string; valore: ReactNode }) {
  return (
    <Box
      style={{
        display: "flex",
        gap: 10,
        padding: "5px 0",
        borderTop: "1px solid var(--mantine-color-default-border)",
      }}
    >
      <Text c="dimmed" size="sm" style={{ flex: "0 0 42%" }}>
        {nome}
      </Text>
      <Text size="sm" component="div" style={{ flex: 1, minWidth: 0 }}>
        {valore}
      </Text>
    </Box>
  );
}
