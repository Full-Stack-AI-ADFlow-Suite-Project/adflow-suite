// Prove browser di T2a-51. Usa Playwright già disponibile nell'ambiente,
// senza aggiungerlo alle dipendenze del progetto.
const { chromium } = require(process.env.PLAYWRIGHT_PATH || 'playwright');
const assert = require('node:assert/strict');
const base = process.env.PROFILO_TEST_URL || 'http://127.0.0.1:5181';
const sessione = 'adflow_utente_esempio';
const chiave = (id) => `adflow_profilo_esempio_${id}`;
const risultati = [];
let browser;
async function prova(nome, funzione) {
  const context = await browser.newContext({ viewport: { width: 1100, height: 900 } });
  const page = await context.newPage();
  await page.route('**/*', (route) => new URL(route.request().url()).origin === new URL(base).origin ? route.continue() : route.abort());
  const errori = [];
  page.on('pageerror', (e) => errori.push(e.message));
  try { await funzione(page, context); assert.deepEqual(errori, []); risultati.push(nome); console.log(`OK ${nome}`); }
  finally { await context.close(); }
}
async function utente(page, id = 42, ruolo = 'artigiano') {
  await page.goto(base + '/accesso', { waitUntil: 'domcontentloaded' });
  await page.evaluate(({ key, id, ruolo }) => localStorage.setItem(key, JSON.stringify({ id, nome: 'Artigiano di prova', email: 'prova@example.test', ruolo })), { key: sessione, id, ruolo });
}
async function passo(page, n) {
  await page.getByRole('button', { name: 'Continua', exact: true }).click();
  await page.getByText(`Passo ${n} di 9`, { exact: true }).waitFor();
}
async function riepilogo(page) { for (let n = 2; n <= 9; n++) await passo(page, n); }
async function seleziona(page, label, scelta) {
  await page.getByRole('combobox', { name: label, exact: true }).click();
  await page.getByRole('option', { name: scelta, exact: true }).click();
}
async function compila(page) {
  await page.getByLabel('Nome della bottega', { exact: false }).fill('La bottega nuova');
  await page.getByLabel('Referente', { exact: false }).fill('Giulia');
  await page.getByLabel('Città', { exact: false }).fill('Torino');
  await passo(page, 2);
  await page.getByLabel('Racconta la tua storia', { exact: true }).fill('Una storia da conservare');
  await passo(page, 3);
  await seleziona(page, 'Tipo di prodotto', 'Ceramica e vetro');
  await passo(page, 4);
  await page.getByLabel('Clienti ideali', { exact: false }).fill('Famiglie della zona');
  await seleziona(page, 'Obiettivo', 'Farmi conoscere');
  await passo(page, 5); await passo(page, 6);
  await page.getByRole('checkbox', { name: 'Facebook', exact: true }).first().check();
  await passo(page, 7); await passo(page, 8); await passo(page, 9);
}
(async () => {
  browser = await chromium.launch({ headless: true, channel: process.env.PROFILO_BROWSER || 'chrome' });
  try {
    await prova('test_ca05_senza_sessione_va_all_accesso', async (p) => {
      await p.goto(base + '/profilo', { waitUntil: 'domcontentloaded' }); await p.waitForURL('**/accesso');
    });
    await prova('test_ca05_nuovo_artigiano_arriva_al_passo_1', async (p) => {
      const richieste = [];
      p.on('request', (r) => { if (new URL(r.url()).pathname.startsWith('/api/')) richieste.push(r.url()); });
      await utente(p); await p.goto(base + '/campagna', { waitUntil: 'domcontentloaded' }); await p.waitForURL('**/profilo');
      await p.getByRole('heading', { name: 'La bottega', exact: true }).waitFor();
      assert.equal(await p.getByLabel('Nome della bottega', { exact: false }).inputValue(), '');
      assert.deepEqual(richieste, []);
    });
    await prova('test_ca07_obbligatori_mancanti_non_salva_e_li_indica', async (p) => {
      await utente(p); await p.goto(base + '/profilo', { waitUntil: 'domcontentloaded' }); await riepilogo(p);
      await p.getByRole('button', { name: 'Salva e vai alla campagna' }).click();
      for (const nome of ['Nome della bottega', 'Referente', 'Città', 'Tipo di prodotto', 'Clienti ideali', 'Obiettivo', 'Canali preferiti'])
        await p.getByRole('button', { name: new RegExp(`^${nome}:`) }).waitFor();
      assert.equal(await p.evaluate((k) => localStorage.getItem(k), chiave(42)), null);
      await p.getByRole('button', { name: /^Nome della bottega:/ }).click();
      await p.getByText('Passo 1 di 9', { exact: true }).waitFor();
      assert.match(await p.getByLabel('Nome della bottega', { exact: false }).getAttribute('aria-describedby'), /error/);
    });
    await prova('test_ca05_salva_solo_al_passo_9_e_rientra_con_profilo', async (p) => {
      await utente(p); await p.goto(base + '/profilo', { waitUntil: 'domcontentloaded' }); await compila(p);
      assert.equal(await p.evaluate((k) => localStorage.getItem(k), chiave(42)), null);
      await p.getByRole('button', { name: 'Salva e vai alla campagna' }).click();
      await p.waitForURL('**/campagna');
      const salvato = await p.evaluate((k) => JSON.parse(localStorage.getItem(k)), chiave(42));
      assert.equal(salvato.nome, 'La bottega nuova'); assert.equal(salvato.tipo_prodotto, 'ceramica_vetro');
      assert.equal(salvato.storia, 'Una storia da conservare'); assert.deepEqual(salvato.canali, ['facebook']);
      assert.equal(salvato.obiettivo, 'notorieta'); assert.equal(salvato.logo, null);
      await p.reload({ waitUntil: 'domcontentloaded' }); assert.match(p.url(), /\/campagna$/);
      await p.goto(base + '/profilo', { waitUntil: 'domcontentloaded' });
      assert.equal(await p.getByLabel('Nome della bottega', { exact: false }).inputValue(), salvato.nome);
      assert.equal(await p.evaluate((k) => JSON.parse(localStorage.getItem(k)).aggiornato_il, chiave(42)), salvato.aggiornato_il);
    });
    await prova('test_ca07_navigazione_indietro_conserva_ma_non_salva', async (p) => {
      await utente(p); await p.goto(base + '/profilo', { waitUntil: 'domcontentloaded' });
      await p.getByLabel('Nome della bottega', { exact: false }).fill('Non ancora salvata');
      await passo(p, 2); await p.getByRole('button', { name: 'Indietro', exact: true }).click();
      assert.equal(await p.getByLabel('Nome della bottega', { exact: false }).inputValue(), 'Non ancora salvata');
      await p.reload({ waitUntil: 'domcontentloaded' }); assert.equal(await p.getByLabel('Nome della bottega', { exact: false }).inputValue(), '');
    });
    await prova('test_ca07_evento_incompleto_blocca_e_rimozione_sblocca', async (p) => {
      await utente(p, 1); await p.goto(base + '/profilo', { waitUntil: 'domcontentloaded' });
      for (let n = 2; n <= 8; n++) await passo(p, n);
      await p.getByRole('button', { name: 'Aggiungi evento' }).click(); await passo(p, 9);
      await p.getByRole('button', { name: 'Salva e vai alla campagna' }).click();
      await p.getByRole('button', { name: /^Eventi ricorrenti:/ }).click();
      await p.getByRole('button', { name: 'Rimuovi evento 1' }).click(); await passo(p, 9);
      await p.getByRole('button', { name: 'Salva e vai alla campagna' }).click(); await p.waitForURL('**/campagna');
    });
    await prova('test_ca07_errore_salvataggio_mantiene_dati_e_permette_riprova', async (p) => {
      await utente(p, 1); await p.goto(base + '/profilo', { waitUntil: 'domcontentloaded' }); await riepilogo(p);
      await p.evaluate(() => { const originale = Storage.prototype.setItem; window.rifiutaSalvataggio = true; Storage.prototype.setItem = function(k, v) { if (window.rifiutaSalvataggio && k.startsWith('adflow_profilo_esempio_')) throw new DOMException('Quota', 'QuotaExceededError'); originale.call(this, k, v); }; });
      await p.getByRole('button', { name: 'Salva e vai alla campagna' }).click();
      await p.getByText('Il profilo non è stato salvato. Libera spazio nel browser e riprova.', { exact: true }).waitFor();
      assert.match(p.url(), /\/profilo$/);
      await p.evaluate(() => { window.rifiutaSalvataggio = false; });
      await p.getByRole('button', { name: 'Salva e vai alla campagna' }).click(); await p.waitForURL('**/campagna');
    });
    await prova('test_ca05_profili_separati_per_utente', async (p) => {
      await utente(p, 42); await p.goto(base + '/profilo', { waitUntil: 'domcontentloaded' }); await compila(p);
      await p.getByRole('button', { name: 'Salva e vai alla campagna' }).click(); await p.waitForURL('**/campagna');
      await utente(p, 43); await p.goto(base + '/campagna', { waitUntil: 'domcontentloaded' }); await p.waitForURL('**/profilo');
      assert.equal(await p.getByLabel('Nome della bottega', { exact: false }).inputValue(), '');
    });
    await prova('test_ca05_operatore_e_admin_non_aprono_profilo', async (p) => {
      for (const ruolo of ['operatore', 'admin']) {
        await utente(p, 2, ruolo); await p.goto(base + '/profilo', { waitUntil: 'domcontentloaded' }); await p.waitForURL('**/da-approvare');
      }
    });
    await prova('test_ca07_modifica_conserva_logo_e_non_tocca_snapshot', async (p) => {
      await utente(p, 1); await p.goto(base + '/profilo', { waitUntil: 'domcontentloaded' }); await riepilogo(p);
      await p.getByRole('button', { name: 'Salva e vai alla campagna' }).click(); await p.waitForURL('**/campagna');
      const campagne = await p.evaluate(() => localStorage.getItem('adflow_esempi_campagne'));
      await p.evaluate((k) => { const v = JSON.parse(localStorage.getItem(k)); v.logo = 'logo-precedente.png'; v.orari = { apertura: '9–18' }; localStorage.setItem(k, JSON.stringify(v)); }, chiave(1));
      await p.goto(base + '/profilo', { waitUntil: 'domcontentloaded' }); await p.getByLabel('Nome della bottega', { exact: false }).fill('Nuovo nome'); await riepilogo(p);
      await p.getByRole('button', { name: 'Salva e vai alla campagna' }).click(); await p.waitForURL('**/campagna');
      const v = await p.evaluate((k) => JSON.parse(localStorage.getItem(k)), chiave(1));
      assert.equal(v.nome, 'Nuovo nome'); assert.equal(v.logo, 'logo-precedente.png'); assert.deepEqual(v.orari, { apertura: '9–18' });
      assert.equal(await p.evaluate(() => localStorage.getItem('adflow_esempi_campagne')), campagne);
    });
    await prova('test_ca05_errore_lettura_con_riprova', async (p) => {
      await utente(p, 42); await p.evaluate((k) => localStorage.setItem(k, '{}'), chiave(42));
      await p.goto(base + '/campagna', { waitUntil: 'domcontentloaded' }); await p.getByText('Non riesco a leggere il profilo. Riprova.', { exact: true }).waitFor();
      await p.evaluate((k) => localStorage.removeItem(k), chiave(42)); await p.getByRole('button', { name: 'Riprova', exact: true }).click();
      await p.waitForURL('**/profilo'); await p.getByText('Passo 1 di 9', { exact: true }).waitFor();
    });
    await prova('test_ca07_riepilogo_mobile_senza_trabocco', async (p) => {
      await p.setViewportSize({ width: 390, height: 844 });
      await utente(p, 1); await p.goto(base + '/profilo', { waitUntil: 'domcontentloaded' }); await riepilogo(p);
      assert.equal(await p.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), true);
      if (process.env.PROFILO_SCREENSHOT) await p.screenshot({ path: process.env.PROFILO_SCREENSHOT, fullPage: true });
    });
    console.log(`${risultati.length} prove browser superate.`);
  } finally { await browser.close(); }
})().catch((e) => { console.error(e); process.exitCode = 1; });
