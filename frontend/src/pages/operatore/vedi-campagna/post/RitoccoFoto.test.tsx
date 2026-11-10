import { fireEvent, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it, vi } from "vitest";

import type { FotoPost, PostVista } from "../../../../api/revisione";
import { server } from "../../../../test/server";
import { disegna } from "../../../../test/render";
import { RitoccoFoto } from "./RitoccoFoto";

function post(foto: Partial<FotoPost> = {}): PostVista {
  return {
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
    interventi: ["ritocca_foto"],
    versione_corrente: null,
    foto: {
      anteprima_url: "/api/post/7/foto/anteprima",
      varianti: {
        disponibili: ["originale", "standard", "spinta"],
        uguali: [],
        scelta: "standard",
      },
      zone_privacy: { numero: 0, decise: 0 },
      avvisi: [],
      ...foto,
    },
  };
}

function ascolta() {
  const corpi: unknown[] = [];
  server.use(
    http.post("*/api/post/7/ritocca-foto", async ({ request }) => {
      corpi.push(await request.json());
      return HttpResponse.json({
        stato: "ok",
        post_aggiornati: [7],
        post_non_aggiornati: [],
      });
    }),
  );
  return corpi;
}

describe("RitoccoFoto", () => {
  it("mostra le tre varianti con la scelta attuale", () => {
    disegna(<RitoccoFoto post={post()} ricarica={() => {}} />);
    const standard = screen.getByRole("radio", { name: "Standard" });
    expect(standard).toBeChecked();
    expect(screen.getByRole("radio", { name: "Originale" })).toBeEnabled();
    expect(screen.getByRole("radio", { name: "Spinta" })).toBeEnabled();
  });

  it("la Spinta non disponibile è spenta e lo dice", () => {
    disegna(
      <RitoccoFoto
        post={post({
          varianti: {
            disponibili: ["originale", "standard"],
            uguali: [],
            scelta: "standard",
          },
        })}
        ricarica={() => {}}
      />,
    );
    expect(screen.getByRole("radio", { name: "Spinta" })).toBeDisabled();
    expect(screen.getByText(/Spinta non è disponibile/)).toBeInTheDocument();
  });

  it("un clic manda la variante giusta e ricarica la vista", async () => {
    const corpi = ascolta();
    const ricarica = vi.fn();
    disegna(<RitoccoFoto post={post()} ricarica={ricarica} />);
    fireEvent.click(screen.getByRole("radio", { name: "Spinta" }));
    await waitFor(() => expect(ricarica).toHaveBeenCalled());
    expect(corpi).toEqual([{ variante: "spinta", privacy: null }]);
  });

  it("dice «Nessuna modifica necessaria» quando la scelta esce uguale all'originale", () => {
    disegna(
      <RitoccoFoto
        post={post({
          varianti: {
            disponibili: ["originale", "standard", "spinta"],
            uguali: ["standard"],
            scelta: "standard",
          },
        })}
        ricarica={() => {}}
      />,
    );
    expect(screen.getByText(/Nessuna modifica necessaria/)).toBeInTheDocument();
  });

  it("l'interruttore della privacy manda solo la privacy", async () => {
    const corpi = ascolta();
    const ricarica = vi.fn();
    disegna(
      <RitoccoFoto
        post={post({ zone_privacy: { numero: 2, decise: 0 } })}
        ricarica={ricarica}
      />,
    );
    fireEvent.click(screen.getByRole("switch", { name: "Oscura 2 zone" }));
    await waitFor(() => expect(ricarica).toHaveBeenCalled());
    expect(corpi).toEqual([{ variante: null, privacy: true }]);
  });

  it("senza zone non c'è l'interruttore", () => {
    disegna(<RitoccoFoto post={post()} ricarica={() => {}} />);
    expect(screen.queryByRole("switch")).not.toBeInTheDocument();
  });

  it("mostra gli avvisi sulla foto con le vie d'uscita", () => {
    disegna(
      <RitoccoFoto
        post={post({ avvisi: ["foto_mossa_forte"] })}
        ricarica={() => {}}
      />,
    );
    expect(screen.getByText(/molto mossa/)).toBeInTheDocument();
    expect(screen.getByText(/Cambia immagine/)).toBeInTheDocument();
  });

  it("un errore del server si legge nella card e non ricarica", async () => {
    server.use(
      http.post("*/api/post/7/ritocca-foto", () =>
        HttpResponse.json({ detail: "Non ammesso adesso." }, { status: 409 }),
      ),
    );
    const ricarica = vi.fn();
    disegna(<RitoccoFoto post={post()} ricarica={ricarica} />);
    fireEvent.click(screen.getByRole("radio", { name: "Originale" }));
    expect(await screen.findByText("Non ammesso adesso.")).toBeInTheDocument();
    expect(ricarica).not.toHaveBeenCalled();
  });
});
