import sqlite3
import json
from datetime import datetime

DB_PATH = "mantenimiento.db"


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_realestate_db():
    with _conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS propiedades (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo              TEXT    NOT NULL UNIQUE,
            titulo              TEXT    NOT NULL,
            tipo                TEXT    NOT NULL,
            operacion           TEXT    NOT NULL,
            precio              REAL,
            moneda              TEXT    NOT NULL DEFAULT 'USD',
            dormitorios         INTEGER DEFAULT 0,
            banos               INTEGER DEFAULT 0,
            area_m2             REAL,
            area_terreno_m2     REAL,
            distrito            TEXT,
            provincia           TEXT,
            departamento        TEXT,
            direccion           TEXT,
            descripcion         TEXT,
            caracteristicas     TEXT,
            estado              TEXT    NOT NULL DEFAULT 'Disponible',
            destacado           INTEGER NOT NULL DEFAULT 0,
            fecha_ingreso       TEXT    NOT NULL,
            fecha_actualizacion TEXT
        );

        CREATE TABLE IF NOT EXISTS propiedad_archivos (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            propiedad_id    INTEGER NOT NULL REFERENCES propiedades(id) ON DELETE CASCADE,
            tipo            TEXT    NOT NULL,
            nombre_archivo  TEXT    NOT NULL,
            nombre_original TEXT,
            es_portada      INTEGER DEFAULT 0,
            orden           INTEGER DEFAULT 0,
            fecha_subida    TEXT    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS publicaciones (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            propiedad_id        INTEGER NOT NULL REFERENCES propiedades(id),
            plataforma          TEXT    NOT NULL,
            contenido_texto     TEXT    NOT NULL,
            hashtags            TEXT,
            titulo_post         TEXT,
            llamada_accion      TEXT,
            notas_adicionales   TEXT,
            estado              TEXT    NOT NULL DEFAULT 'Borrador',
            fecha_generacion    TEXT    NOT NULL,
            fecha_publicacion   TEXT,
            publicado_por       TEXT
        );

        CREATE TABLE IF NOT EXISTS leads (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            propiedad_id    INTEGER REFERENCES propiedades(id),
            nombre          TEXT,
            telefono        TEXT,
            email           TEXT,
            mensaje         TEXT,
            origen          TEXT    NOT NULL DEFAULT 'chatbot',
            estado          TEXT    NOT NULL DEFAULT 'Nuevo',
            fecha_contacto  TEXT    NOT NULL,
            notas           TEXT
        );

        CREATE TABLE IF NOT EXISTS chat_sesiones (
            id                      INTEGER PRIMARY KEY AUTOINCREMENT,
            session_token           TEXT    NOT NULL UNIQUE,
            nombre_cliente          TEXT,
            fecha_inicio            TEXT    NOT NULL,
            fecha_ultimo_mensaje    TEXT
        );

        CREATE TABLE IF NOT EXISTS chat_mensajes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            sesion_id   INTEGER NOT NULL REFERENCES chat_sesiones(id),
            rol         TEXT    NOT NULL,
            contenido   TEXT    NOT NULL,
            timestamp   TEXT    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS rag_documentos (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            propiedad_id    INTEGER REFERENCES propiedades(id) ON DELETE CASCADE,
            nombre          TEXT    NOT NULL,
            chunks_count    INTEGER DEFAULT 0,
            estado_indexado TEXT    NOT NULL DEFAULT 'pendiente',
            fecha_indexado  TEXT
        );
        """)


# ── Propiedades ──────────────────────────────────────────────────────────────

def _gen_codigo():
    with _conn() as conn:
        row = conn.execute("SELECT MAX(id) as m FROM propiedades").fetchone()
        n = (row["m"] or 0) + 1
        return f"PROP-{n:04d}"


def crear_propiedad(data: dict) -> int:
    codigo = _gen_codigo()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    caract = data.get("caracteristicas", "[]")
    if isinstance(caract, list):
        caract = json.dumps(caract, ensure_ascii=False)
    with _conn() as conn:
        cur = conn.execute("""
            INSERT INTO propiedades
              (codigo, titulo, tipo, operacion, precio, moneda,
               dormitorios, banos, area_m2, area_terreno_m2,
               distrito, provincia, departamento, direccion,
               descripcion, caracteristicas, estado, destacado, fecha_ingreso)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            codigo,
            data.get("titulo", ""),
            data.get("tipo", "Casa"),
            data.get("operacion", "Venta"),
            data.get("precio") or None,
            data.get("moneda", "USD"),
            int(data.get("dormitorios") or 0),
            int(data.get("banos") or 0),
            data.get("area_m2") or None,
            data.get("area_terreno_m2") or None,
            data.get("distrito", ""),
            data.get("provincia", ""),
            data.get("departamento", ""),
            data.get("direccion", ""),
            data.get("descripcion", ""),
            caract,
            data.get("estado", "Disponible"),
            int(data.get("destacado", 0)),
            now,
        ))
        return cur.lastrowid


