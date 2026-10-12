/** Regressione del logo nel passo 7. Playwright può essere fornito dall'ambiente. */
const { chromium } = require(process.env.PLAYWRIGHT_PATH || 'playwright');
const assert = require('node:assert/strict');
const base = process.env.PROFILO_TEST_URL || 'http://127.0.0.1:5182';
const rosso = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAASwAAAEsCAIAAAD2HxkiAAADVUlEQVR4nO3VMREAMAwDsST8ObcwfpEIePrzvgFKl64DIoSaJ4SYCCEmQoiJEGIihJgIISZCiIkQYiKEmAghJkKIiRBiIoSYCCEmQoiJEGIihJgIISZCiIkQYiKEmAghJkKIiRBiIoSYCCEmQoiJEGIihJgIISZCiIkQYiKEmAghJkKIiRBiIoSYCCEmQoiJEGIihJgIISZCiIkQYiKEmAghJkKIiRBiIoSYCCEmQoiJEGIihJgIISZCiIkQYiKEmAghJkKIiRBiIoSYCCEmQoiJEGIihJgIISZCiIkQYiKEmAghJkKIiRBiIoSYCCEmQoiJEGIihJgIISZCiIkQYiKEmAghJkKIiRBiIoSYCCEmQoiJEGIihJgIISZCiIkQYiKEmAghJkKIiRBiIoSYCCEmQoiJEGIihJgIISZCiIkQYiKEmAghJkKIiRBiIoSYCCEmQoiJEGIihJgIISZCiIkQYiKEmAghJkKIiRBiIoSYCCEmQoiJEGIihJgIISZCiIkQYiKEmAghJkKIiRBiIoSYCCEmQoiJEGIihJgIISZCiIkQYiKEmAghJkKIiRBiIoSYCCEmQoiJEGIihJgIISZCiIkQYiKEmAghJkKIiRBiIoSYCCEmQoiJEGIihJgIISZCiIkQYiKEmAghJkKIiRBiIoSYCCEmQoiJEGIihJgIISZCiIkQYiKEmAghJkKIiRBiIoSYCCEmQoiJEGIihJgIISZCiIkQYiKEmAghJkKIiRBiIoSYCCEmQoiJEGIihJgIISZCiIkQYiKEmAghJkKIiRBiIoSYCCEmQoiJEGIihJgIISZCiIkQYiKEmAghJkKIiRBiIoSYCCEmQoiJEGIihJgIISZCiIkQYiKEmAghJkKIiRBiIoSYCCEmQoiJEGIihJgIISZCiIkQYiKEmAghJkKIiRBiIoSYCCEmQoiJEGIihJgIISZCiIkQYiKEmAghJkKIiRBiIoSYCCEmQoiJEGIihJgIISZCiIkQYiKEmAghJkKIiRBiIoSYCCEmQoiJEGIihJgIISZCiIkQYiKEmAghJkKIiRBiIoSYCCEmQoiJEGIihJgIISZCiIkQYiKEmAghJkKIiRBiIoSYCCEmQoiJEGIihJgIISZCiIkQYiKEaX23LANX50PPIAAAAABJRU5ErkJggg==', 'base64');
const blu = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAASwAAAEsCAIAAAD2HxkiAAADVklEQVR4nO3VMREAIAADsYJ/zyDjl8RAp7+e7Q3o3HAbECH0PCHERAgxEUJMhBATIcRECDERQkyEEBMhxEQIMRFCTIQQEyHERAgxEUJMhBATIcRECDERQkyEEBMhxEQIMRFCTIQQEyHERAgxEUJMhBATIcRECDERQkyEEBMhxEQIMRFCTIQQEyHERAgxEUJMhBATIcRECDERQkyEEBMhxEQIMRFCTIQQEyHERAgxEUJMhBATIcRECDERQkyEEBMhxEQIMRFCTIQQEyHERAgxEUJMhBATIcRECDERQkyEEBMhxEQIMRFCTIQQEyHERAgxEUJMhBATIcRECDERQkyEEBMhxEQIMRFCTIQQEyHERAgxEUJMhBATIcRECDERQkyEEBMhxEQIMRFCTIQQEyHERAgxEUJMhBATIcRECDERQkyEEBMhxEQIMRFCTIQQEyHERAgxEUJMhBATIcRECDERQkyEEBMhxEQIMRFCTIQQEyHERAgxEUJMhBATIcRECDERQkyEEBMhxEQIMRFCTIQQEyHERAgxEUJMhBATIcRECDERQkyEEBMhxEQIMRFCTIQQEyHERAgxEUJMhBATIcRECDERQkyEEBMhxEQIMRFCTIQQEyHERAgxEUJMhBATIcRECDERQkyEEBMhxEQIMRFCTIQQEyHERAgxEUJMhBATIcRECDERQkyEEBMhxEQIMRFCTIQQEyHERAgxEUJMhBATIcRECDERQkyEEBMhxEQIMRFCTIQQEyHERAgxEUJMhBATIcRECDERQkyEEBMhxEQIMRFCTIQQEyHERAgxEUJMhBATIcRECDERQkyEEBMhxEQIMRFCTIQQEyHERAgxEUJMhBATIcRECDERQkyEEBMhxEQIMRFCTIQQEyHERAgxEUJMhBATIcRECDERQkyEEBMhxEQIMRFCTIQQEyHERAgxEUJMhBATIcRECDERQkyEEBMhxEQIMRFCTIQQEyHERAgxEUJMhBATIcRECDERQkyEEBMhxEQIMRFCTIQQEyHERAgxEUJMhBATIcRECDERQkyEEBMhxEQIMRFCTIQQEyHERAgxEUJMhBATIcRECDERQkyEEBMhxEQIMRFCTIQQEyHERAgxEUJMhBATIcRECDERQkyEEBMhrPUBtS4DV36ocdEAAAAASUVORK5CYII=', 'base64');
const iniziale = {
  id: 1, nome: 'Bottega di prova', referente: 'Mario', citta: 'Bra',
  tipo_prodotto: 'legno_mobili', clienti_ideali: 'Famiglie', obiettivo: 'notorieta',
  canali: ['facebook'], anni_attivita: null, sito: null, storia: null, origine: null,
  valori: null, gamma: null, fascia_prezzo: null, stagionalita: null, zona: null,
  tono: null, cortesia: null, vincoli: null, frequenza: 'f3_4', orari: null,
  social_esistenti: null, foto_policy: null, eventi_ricorrenti: null, chiusure: null,
  logo: 'logo-rosso.png', aggiornato_il: '2026-10-12T00:00:00Z',
};
async function colore(img) {
  await img.evaluate((e) => e.decode());
  return img.evaluate((e) => {
    const canvas = document.createElement('canvas'); canvas.width = canvas.height = 1;
    const ctx = canvas.getContext('2d'); ctx.drawImage(e, 0, 0, 1, 1);
    return [...ctx.getImageData(0, 0, 1, 1).data];
  });
}
(async () => {
  const browser = await chromium.launch({ channel: process.env.PROFILO_BROWSER || 'chrome', headless: true });
  try {
    const context = await browser.newContext();
    const page = await context.newPage();
    const errori = [];
    page.on('pageerror', (e) => errori.push(e.message));
    let profilo = { ...iniziale };
    let bytes = rosso;
    let rifiuta = false;
    let letture = 0;
    let salvataggiProfilo = 0;
    const versioni = [];
    // Funziona prima e dopo il ponte API di T2a-07: nessun dato reale o archivio condiviso.
    await context.addInitScript((p) => localStorage.setItem('adflow_profilo_esempio_anteprima', JSON.stringify(p)), iniziale);
    await page.route('**/*', async (route) => {
      const u = new URL(route.request().url());
      if (u.origin !== new URL(base).origin) return route.abort();
      if (!u.pathname.startsWith('/api/')) return route.continue();
      const metodo = route.request().method();
      const json = (body, status = 200) => route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body) });
      if (u.pathname === '/api/auth/me') return json({ id: 1, nome: 'Mario', email: 'prova@example.test', ruolo: 'artigiano' });
      if (u.pathname === '/api/consorzio') return json({ nome: 'Consorzio', telefono: '000', email: 'info@example.test' });
      if (u.pathname === '/api/profilo') { if (metodo === 'PUT') salvataggiProfilo++; return json(profilo); }
      if (u.pathname === '/api/archivio') return json([]);
      if (u.pathname === '/api/profilo/logo' && metodo === 'GET') {
        letture++; versioni.push(u.searchParams.get('v'));
        return route.fulfill({ status: 200, contentType: 'image/png', headers: { 'Cache-Control': 'no-store' }, body: bytes });
      }
      if (u.pathname === '/api/profilo/logo' && metodo === 'PUT') {
        if (rifiuta) return json({ detail: 'Il logo deve essere una immagine valida.' }, 422);
        profilo = { ...profilo, logo: 'logo-blu.png' }; bytes = blu;
        return json(profilo);
      }
      if (u.pathname === '/api/profilo/logo' && metodo === 'DELETE') { profilo = { ...profilo, logo: null }; return route.fulfill({ status: 204 }); }
      return json({ detail: 'Richiesta non prevista dal test.' }, 404);
    });
    await page.goto(base + '/profilo', { waitUntil: 'domcontentloaded' });
    for (let n = 2; n <= 7; n++) {
      await page.getByRole('button', { name: 'Continua', exact: true }).click();
      await page.getByText(`Passo ${n} di 9`, { exact: true }).waitFor();
    }
    const img = page.getByRole('img', { name: 'Logo bottega', exact: true });
    assert.deepEqual(await colore(img), [255, 0, 0, 255]);
    assert.equal(letture, 1);
    const risposta = page.waitForResponse((r) => new URL(r.url()).pathname === '/api/profilo/logo' && r.request().method() === 'PUT');
    const secondaImmagine = page.waitForResponse((r) => new URL(r.url()).pathname === '/api/profilo/logo' && r.request().method() === 'GET');
    await page.locator('input[type=file]').first().setInputFiles({ name: 'logo.png', mimeType: 'image/png', buffer: blu });
    assert.equal((await risposta).status(), 200); await secondaImmagine;
    assert.deepEqual(await colore(img), [0, 0, 255, 255]);
    assert.deepEqual(versioni, ['logo-rosso.png', 'logo-blu.png']);
    assert.equal(letture, 2);
    console.log('OK test_ca77_sostituzione_aggiorna_anteprima_senza_ricaricare_pagina');

    rifiuta = true;
    const rifiuto = page.waitForResponse((r) => new URL(r.url()).pathname === '/api/profilo/logo' && r.request().method() === 'PUT');
    await page.locator('input[type=file]').first().setInputFiles({ name: 'logo.pdf', mimeType: 'application/pdf', buffer: Buffer.from('%PDF-1.7') });
    assert.equal((await rifiuto).status(), 422);
    await page.getByText('Il logo deve essere una immagine valida.', { exact: true }).waitFor();
    assert.deepEqual(await colore(img), [0, 0, 255, 255]); assert.equal(letture, 2);
    console.log('OK test_ca78_caricamento_rifiutato_conserva_anteprima_corrente');

    const cancellazione = page.waitForResponse((r) => new URL(r.url()).pathname === '/api/profilo/logo' && r.request().method() === 'DELETE');
    await page.getByRole('button', { name: 'Rimuovi logo', exact: true }).click();
    assert.equal((await cancellazione).status(), 204);
    await img.waitFor({ state: 'detached' });
    await page.getByRole('button', { name: 'Carica logo', exact: true }).waitFor();
    assert.equal(letture, 2); assert.equal(salvataggiProfilo, 0); assert.deepEqual(errori, []);
    console.log('OK test_ca77_rimozione_toglie_anteprima_senza_salvare_profilo');
    await context.close();
  } finally { await browser.close(); }
})().catch((e) => { console.error(e); process.exitCode = 1; });
