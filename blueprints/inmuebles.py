import os
import uuid
import json
import threading
from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, jsonify, current_app)
from werkzeug.utils import secure_filename
import realestate_db as rdb

inmuebles_bp = Blueprint("inmuebles", __name__)

ALLOWED_FOTO = {"jpg", "jpeg", "png", "webp", "gif"}
ALLOWED_PDF  = {"pdf"}


def _ext(filename):
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def _save_file(f, subfolder):
    ext = _ext(f.filename)
    safe = secure_filename(f.filename)
    unique = f"{uuid.uuid4().hex[:8]}_{safe}"
    upload_dir = os.path.join(current_app.root_path, "static", "uploads", subfolder)
    os.makedirs(upload_dir, exist_ok=True)
    path = os.path.join(upload_dir, unique)
    f.save(path)
    return unique


# ── Lista ─────────────────────────────────────────────────────────────────────

@inmuebles_bp.route("/inmuebles/")
def inmuebles_lista():
    ft = request.args.get("tipo", "")
    fo = request.args.get("operacion", "")
    fe = request.args.get("estado", "")
    propiedades = rdb.listar_propiedades(ft or None, fo or None, fe or None)
    kpi = rdb.kpi_propiedades()
    return render_template("inmuebles/lista.html",
                           propiedades=propiedades, kpi=kpi,
                           filtro_tipo=ft, filtro_operacion=fo, filtro_estado=fe)


# ── Nueva ─────────────────────────────────────────────────────────────────────

@inmuebles_bp.route("/inmuebles/nueva", methods=["GET", "POST"])
def inmuebles_nueva():
    if request.method == "POST":
        data = request.form.to_dict()
        data["caracteristicas"] = json.dumps(
            request.form.getlist("caracteristicas"), ensure_ascii=False
        )
        pid = rdb.crear_propiedad(data)
        # Subir archivos si vienen
        fotos = request.files.getlist("fotos")
        pdfs  = request.files.getlist("pdfs")
        primera_foto = True
        for f in fotos:
            if f and f.filename and _ext(f.filename) in ALLOWED_FOTO:
                nombre = _save_file(f, "fotos")
                rdb.crear_archivo(pid, "foto", nombre, f.filename,
                                  es_portada=1 if primera_foto else 0)
                primera_foto = False
        for f in pdfs:
            if f and f.filename and _ext(f.filename) in ALLOWED_PDF:
                nombre = _save_file(f, "pdfs")
                rdb.crear_archivo(pid, "pdf", nombre, f.filename)
        flash("Propiedad registrada exitosamente.", "success")
        return redirect(url_for("inmuebles.inmuebles_detalle", pid=pid))
    return render_template("inmuebles/nueva.html")


# ── Detalle ───────────────────────────────────────────────────────────────────

@inmuebles_bp.route("/inmuebles/<int:pid>")
def inmuebles_detalle(pid):
    prop = rdb.get_propiedad(pid)
    if not prop:
        flash("Propiedad no encontrada.", "danger")
        return redirect(url_for("inmuebles.inmuebles_lista"))
    archivos = rdb.listar_archivos(pid)
    fotos = [a for a in archivos if a["tipo"] == "foto"]
    pdfs  = [a for a in archivos if a["tipo"] == "pdf"]
    publicaciones = rdb.listar_publicaciones(propiedad_id=pid)
    leads = rdb.listar_leads()
    leads = [l for l in leads if l.get("propiedad_id") == pid]
    rag_estado = rdb.get_rag_estado(pid)
    try:
        caract = json.loads(prop.get("caracteristicas") or "[]")
    except Exception:
        caract = []
    return render_template("inmuebles/detalle.html",
                           prop=prop, fotos=fotos, pdfs=pdfs,
                           publicaciones=publicaciones, leads=leads,
                           rag_estado=rag_estado, caract=caract)


# ── Editar ────────────────────────────────────────────────────────────────────

