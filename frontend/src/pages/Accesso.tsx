import layout from "../components/Layout.module.css";
import stili from "./Accesso.module.css";
/**
 * Accesso: una sola pagina per artigiano, operatore e admin
 * (docs/pagine/AdFlow-login.html). Un solo messaggio di errore
 * per ogni credenziale sbagliata (CA-02); nessuna registrazione né
 * recupero password: sotto il modulo il contatto del consorzio.
 */
import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  Alert,
  Button,
  Checkbox,
  Container,
  Paper,
  PasswordInput,
  Stack,
  Text,
  TextInput,
} from "@mantine/core";

import { paginaIniziale, useAuth } from "../contesto-auth";
import { Wordmark } from "../components/Wordmark";
import { consorzio } from "../api/consorzio";
import type { Consorzio } from "../api/accesso";
import { ApiErrore } from "../api/http";

export function Accesso() {
  const { utente, sessioneScaduta, entra } = useAuth();
  const naviga = useNavigate();
  const posizione = useLocation();
  const [contatto, setContatto] = useState<Consorzio | null>(null);
  const [email, setEmail] = useState(
    () => localStorage.getItem("adflow.email") ?? "",
  );
  const [ricordami, setRicordami] = useState(
    () => localStorage.getItem("adflow.email") !== null,
  );
  const [password, setPassword] = useState("");
  const [errore, setErrore] = useState("");
  const [inCorso, setInCorso] = useState(false);

  useEffect(() => {
    consorzio()
      .then(setContatto)
      .catch(() => setContatto(null));
  }, []);

  useEffect(() => {
    if (!utente) return;
    const da = (posizione.state as { from?: { pathname?: string } } | null)
      ?.from;
    const meta =
      da?.pathname && da.pathname !== "/accesso" ? da.pathname : null;
    naviga(meta ?? paginaIniziale(utente.ruolo), { replace: true });
  }, [utente, naviga, posizione.state]);

  const invia = async (evento: React.FormEvent) => {
    evento.preventDefault();
    setErrore("");
    setInCorso(true);
    try {
      await entra(email, password);
      if (ricordami) {
        localStorage.setItem("adflow.email", email);
      } else {
        localStorage.removeItem("adflow.email");
      }
    } catch (e) {
      setErrore(
        e instanceof ApiErrore
          ? e.dettaglio
          : "Impossibile completare l’operazione. Riprova.",
      );
      setPassword("");
    } finally {
      setInCorso(false);
    }
  };

  return (
    <div className={`${layout.accesso} ${stili.pagina}`}>
      <Button
        className={stili.tornaHome}
        component={Link}
        to="/"
        variant="white"
        color="dark"
        radius="xl"
        size="compact-md"
        leftSection={<span aria-hidden>←</span>}
      >
        Torna alla home
      </Button>
      <Container className={stili.contenuto} size={400} px={0}>
        <Paper
          className={stili.card}
          radius="lg"
          shadow="xl"
          p={{ base: "lg", sm: "xl" }}
        >
          <Stack gap={10} align="center">
            <Wordmark dimensione={34} />
            <Text className={stili.sottotitolo}>Consorzio artigiani</Text>
          </Stack>
          {sessioneScaduta && (
            <Alert color="verde" variant="light" mt="md">
              La sessione è scaduta. Entra di nuovo per continuare.
            </Alert>
          )}
          <form onSubmit={invia}>
            <Stack mt="lg" gap="sm">
              <TextInput
                label="Email"
                type="email"
                required
                autoComplete="username"
                placeholder="nome@bottega.it"
                value={email}
                onChange={(e) => setEmail(e.currentTarget.value)}
              />
              <PasswordInput
                label="Password"
                required
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.currentTarget.value)}
              />
              <Checkbox
                label="Ricordami su questo dispositivo"
                color="verde"
                checked={ricordami}
                onChange={(e) => setRicordami(e.currentTarget.checked)}
              />
              <Button
                type="submit"
                color="verde"
                fullWidth
                loading={inCorso}
                mt="xs"
              >
                Entra
              </Button>
            </Stack>
          </form>
          {errore && (
            <Alert color="red" variant="light" mt="md">
              {errore}
            </Alert>
          )}
          <Text
            size="xs"
            c="dimmed"
            ta="center"
            lh={1.5}
            className={stili.piede}
          >
            {contatto &&
              `Hai dimenticato la password? Contatta il consorzio: ti ridà
            l'accesso un operatore. Tel. ${contatto.telefono} · ${contatto.email}`}
          </Text>
        </Paper>
        <Text className={stili.didascalia}>
          La vetrina delle botteghe del consorzio ·{" "}
          <Link to="/privacy" className={stili.linkChiaro}>
            Privacy
          </Link>
        </Text>
      </Container>
    </div>
  );
}
