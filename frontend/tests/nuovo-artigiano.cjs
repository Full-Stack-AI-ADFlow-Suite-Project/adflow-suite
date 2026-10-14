/** T3-54 / CA-79: browser locale, API intercettate, nessun servizio reale. */
const { chromium } = require(process.env.PLAYWRIGHT_PATH || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const api = process.env.ARTIGIANO_API_TEST_URL || 'http://127.0.0.1:5185';
const anteprima = process.env.ARTIGIANO_ESEMPI_TEST_URL || 'http://127.0.0.1:5184';
for (const base of [api, anteprima]) assert.ok(['127.0.0.1', 'localhost'].includes(new URL(base).hostname));
const passwordFinta = 'SOLO-PROVA-browser-una-volta';
let verifiche = 0;
const ok = nome => { verifiche++; console.log('OK ' + nome); };

async function prepara(browser, base = api, ruolo = 'operatore', viewport = {width: 1280, height: 900}) {
  const context = await browser.newContext({viewport});
  const page = await context.newPage();
  page.setDefaultTimeout(10000);
  const errori = [];
  page.on('pageerror', e => errori.push(e.message));
  const messaggi = [];
  page.on('console', m => messaggi.push(m.text()));
  const stato = { post: [], status: 201, detail: '', attendi: null, visto: null };
  let utente = ruolo === 'anonimo' ? null : {id: 2, nome: 'Operatore di prova', email: 'operatore@example.test', ruolo};
  await page.route('**/*', async route => {
    const url = new URL(route.request().url());
    if (url.origin !== new URL(base).origin) return route.abort();
    if (!url.pathname.startsWith('/api/')) return route.continue();
    const json = (body, status = 200) => route.fulfill({status, contentType: 'application/json', body: JSON.stringify(body)});
    if (url.pathname === '/api/auth/me') return utente ? json(utente) : json({detail: 'Sessione assente.'}, 401);
    if (url.pathname === '/api/consorzio') return json({nome: 'Consorzio di prova', telefono: '000', email: 'info@example.test'});
    if (url.pathname === '/api/auth/logout') { utente = null; return route.fulfill({status: 204}); }
    if (['/api/campagne', '/api/da-approvare', '/api/canali'].includes(url.pathname)) return json([]);
    if (url.pathname === '/api/profilo') return json({detail: 'Profilo assente.'}, 404);
    if (url.pathname === '/api/artigiani' && route.request().method() === 'POST') {
      const corpo = route.request().postDataJSON();
      stato.post.push(corpo);
      stato.visto?.();
      if (stato.attendi) await stato.attendi;
      if (stato.status !== 201) return json({detail: stato.detail}, stato.status);
      return json({id: 42, email: corpo.email.toLowerCase(), nome: corpo.nome, password_provvisoria: passwordFinta}, 201);
    }
    return json({detail: 'Richiesta non prevista dal test.'}, 404);
  });
  await page.goto(base + '/nuovo-artigiano', {waitUntil: 'domcontentloaded'});
  return {context, page, stato, errori, messaggi};
}

async function compila(page, email = 'nuova@example.test', nome = 'Giulia Rossi') {
  await page.getByLabel('Email di accesso', {exact: false}).fill(email);
  await page.getByLabel('Nome del referente', {exact: false}).fill(nome);
}

async function controllaSegreto(page, password, messaggi) {
  const salvati = await page.evaluate(() => JSON.stringify({locale: {...localStorage}, sessione: {...sessionStorage}, storia: history.state, url: location.href}));
  assert.equal(salvati.includes(password), false);
  assert.equal(messaggi.some(m => m.includes(password)), false);
}

(async () => {
  const browser = await chromium.launch({channel: process.env.ARTIGIANO_BROWSER || 'chrome', headless: true});
  try {
    {
      const {context, page, stato, errori, messaggi} = await prepara(browser, anteprima);
      await page.getByText('Gli account creati qui sono di prova', {exact: false}).waitFor();
      await compila(page);
      await page.getByRole('button', {name: 'Crea artigiano', exact: true}).click();
      const password = await page.getByLabel('Password provvisoria', {exact: true}).inputValue();
      assert.ok(password.length >= 20);
      assert.equal(stato.post.length, 0);
      await controllaSegreto(page, password, messaggi);
      await page.getByRole('button', {name: 'Ho annotato la password'}).click();
      assert.equal(await page.getByLabel('Password provvisoria', {exact: true}).count(), 0);
      await compila(page, 'NUOVA@example.test');
      await page.getByRole('button', {name: 'Crea artigiano', exact: true}).click();
      await page.getByRole('alert').filter({hasText: 'Email già registrata.'}).waitFor();
      assert.equal(stato.post.length, 0);
      assert.deepEqual(errori, []);
      ok('test_ca79_anteprima_senza_api_duplicato_password_effimera');
      await context.close();
    }
    {
      const {context, page, stato, errori, messaggi} = await prepara(browser);
      assert.equal(await page.getByText('Gli account creati qui sono di prova', {exact: false}).count(), 0);
      await compila(page, 'nuova@example.test', '  Giulia Rossi  ');
      let rilascia;
      stato.attendi = new Promise(resolve => { rilascia = resolve; });
      const ricevuto = new Promise(resolve => { stato.visto = resolve; });
      await page.locator('form').evaluate(form => { form.requestSubmit(); form.requestSubmit(); });
      await ricevuto;
      assert.equal(stato.post.length, 1);
      assert.deepEqual(stato.post[0], {email: 'nuova@example.test', nome: 'Giulia Rossi'});
      assert.equal(await page.getByRole('button', {name: 'Crea artigiano', exact: true}).isDisabled(), true);
      rilascia();
      await page.getByRole('heading', {name: 'Artigiano creato', exact: true}).waitFor();
      assert.equal(await page.getByLabel('Password provvisoria', {exact: true}).inputValue(), passwordFinta);
      await controllaSegreto(page, passwordFinta, messaggi);
      await context.grantPermissions(['clipboard-read', 'clipboard-write']);
      await page.getByRole('button', {name: 'Copia password', exact: true}).click();
      await page.getByText('Password copiata.', {exact: true}).waitFor();
      assert.equal(await page.evaluate(() => navigator.clipboard.readText()), passwordFinta);
      // La clipboard si usa solo su richiesta esplicita; il test la ripulisce.
      await page.evaluate(() => navigator.clipboard.writeText(''));
      if (process.env.SCREENSHOT_DIR) {
        await fs.mkdir(process.env.SCREENSHOT_DIR, {recursive: true});
        await page.screenshot({path: path.join(process.env.SCREENSHOT_DIR, 't354-credenziali-finte-desktop.png'), fullPage: true});
      }
      await page.getByRole('link', {name: 'Da approvare', exact: true}).click();
      await page.getByRole('heading', {name: 'Campagne da approvare', exact: true}).waitFor();
      await page.goBack();
      await page.getByRole('button', {name: 'Crea artigiano', exact: true}).waitFor();
      assert.equal(await page.getByLabel('Password provvisoria', {exact: true}).count(), 0);
      await compila(page);
      stato.attendi = null;
      await page.getByRole('button', {name: 'Crea artigiano', exact: true}).click();
      await page.getByRole('heading', {name: 'Artigiano creato', exact: true}).waitFor();
      await page.reload();
      await page.getByRole('button', {name: 'Crea artigiano', exact: true}).waitFor();
      assert.equal(await page.getByLabel('Password provvisoria', {exact: true}).count(), 0);
      await controllaSegreto(page, passwordFinta, messaggi);
      assert.deepEqual(errori, []);
      ok('test_ca79_api_payload_doppio_invio_copia_navigazione_reload');
      await context.close();
    }
    {
      const {context, page, stato} = await prepara(browser);
      await page.getByRole('button', {name: 'Crea artigiano', exact: true}).click();
      assert.equal(stato.post.length, 0);
      await compila(page, 'valida@example.test', '   ');
      await page.getByRole('button', {name: 'Crea artigiano', exact: true}).click();
      await page.getByRole('alert').filter({hasText: 'Inserisci il nome del referente.'}).waitFor();
      assert.equal(stato.post.length, 0);
      await compila(page, 'email-non-valida', 'Giulia');
      await page.getByRole('button', {name: 'Crea artigiano', exact: true}).click();
      assert.equal(stato.post.length, 0);
      ok('test_ca79_obbligatori_nome_vuoto_email_errata');
      await context.close();
    }
    for (const [status, detail] of [[409, 'Email già registrata.'], [422, 'Email non valida.'], [403, 'Operazione non permessa.'], [500, 'Servizio temporaneamente non disponibile.']]) {
      const {context, page, stato, errori} = await prepara(browser);
      stato.status = status; stato.detail = detail;
      await compila(page);
      await page.getByRole('button', {name: 'Crea artigiano', exact: true}).click();
      await page.getByRole('alert').filter({hasText: detail}).waitFor();
      assert.equal(await page.getByLabel('Email di accesso', {exact: false}).inputValue(), 'nuova@example.test');
      assert.equal(await page.getByLabel('Password provvisoria', {exact: true}).count(), 0);
      assert.equal(stato.post.length, 1);
      assert.deepEqual(errori, []);
      ok('test_ca79_errore_' + status);
      await context.close();
    }
    {
      const {context, page, stato} = await prepara(browser);
      stato.status = 401; stato.detail = 'Sessione scaduta.';
      await compila(page);
      await page.getByRole('button', {name: 'Crea artigiano', exact: true}).click();
      await page.waitForURL('**/accesso');
      await page.getByText('La sessione è scaduta.', {exact: false}).waitFor();
      assert.equal(await page.getByLabel('Password provvisoria', {exact: true}).count(), 0);
      ok('test_ca79_sessione_scaduta_torna_all_accesso');
      await context.close();
    }
    for (const ruolo of ['admin', 'artigiano', 'anonimo']) {
      const {context, page, stato, errori} = await prepara(browser, api, ruolo);
      if (ruolo === 'admin') await page.getByRole('button', {name: 'Crea artigiano', exact: true}).waitFor();
      else {
        await page.waitForURL(ruolo === 'anonimo' ? '**/accesso' : '**/profilo');
        assert.equal(await page.getByRole('heading', {name: 'Nuovo artigiano', exact: true}).count(), 0);
        assert.equal(stato.post.length, 0);
      }
      assert.deepEqual(errori, []);
      ok('test_ca79_ruolo_' + ruolo);
      await context.close();
    }
    {
      const {context, page, stato, errori} = await prepara(browser);
      let rilascia;
      stato.attendi = new Promise(resolve => { rilascia = resolve; });
      const ricevuto = new Promise(resolve => { stato.visto = resolve; });
      await compila(page);
      await page.getByRole('button', {name: 'Crea artigiano', exact: true}).click();
      await ricevuto;
      await page.getByRole('link', {name: 'Da approvare', exact: true}).click();
      rilascia();
      await page.getByRole('link', {name: 'Nuovo artigiano', exact: true}).click();
      await page.getByRole('button', {name: 'Crea artigiano', exact: true}).waitFor();
      assert.equal(await page.getByLabel('Password provvisoria', {exact: true}).count(), 0);
      assert.deepEqual(errori, []);
      ok('test_ca79_risposta_dopo_uscita_non_ripristina_password');
      await context.close();
    }
    {
      const {context, page, errori} = await prepara(browser, api, 'admin', {width: 390, height: 844});
      await page.getByRole('button', {name: 'Crea artigiano', exact: true}).waitFor();
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), true);
      if (process.env.SCREENSHOT_DIR) await page.screenshot({path: path.join(process.env.SCREENSHOT_DIR, 't354-modulo-mobile.png'), fullPage: true});
      await compila(page, 'mobile@example.test');
      await page.getByRole('button', {name: 'Crea artigiano', exact: true}).click();
      await page.getByRole('heading', {name: 'Artigiano creato', exact: true}).waitFor();
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), true);
      assert.deepEqual(errori, []);
      ok('test_ca79_modulo_e_risultato_mobile');
      await context.close();
    }
    console.log(`${verifiche} scenari browser passati; tutte le API intercettate.`);
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
