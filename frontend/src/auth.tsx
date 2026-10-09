/**
 * Provider della sessione e guard delle rotte. Un 401 riporta all'accesso
 * con l'avviso di sessione scaduta; dopo l'accesso si riapre la pagina
 * di partenza (state.from di react-router). Chi apre una pagina di un
 * altro ruolo torna alla propria pagina di partenza (spec R-29).
 */
import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { Navigate, useLocation } from "react-router-dom";
import { Center, Loader } from "@mantine/core";

import {
  login as apiLogin,
  logout as apiLogout,
  me,
  type Ruolo,
  type UtentePubblico,
} from "./api/accesso";
import { impostaGestore401 } from "./api/http";
import { ContestoAuth, paginaIniziale, useAuth } from "./contesto-auth";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [utente, setUtente] = useState<UtentePubblico | null | undefined>(
    undefined,
  );
  const [sessioneScaduta, setSessioneScaduta] = useState(false);

  useEffect(() => {
    me()
      .then(setUtente)
      .catch(() => setUtente(null));
    impostaGestore401(() => {
      setUtente(null);
      setSessioneScaduta(true);
    });
  }, []);

  const entra = useCallback(async (email: string, password: string) => {
    const u = await apiLogin({ email, password });
    setSessioneScaduta(false);
    setUtente(u);
    return u;
  }, []);

  const esci = useCallback(async () => {
    await apiLogout().catch(() => undefined);
    setUtente(null);
  }, []);

  const valore = useMemo(
    () => ({ utente, sessioneScaduta, entra, esci }),
    [utente, sessioneScaduta, entra, esci],
  );

  return (
    <ContestoAuth.Provider value={valore}>{children}</ContestoAuth.Provider>
  );
}

export function RichiedeRuolo({
  ruoli,
  children,
}: {
  ruoli: Ruolo[];
  children: ReactNode;
}) {
  const { utente } = useAuth();
  const posizione = useLocation();

  if (utente === undefined) {
    return (
      <Center mih="100vh">
        <Loader color="verde" />
      </Center>
    );
  }
  if (utente === null) {
    return <Navigate to="/accesso" state={{ from: posizione }} replace />;
  }
  if (!ruoli.includes(utente.ruolo)) {
    return <Navigate to={paginaIniziale(utente.ruolo)} replace />;
  }
  return children;
}
