import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterAll, afterEach, beforeAll } from "vitest";

import { server } from "./server";

// Mantine usa queste API del browser, che jsdom non ha.
window.matchMedia ??= ((query: string) => ({
  matches: false,
  media: query,
  onchange: null,
  addEventListener: () => {},
  removeEventListener: () => {},
  addListener: () => {},
  removeListener: () => {},
  dispatchEvent: () => false,
})) as typeof window.matchMedia;

class ResizeObserverFinto {
  observe() {}
  unobserve() {}
  disconnect() {}
}
globalThis.ResizeObserver ??= ResizeObserverFinto;
Element.prototype.scrollIntoView ??= () => {};

// Il codice chiama `fetch("/api/...")`: nel browser il percorso è relativo alla
// pagina, in Node no. Lo si risolve sull'origine di jsdom, così MSW lo intercetta.
const fetchNativo = globalThis.fetch.bind(globalThis);
globalThis.fetch = ((input: RequestInfo | URL, init?: RequestInit) =>
  fetchNativo(
    typeof input === "string" && input.startsWith("/")
      ? new URL(input, window.location.origin)
      : input,
    init,
  )) as typeof fetch;

// Una richiesta che nessun test ha previsto è un errore, non una chiamata vera.
beforeAll(() => server.listen({ onUnhandledFrame: "error" }));
afterEach(() => {
  cleanup();
  server.resetHandlers();
});
afterAll(() => server.close());
