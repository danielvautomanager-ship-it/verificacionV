#!/usr/bin/env python3
"""
PASO 1 — Generar la voz en español y la línea de tiempo.

Qué hace, en orden:
  1. Lee el guion (guion/completo.json o guion/corto.json).
  2. Convierte cada frase en audio con Piper (TTS neuronal que corre en esta máquina,
     sin internet una vez descargada la voz).
  3. Pega todas las frases en UN SOLO archivo `narracion.wav`, agregando los silencios.
  4. Como conoce la duración real de cada frase, escribe `timeline.json`: en qué segundo
     empieza y termina cada frase y cada escena. Ese archivo es el que manda en el video:
     la animación y los subtítulos se acomodan a la voz, y no al revés.
  5. También escribe `subtitulos.srt` (por si subes el video a YouTube).

Uso:
    python3 paso1_voz.py guion/completo.json --salida salida/completo
"""
import argparse
import io
import json
import re
import wave
from pathlib import Path

from piper import PiperVoice, SynthesisConfig

RAIZ = Path(__file__).resolve().parent
SILENCIO_INICIAL = 0.9   # segundos de aire antes de la primera frase
MAX_CARACTERES_SUBTITULO = 64   # un subtítulo más largo que esto se parte en dos


def sintetizar(voz, texto, syn):
    """Convierte un texto en audio y devuelve (rate, sampwidth, bytes_de_audio)."""
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as w:
        voz.synthesize_wav(texto, w, syn_config=syn)
    buffer.seek(0)
    with wave.open(buffer, "rb") as w:
        return w.getframerate(), w.getsampwidth(), w.readframes(w.getnframes())


def partir_en_subtitulos(texto):
    """Parte una frase larga en trozos legibles, cortando en comas y puntos cuando se puede."""
    partes = re.split(r"(?<=[,;:.…])\s+", texto)
    trozos, actual = [], ""
    for parte in partes:
        candidato = (actual + " " + parte).strip()
        if actual and len(candidato) > MAX_CARACTERES_SUBTITULO:
            trozos.append(actual)
            actual = parte
        else:
            actual = candidato
    if actual:
        trozos.append(actual)

    # Si algún trozo sigue siendo enorme (frase sin comas), lo partimos por palabras.
    finales = []
    for trozo in trozos:
        while len(trozo) > MAX_CARACTERES_SUBTITULO:
            corte = trozo.rfind(" ", 0, MAX_CARACTERES_SUBTITULO)
            corte = corte if corte > 0 else MAX_CARACTERES_SUBTITULO
            finales.append(trozo[:corte].strip())
            trozo = trozo[corte:].strip()
        if trozo:
            finales.append(trozo)
    return finales


def repartir_tiempo(trozos, inicio, fin):
    """Reparte el tiempo de la frase entre sus subtítulos, en proporción a su largo."""
    total = sum(len(t) for t in trozos) or 1
    subs, t = [], inicio
    for i, trozo in enumerate(trozos):
        dur = (fin - inicio) * len(trozo) / total
        t_fin = fin if i == len(trozos) - 1 else t + dur
        subs.append({"texto": trozo, "inicio": round(t, 3), "fin": round(t_fin, 3)})
        t = t_fin
    return subs


def tiempo_srt(segundos):
    h, resto = divmod(segundos, 3600)
    m, s = divmod(resto, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):06.3f}".replace(".", ",")


