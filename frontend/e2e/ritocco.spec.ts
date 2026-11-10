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
  await page
    .getByRole("textbox", { name: "Password" })
    .fill(OPERATORE.password);
  await page.getByRole("button", { name: "Entra" }).click();
  await expect(page).toHaveURL(/\/da-approvare/);

  await expect(page.getByText("Campagna del ritocco")).toBeVisible();
  await page
    .getByRole("link", { name: /Vedi campagna/ })
    .first()
    .click();
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

/**
 * Il percorso completo (RT-33): Standard, Spinta, Originale, Oscura (se la foto ha zone
 * da proteggere), Approva con la conferma, pubblicazione con il social finto. Si attende
 * sulle risposte di rete della rotta `ritocca-foto`, mai su tempi fissi. I byte inviati
 * al social finto vivono nel suo processo: che siano quelli del render approvato lo prova
 * il test del backend (RT-07).
 */
test("scelta della variante, Approva con la conferma e pubblicazione", async ({
  page,
}) => {
  await page.goto("/accesso");
  await page.getByRole("textbox", { name: "Email" }).fill(OPERATORE.email);
  await page
    .getByRole("textbox", { name: "Password" })
    .fill(OPERATORE.password);
  await page.getByRole("button", { name: "Entra" }).click();
  await expect(page).toHaveURL(/\/da-approvare/);
  await page
    .getByRole("link", { name: /Vedi campagna/ })
    .first()
    .click();
  await expect(page).toHaveURL(/\/campagne\/\d+/);

  const gruppo = page
    .getByRole("group", { name: "Ritocco della foto" })
    .first();
  await expect(gruppo).toBeVisible();

  const scegli = async (nome: "Originale" | "Standard" | "Spinta") => {
    const risposta = page.waitForResponse(
      (r) =>
        r.url().includes("/ritocca-foto") && r.request().method() === "POST",
    );
    await gruppo.getByText(nome, { exact: true }).click();
    expect((await risposta).status()).toBe(200);
    await expect(gruppo.getByRole("radio", { name: nome })).toBeChecked();
  };
  await scegli("Spinta");
  await scegli("Originale");
  await scegli("Standard");

  // Le zone da proteggere, se la foto ne ha: l'interruttore manda solo la privacy.
  const interruttore = gruppo.getByRole("switch", { name: /^Oscura \d+ zon/ });
  if ((await interruttore.count()) > 0) {
    const risposta = page.waitForResponse((r) =>
      r.url().includes("/ritocca-foto"),
    );
    await interruttore.click();
    expect((await risposta).status()).toBe(200);
    await expect(interruttore).toBeChecked();
  }

  // Approva: il dialogo chiede la conferma; con zone da decidere ne offre due.
  await page.getByRole("button", { name: /^Approva \d+ post/ }).click();
  const approva = page.waitForResponse(
    (r) => r.url().includes("/approva") && r.request().method() === "POST",
  );
  const oscuraTutte = page.getByRole("button", {
    name: /Oscura tutte e approva/,
  });
  if ((await oscuraTutte.count()) > 0) await oscuraTutte.click();
  else await page.getByRole("button", { name: /^Conferma: approva/ }).click();
  expect((await approva).status()).toBe(200);
  await expect(page.getByText("Campagna attiva")).toBeVisible();

  // I post escono con il social finto.
  execFileSync(
    "bash",
    [fileURLToPath(new URL("./pubblica-ora.sh", import.meta.url))],
    { stdio: "inherit", timeout: 120_000 },
  );
  await page.reload();
  await expect(page.getByText(/\d+ pubblicati/)).toBeVisible();
});
