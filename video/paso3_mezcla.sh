#!/usr/bin/env bash
# PASO 3 — Pegarle la voz al video mudo.
#   ./paso3_mezcla.sh salida/completo/video-mudo.mp4 salida/completo/narracion.wav salida/video-completo.mp4
set -euo pipefail
VIDEO="$1"; AUDIO="$2"; FINAL="$3"

ffmpeg -y -loglevel error \
  -i "$VIDEO" -i "$AUDIO" \
  -c:v copy \
  -c:a aac -b:a 192k -ar 48000 -ac 2 \
  -shortest -movflags +faststart \
  "$FINAL"

echo "Video final: $FINAL"
ffprobe -v error -show_entries format=duration,size:stream=codec_type,codec_name,width,height,r_frame_rate \
  -of default=noprint_wrappers=1 "$FINAL"
