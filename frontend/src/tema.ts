import { createTheme, rem } from "@mantine/core";
import type { CSSVariablesResolver, MantineColorsTuple } from "@mantine/core";

// Scala teal di Tailwind (50 → 900), il verde primario dell'app.
const tealTemplate: MantineColorsTuple = [
  "#f0fdfa",
  "#ccfbf1",
  "#99f6e4",
  "#5eead4",
  "#2dd4bf",
  "#14b8a6",
  "#0d9488",
  "#0f766e",
  "#115e59",
  "#134e4a",
];

const grigi: MantineColorsTuple = [
  "#f8fafc",
  "#f1f5f9",
  "#e2e8f0",
  "#cbd5e1",
  "#94a3b8",
  "#64748b",
  "#475569",
  "#334155",
  "#1e293b",
  "#0f172a",
];

const inter =
  '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
const spaceGrotesk =
  '"Space Grotesk", "Inter", -apple-system, BlinkMacSystemFont, sans-serif';

export const tema = createTheme({
  colors: {
    // Nomi usati dai componenti esistenti, tutti allineati al teal del demo.
    blu: tealTemplate,
    verde: tealTemplate,
    green: tealTemplate,
    gray: grigi,
  },
  primaryColor: "verde",
  primaryShade: 6,
  black: "#0f172a",
  fontFamily: inter,
  fontFamilyMonospace:
    '"JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
  headings: {
    fontFamily: spaceGrotesk,
    fontWeight: "600",
    textWrap: "balance",
  },
  radius: { xs: rem(8), sm: rem(12), md: rem(17.6), lg: rem(20), xl: rem(24) },
  defaultRadius: "md",
});

export const variabili: CSSVariablesResolver = () => ({
  variables: {},
  light: {
    "--mantine-color-body": "#f8fafc",
    "--mantine-color-default": "#ffffff",
    "--mantine-color-default-border": "#e2e8f0",
    "--mantine-color-default-hover": "#f1f5f9",
    "--mantine-color-dimmed": "#475569",
  },
  dark: {},
});
