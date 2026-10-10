import { createTheme, rem } from "@mantine/core";
import type { CSSVariablesResolver, MantineColorsTuple } from "@mantine/core";

// Palette e caratteri del foglio di stile delle pagine statiche
// (docs/appunti/pagine/assets/adflow.css, ADR-113). Solo tema chiaro.
const blu: MantineColorsTuple = [
  "#eff6ff", // --primary-light
  "#dbeafe",
  "#bfdbfe", // --primary-border
  "#93c5fd",
  "#60a5fa",
  "#3b82f6",
  "#2563eb", // --primary
  "#1d4ed8", // --primary-hover
  "#1e40af",
  "#1e3a8a",
];

// I grigi di Mantine con i valori del foglio di stile: fondo, bordi e testi.
const gray: MantineColorsTuple = [
  "#f8fafc", // --bg-app
  "#f1f5f9", // --bg-surface-subtle
  "#e9eef5",
  "#e2e8f0", // --border-hairline
  "#cbd5e1", // --border-strong
  "#94a3b8", // --text-faint
  "#64748b", // --text-muted
  "#475569", // --text-secondary
  "#1e293b",
  "#0f172a", // --text-main
];

const inter =
  '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';

export const tema = createTheme({
  // `verde` è il nome di prima del colore primario: le pagine lo scrivono
  // ancora (`color="verde"`). Resta finché non lo tolgono (#76).
  colors: { blu, verde: blu, gray },
  primaryColor: "blu",
  primaryShade: 6,
  black: gray[9],
  fontFamily: inter,
  fontFamilyMonospace:
    '"JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, monospace',
  headings: {
    fontFamily: inter,
    fontWeight: "700",
    textWrap: "balance",
  },
  radius: { sm: rem(6), md: rem(10), lg: rem(14) },
  defaultRadius: "md",
});

// Bordo delle card e fondo al passaggio del mouse: Mantine li prende da
// due grigi più scuri di quelli del foglio di stile.
export const variabili: CSSVariablesResolver = () => ({
  variables: {},
  light: {
    "--mantine-color-default-border": "var(--mantine-color-gray-3)",
    "--mantine-color-default-hover": "var(--mantine-color-gray-1)",
  },
  dark: {},
});
