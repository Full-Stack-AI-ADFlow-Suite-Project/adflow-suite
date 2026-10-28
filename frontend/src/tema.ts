import { Button, Card, createTheme, Paper, rem } from "@mantine/core";
import type { CSSVariablesResolver, MantineColorsTuple } from "@mantine/core";

// Palette e caratteri del foglio di stile delle pagine statiche
// (docs/pagine/assets/adflow.css, ADR-113). Solo tema chiaro.
const blu: MantineColorsTuple = [
  "#eef5f1", // --primary-light
  "#d9e9df",
  "#b8d5c4", // --primary-border
  "#8ebba2",
  "#5f9a7a",
  "#3f7a5b",
  "#2f5d46", // --primary
  "#254b38", // --primary-hover
  "#1d3b2c",
  "#152b20",
];

// I grigi di Mantine con i valori del foglio di stile: fondo, bordi e testi.
const gray: MantineColorsTuple = [
  "#f7f5ef", // --bg-app
  "#efeae0", // --bg-surface-subtle
  "#e6e0d4",
  "#ddd6c7", // --border-hairline
  "#c7bfb0", // --border-strong
  "#8c8578", // --text-faint
  "#635d52", // --text-muted
  "#474239", // --text-secondary
  "#2c352f",
  "#1f2a24", // --text-main
];

const sourceSans =
  '"Source Sans 3", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';

export const tema = createTheme({
  // `verde` è il nome di prima del colore primario: le pagine lo scrivono
  // ancora (`color="verde"`). Resta finché non lo tolgono (#76).
  colors: { blu, verde: blu, gray },
  primaryColor: "blu",
  primaryShade: 6,
  black: gray[9],
  fontFamily: sourceSans,
  fontFamilyMonospace:
    '"JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, monospace',
  headings: {
    fontFamily: sourceSans,
    fontWeight: "700",
    textWrap: "balance",
  },
  radius: { sm: rem(6), md: rem(10), lg: rem(14) },
  defaultRadius: "md",
  shadows: {
    xs: "0 1px 2px 0 rgba(31, 42, 36, 0.05)",
    sm: "0 1px 3px 0 rgba(31, 42, 36, 0.05)",
    md: "0 4px 6px -1px rgba(31, 42, 36, 0.05)",
    lg: "0 10px 15px -3px rgba(31, 42, 36, 0.05)",
    xl: "0 20px 25px -5px rgba(31, 42, 36, 0.05)",
  },
  components: {
    Button: Button.extend({ defaultProps: { radius: "md" } }),
    Card: Card.extend({ defaultProps: { radius: "lg", shadow: "xs" } }),
    Paper: Paper.extend({ defaultProps: { radius: "lg", shadow: "xs" } }),
  },
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