@inmuebles_bp.route("/inmuebles/<int:pid>/editar", methods=["GET", "POST"])
def inmuebles_editar(pid):
    prop = rdb.get_propiedad(pid)
    if not prop:
        flash("Propiedad no encontrada.", "danger")
        return redirect(url_for("inmuebles.inmuebles_lista"))
    if request.method == "POST":
        data = request.form.to_dict()
        data["caracteristicas"] = json.dumps(
            request.form.getlist("caracteristicas"), ensure_ascii=False
        )
        rdb.actualizar_propiedad(pid, data)
        # Reindexar en background si ya estaba indexado
        if rdb.get_rag_estado(pid) == "indexado":
            try:
                from rag_engine import index_property
                threading.Thread(target=index_property, args=(pid,), daemon=True).start()
            except Exception:
                pass
        flash("Propiedad actualizada.", "success")
        return redirect(url_for("inmuebles.inmuebles_detalle", pid=pid))
    try:
        caract = json.loads(prop.get("caracteristicas") or "[]")
    except Exception:
        caract = []
    return render_template("inmuebles/editar.html", prop=prop, caract=caract)


# ── Upload archivos ───────────────────────────────────────────────────────────

@inmuebles_bp.route("/inmuebles/<int:pid>/archivos", methods=["POST"])
def inmuebles_subir_archivo(pid):
    prop = rdb.get_propiedad(pid)
    if not prop:
        return jsonify({"error": "No encontrado"}), 404
    archivos_subidos = []
    fotos = request.files.getlist("fotos")
    pdfs  = request.files.getlist("pdfs")
    archivos_existentes = rdb.listar_archivos(pid)
    tiene_portada = any(a["es_portada"] for a in archivos_existentes if a["tipo"] == "foto")
    for f in fotos:
        if f and f.filename and _ext(f.filename) in ALLOWED_FOTO:
            nombre = _save_file(f, "fotos")
            aid = rdb.crear_archivo(pid, "foto", nombre, f.filename,
                                    es_portada=0 if tiene_portada else 1)
            tiene_portada = True
            archivos_subidos.append({"id": aid, "tipo": "foto", "nombre": nombre})
    for f in pdfs:
        if f and f.filename and _ext(f.filename) in ALLOWED_PDF:
            nombre = _save_file(f, "pdfs")
            aid = rdb.crear_archivo(pid, "pdf", nombre, f.filename)
            archivos_subidos.append({"id": aid, "tipo": "pdf", "nombre": nombre})
    flash(f"{len(archivos_subidos)} archivo(s) subido(s).", "success")
    return redirect(url_for("inmuebles.inmuebles_detalle", pid=pid))


@inmuebles_bp.route("/inmuebles/<int:pid>/archivos/<int:aid>/eliminar", methods=["POST"])
def inmuebles_eliminar_archivo(pid, aid):
    archivo = rdb.get_archivo(aid)
    if archivo:
        subfolder = "fotos" if archivo["tipo"] == "foto" else "pdfs"
        filepath = os.path.join(
            current_app.root_path, "static", "uploads", subfolder, archivo["nombre_archivo"]
        )
        if os.path.exists(filepath):
            os.remove(filepath)
        rdb.eliminar_archivo(aid)
        flash("Archivo eliminado.", "success")
    return redirect(url_for("inmuebles.inmuebles_detalle", pid=pid))


@inmuebles_bp.route("/inmuebles/<int:pid>/portada/<int:aid>", methods=["POST"])
def inmuebles_set_portada(pid, aid):
    rdb.set_portada(pid, aid)
    return redirect(url_for("inmuebles.inmuebles_detalle", pid=pid))


# ── Estado rápido ─────────────────────────────────────────────────────────────

@inmuebles_bp.route("/inmuebles/<int:pid>/estado", methods=["POST"])
def inmuebles_cambiar_estado(pid):
    estado = request.form.get("estado", "Disponible")
    rdb.cambiar_estado_propiedad(pid, estado)
    flash(f"Estado cambiado a {estado}.", "success")
    return redirect(url_for("inmuebles.inmuebles_detalle", pid=pid))


# ── Indexar para chatbot ──────────────────────────────────────────────────────

