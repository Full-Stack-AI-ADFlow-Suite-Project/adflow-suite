import { defineConfig, devices } from "@playwright/test";

/**
 * Configurazione Playwright della simulazione di accettazione (T4-106).
 *
 * Due server: il backend su :8000 con il database dedicato `adflow_e2e`
 * (creato, migrato e riempito dal seed dallo script `e2e/prepara-backend.sh`)
 * e il frontend Vite su :5173 con il proxy `/api` già configurato.
 * Video e traccia si salvano in `test-results/` (che non entra in git).
 */
export default defineConfig({
  testDir: "./e2e",
  timeout: 120_000,
  expect: { timeout: 15_000 },
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [["list"], ["html", { outputFolder: "playwright-report", open: "never" }]],
  use: {
    baseURL: "http://127.0.0.1:5173",
    trace: process.env.PLAYWRIGHT_TRACE === "on" ? "on" : "on-first-retry",
    video: process.env.PLAYWRIGHT_VIDEO === "on" ? "on" : "retain-on-failure",
    screenshot: "only-on-failure",
    locale: "it-IT",
    timezoneId: "Europe/Rome",
  },
  projects: [
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        // Sull'Ubuntu di questa macchina `playwright install` non supporta la
        // versione del sistema: si usa il Chromium già in cache, se c'è.
        launchOptions: process.env.PLAYWRIGHT_CHROMIUM
          ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM }
          : {},
      },
    },
  ],
  webServer: [
    {
      command: "bash e2e/prepara-backend.sh",
      url: "http://127.0.0.1:8000/api/health",
      reuseExistingServer: false,
      timeout: 180_000,
    },
    {
      command: "npm run dev -- --port 5173 --strictPort",
      url: "http://127.0.0.1:5173",
      reuseExistingServer: true,
      timeout: 120_000,
    },
  ],
});
