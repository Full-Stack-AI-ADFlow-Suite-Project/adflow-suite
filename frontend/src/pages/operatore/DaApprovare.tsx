/** Campagne da approvare: partenza di operatore e admin; il contenuto è di T1-53. */
import { Text } from "@mantine/core";

import { Guscio } from "../../components/Guscio";

export function DaApprovare() {
  return (
    <Guscio titolo="Campagne da approvare">
      <Text c="dimmed">
        L'elenco delle campagne da approvare arriva con T1-53.
      </Text>
    </Guscio>
  );
}
