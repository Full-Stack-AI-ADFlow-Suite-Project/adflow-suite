/**
 * "Qualcosa non va? Chiama il consorzio" (spec §4, R-29): in campagna attiva o
 * sospesa l'artigiano legge i post ma non ha pulsanti per chiedere modifiche.
 */
import { Text } from "@mantine/core";
import { useEffect, useState } from "react";

import type { Consorzio } from "../../../../api/accesso";
import { consorzio } from "../../../../api/consorzio";

export function ContattoConsorzio() {
  const [contatto, setContatto] = useState<Consorzio | null>(null);

  useEffect(() => {
    consorzio()
      .then(setContatto)
      .catch(() => setContatto(null));
  }, []);

  return (
    <Text size="sm" mt="md">
      Qualcosa non va? Chiama il consorzio
      {contatto ? `: ${contatto.telefono} · ${contatto.email}` : "."}
    </Text>
  );
}
