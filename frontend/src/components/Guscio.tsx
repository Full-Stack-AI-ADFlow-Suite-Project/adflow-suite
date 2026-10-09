/** Cornice delle pagine interne: marca, utente collegato, Esci. */
import { AppShell, Button, Group, Text, Title } from "@mantine/core";
import { useNavigate } from "react-router-dom";
import type { ReactNode } from "react";

import { useAuth } from "../contesto-auth";

export function Guscio({
  titolo,
  children,
}: {
  titolo: string;
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
          <Title order={3}>AdFlow</Title>
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
      <AppShell.Main>
        <Title order={1} mb="md">
          {titolo}
        </Title>
        {children}
      </AppShell.Main>
    </AppShell>
  );
}
