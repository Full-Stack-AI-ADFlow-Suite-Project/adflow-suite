/**
 * Accesso: una sola pagina per artigiano, operatore e admin
 * (docs/pagine/AdFlow-login.html). Un solo messaggio di errore
 * per ogni credenziale sbagliata (CA-02); nessuna registrazione né
 * recupero password: sotto il modulo il contatto del consorzio.
 */
import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
  Alert,
  Button,
  Checkbox,
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
import { LogoAdFlow } from "../components/LogoAdFlow";
import stile from "./Accesso.module.css";

const CHIAVE_RICORDAMI = "adflow_ricorda_email";

export function Accesso() {
  const { utente, sessioneScaduta, entra } = useAuth();
  const naviga = useNavigate();
  const posizione = useLocation();
  const [contatto, setContatto] = useState<Consorzio | null>(null);
  const [email, setEmail] = useState(
    () => localStorage.getItem(CHIAVE_RICORDAMI) ?? "",
  );
  const [password, setPassword] = useState("");
  const [ricordami, setRicordami] = useState(() =>
    Boolean(localStorage.getItem(CHIAVE_RICORDAMI)),
  );
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
      if (ricordami) localStorage.setItem(CHIAVE_RICORDAMI, email.trim());
      else localStorage.removeItem(CHIAVE_RICORDAMI);
      await entra(email, password);
    } catch (e) {
      setErrore(e instanceof ApiErrore ? e.dettaglio : "Errore inatteso.");
      setPassword("");
    } finally {
      setInCorso(false);
    }
  };

  return (
    <div className={stile.pagina}>
      <section className={stile.latoBrand} aria-label="Presentazione AdFlow">
        <div className={stile.marca}>
          <span className={stile.marcaIcona}>
            <LogoAdFlow size={24} />
          </span>
          <span className={stile.marcaTesto}>
            <b>AdFlow</b>
            <span>Suite · Consorzio artigiani</span>
          </span>
        </div>

        <div className={stile.hero}>
          <div className={stile.badgeBrand}>Piattaforma editoriale</div>
          <h1 className={stile.titoloHero}>
            La comunicazione social della tua bottega, curata insieme al
            consorzio.
          </h1>
          <p className={stile.sottotitoloHero}>
            Pianificazione dei contenuti, revisione consortile e pubblicazione
            programmata su Facebook e Instagram.
          </p>
          <div className={stile.pillole}>
            <span className={stile.pillola}>
              <svg
                viewBox="0 0 24 24"
                fill="none"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
              </svg>
              <span>Identità d'impresa</span>
            </span>
            <span className={stile.pillola}>
              <svg
                viewBox="0 0 24 24"
                fill="none"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <rect x="3" y="3" width="18" height="18" rx="3" />
                <circle cx="8.5" cy="8.5" r="1.5" />
                <path d="M21 15l-5-5L5 21" />
              </svg>
              <span>Redazione assistita</span>
            </span>
            <span className={stile.pillola}>
              <svg
                viewBox="0 0 24 24"
                fill="none"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <rect x="3" y="4" width="18" height="18" rx="2" />
                <line x1="16" y1="2" x2="16" y2="6" />
                <line x1="8" y1="2" x2="8" y2="6" />
                <line x1="3" y1="10" x2="21" y2="10" />
              </svg>
              <span>Pianificazione social</span>
            </span>
          </div>
        </div>
      </section>

      <main className={stile.latoForm}>
        <Paper className={stile.card}>
          <div className={stile.cardHeader}>
            <span className={stile.cardLogo}>
              <LogoAdFlow size={24} />
            </span>
            <div>
              <Title order={3} size="h4">
                AdFlow
              </Title>
              <Text size="xs" c="dimmed" fw={500}>
                Suite · Consorzio artigiani
              </Text>
            </div>
          </div>

          <Title order={2} size="h3">
            Accedi alla piattaforma
          </Title>
          <Text size="sm" c="dimmed" mt={4}>
            Inserisci le credenziali assegnate dal consorzio per continuare.
          </Text>

          {sessioneScaduta && (
            <Alert color="verde" variant="light" mt="md">
              La sessione è scaduta. Entra di nuovo per continuare.
            </Alert>
          )}
          <form onSubmit={invia}>
            <Stack mt="md" gap="sm">
              <TextInput
                label="Email"
                name="email"
                type="email"
                required
                autoComplete="username"
                placeholder="nome@bottega.it"
                value={email}
                onChange={(e) => setEmail(e.currentTarget.value)}
              />
              <PasswordInput
                label="Password"
                name="password"
                required
                autoComplete="current-password"
                placeholder="La tua password"
                value={password}
                onChange={(e) => setPassword(e.currentTarget.value)}
              />
              <Checkbox
                size="xs"
                color="verde"
                checked={ricordami}
                onChange={(e) => setRicordami(e.currentTarget.checked)}
                label="Ricordami su questo dispositivo"
              />
              <Button
                type="submit"
                color="verde"
                fullWidth
                mt={2}
                loading={inCorso}
              >
                Entra nella piattaforma →
              </Button>
            </Stack>
          </form>
          {errore && (
            <Alert color="red" variant="light" mt="md">
              {errore}
            </Alert>
          )}
          <Text size="xs" c="dimmed" ta="center" mt="md" lh={1.5}>
            Password dimenticata? Per il ripristino delle credenziali rivolgiti
            alla segreteria del consorzio.
            {contatto && (contatto.telefono || contatto.email)
              ? ` ${[
                  contatto.telefono ? `Tel. ${contatto.telefono}` : "",
                  contatto.email,
                ]
                  .filter(Boolean)
                  .join(" · ")}`
              : ""}
          </Text>
        </Paper>
      </main>
    </div>
  );
}
