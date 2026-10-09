import { createTheme } from "@mantine/core";

// Palette e caratteri delle pagine statiche approvate (docs/appunti/pagine).
const verde: [
  string,
  string,
  string,
  string,
  string,
  string,
  string,
  string,
  string,
  string,
] = [
  "#eaf4ef",
  "#dceae3",
  "#c0dccf",
  "#9cc9b6",
  "#74b39b",
  "#529c82",
  "#3a8069",
  "#2e6b5c",
  "#245546",
  "#1d4a3f",
];

export const tema = createTheme({
  colors: { verde },
  primaryColor: "verde",
  primaryShade: 7,
  fontFamily: '"IBM Plex Sans", system-ui, sans-serif',
  fontFamilyMonospace: '"IBM Plex Mono", ui-monospace, monospace',
  headings: {
    fontFamily: '"Fraunces", Georgia, serif',
    fontWeight: "600",
  },
  defaultRadius: "md",
});
