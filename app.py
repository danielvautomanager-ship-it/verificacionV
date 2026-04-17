import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import database as db
import realestate_db as rdb
from blueprints.inmuebles import inmuebles_bp
from blueprints.chatbot import chatbot_bp

app = Flask(__name__)
app.secret_key = "erp-mantenimiento-2025"
app.config["UPLOAD_FOLDER"] = os.path.join("static", "uploads")
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024

db.init_db()
rdb.init_realestate_db()

app.register_blueprint(inmuebles_bp)
app.register_blueprint(chatbot_bp)

# ── Dashboard ─────────────────────────────────────────────────────────────────

@app.route("/")
def dashboard():
    kpi = db.kpi_resumen()
    por_mes = db.kpi_por_mes()
    disponibilidad = db.kpi_disponibilidad()
    os_recientes = db.listar_os()[:8]
    return render_template("dashboard.html",
                           kpi=kpi,
                           por_mes=por_mes,
                           disponibilidad=disponibilidad,
                           os_recientes=os_recientes)

@app.route("/api/kpi")
def api_kpi():
    return jsonify({
        "resumen": db.kpi_resumen(),
        "por_mes": db.kpi_por_mes(),
        "disponibilidad": db.kpi_disponibilidad(),
    })

# ── Órdenes de Servicio ───────────────────────────────────────────────────────

@app.route("/ordenes")
def ordenes_lista():
    filtro_estado = request.args.get("estado", "")
    filtro_tipo = request.args.get("tipo", "")
    filtro_equipo = request.args.get("equipo", "")
    ordenes = db.listar_os(
        filtro_estado or None,
        filtro_tipo or None,
        filtro_equipo or None,
    )
    equipos = db.listar_equipos()
    return render_template("ordenes/lista.html",
                           ordenes=ordenes,
                           equipos=equipos,
                           filtro_estado=filtro_estado,
                           filtro_tipo=filtro_tipo,
                           filtro_equipo=filtro_equipo)

@app.route("/ordenes/nueva", methods=["GET", "POST"])
def ordenes_nueva():
    equipos = db.listar_equipos()
    tecnicos = db.listar_tecnicos(solo_activos=True)
    if request.method == "POST":
        data = request.form.to_dict()
        os_id = db.crear_os(data)
        flash(f"Orden de servicio creada exitosamente.", "success")
        return redirect(url_for("ordenes_detalle", os_id=os_id))
    return render_template("ordenes/nueva.html", equipos=equipos, tecnicos=tecnicos)

@app.route("/ordenes/<int:os_id>")
def ordenes_detalle(os_id):
    orden = db.get_os(os_id)
    if not orden:
        flash("Orden no encontrada.", "danger")
        return redirect(url_for("ordenes_lista"))
    tecnicos = db.listar_tecnicos(solo_activos=True)
    return render_template("ordenes/detalle.html", orden=orden, tecnicos=tecnicos)

@app.route("/ordenes/<int:os_id>/editar", methods=["POST"])
def ordenes_editar(os_id):
    data = request.form.to_dict()
    db.actualizar_os(os_id, data)
    flash("Orden actualizada correctamente.", "success")
    return redirect(url_for("ordenes_detalle", os_id=os_id))

# ── Equipos ───────────────────────────────────────────────────────────────────

@app.route("/equipos")
def equipos_lista():
    equipos = db.listar_equipos()
    return render_template("equipos/lista.html", equipos=equipos)

@app.route("/equipos/nuevo", methods=["GET", "POST"])
def equipos_nuevo():
    if request.method == "POST":
        data = request.form.to_dict()
        try:
            db.crear_equipo(data)
            flash("Equipo registrado exitosamente.", "success")
            return redirect(url_for("equipos_lista"))
        except Exception as e:
            flash(f"Error: {e}", "danger")
    return render_template("equipos/form.html", equipo=None, titulo="Nuevo Equipo")

@app.route("/equipos/<int:equipo_id>/editar", methods=["GET", "POST"])
def equipos_editar(equipo_id):
    equipo = db.get_equipo(equipo_id)
    if not equipo:
        flash("Equipo no encontrado.", "danger")
        return redirect(url_for("equipos_lista"))
    if request.method == "POST":
        data = request.form.to_dict()
        db.actualizar_equipo(equipo_id, data)
        flash("Equipo actualizado.", "success")
        return redirect(url_for("equipos_lista"))
    return render_template("equipos/form.html", equipo=equipo, titulo="Editar Equipo")

# ── Técnicos ──────────────────────────────────────────────────────────────────

@app.route("/tecnicos")
def tecnicos_lista():
    tecnicos = db.listar_tecnicos()
    return render_template("tecnicos/lista.html", tecnicos=tecnicos)

@app.route("/tecnicos/nuevo", methods=["GET", "POST"])
def tecnicos_nuevo():
    if request.method == "POST":
        data = request.form.to_dict()
        try:
            db.crear_tecnico(data)
            flash("Técnico registrado exitosamente.", "success")
            return redirect(url_for("tecnicos_lista"))
        except Exception as e:
            flash(f"Error: {e}", "danger")
    return render_template("tecnicos/form.html", tecnico=None, titulo="Nuevo Técnico")

@app.route("/tecnicos/<int:tec_id>/editar", methods=["GET", "POST"])
def tecnicos_editar(tec_id):
    tecnicos = db.listar_tecnicos()
    tecnico = next((t for t in tecnicos if t["id"] == tec_id), None)
    if not tecnico:
        flash("Técnico no encontrado.", "danger")
        return redirect(url_for("tecnicos_lista"))
    if request.method == "POST":
        data = request.form.to_dict()
        db.actualizar_tecnico(tec_id, data)
        flash("Técnico actualizado.", "success")
        return redirect(url_for("tecnicos_lista"))
    return render_template("tecnicos/form.html", tecnico=tecnico, titulo="Editar Técnico")

# ── Reportes ──────────────────────────────────────────────────────────────────

@app.route("/reportes")
def reportes():
    kpi = db.kpi_resumen()
    por_mes = db.kpi_por_mes()
    disponibilidad = db.kpi_disponibilidad()
    return render_template("reportes/indicadores.html",
                           kpi=kpi,
                           por_mes=por_mes,
                           disponibilidad=disponibilidad)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
