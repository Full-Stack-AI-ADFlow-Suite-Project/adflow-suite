import { createTheme, rem } from "@mantine/core";
import type { CSSVariablesResolver, MantineColorsTuple } from "@mantine/core";

// Palette teal estratta dal CSS del template Bill Splitter.
const tealTemplate: MantineColorsTuple = [
  "#e7f6f5",
  "#d9f5f3",
  "#c6eae7",
  "#a5d9d5",
  "#72c2bd",
  "#258b86",
  "#007974",
  "#006c68",
  "#005a57",
  "#004743",
];

const grigi: MantineColorsTuple = [
  "#f2f8f8",
  "#e3f4f3",
  "#d9f5f3",
  "#cbdedd",
  "#b5cdcb",
  "#94afad",
  "#718b89",
  "#53696b",
  "#304649",
  "#101d21",
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
  black: "#101d21",
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
    "--mantine-color-body": "#f2f8f8",
    "--mantine-color-default": "#ffffff",
    "--mantine-color-default-border": "rgba(16, 29, 33, 0.13)",
    "--mantine-color-default-hover": "#f7fbfa",
    "--mantine-color-dimmed": "#53696b",
  },
  dark: {},
});
