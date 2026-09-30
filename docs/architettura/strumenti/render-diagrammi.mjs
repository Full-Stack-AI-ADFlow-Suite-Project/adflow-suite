// Rigenera i PNG dei diagrammi da AdFlow-diagrammi.html, a 2x come gli originali.
// Uso (da docs/architettura):  node strumenti/render-diagrammi.mjs [d01,d09,...]
// Senza argomenti rende tutti i diagrammi. Chrome: percorso standard di Windows, oppure variabile CHROME.
import { spawn } from "node:child_process";
import { writeFileSync, mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const HTML = resolve(here, "..", "AdFlow-diagrammi.html");
const OUT = resolve(here, "..", "diagrammi");
const CHROME = process.env.CHROME || "C:/Program Files/Google/Chrome/Application/chrome.exe";
const PORT = 9333;
const profile = mkdtempSync(join(tmpdir(), "adflow-chrome-"));
const chrome = spawn(CHROME, ["--headless=new", `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`,
  "--hide-scrollbars", "--disable-gpu", "--no-first-run", "--no-default-browser-check", "about:blank"], { stdio: "ignore" });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let targets;
for (let i = 0; i < 60 && !targets; i++) {
  try { targets = await (await fetch(`http://127.0.0.1:${PORT}/json`)).json(); } catch { await sleep(250); }
}
if (!targets) throw new Error("Chrome non risponde: controlla il percorso (variabile CHROME)");

const ws = new WebSocket(targets.find((t) => t.type === "page").webSocketDebuggerUrl);
await new Promise((r) => ws.addEventListener("open", r, { once: true }));
let seq = 0; const pending = new Map();
ws.addEventListener("message", (ev) => {
  const m = JSON.parse(ev.data);
  if (m.id && pending.has(m.id)) { const p = pending.get(m.id); pending.delete(m.id); m.error ? p.rej(new Error(JSON.stringify(m.error))) : p.res(m.result); }
});
const send = (method, params = {}) => new Promise((res, rej) => { const id = ++seq; pending.set(id, { res, rej }); ws.send(JSON.stringify({ id, method, params })); });
const js = async (expr) => (await send("Runtime.evaluate", { expression: expr, returnByValue: true })).result.value;

await send("Page.enable");
await send("Emulation.setDeviceMetricsOverride", { width: 1720, height: 1200, deviceScaleFactor: 2, mobile: false });
await send("Page.navigate", { url: pathToFileURL(HTML).href });
for (let i = 0; i < 80 && !(await js("window.__done===true")); i++) await sleep(250);
await sleep(400);

const missing = await js("(window.__missing||[]).join(', ')");
if (missing) console.warn("Attenzione, connettori con id inesistente:", missing);

const ids = process.argv[2] ? process.argv[2].split(",") : await js("[...document.querySelectorAll('.dg[data-png]')].map(e=>e.id)");
for (const id of ids) {
  const b = await js(`(()=>{const e=document.getElementById(${JSON.stringify(id)});const r=e.getBoundingClientRect();return {x:r.left+scrollX,y:r.top+scrollY,w:r.width,h:r.height,png:e.dataset.png}})()`);
  const shot = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: true, clip: { x: b.x, y: b.y, width: b.w, height: b.h, scale: 1 } });
  writeFileSync(join(OUT, `${b.png}.png`), Buffer.from(shot.data, "base64"));
  console.log(`${id} → diagrammi/${b.png}.png`);
}
ws.close(); chrome.kill();
await sleep(500);
try { rmSync(profile, { recursive: true, force: true }); } catch {}