def listar_propiedades(filtro_tipo=None, filtro_operacion=None, filtro_estado=None):
    sql = """
        SELECT p.*,
               (SELECT nombre_archivo FROM propiedad_archivos
                WHERE propiedad_id = p.id AND tipo='foto' AND es_portada=1
                LIMIT 1) AS foto_portada
        FROM propiedades p WHERE 1=1
    """
    params = []
    if filtro_tipo:
        sql += " AND p.tipo = ?"
        params.append(filtro_tipo)
    if filtro_operacion:
        sql += " AND p.operacion = ?"
        params.append(filtro_operacion)
    if filtro_estado:
        sql += " AND p.estado = ?"
        params.append(filtro_estado)
    sql += " ORDER BY p.destacado DESC, p.fecha_ingreso DESC"
    with _conn() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def get_propiedad(pid: int) -> dict | None:
    with _conn() as conn:
        row = conn.execute("SELECT * FROM propiedades WHERE id=?", (pid,)).fetchone()
        return dict(row) if row else None


def actualizar_propiedad(pid: int, data: dict):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    caract = data.get("caracteristicas", "[]")
    if isinstance(caract, list):
        caract = json.dumps(caract, ensure_ascii=False)
    with _conn() as conn:
        conn.execute("""
            UPDATE propiedades SET
              titulo=?, tipo=?, operacion=?, precio=?, moneda=?,
              dormitorios=?, banos=?, area_m2=?, area_terreno_m2=?,
              distrito=?, provincia=?, departamento=?, direccion=?,
              descripcion=?, caracteristicas=?, estado=?, destacado=?,
              fecha_actualizacion=?
            WHERE id=?
        """, (
            data.get("titulo", ""),
            data.get("tipo", "Casa"),
            data.get("operacion", "Venta"),
            data.get("precio") or None,
            data.get("moneda", "USD"),
            int(data.get("dormitorios") or 0),
            int(data.get("banos") or 0),
            data.get("area_m2") or None,
            data.get("area_terreno_m2") or None,
            data.get("distrito", ""),
            data.get("provincia", ""),
            data.get("departamento", ""),
            data.get("direccion", ""),
            data.get("descripcion", ""),
            caract,
            data.get("estado", "Disponible"),
            int(data.get("destacado", 0)),
            now,
            pid,
        ))


def cambiar_estado_propiedad(pid: int, estado: str):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _conn() as conn:
        conn.execute(
            "UPDATE propiedades SET estado=?, fecha_actualizacion=? WHERE id=?",
            (estado, now, pid)
        )


def kpi_propiedades() -> dict:
    with _conn() as conn:
        total = conn.execute("SELECT COUNT(*) FROM propiedades").fetchone()[0]
        disponibles = conn.execute(
            "SELECT COUNT(*) FROM propiedades WHERE estado='Disponible'"
        ).fetchone()[0]
        reservados = conn.execute(
            "SELECT COUNT(*) FROM propiedades WHERE estado='Reservado'"
        ).fetchone()[0]
        vendidos = conn.execute(
            "SELECT COUNT(*) FROM propiedades WHERE estado='Vendido'"
        ).fetchone()[0]
        leads_nuevos = conn.execute(
            "SELECT COUNT(*) FROM leads WHERE estado='Nuevo'"
        ).fetchone()[0]
    return {
        "total": total,
        "disponibles": disponibles,
        "reservados": reservados,
        "vendidos": vendidos,
        "leads_nuevos": leads_nuevos,
    }


# ── Archivos ─────────────────────────────────────────────────────────────────

def crear_archivo(propiedad_id: int, tipo: str, nombre_archivo: str,
                  nombre_original: str, es_portada: int = 0) -> int:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _conn() as conn:
        cur = conn.execute("""
            INSERT INTO propiedad_archivos
              (propiedad_id, tipo, nombre_archivo, nombre_original, es_portada, fecha_subida)
            VALUES (?,?,?,?,?,?)
        """, (propiedad_id, tipo, nombre_archivo, nombre_original, es_portada, now))
        return cur.lastrowid


def listar_archivos(propiedad_id: int) -> list:
    with _conn() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM propiedad_archivos WHERE propiedad_id=? ORDER BY es_portada DESC, orden, id",
            (propiedad_id,)
        ).fetchall()]


def get_archivo(archivo_id: int) -> dict | None:
    with _conn() as conn:
        row = conn.execute("SELECT * FROM propiedad_archivos WHERE id=?", (archivo_id,)).fetchone()
        return dict(row) if row else None


def eliminar_archivo(archivo_id: int):
    with _conn() as conn:
        conn.execute("DELETE FROM propiedad_archivos WHERE id=?", (archivo_id,))


def set_portada(propiedad_id: int, archivo_id: int):
    with _conn() as conn:
        conn.execute(
            "UPDATE propiedad_archivos SET es_portada=0 WHERE propiedad_id=?",
            (propiedad_id,)
        )
        conn.execute(
            "UPDATE propiedad_archivos SET es_portada=1 WHERE id=?",
            (archivo_id,)
        )


