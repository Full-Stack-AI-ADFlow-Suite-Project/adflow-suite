/** Cornice delle pagine interne: marca, navigazione, utente collegato, Esci. */
import { AppShell, Button, Group, Text, Title, Tooltip } from "@mantine/core";
import { useNavigate } from "react-router-dom";
import type { ReactNode } from "react";

import { useAuth } from "../contesto-auth";

export interface VoceNav {
  label: string;
  attivo?: boolean;
  disabilitato?: boolean;
}

export function Guscio({
  titolo,
  nav = [],
  largo = 720,
  children,
}: {
  titolo: string;
  nav?: VoceNav[];
  largo?: number;
  children: ReactNode;
}) {
  const { utente, esci } = useAuth();
  const naviga = useNavigate();

  const esciEVai = async () => {
    await esci();
    naviga("/accesso", { replace: true });
  };

  return (
    <AppShell header={{ height: 56 }} padding="lg">
      <AppShell.Header>
        <Group h="100%" px="md" justify="space-between">
          <Group gap="lg">
            <Title order={3}>AdFlow</Title>
            {nav.map((voce) =>
              voce.disabilitato ? (
                <Tooltip key={voce.label} label="Arriva con lo sprint 2a">
                  <Text size="sm" c="dimmed" td="underline dotted">
                    {voce.label}
                  </Text>
                </Tooltip>
              ) : (
                <Text
                  key={voce.label}
                  size="sm"
                  fw={voce.attivo ? 600 : 400}
                  c={voce.attivo ? "verde" : undefined}
                >
                  {voce.label}
                </Text>
              ),
            )}
          </Group>
          <Group gap="sm">
            {utente && (
              <Text size="sm" c="dimmed">
                {utente.nome}
              </Text>
            )}
            <Button
              variant="subtle"
              color="verde"
              size="compact-sm"
              onClick={esciEVai}
            >
              Esci
            </Button>
          </Group>
        </Group>
      </AppShell.Header>
      <AppShell.Main maw={largo}>
        <Title order={1} mb="md">
          {titolo}
        </Title>
        {children}
      </AppShell.Main>
    </AppShell>
  );
}
