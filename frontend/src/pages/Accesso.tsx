/**
 * Accesso: una sola pagina per artigiano, operatore e admin
 * (docs/appunti/pagine/AdFlow-login.html). Un solo messaggio di errore
 * per ogni credenziale sbagliata (CA-02); nessuna registrazione né
 * recupero password: sotto il modulo il contatto del consorzio.
 */
import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
  Alert,
  Button,
  Container,
  Paper,
  PasswordInput,
  Stack,
  Text,
  TextInput,
  Title,
} from "@mantine/core";

import { paginaIniziale, useAuth } from "../contesto-auth";
import { consorzio } from "../api/consorzio";
import type { Consorzio } from "../api/accesso";
import { ApiErrore } from "../api/http";

export function Accesso() {
  const { utente, sessioneScaduta, entra } = useAuth();
  const naviga = useNavigate();
  const posizione = useLocation();
  const [contatto, setContatto] = useState<Consorzio | null>(null);
  const [email, setEmail] = useState("");
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
    } catch (e) {
      setErrore(e instanceof ApiErrore ? e.dettaglio : "Errore inatteso.");
      setPassword("");
    } finally {
      setInCorso(false);
    }
  };

  return (
    <Container size={420} py="xl">
      <Paper withBorder radius="md" p="xl" maw={380} mx="auto" mt="10vh">
        <Stack gap="xs" align="center">
          <Title order={2}>AdFlow</Title>
          <Text size="xs" c="dimmed" ff="monospace" tt="uppercase" lts={1}>
            Consorzio artigiani
          </Text>
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
            <Button type="submit" color="verde" fullWidth loading={inCorso}>
              Entra
            </Button>
          </Stack>
        </form>
        {errore && (
          <Alert color="red" variant="light" mt="md">
            {errore}
          </Alert>
        )}
        {contatto && (
          <Text size="xs" c="dimmed" ta="center" mt="lg" lh={1.5}>
            Hai dimenticato la password? Contatta il consorzio: ti ridà
            l'accesso un operatore. Tel. {contatto.telefono} · {contatto.email}
          </Text>
        )}
      </Paper>
    </Container>
  );
}
