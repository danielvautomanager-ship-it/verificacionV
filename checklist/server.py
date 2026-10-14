"""Servidor del Checklist PMM.

Hace dos cosas:
  1. Sirve la app (carpeta static/) para instalarla en Android.
  2. Recibe el PDF ya llenado y lo envía por correo a los 3 destinatarios.

Las credenciales del correo NO van en el código: se leen de variables de entorno.
"""
import base64
import binascii
import os
import re
import smtplib
from email.message import EmailMessage

from flask import Flask, jsonify, request, send_from_directory

# Destinatarios fijos (el celular no puede cambiarlos).
DESTINATARIOS = [
    "supervisorflotillas@pmm.com.mx",
    "flotillas@pmm.com.mx",
    "gerenciatpc@pmm.com.mx",
]

MAX_PDF_BYTES = 15 * 1024 * 1024

app = Flask(__name__, static_folder="static", static_url_path="")
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024


def smtp_config():
    """Lee la configuración del correo; devuelve None si falta algo."""
    cfg = {
        "host": os.environ.get("SMTP_HOST", "smtp.gmail.com"),
        "port": int(os.environ.get("SMTP_PORT", "587")),
        "user": os.environ.get("SMTP_USER", ""),
        "password": os.environ.get("SMTP_PASSWORD", ""),
    }
    cfg["from"] = os.environ.get("SMTP_FROM", cfg["user"])
    if not cfg["user"] or not cfg["password"]:
        return None
    return cfg


def limpiar(texto, largo=60):
    """Deja solo caracteres seguros para asunto y nombre de archivo."""
    return re.sub(r"[^\w\-. ]", "", str(texto or "").replace("/", "-"))[:largo].strip() or "SN"


@app.get("/")
def inicio():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/sw.js")
def service_worker():
    # Se sirve desde la raíz para que controle toda la app.
    resp = send_from_directory(app.static_folder, "sw.js")
    resp.headers["Cache-Control"] = "no-cache"
    return resp


@app.post("/enviar")
def enviar():
    datos = request.get_json(silent=True) or {}
    cfg = smtp_config()
    if cfg is None:
        return jsonify(ok=False, error="El servidor no tiene configurado el correo."), 503

    try:
        pdf = base64.b64decode(datos.get("pdf", ""), validate=True)
    except (binascii.Error, ValueError):
        return jsonify(ok=False, error="PDF inválido."), 400
    if not pdf.startswith(b"%PDF") or len(pdf) > MAX_PDF_BYTES:
        return jsonify(ok=False, error="PDF inválido o demasiado grande."), 400

    eco = limpiar(datos.get("eco"))
    fecha = limpiar(datos.get("fecha"), 20)
    conductor = limpiar(datos.get("conductor"), 80)
    archivo = f"Checklist_{eco}_{fecha}.pdf"

    msg = EmailMessage()
    msg["Subject"] = f"Checklist de unidad {eco} - {fecha}"
    msg["From"] = cfg["from"]
    msg["To"] = ", ".join(DESTINATARIOS)
    msg.set_content(
        f"Se adjunta el checklist de revisión de la unidad {eco}.\n"
        f"Fecha: {fecha}\nConductor: {conductor}\n\n"
        "Enviado desde la app Checklist PMM."
    )
    msg.add_attachment(pdf, maintype="application", subtype="pdf", filename=archivo)

    try:
        with smtplib.SMTP(cfg["host"], cfg["port"], timeout=30) as smtp:
            smtp.starttls()
            smtp.login(cfg["user"], cfg["password"])
            smtp.send_message(msg, to_addrs=DESTINATARIOS)
    except (smtplib.SMTPException, OSError) as exc:
        app.logger.error("Fallo al enviar correo: %s", exc)
        return jsonify(ok=False, error="No se pudo enviar el correo."), 502

    return jsonify(ok=True, destinatarios=DESTINATARIOS)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
