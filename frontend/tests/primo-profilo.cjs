/** Regressioni del passo 7 prima e dopo il primo salvataggio del profilo. */
const { chromium } = require(process.env.PLAYWRIGHT_PATH || 'playwright');
const assert = require('node:assert/strict');
const base = process.env.PROFILO_TEST_URL || 'http://127.0.0.1:5182';
const iniziale = { id:1,nome:'Bottega',referente:'Mario',citta:'Bra',tipo_prodotto:'legno_mobili',clienti_ideali:'Famiglie',obiettivo:'notorieta',canali:['facebook'],anni_attivita:null,sito:null,storia:null,origine:null,valori:null,gamma:null,fascia_prezzo:null,stagionalita:null,zona:null,tono:null,cortesia:null,vincoli:null,frequenza:'f3_4',orari:null,social_esistenti:null,foto_policy:null,eventi_ricorrenti:null,chiusure:null,logo:null,aggiornato_il:'2026-10-12T00:00:00Z' };
async function avanti(page,n) { await page.getByRole('button',{name:'Continua',exact:true}).click(); await page.getByText(`Passo ${n} di 9`,{exact:true}).waitFor(); }
async function setup(browser,nuovo) {
  const context=await browser.newContext();
  const page=await context.newPage();
  const errori=[];page.on('pageerror',(e)=>errori.push(e.message));
  const stato={profilo:nuovo?null:iniziale,errore:false,archivio:0,salvataggi:0};
  await context.addInitScript((p)=>{if(localStorage.getItem('adflow_profilo_esempio_anteprima')===null)localStorage.setItem('adflow_profilo_esempio_anteprima',JSON.stringify(p));},stato.profilo);
  await page.route('**/*',async (route)=>{
    const u=new URL(route.request().url());
    if(u.origin!==new URL(base).origin)return route.abort();
    if(!u.pathname.startsWith('/api/'))return route.continue();
    const json=(body,status=200)=>route.fulfill({status,contentType:'application/json',body:JSON.stringify(body)});
    if(u.pathname==='/api/auth/me')return json({id:1,nome:'Mario',email:'prova@example.test',ruolo:'artigiano'});
    if(u.pathname==='/api/consorzio')return json({nome:'Consorzio',telefono:'000',email:'info@example.test'});
    if(u.pathname==='/api/profilo'){
      if(route.request().method()==='PUT'){stato.salvataggi++;stato.profilo={...iniziale,...route.request().postDataJSON()};return json(stato.profilo);}
      if(stato.errore)return json({detail:'Errore temporaneo.'},500);
      return stato.profilo?json(stato.profilo):json({detail:'Profilo bottega non trovato.'},404);
    }
    if(u.pathname==='/api/archivio'){stato.archivio++;return json([]);}
    if(u.pathname==='/api/campagne')return json([]);
    if(u.pathname==='/api/canali')return json([{canale:'facebook',collegato:true},{canale:'instagram',collegato:false}]);
    return json({detail:'Richiesta non prevista.'},404);
  });
  return {context,page,stato,errori};
}
(async()=>{
  const browser=await chromium.launch({channel:process.env.PROFILO_BROWSER||'chrome',headless:true});
  try {
    {
      const {context,page,stato,errori}=await setup(browser,true);
      await page.goto(base+'/profilo',{waitUntil:'domcontentloaded'});
      await page.getByLabel('Nome della bottega',{exact:false}).fill('Bottega nuova');
      await page.getByLabel('Referente',{exact:false}).fill('Giulia');
      await page.getByLabel('Città',{exact:false}).fill('Torino');
      await avanti(page,2);await avanti(page,3);
      await page.getByRole('combobox',{name:'Tipo di prodotto',exact:true}).click();await page.getByRole('option',{name:'Legno e mobili',exact:true}).click();
      await avanti(page,4);
      await page.getByLabel('Clienti ideali',{exact:false}).fill('Famiglie');
      await page.getByRole('combobox',{name:'Obiettivo',exact:true}).click();await page.getByRole('option',{name:'Farmi conoscere',exact:true}).click();
      await avanti(page,5);await avanti(page,6);
      await page.getByRole('checkbox',{name:'Facebook',exact:true}).first().check();await avanti(page,7);
      await page.getByText('Prima salva il profilo',{exact:true}).waitFor();
      assert.equal(await page.getByRole('button',{name:'Carica logo',exact:true}).count(),0);
      assert.equal(stato.archivio,0);assert.equal(stato.salvataggi,0);
      await avanti(page,8);await avanti(page,9);
      await page.getByRole('button',{name:'Salva e vai alla campagna',exact:true}).click();await page.waitForURL('**/campagna');
      const archivioCaricato=page.waitForResponse((r)=>new URL(r.url()).pathname==='/api/archivio');
      await page.goto(base+'/profilo',{waitUntil:'domcontentloaded'});
      for(let n=2;n<=7;n++)await avanti(page,n);
      await page.getByRole('button',{name:'Carica logo',exact:true}).waitFor();
      await archivioCaricato;
      assert.equal(await page.getByText('Prima salva il profilo',{exact:true}).count(),0);
      assert.ok(stato.archivio>=1);assert.deepEqual(errori,[]);
      console.log('OK test_ca05_passo7_attende_primo_salvataggio_e_attiva_upload_al_rientro');
      await context.close();
    }
    {
      const {context,page,stato,errori}=await setup(browser,false);
      await page.goto(base+'/profilo',{waitUntil:'domcontentloaded'});
      for(let n=2;n<=6;n++)await avanti(page,n);
      stato.errore=true;
      await page.evaluate(()=>localStorage.setItem('adflow_profilo_esempio_anteprima','{}'));
      await avanti(page,7);
      await page.getByText('Logo e archivio non disponibili',{exact:true}).waitFor();
      assert.equal(stato.archivio,0);
      assert.equal(await page.getByRole('button',{name:'Carica logo',exact:true}).count(),0);
      stato.errore=false;
      await page.evaluate((p)=>{if(localStorage.getItem('adflow_profilo_esempio_anteprima')===null)localStorage.setItem('adflow_profilo_esempio_anteprima',JSON.stringify(p));},iniziale);
      const archivioDopoRiprova=page.waitForResponse((r)=>new URL(r.url()).pathname==='/api/archivio');
      await page.getByRole('button',{name:'Riprova',exact:true}).click();
      await page.getByRole('button',{name:'Carica logo',exact:true}).waitFor();
      await archivioDopoRiprova;
      assert.ok(stato.archivio>=1);assert.deepEqual(errori,[]);
      console.log('OK test_ca05_errore_verifica_profilo_disabilita_upload_e_riprova_li_riattiva');
      await context.close();
    }
  }finally{await browser.close();}
})().catch((e)=>{console.error(e);process.exitCode=1;});
