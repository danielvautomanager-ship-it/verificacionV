/**
 * Herramienta de revisión: saca fotos (png) de segundos concretos del video,
 * sin tener que renderizarlo completo. Sirve para revisar cómo se ve cada escena.
 *
 *   node revisar.mjs --tl salida/completo/timeline.json --segundos 0,20,120
 *   node revisar.mjs --tl salida/completo/timeline.json --escenas   (una foto por escena)
 */
import { chromium } from 'playwright';
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { mkdirSync } from 'node:fs';
import { dirname, extname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const RAIZ = dirname(fileURLToPath(import.meta.url));
const args = {};
for (let i = 2; i < process.argv.length; i++) {
  if (process.argv[i].startsWith('--')) {
    const clave = process.argv[i].replace(/^--/, '');
    const valor = (process.argv[i + 1] && !process.argv[i + 1].startsWith('--')) ? process.argv[++i] : true;
    args[clave] = valor;
  }
}
const TL = args.tl || 'salida/completo/timeline.json';
const CARPETA = args.carpeta || 'salida/revision';
const ESCALA = parseFloat(args.escala || 0.5);

const TIPOS = { '.html':'text/html; charset=utf-8', '.json':'application/json; charset=utf-8',
  '.css':'text/css; charset=utf-8', '.woff2':'font/woff2', '.wav':'audio/wav' };
const servidor = createServer(async (req, res) => {
  try {
    const ruta = resolve(RAIZ, decodeURIComponent(req.url.split('?')[0]).replace(/^\/+/, ''));
    const datos = await readFile(ruta);
    res.writeHead(200, { 'Content-Type': TIPOS[extname(ruta)] || 'application/octet-stream' });
    res.end(datos);
  } catch { res.writeHead(404).end(); }
});
await new Promise(r => servidor.listen(0, '127.0.0.1', r));

const timeline = JSON.parse(await readFile(join(RAIZ, TL), 'utf8'));
let segundos;
if (args.escenas) segundos = timeline.escenas.map(e => +(e.inicio + Math.min(3.2, (e.fin - e.inicio) * 0.55)).toFixed(2));
else segundos = String(args.segundos || '0').split(',').map(Number);

const navegador = await chromium.launch();
const pagina = await navegador.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: ESCALA });
await pagina.goto(`http://127.0.0.1:${servidor.address().port}/escena.html?tl=${encodeURIComponent(TL)}`, { waitUntil: 'load' });
await pagina.waitForFunction('window.LISTO === true', null, { timeout: 60000 });
const errores = [];
pagina.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') errores.push(m.text()); });

mkdirSync(join(RAIZ, CARPETA), { recursive: true });
for (const t of segundos) {
  await pagina.evaluate(seg => window.seek(seg), t);
  const esc = timeline.escenas.find(e => t >= e.inicio && t < e.fin);
  const nombre = `t${String(Math.round(t)).padStart(3, '0')}-${esc ? esc.nombre : 'fin'}.png`;
  await pagina.screenshot({ path: join(RAIZ, CARPETA, nombre) });
  console.log('  ' + nombre);
}
if (errores.length) console.log('Avisos del navegador:', errores.slice(0, 10));
await navegador.close();
servidor.close();
