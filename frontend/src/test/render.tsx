import { MantineProvider } from "@mantine/core";
import { render } from "@testing-library/react";
import type { ReactElement } from "react";
import { MemoryRouter } from "react-router-dom";

import type { UtentePubblico } from "../api/accesso";
import { ContestoAuth, type Auth } from "../contesto-auth";
import { tema, variabili } from "../tema";

export const OPERATORE: UtentePubblico = {
  id: 1,
  email: "operatore@esempio.it",
  nome: "Operatore di prova",
  ruolo: "operatore",
};

/** Disegna un componente con il tema di Mantine, un router in memoria e una sessione finta. */
export function disegna(
  elemento: ReactElement,
  { percorso = "/", utente = OPERATORE }: { percorso?: string; utente?: UtentePubblico } = {},
) {
  const auth: Auth = {
    utente,
    sessioneScaduta: false,
    entra: async () => utente,
    esci: async () => {},
  };
  return render(
    <MantineProvider
      theme={tema}
      cssVariablesResolver={variabili}
      forceColorScheme="light"
    >
      <ContestoAuth.Provider value={auth}>
        <MemoryRouter initialEntries={[percorso]}>{elemento}</MemoryRouter>
      </ContestoAuth.Provider>
    </MantineProvider>,
  );
}
