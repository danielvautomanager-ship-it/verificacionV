#!/usr/bin/env bash
# ============================================================
#  Hace el video completo, de principio a fin.
#
#    ./hacer_video.sh instalar    → instala las dependencias (una sola vez)
#    ./hacer_video.sh prueba      → render corto de 12 s en baja calidad (para revisar)
#    ./hacer_video.sh corto       → video de ~70 s
#    ./hacer_video.sh completo    → video de ~4:45 min
#    ./hacer_video.sh todo        → los dos videos
# ============================================================
set -euo pipefail
cd "$(dirname "$0")"
VOZ_URL="https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_MX/claude/high"

instalar() {
  echo "== 1/4 ffmpeg =="
  command -v ffmpeg >/dev/null || { apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq ffmpeg; }
  echo "== 2/4 Piper (voz) =="
  python3 -c "import piper" 2>/dev/null || pip install -q piper-tts
  echo "== 3/4 modelo de voz en español =="
  mkdir -p assets/voz
  for f in es_MX-claude-high.onnx es_MX-claude-high.onnx.json; do
    [ -f "assets/voz/$f" ] || curl -sSL -o "assets/voz/$f" "$VOZ_URL/$f"
  done
  echo "== 4/4 Playwright =="
  [ -d node_modules/playwright ] || npm install --no-audit --no-fund
  npx playwright install chromium 2>/dev/null || true
  echo "Listo."
}

hacer() {                       # $1 = completo | corto
  local nombre="$1"
  echo "=============== $nombre ==============="
  python3 paso1_voz.py "guion/$nombre.json" --salida "salida/$nombre"
  node paso2_render.mjs --tl "salida/$nombre/timeline.json" --salida "salida/$nombre/video-mudo.mp4"
  ./paso3_mezcla.sh "salida/$nombre/video-mudo.mp4" "salida/$nombre/narracion.wav" "salida/video-$nombre.mp4"
  cp "salida/$nombre/subtitulos.srt" "salida/video-$nombre.srt"
}

case "${1:-completo}" in
  instalar) instalar ;;
  prueba)
    [ -f salida/completo/timeline.json ] || python3 paso1_voz.py guion/completo.json --salida salida/completo
    node paso2_render.mjs --tl salida/completo/timeline.json --salida salida/prueba-mudo.mp4 --escala 0.5 --desde 0 --hasta 12
    ./paso3_mezcla.sh salida/prueba-mudo.mp4 salida/completo/narracion.wav salida/prueba.mp4 ;;
  corto)    hacer corto ;;
  completo) hacer completo ;;
  todo)     hacer corto; hacer completo ;;
  *) echo "Opciones: instalar | prueba | corto | completo | todo"; exit 1 ;;
esac
