import uuid
from flask import Blueprint, render_template, request, jsonify
import realestate_db as rdb

chatbot_bp = Blueprint("chatbot", __name__)


@chatbot_bp.route("/chatbot/")
def chatbot_ui():
    return render_template("chatbot/chat.html")


@chatbot_bp.route("/chatbot/api/sesion", methods=["POST"])
def chatbot_nueva_sesion():
    token = uuid.uuid4().hex
    sid = rdb.crear_sesion(token)
    return jsonify({"session_token": token, "sesion_id": sid})


@chatbot_bp.route("/chatbot/api/mensaje", methods=["POST"])
def chatbot_mensaje():
    data = request.get_json(force=True) or {}
    token = data.get("session_token", "")
    pregunta = data.get("message", "").strip()
    if not pregunta:
        return jsonify({"error": "Mensaje vacío"}), 400

    sesion = rdb.get_sesion(token)
    if not sesion:
        return jsonify({"error": "Sesión inválida"}), 401

    sid = sesion["id"]
    historial = rdb.get_historial(sid, limite=12)
    rdb.guardar_mensaje(sid, "user", pregunta)

    try:
        from rag_engine import consultar
        respuesta = consultar(pregunta, historial)
    except Exception as e:
        respuesta = (
            "Hola, soy el asistente de la inmobiliaria. "
            "En este momento el servicio de IA no está disponible. "
            "Por favor comuníquese directamente con nuestro asesor."
        )

    rdb.guardar_mensaje(sid, "assistant", respuesta)
    return jsonify({"respuesta": respuesta})


@chatbot_bp.route("/chatbot/api/historial/<token>")
def chatbot_historial(token):
    sesion = rdb.get_sesion(token)
    if not sesion:
        return jsonify({"mensajes": []})
    historial = rdb.get_historial(sesion["id"])
    return jsonify({"mensajes": historial})


@chatbot_bp.route("/chatbot/api/lead", methods=["POST"])
def chatbot_guardar_lead():
    data = request.get_json(force=True) or {}
    if not data.get("nombre") and not data.get("telefono"):
        return jsonify({"error": "Faltan datos"}), 400
    lead_id = rdb.crear_lead({
        "nombre": data.get("nombre", ""),
        "telefono": data.get("telefono", ""),
        "email": data.get("email", ""),
        "mensaje": data.get("mensaje", ""),
        "origen": "chatbot",
    })
    return jsonify({"ok": True, "lead_id": lead_id})
