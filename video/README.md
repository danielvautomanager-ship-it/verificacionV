# Video: "Administra el dinero de tu negocio"

Genera un video educativo en 1080p **con voz en español y subtítulos**, a partir del guion
del PDF. El video no se filma ni se descarga: se **dibuja en un navegador** (HTML + CSS + SVG)
y Playwright lo va fotografiando cuadro por cuadro.

| Archivo final | Qué es |
|---|---|
| `salida/video-completo.mp4` | Video largo (~4:45 min) con todo el guion |
| `salida/video-corto.mp4` | Versión de ~70 s para redes sociales |
| `salida/video-*.srt` | Subtítulos, por si lo subes a YouTube |

---

## Cómo lo hago correr

```bash
cd video
./hacer_video.sh instalar    # sólo la primera vez (ffmpeg, Piper, Playwright, la voz)
./hacer_video.sh prueba      # 12 segundos en baja calidad, para revisar rápido
./hacer_video.sh completo    # el video largo   (~20 min de render)
./hacer_video.sh corto       # el video corto   (~5 min de render)
./hacer_video.sh todo        # los dos
```

Si el render parece "trabado", no lo está: dibujar 8.400 fotogramas toma tiempo.
En pantalla verás el avance (`1234/8448 · 6.9 fps · faltan ~17 min`).

---

## Cómo funciona (los tres pasos)

```
guion/completo.json ──▶ paso1_voz.py ──▶ narracion.wav + timeline.json + subtitulos.srt
                                              │
                        escena.html ◀─────────┘   (la animación lee los tiempos de la voz)
                             │
                             ▼
                      paso2_render.mjs  (Playwright fotografía cada cuadro → ffmpeg)
                             │
                             ▼
                      paso3_mezcla.sh   (le pega la voz)  ──▶  salida/video-completo.mp4
```

**Paso 1 · `paso1_voz.py`** — Convierte cada frase del guion en audio con **Piper**
(un sintetizador de voz que corre en tu computadora, sin internet ni cuentas). Como el
programa sabe cuánto dura cada frase, escribe `timeline.json` con el segundo exacto en que
empieza y termina cada frase y cada escena. **Ese archivo manda:** la animación se acomoda a
la voz, nunca al revés.

**Paso 2 · `paso2_render.mjs`** — Abre `escena.html` con Playwright en 1920x1080. Para cada
fotograma le dice a la página *"colócate en el segundo 12.7"*, toma una foto y se la pasa a
ffmpeg por una tubería (así los miles de imágenes nunca tocan el disco). Usa 4 pestañas en
paralelo, cada una con un pedazo del video, y al final los pega.

**Paso 3 · `paso3_mezcla.sh`** — ffmpeg une el video mudo con `narracion.wav`. Como los dos
salieron del mismo `timeline.json`, la sincronía es exacta.

### Por qué no se usa la grabación de pantalla de Playwright
Playwright puede grabar video (`recordVideo`), pero graba *en tiempo real*: si la máquina se
atora, pierde cuadros, y además su ffmpeg no trae códecs de audio. Al fotografiar cuadro por
cuadro el resultado es siempre idéntico, va a 30 fps exactos y sale en `.mp4` con sonido.

---

## Los archivos

| Archivo | Para qué sirve |
|---|---|
| `guion/completo.json` | El texto del PDF partido en frases, y a qué escena pertenece cada una |
| `guion/corto.json` | El resumen de ~70 s |
| `escena.html` | **El "set de grabación"**: las 20 escenas dibujadas con HTML/CSS/SVG |
| `paso1_voz.py` | Voz + línea de tiempo + subtítulos |
| `paso2_render.mjs` | Fotogramas → video mudo |
| `paso3_mezcla.sh` | Video mudo + voz → video final |
| `revisar.mjs` | Saca fotos de segundos sueltos, sin renderizar todo |
| `hacer_video.sh` | Corre los tres pasos en orden |
| `assets/fonts/` | Tipografías (Fraunces e Inter) guardadas localmente |
| `assets/voz/` | Modelo de voz de Piper (no se sube a git: pesa 63 MB) |

---

## Cómo le cambio cosas

**El texto o el orden de las frases** → edita `guion/completo.json`. Cada entrada tiene:

```json
{ "id": "12", "escena": "error1", "texto": "El primer peligro es...", "pausa": 0.2 }
```

`escena` debe coincidir con una de las plantillas de `escena.html`
(`<template data-escena="error1">`). `pausa` son los segundos de silencio después de la frase.
Luego vuelve a correr `./hacer_video.sh completo`.

**Cuándo aparece cada elemento en pantalla** → en `escena.html`, cada elemento animado lleva:

- `data-in="1.5"` → entra 1.5 s después de que empieza la escena.
- `data-linea="1" data-desfase="0.8"` → entra 0.8 s después de que empieza la **segunda**
  frase de esa escena (se sincroniza solo con la voz, aunque cambies el texto).
- `data-y="30"` / `data-x="-70"` → desde dónde entra (píxeles).

**Los colores** → las variables de arriba de `escena.html` (`--crema`, `--terracota`, `--ambar`…).

**La voz** → en `guion/*.json`, el campo `"voz"`. Vienen dos opciones descargables:
`es_MX-claude-high` (mexicana, la que se usa) y `es_ES-davefx-medium` (española).
El campo `"velocidad"` es el ritmo: más de 1 habla más lento, menos de 1 más rápido.

**Revisar sin renderizar** →
```bash
node revisar.mjs --tl salida/completo/timeline.json --escenas       # una foto por escena
node revisar.mjs --tl salida/completo/timeline.json --segundos 12,45,200
```
o abre `escena.html?ui=1` en un navegador (con `npx serve .`): aparece una barra para moverte
por el video y la **barra espaciadora** lo reproduce con audio.

---

## Cosas que conviene saber

- **No hay música de fondo.** Se puede agregar después con un comando de ffmpeg si consigues
  una pista con licencia libre.
- **La voz es sintética** (Piper). Suena natural pero no es un locutor humano.
- **El "presentador" y el B-roll son ilustraciones**, no video filmado: Playwright dibuja
  páginas web, no graba personas. El contenido y la estructura del guion sí se respetan tal cual.
- `salida/` y `node_modules/` no se suben a git (los videos pesan decenas de MB).
