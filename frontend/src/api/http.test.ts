import { http, HttpResponse } from "msw";
import { describe, expect, it, vi } from "vitest";

import { server } from "../test/server";
import { ApiErrore, impostaGestore401, richiesta } from "./http";

describe("richiesta", () => {
  it("legge il JSON della risposta", async () => {
    server.use(
      http.get("*/api/post/7", () => HttpResponse.json({ post_id: 7 })),
    );
    expect(await richiesta<{ post_id: number }>("GET", "/post/7")).toEqual({
      post_id: 7,
    });
  });

  it("manda il corpo come JSON", async () => {
    let ricevuto: unknown = null;
    server.use(
      http.post("*/api/post/7/prova", async ({ request }) => {
        ricevuto = await request.json();
        return HttpResponse.json({ stato: "ok" });
      }),
    );
    await richiesta("POST", "/post/7/prova", { a: 1 });
    expect(ricevuto).toEqual({ a: 1 });
  });

  it("un errore diventa ApiErrore con la frase del server", async () => {
    server.use(
      http.get("*/api/post/9", () =>
        HttpResponse.json({ detail: "Post non trovato." }, { status: 404 }),
      ),
    );
    await expect(richiesta("GET", "/post/9")).rejects.toMatchObject({
      stato: 404,
      dettaglio: "Post non trovato.",
    });
    await expect(richiesta("GET", "/post/9")).rejects.toBeInstanceOf(ApiErrore);
  });

  it("un 401 chiama il gestore della sessione scaduta", async () => {
    const gestore = vi.fn();
    impostaGestore401(gestore);
    server.use(
      http.get("*/api/me", () =>
        HttpResponse.json({ detail: "Sessione scaduta." }, { status: 401 }),
      ),
    );
    await expect(richiesta("GET", "/me")).rejects.toBeInstanceOf(ApiErrore);
    expect(gestore).toHaveBeenCalledOnce();
  });
});
