/** Una riga etichetta-valore del riepilogo (le .rev-line dei mockup). */
import { Box, Text } from "@mantine/core";
import type { ReactNode } from "react";

export function Riga({ nome, valore }: { nome: ReactNode; valore: ReactNode }) {
  return (
    <Box
      style={{
        display: "grid",
        gridTemplateColumns: "minmax(118px, 38%) minmax(0, 1fr)",
        alignItems: "baseline",
        gap: 12,
        padding: "9px 0",
        borderTop: "1px solid rgba(15, 23, 42, 0.08)",
      }}
    >
      <Text
        c="dimmed"
        size="xs"
        fw={600}
        component="div"
        style={{ letterSpacing: "0.02em" }}
      >
        {nome}
      </Text>
      <Text size="sm" fw={500} component="div" style={{ minWidth: 0 }}>
        {valore}
      </Text>
    </Box>
  );
}
