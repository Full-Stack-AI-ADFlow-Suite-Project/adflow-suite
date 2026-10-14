import { useEffect, useRef, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import {
  Alert,
  Button,
  Card,
  Group,
  Stack,
  Text,
  TextInput,
  Title,
} from "@mantine/core";

import {
  creaArtigiano,
  CREAZIONE_USA_ESEMPI,
  type ArtigianoCreato,
} from "../../api/artigiani";
import { ApiErrore } from "../../api/http";
import { Guscio } from "../../components/Guscio";

export function NuovoArtigiano() {
  const [email, setEmail] = useState("");
  const [nome, setNome] = useState("");
  const [errore, setErrore] = useState("");
  const [inCorso, setInCorso] = useState(false);
  const [creato, setCreato] = useState<ArtigianoCreato | null>(null);
  const [copia, setCopia] = useState("");
  const attesa = useRef(false);
  const montato = useRef(true);

  useEffect(() => {
    montato.current = true;
    const dimentica = () => setCreato(null);
    window.addEventListener("pagehide", dimentica);
    return () => {
      montato.current = false;
      window.removeEventListener("pagehide", dimentica);
    };
  }, []);

  async function invia(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    if (attesa.current) return;
    if (!nome.trim()) {
      setErrore("Inserisci il nome del referente.");
      return;
    }
    attesa.current = true;
    setInCorso(true);
    setErrore("");
    try {
      const risultato = await creaArtigiano({ email, nome });
      if (montato.current) {
        setCreato(risultato);
        setEmail("");
        setNome("");
      }
    } catch (e) {
      if (montato.current)
        setErrore(
          e instanceof ApiErrore
            ? e.dettaglio
            : "Non è stato possibile confermare la creazione. Verifica l'esito prima di riprovare.",
        );
    } finally {
      attesa.current = false;
      if (montato.current) setInCorso(false);
    }
  }

  async function copiaPassword() {
    if (!creato) return;
    try {
      await navigator.clipboard.writeText(creato.password_provvisoria);
      if (montato.current) setCopia("Password copiata.");
    } catch {
      if (montato.current)
        setCopia("Copia manualmente la password dal campo qui sopra.");
    }
  }

  return (
    <Guscio titolo="Nuovo artigiano" largo={680}>
      <Stack gap="lg">
        <Text c="dimmed">
          Crea l'accesso dell'artigiano. Il profilo della bottega lo compilerà
          al primo accesso.
        </Text>
        {CREAZIONE_USA_ESEMPI && (
          <Alert color="yellow" title="Anteprima">
            Gli account creati qui sono di prova e non permettono l'accesso alla
            piattaforma.
          </Alert>
        )}
        {creato ? (
          <Card withBorder padding="lg">
            <Stack gap="md">
              <div role="status">
                <Title order={2} size="h3">
                  Artigiano creato
                </Title>
                <Text mt="xs">
                  Annota le credenziali e comunicale all'artigiano. La password
                  è visibile soltanto qui: quando chiudi o lasci la pagina non
                  potrai rivederla.
                </Text>
              </div>
              <Text fw={600}>{creato.nome}</Text>
              <TextInput
                label="Email dell'artigiano"
                value={creato.email}
                readOnly
                autoComplete="off"
              />
              <TextInput
                label="Password provvisoria"
                value={creato.password_provvisoria}
                readOnly
                autoComplete="off"
                styles={{
                  input: { fontFamily: "var(--mantine-font-family-monospace)" },
                }}
              />
              <Group>
                <Button variant="light" onClick={copiaPassword}>
                  Copia password
                </Button>
                <Text size="sm" role="status">
                  {copia}
                </Text>
              </Group>
              <Button
                onClick={() => {
                  setCreato(null);
                  setCopia("");
                }}
              >
                Ho annotato la password
              </Button>
            </Stack>
          </Card>
        ) : (
          <Card withBorder padding="lg">
            <form onSubmit={invia}>
              <Stack gap="md">
                <TextInput
                  label="Email di accesso"
                  type="email"
                  required
                  maxLength={320}
                  autoComplete="off"
                  placeholder="nome@bottega.it"
                  value={email}
                  disabled={inCorso}
                  onChange={(e) => setEmail(e.currentTarget.value)}
                />
                <TextInput
                  label="Nome del referente"
                  required
                  autoComplete="off"
                  placeholder="Nome e cognome"
                  value={nome}
                  disabled={inCorso}
                  onChange={(e) => setNome(e.currentTarget.value)}
                />
                {errore && (
                  <Alert color="red" role="alert">
                    {errore}
                  </Alert>
                )}
                <Group justify="space-between">
                  <Button
                    variant="default"
                    component={Link}
                    to="/da-approvare"
                    disabled={inCorso}
                  >
                    Torna alle campagne
                  </Button>
                  <Button type="submit" loading={inCorso}>
                    Crea artigiano
                  </Button>
                </Group>
              </Stack>
            </form>
          </Card>
        )}
      </Stack>
    </Guscio>
  );
}
