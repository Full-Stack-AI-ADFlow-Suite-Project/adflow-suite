import { setupServer } from "msw/node";

/** Il finto server dei test: ogni test dichiara le sue risposte con `server.use(...)`. */
export const server = setupServer();