def main():
    ap = argparse.ArgumentParser(description="Genera narración + timeline a partir del guion")
    ap.add_argument("guion", help="ruta al json del guion")
    ap.add_argument("--salida", required=True, help="carpeta donde escribir narracion.wav y timeline.json")
    ap.add_argument("--voz", help="nombre del modelo de voz (por defecto, el del guion)")
    args = ap.parse_args()

    guion = json.loads(Path(args.guion).read_text(encoding="utf-8"))
    salida = Path(args.salida)
    salida.mkdir(parents=True, exist_ok=True)

    nombre_voz = args.voz or guion.get("voz", "es_MX-claude-high")
    modelo = RAIZ / "assets" / "voz" / f"{nombre_voz}.onnx"
    if not modelo.exists():
        raise SystemExit(f"No encuentro la voz {modelo}. Ejecuta ./hacer_video.sh instalar")

    print(f"Cargando voz {nombre_voz}...")
    voz = PiperVoice.load(str(modelo))
    # length_scale > 1 = habla más lento y pausado; < 1 = más rápido.
    syn = SynthesisConfig(length_scale=guion.get("velocidad", 1.0), normalize_audio=True)

    audio, lineas = [], []
    rate = sampwidth = None
    t = SILENCIO_INICIAL

    def silencio(seg):
        return b"\x00" * int(rate * sampwidth * seg)

    for i, linea in enumerate(guion["lineas"], 1):
        rate_i, sw_i, datos = sintetizar(voz, linea["texto"], syn)
        if rate is None:
            rate, sampwidth = rate_i, sw_i
            audio.append(b"\x00" * int(rate * sampwidth * SILENCIO_INICIAL))
        duracion = len(datos) / (rate * sampwidth)
        audio.append(datos)

        inicio, fin = t, t + duracion
        trozos = partir_en_subtitulos(linea["texto"])
        lineas.append({
            "id": linea["id"],
            "escena": linea["escena"],
            "texto": linea["texto"],
            "inicio": round(inicio, 3),
            "fin": round(fin, 3),
            "subs": repartir_tiempo(trozos, inicio, fin),
        })
        print(f"  [{i:2d}/{len(guion['lineas'])}] {linea['escena']:<20} {duracion:5.2f}s  {linea['texto'][:52]}...")

        pausa = float(linea.get("pausa", 0.3))
        audio.append(silencio(pausa))
        t = fin + pausa

    duracion_total = t

    with wave.open(str(salida / "narracion.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(sampwidth)
        w.setframerate(rate)
        w.writeframes(b"".join(audio))

    # Cada escena dura desde que empieza su primera frase hasta que acaba la última.
    escenas, orden = {}, []
    for linea in lineas:
        nombre = linea["escena"]
        if nombre not in escenas:
            escenas[nombre] = {"nombre": nombre, "inicio": linea["inicio"], "fin": linea["fin"]}
            orden.append(nombre)
        escenas[nombre]["fin"] = linea["fin"]

    lista_escenas = [escenas[n] for n in orden]
    # La escena empieza un poco antes de la voz (para que la animación entre) y termina
    # justo cuando arranca la siguiente, así no hay huecos en negro.
    for i, esc in enumerate(lista_escenas):
        esc["inicio"] = round(max(0.0, esc["inicio"] - (SILENCIO_INICIAL if i == 0 else 0.55)), 3)
        esc["fin"] = round(lista_escenas[i + 1]["inicio"] if i + 1 < len(lista_escenas) else duracion_total, 3)
    lista_escenas[0]["inicio"] = 0.0

    timeline = {
        "titulo": guion["titulo"],
        "subtitulo": guion.get("subtitulo", ""),
        "duracion": round(duracion_total, 3),
        "escenas": lista_escenas,
        "lineas": lineas,
    }
    (salida / "timeline.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=2), encoding="utf-8")

    with (salida / "subtitulos.srt").open("w", encoding="utf-8") as f:
        n = 1
        for linea in lineas:
            for sub in linea["subs"]:
                f.write(f"{n}\n{tiempo_srt(sub['inicio'])} --> {tiempo_srt(sub['fin'])}\n{sub['texto']}\n\n")
                n += 1

    print(f"\nListo: {duracion_total/60:.2f} min ({duracion_total:.1f} s), {len(lineas)} frases, {len(lista_escenas)} escenas")
    print(f"  {salida/'narracion.wav'}\n  {salida/'timeline.json'}\n  {salida/'subtitulos.srt'}")


if __name__ == "__main__":
    main()
