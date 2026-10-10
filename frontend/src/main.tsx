import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { MantineProvider } from "@mantine/core";

import "@mantine/core/styles.css";
import "./index.css";

import App from "./App.tsx";
import { AuthProvider } from "./auth.tsx";
import { tema, variabili } from "./tema.ts";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <MantineProvider
      theme={tema}
      cssVariablesResolver={variabili}
      forceColorScheme="light"
    >
      <BrowserRouter>
        <AuthProvider>
          <App />
        </AuthProvider>
      </BrowserRouter>
    </MantineProvider>
  </StrictMode>,
);