@inmuebles_bp.route("/inmuebles/<int:pid>/indexar", methods=["POST"])
def inmuebles_indexar(pid):
    prop = rdb.get_propiedad(pid)
    if not prop:
        return jsonify({"error": "No encontrado"}), 404
    rdb.upsert_rag_doc(pid, prop["titulo"], 0, "indexando")
    def _do_index():
        try:
            from rag_engine import index_property
            index_property(pid)
        except Exception as e:
            rdb.upsert_rag_doc(pid, prop["titulo"], 0, "error")
    threading.Thread(target=_do_index, daemon=True).start()
    return jsonify({"status": "indexando"})


@inmuebles_bp.route("/inmuebles/<int:pid>/rag_estado")
def inmuebles_rag_estado(pid):
    return jsonify({"estado": rdb.get_rag_estado(pid)})


# ── Publicar en Facebook ──────────────────────────────────────────────────────

@inmuebles_bp.route("/inmuebles/<int:pid>/publicar", methods=["GET", "POST"])
def inmuebles_publicar(pid):
    prop = rdb.get_propiedad(pid)
    if not prop:
        flash("Propiedad no encontrada.", "danger")
        return redirect(url_for("inmuebles.inmuebles_lista"))
    if request.method == "POST":
        plataforma = request.form.get("plataforma", "facebook_marketplace")
        # Si es una petición AJAX de generación
        if request.is_json or request.form.get("action") == "generar":
            try:
                from facebook_generator import generar_publicacion
                resultado = generar_publicacion(dict(prop), plataforma)
                return jsonify({"ok": True, "resultado": resultado})
            except Exception as e:
                return jsonify({"ok": False, "error": str(e)}), 500
        # Si es guardar borrador
        data = {
            "propiedad_id": pid,
            "plataforma": request.form.get("plataforma", "facebook_marketplace"),
            "titulo_post": request.form.get("titulo_post", ""),
            "contenido_texto": request.form.get("contenido_texto", ""),
            "hashtags": request.form.get("hashtags", ""),
            "llamada_accion": request.form.get("llamada_accion", ""),
            "estado": "Borrador",
        }
        rdb.crear_publicacion(data)
        flash("Publicación guardada como borrador.", "success")
        return redirect(url_for("inmuebles.inmuebles_detalle", pid=pid))
    publicaciones_prev = rdb.listar_publicaciones(propiedad_id=pid)
    return render_template("inmuebles/publicar.html",
                           prop=prop, publicaciones_prev=publicaciones_prev)


# ── Lista publicaciones ───────────────────────────────────────────────────────

@inmuebles_bp.route("/publicaciones/")
def publicaciones_lista():
    estado = request.args.get("estado", "")
    pubs = rdb.listar_publicaciones(estado=estado or None)
    return render_template("publicaciones/lista.html", pubs=pubs, filtro_estado=estado)


@inmuebles_bp.route("/publicaciones/<int:pub_id>/marcar_publicado", methods=["POST"])
def publicaciones_marcar_publicado(pub_id):
    rdb.marcar_publicado(pub_id)
    flash("Publicación marcada como publicada.", "success")
    return redirect(url_for("inmuebles.publicaciones_lista"))


# ── Leads ─────────────────────────────────────────────────────────────────────

@inmuebles_bp.route("/leads/")
def leads_lista():
    estado = request.args.get("estado", "")
    leads = rdb.listar_leads(estado=estado or None)
    return render_template("leads/lista.html", leads=leads, filtro_estado=estado)


@inmuebles_bp.route("/leads/<int:lead_id>/estado", methods=["POST"])
def leads_actualizar_estado(lead_id):
    estado = request.form.get("estado", "Nuevo")
    notas  = request.form.get("notas", "")
    rdb.actualizar_estado_lead(lead_id, estado, notas)
    return jsonify({"ok": True})


# ── API ───────────────────────────────────────────────────────────────────────

@inmuebles_bp.route("/inmuebles/api/lista")
def api_inmuebles_lista():
    props = rdb.listar_propiedades(filtro_estado="Disponible")
    return jsonify(props)
