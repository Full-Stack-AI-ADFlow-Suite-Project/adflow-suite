import { fireEvent, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it, vi } from "vitest";

import type {
  PostVista,
  PrivacyDaDecidere,
  VediCampagna,
} from "../../../api/revisione";
import { server } from "../../../test/server";
import { disegna } from "../../../test/render";
import { Decidi } from "./Decidi";

const POST: PostVista = {
  post_id: 7,
  canale: "instagram",
  formato: "foto",
  riempitivo: null,
  data_ora: "2030-01-09T12:00:00Z",
  stato: "da_approvare",
  da_rivedere: false,
  controllato_da: null,
  controllato_il: null,
  intervento_in_corso: null,
  intervento_dal: null,
  versioni: [],
  interventi: [],
  versione_corrente: null,
};

function vista(privacy?: PrivacyDaDecidere): VediCampagna {
  return {
    campagna: {
      id: 3,
      profilo_id: 1,
      titolo: "Primavera",
      inizio: "2030-01-01",
      fine: "2030-01-31",
      descrizione: null,
      stato: "in_revisione",
      canali: ["instagram"],
      canali_tolti: null,
      frequenza: null,
      obiettivo: null,
      inviata_il: null,
      chiusa_il: null,
    },
    piano: null,
    uscite: [{ id: 1, numero: 1, tema: "Vasi", gruppo: null, post: [POST] }],
    foto_non_usate: [],
    ultimo_errore: null,
    costo_ai: 0,
    privacy_da_decidere: privacy,
  };
}

const CON_ZONE: PrivacyDaDecidere = {
  foto: 1,
  zone: 2,
  minori: 0,
  dettaglio: [{ foto_id: 41, post_ids: [7], zone: 2, minori: 0 }],
};

function apri(v: VediCampagna, ricarica = () => {}) {
  disegna(<Decidi vista={v} campagna={null} ricarica={ricarica} />);
  fireEvent.click(screen.getByRole("button", { name: /^Approva 1 post/ }));
}

function ascolta() {
  const corpi: unknown[] = [];
  server.use(
    http.post("*/api/campagne/3/approva", async ({ request }) => {
      corpi.push(await request.json());
      return HttpResponse.json({ stato: "attiva" });
    }),
  );
  return corpi;
}

describe("Decidi · Approva e privacy", () => {
  it("con zone da decidere mostra il riepilogo e non c'è la conferma semplice", () => {
    apri(vista(CON_ZONE));
    expect(
      screen.getByText(/1 foto con 2 zone da decidere/),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Rivedi" })).toHaveAttribute(
      "href",
      "#post-7",
    );
    expect(
      screen.queryByRole("button", { name: /^Conferma: approva/ }),
    ).not.toBeInTheDocument();
  });

  it("«Oscura tutte» manda oscura_tutte", async () => {
    const corpi = ascolta();
    const ricarica = vi.fn();
    apri(vista(CON_ZONE), ricarica);
    fireEvent.click(
      screen.getByRole("button", { name: /Oscura tutte e approva/ }),
    );
    await waitFor(() => expect(ricarica).toHaveBeenCalled());
    expect(corpi).toEqual([{ oscura_tutte: true }]);
  });

  it("la conferma esplicita manda conferma_privacy", async () => {
    const corpi = ascolta();
    const ricarica = vi.fn();
    apri(vista(CON_ZONE), ricarica);
    fireEvent.click(
      screen.getByRole("button", { name: /Lascia le zone come sono/ }),
    );
    await waitFor(() => expect(ricarica).toHaveBeenCalled());
    expect(corpi).toEqual([{ conferma_privacy: true }]);
  });

  it("senza zone il dialogo è quello di sempre", async () => {
    const corpi = ascolta();
    const ricarica = vi.fn();
    apri(vista({ foto: 0, zone: 0, minori: 0, dettaglio: [] }), ricarica);
    expect(screen.queryByText(/zone da decidere/)).not.toBeInTheDocument();
    fireEvent.click(
      screen.getByRole("button", { name: /^Conferma: approva 1/ }),
    );
    await waitFor(() => expect(ricarica).toHaveBeenCalled());
    expect(corpi).toEqual([{}]);
  });

  it("segnala i volti di minori", () => {
    apri(vista({ ...CON_ZONE, minori: 1 }));
    expect(screen.getByText(/sembra di un minore/)).toBeInTheDocument();
  });
});