# ── Publicaciones ─────────────────────────────────────────────────────────────

def crear_publicacion(data: dict) -> int:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _conn() as conn:
        cur = conn.execute("""
            INSERT INTO publicaciones
              (propiedad_id, plataforma, contenido_texto, hashtags,
               titulo_post, llamada_accion, notas_adicionales, estado, fecha_generacion)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            data["propiedad_id"],
            data["plataforma"],
            data.get("contenido_texto", ""),
            data.get("hashtags", ""),
            data.get("titulo_post", ""),
            data.get("llamada_accion", ""),
            data.get("notas_adicionales", ""),
            data.get("estado", "Borrador"),
            now,
        ))
        return cur.lastrowid


def listar_publicaciones(propiedad_id=None, estado=None):
    sql = """
        SELECT pub.*, p.titulo AS propiedad_titulo, p.codigo AS propiedad_codigo
        FROM publicaciones pub
        JOIN propiedades p ON p.id = pub.propiedad_id
        WHERE 1=1
    """
    params = []
    if propiedad_id:
        sql += " AND pub.propiedad_id=?"
        params.append(propiedad_id)
    if estado:
        sql += " AND pub.estado=?"
        params.append(estado)
    sql += " ORDER BY pub.fecha_generacion DESC"
    with _conn() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def marcar_publicado(pub_id: int):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _conn() as conn:
        conn.execute(
            "UPDATE publicaciones SET estado='Publicado', fecha_publicacion=? WHERE id=?",
            (now, pub_id)
        )


# ── Leads ─────────────────────────────────────────────────────────────────────

def crear_lead(data: dict) -> int:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _conn() as conn:
        cur = conn.execute("""
            INSERT INTO leads
              (propiedad_id, nombre, telefono, email, mensaje, origen, estado, fecha_contacto)
            VALUES (?,?,?,?,?,?,?,?)
        """, (
            data.get("propiedad_id"),
            data.get("nombre", ""),
            data.get("telefono", ""),
            data.get("email", ""),
            data.get("mensaje", ""),
            data.get("origen", "chatbot"),
            "Nuevo",
            now,
        ))
        return cur.lastrowid


def listar_leads(estado=None):
    sql = """
        SELECT l.*, p.titulo AS propiedad_titulo
        FROM leads l
        LEFT JOIN propiedades p ON p.id = l.propiedad_id
        WHERE 1=1
    """
    params = []
    if estado:
        sql += " AND l.estado=?"
        params.append(estado)
    sql += " ORDER BY l.fecha_contacto DESC"
    with _conn() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def actualizar_estado_lead(lead_id: int, estado: str, notas: str = ""):
    with _conn() as conn:
        conn.execute(
            "UPDATE leads SET estado=?, notas=? WHERE id=?",
            (estado, notas, lead_id)
        )


# ── Chat ──────────────────────────────────────────────────────────────────────

def crear_sesion(token: str) -> int:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _conn() as conn:
        cur = conn.execute(
            "INSERT INTO chat_sesiones (session_token, fecha_inicio) VALUES (?,?)",
            (token, now)
        )
        return cur.lastrowid


def get_sesion(token: str) -> dict | None:
    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM chat_sesiones WHERE session_token=?", (token,)
        ).fetchone()
        return dict(row) if row else None


def guardar_mensaje(sesion_id: int, rol: str, contenido: str):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _conn() as conn:
        conn.execute(
            "INSERT INTO chat_mensajes (sesion_id, rol, contenido, timestamp) VALUES (?,?,?,?)",
            (sesion_id, rol, contenido, now)
        )
        conn.execute(
            "UPDATE chat_sesiones SET fecha_ultimo_mensaje=? WHERE id=?",
            (now, sesion_id)
        )


def get_historial(sesion_id: int, limite: int = 20) -> list:
    with _conn() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM chat_mensajes WHERE sesion_id=? ORDER BY id DESC LIMIT ?",
            (sesion_id, limite)
        ).fetchall()][::-1]


# ── RAG docs ──────────────────────────────────────────────────────────────────

def upsert_rag_doc(propiedad_id: int, nombre: str, chunks: int, estado: str):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _conn() as conn:
        existing = conn.execute(
            "SELECT id FROM rag_documentos WHERE propiedad_id=?", (propiedad_id,)
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE rag_documentos SET nombre=?, chunks_count=?, estado_indexado=?, fecha_indexado=? WHERE propiedad_id=?",
                (nombre, chunks, estado, now, propiedad_id)
            )
        else:
            conn.execute(
                "INSERT INTO rag_documentos (propiedad_id, nombre, chunks_count, estado_indexado, fecha_indexado) VALUES (?,?,?,?,?)",
                (propiedad_id, nombre, chunks, estado, now)
            )


def get_rag_estado(propiedad_id: int) -> str:
    with _conn() as conn:
        row = conn.execute(
            "SELECT estado_indexado FROM rag_documentos WHERE propiedad_id=?",
            (propiedad_id,)
        ).fetchone()
        return row[0] if row else "pendiente"
