/**
 * Percorso del ritocco (RT-10, ADR-124): l'operatore entra, apre Vedi campagna e
 * la foto di ogni post è il render, non l'originale.
 *
 * I dati (una campagna con quattro foto sintetiche, una in Display P3, una
 * storta, una buia, una buona, generata con l'AI finta) li prepara
 * `prepara-dati-ritocco.sh` prima del test: il test della demo, che gira per
 * primo, vuole il database vuoto. Si attende sulle risposte di rete, mai su
 * tempi fissi.
 */
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";

import { expect, test } from "@playwright/test";

const PASSWORD = "E2eSonda!2026";
const OPERATORE = { email: "operatore@example.com", password: PASSWORD };

test.beforeAll(() => {
  execFileSync(
    "bash",
    [fileURLToPath(new URL("./prepara-dati-ritocco.sh", import.meta.url))],
    { stdio: "inherit", timeout: 120_000 },
  );
});

test("la foto del post è il render: JPEG con il lato corto a 1080", async ({
  page,
}) => {
  await page.goto("/accesso");
  await page.getByRole("textbox", { name: "Email" }).fill(OPERATORE.email);
  await page.getByRole("textbox", { name: "Password" }).fill(OPERATORE.password);
  await page.getByRole("button", { name: "Entra" }).click();
  await expect(page).toHaveURL(/\/da-approvare/);

  await expect(page.getByText("Campagna del ritocco")).toBeVisible();
  await page.getByRole("link", { name: /Vedi campagna/ }).first().click();
  await expect(page).toHaveURL(/\/campagne\/\d+/);

  // La prima card con una foto: l'immagine viene dalla rotta dell'anteprima.
  const anteprima = page.locator('img[src^="/api/post/"]').first();
  await expect(anteprima).toBeVisible();
  const src = await anteprima.getAttribute("src");
  expect(src).toMatch(/^\/api\/post\/\d+\/foto\/anteprima/);

  const risposta = await page.request.get(src!);
  expect(risposta.status()).toBe(200);
  expect(risposta.headers()["content-type"]).toBe("image/jpeg");

  const [larghezza, altezza] = await anteprima.evaluate((el) => {
    const img = el as HTMLImageElement;
    return [img.naturalWidth, img.naturalHeight];
  });
  expect(Math.min(larghezza, altezza)).toBe(1080);
});
