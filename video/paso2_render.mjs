/**
 * PASO 2 — Convertir la animación del navegador en fotogramas de video.
 *
 * Cómo funciona:
 *   1. Levanta un servidor web local (Chromium necesita http:// para leer timeline.json).
 *   2. Abre escena.html con Playwright a 1920x1080.
 *   3. Para cada fotograma: le dice a la página "colócate en el segundo X" (seek),
 *      toma una foto y se la manda a ffmpeg por una tubería.
 *   4. ffmpeg junta las fotos en un .mp4 (todavía sin sonido).
 *
 * Uso:
 *   node paso2_render.mjs --tl salida/completo/timeline.json --salida salida/completo/video-mudo.mp4
 *   node paso2_render.mjs ... --escala 0.5 --desde 0 --hasta 10     (prueba rápida)
 */
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { createServer } from 'node:http';
import { readFile, writeFile, unlink } from 'node:fs/promises';
import { mkdirSync } from 'node:fs';
import { cpus } from 'node:os';
import { dirname, extname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const RAIZ = dirname(fileURLToPath(import.meta.url));

// --- argumentos de la línea de comandos ---
const args = {};
for (let i = 2; i < process.argv.length; i += 2) args[process.argv[i].replace(/^--/, '')] = process.argv[i + 1];
const TL       = args.tl     || 'salida/completo/timeline.json';
const SALIDA   = args.salida || 'salida/completo/video-mudo.mp4';
const FPS      = parseInt(args.fps || 30);
const ESCALA   = parseFloat(args.escala || 1);
const CRF      = args.crf || '19';
const DESDE    = parseFloat(args.desde || 0);
const HASTA    = args.hasta !== undefined ? parseFloat(args.hasta) : null;
// Varias pestañas rinden trozos distintos del video al mismo tiempo y luego se pegan.
const TRABAJADORES = Math.max(1, parseInt(args.trabajadores || Math.min(4, cpus().length)));

const TIPOS = { '.html':'text/html; charset=utf-8', '.json':'application/json; charset=utf-8',
  '.css':'text/css; charset=utf-8', '.woff2':'font/woff2', '.wav':'audio/wav', '.js':'text/javascript' };

// 1) servidor local mínimo sobre la carpeta video/
const servidor = createServer(async (req, res) => {
  try {
    const ruta = resolve(RAIZ, decodeURIComponent(req.url.split('?')[0]).replace(/^\/+/, ''));
    if (!ruta.startsWith(RAIZ)) { res.writeHead(403).end(); return; }
    const datos = await readFile(ruta);
    res.writeHead(200, { 'Content-Type': TIPOS[extname(ruta)] || 'application/octet-stream' });
    res.end(datos);
  } catch { res.writeHead(404).end('no encontrado'); }
});
await new Promise(r => servidor.listen(0, '127.0.0.1', r));
const PUERTO = servidor.address().port;

// 2) navegador
const timeline = JSON.parse(await readFile(join(RAIZ, TL), 'utf8'));
const duracion = HASTA !== null ? Math.min(HASTA, timeline.duracion) : timeline.duracion;
const total = Math.round((duracion - DESDE) * FPS);

const navegador = await chromium.launch({ args: ['--force-color-profile=srgb', '--disable-lcd-text'] });
mkdirSync(dirname(join(RAIZ, SALIDA)), { recursive: true });

console.log(`Renderizando ${total} fotogramas · ${FPS} fps · ${Math.round(1920 * ESCALA)}x${Math.round(1080 * ESCALA)} · ` +
            `${duracion.toFixed(1)}s · ${TRABAJADORES} trabajador(es)`);
const t0 = Date.now();
let hechos = 0;

function avisar() {
  hechos++;
  if (hechos % 30 && hechos !== total) return;
  const seg = (Date.now() - t0) / 1000;
  const faltan = seg / hechos * (total - hechos);
  process.stdout.write(`\r  ${String(hechos).padStart(6)}/${total}  (${(hechos / total * 100).toFixed(1)}%)  ` +
    `${(hechos / seg).toFixed(1)} fps  ·  faltan ~${Math.max(0, Math.round(faltan / 60))} min   `);
}

/** Rinde los fotogramas [desde, hasta) en su propio archivo de video. */
async function renderizarTrozo(desdeFrame, hastaFrame, archivo) {
  const pagina = await navegador.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: ESCALA });
  await pagina.goto(`http://127.0.0.1:${PUERTO}/escena.html?tl=${encodeURIComponent(TL)}`, { waitUntil: 'load' });
  await pagina.waitForFunction('window.LISTO === true', null, { timeout: 60000 });

  const ff = spawn('ffmpeg', [
    '-y', '-loglevel', 'error',
    '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', 'pipe:0',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', String(CRF),
    '-pix_fmt', 'yuv420p', '-g', String(FPS * 2), '-movflags', '+faststart',
    archivo
  ], { stdio: ['pipe', 'inherit', 'inherit'] });

  for (let i = desdeFrame; i < hastaFrame; i++) {
    await pagina.evaluate(seg => window.seek(seg), DESDE + i / FPS);
    const foto = await pagina.screenshot({ type: 'jpeg', quality: 92, caret: 'hide', animations: 'disabled' });
    if (!ff.stdin.write(foto)) await new Promise(r => ff.stdin.once('drain', r));
    avisar();
  }
  ff.stdin.end();
  await new Promise((ok, mal) => ff.on('close', c => c === 0 ? ok() : mal(new Error('ffmpeg salió con código ' + c))));
  await pagina.close();
}

const destino = join(RAIZ, SALIDA);
if (TRABAJADORES === 1) {
  await renderizarTrozo(0, total, destino);
} else {
  const corte = Math.ceil(total / TRABAJADORES);
  const trozos = [];
  for (let i = 0; i < TRABAJADORES; i++) {
    const desde = i * corte, hasta = Math.min(total, (i + 1) * corte);
    if (desde < hasta) trozos.push({ desde, hasta, archivo: `${destino}.parte${i}.mp4` });
  }
  await Promise.all(trozos.map(t => renderizarTrozo(t.desde, t.hasta, t.archivo)));

  // pegamos los trozos sin recomprimir
  const lista = `${destino}.partes.txt`;
  await writeFile(lista, trozos.map(t => `file '${t.archivo}'`).join('\n') + '\n');
  const pegar = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lista,
                                 '-c', 'copy', '-movflags', '+faststart', destino], { stdio: 'inherit' });
  await new Promise((ok, mal) => pegar.on('close', c => c === 0 ? ok() : mal(new Error('no se pudieron pegar los trozos'))));
  for (const t of trozos) await unlink(t.archivo);
  await unlink(lista);
}

await navegador.close();
servidor.close();
console.log(`\nVideo mudo listo: ${SALIDA}  (${((Date.now() - t0) / 60000).toFixed(1)} min de render)`);
