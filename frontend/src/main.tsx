import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { MantineProvider } from "@mantine/core";

import "@mantine/core/styles.css";
import "./index.css";

import App from "./App.tsx";
import { AuthProvider } from "./auth.tsx";
import { tema } from "./tema.ts";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <MantineProvider theme={tema} defaultColorScheme="auto">
      <BrowserRouter>
        <AuthProvider>
          <App />
        </AuthProvider>
      </BrowserRouter>
    </MantineProvider>
  </StrictMode>,
);
