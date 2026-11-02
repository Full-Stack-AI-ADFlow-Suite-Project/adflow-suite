/**
 * Percorso della demo di `docs/agenti/converge.md` §4, a due ruoli, da database
 * vuoto (T4-106). Copre i passi che si possono fare senza caricare file:
 * accesso dell'operatore e dell'artigiano, le loro pagine d'arrivo, gli elenchi
 * vuoti del database appena creato, la navigazione principale.
 *
 * Accessibilità: ogni pagina visitata passa da `@axe-core/playwright` con le
 * regole WCAG 2.2 AA; le violazioni sono allegate al report e quelle gravi o
 * critiche sono un rilievo (T4-106-frontend.md). Il test non fallisce per una
 * violazione: la registra, così il percorso resta ripetibile e il difetto
 * resta nel registro.
 */
import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

const PASSWORD = "E2eSonda!2026";
const OPERATORE = { email: "operatore@example.com", password: PASSWORD };
const ARTIGIANO = { email: "artigiano@example.com", password: PASSWORD };

const REGOLE = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"];

async function accedi(page: Page, credenziali: { email: string; password: string }) {
  await page.goto("/accesso");
  await page.getByRole("textbox", { name: "Email" }).fill(credenziali.email);
  await page.getByRole("textbox", { name: "Password" }).fill(credenziali.password);
  await page.getByRole("button", { name: "Entra" }).click();
}

async function controllaAccessibilita(page: Page, nome: string) {
  const risultato = await new AxeBuilder({ page }).withTags(REGOLE).analyze();
  const gravi = risultato.violations.filter(
    (v) => v.impact === "serious" || v.impact === "critical",
  );
  await test.info().attach(`axe-${nome}.json`, {
    body: JSON.stringify(
      {
        pagina: nome,
        url: page.url(),
        violazioni: risultato.violations.map((v) => ({
          id: v.id,
          impatto: v.impact,
          descrizione: v.help,
          nodi: v.nodes.length,
        })),
      },
      null,
      2,
    ),
    contentType: "application/json",
  });
  return gravi.length;
}

test("percorso della demo: operatore e artigiano dal database vuoto", async ({ page }) => {
  const violazioniGravi: string[] = [];

  // 1. Operatore: entra e arriva su Campagne da approvare, vuoto.
  await accedi(page, OPERATORE);
  await expect(page).toHaveURL(/\/da-approvare/);
  await expect(
    page.getByRole("heading", { name: "Campagne da approvare", level: 1 }),
  ).toBeVisible();
  await expect(page.getByText(/Nessuna campagna da approvare/i)).toBeVisible();
  if (await controllaAccessibilita(page, "operatore-da-approvare")) {
    violazioniGravi.push("operatore-da-approvare");
  }

  // 2. Operatore: elenco artigiani (il seed ne ha uno) e nuovo artigiano.
  await page.goto("/artigiani");
  await expect(page.getByRole("heading", { name: /Artigiani/i, level: 1 })).toBeVisible();
  await expect(page.getByText(/Bottega di prova|artigiano/i).first()).toBeVisible();
  if (await controllaAccessibilita(page, "operatore-artigiani")) {
    violazioniGravi.push("operatore-artigiani");
  }

  // 3. Operatore: storico AI, vuoto.
  await page.goto("/storico-ai");
  await expect(page.getByRole("heading", { name: /Storico AI/i, level: 1 })).toBeVisible();
  if (await controllaAccessibilita(page, "operatore-storico-ai")) {
    violazioniGravi.push("operatore-storico-ai");
  }

  // 4. Esci e 5. Artigiano: entra e arriva sull'Ingresso.
  await page.getByRole("button", { name: /Esci/ }).click();
  await expect(page).toHaveURL(/\/accesso/);
  await accedi(page, ARTIGIANO);
  await expect(page).toHaveURL(/\/ingresso/);
  await expect(page.getByRole("heading", { name: /Buongiorno/i, level: 1 })).toBeVisible();
  await expect(page.getByText(/Qui trovi che cosa ti chiede il consorzio/i)).toBeVisible();
  if (await controllaAccessibilita(page, "artigiano-ingresso")) {
    violazioniGravi.push("artigiano-ingresso");
  }

  // 6. Artigiano: campagne (vuote), calendario, archivio foto.
  await page.goto("/campagne");
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  if (await controllaAccessibilita(page, "artigiano-campagne")) {
    violazioniGravi.push("artigiano-campagne");
  }

  await page.goto("/calendario");
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  if (await controllaAccessibilita(page, "artigiano-calendario")) {
    violazioniGravi.push("artigiano-calendario");
  }

  await page.goto("/archivio");
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  if (await controllaAccessibilita(page, "artigiano-archivio")) {
    violazioniGravi.push("artigiano-archivio");
  }

  // 7. Una pagina dell'operatore non è per l'artigiano: viene riportato indietro.
  await page.goto("/da-approvare");
  await expect(page).not.toHaveURL(/\/da-approvare/);

  // Il passo 7 di converge §4 (controllo visivo) e le violazioni gravi di axe
  // finiscono nel report T4-106-frontend.md; qui resta la traccia.
  await test.info().attach("violazioni-gravi.txt", {
    body: violazioniGravi.join("\n") || "nessuna",
    contentType: "text/plain",
  });
});
