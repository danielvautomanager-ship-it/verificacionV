import sqlite3
from datetime import datetime

DB_PATH = "mantenimiento.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.executescript("""
        CREATE TABLE IF NOT EXISTS equipos (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo      TEXT    NOT NULL UNIQUE,
            nombre      TEXT    NOT NULL,
            area        TEXT    NOT NULL,
            tipo        TEXT    NOT NULL,
            criticidad  TEXT    NOT NULL DEFAULT 'Media',
            estado      TEXT    NOT NULL DEFAULT 'Operativo',
            fecha_alta  TEXT    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS tecnicos (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo      TEXT    NOT NULL UNIQUE,
            nombre      TEXT    NOT NULL,
            especialidad TEXT   NOT NULL,
            turno       TEXT    NOT NULL,
            activo      INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS ordenes_servicio (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            numero          TEXT    NOT NULL UNIQUE,
            tipo            TEXT    NOT NULL,
            prioridad       TEXT    NOT NULL DEFAULT 'Media',
            estado          TEXT    NOT NULL DEFAULT 'Pendiente',
            equipo_id       INTEGER NOT NULL REFERENCES equipos(id),
            tecnico_id      INTEGER REFERENCES tecnicos(id),
            descripcion     TEXT    NOT NULL,
            diagnostico     TEXT,
            accion_tomada   TEXT,
            fecha_apertura  TEXT    NOT NULL,
            fecha_inicio    TEXT,
            fecha_cierre    TEXT,
            tiempo_parada   REAL    DEFAULT 0,
            costo           REAL    DEFAULT 0,
            observaciones   TEXT
        );

        CREATE TABLE IF NOT EXISTS historial_estados (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            os_id       INTEGER NOT NULL REFERENCES ordenes_servicio(id),
            estado      TEXT    NOT NULL,
            fecha       TEXT    NOT NULL,
            comentario  TEXT
        );
    """)

    # Demo data
    c.execute("SELECT COUNT(*) FROM equipos")
    if c.fetchone()[0] == 0:
        hoy = datetime.now().strftime("%Y-%m-%d")
        equipos = [
            ("EQ-001", "Compresor Atlas Copco GA110", "Produccion", "Compresor", "Alta", "Operativo", hoy),
            ("EQ-002", "Bomba Centrifuga KSB 65-200", "Planta", "Bomba", "Alta", "Operativo", hoy),
            ("EQ-003", "Faja Transportadora #3", "Almacen", "Transportador", "Media", "Operativo", hoy),
            ("EQ-004", "Chiller York YK-500", "Utilidades", "Enfriador", "Alta", "En Mantenimiento", hoy),
            ("EQ-005", "Generador Caterpillar 500KVA", "Energia", "Generador", "Critica", "Operativo", hoy),
        ]
        c.executemany(
            "INSERT INTO equipos (codigo,nombre,area,tipo,criticidad,estado,fecha_alta) VALUES (?,?,?,?,?,?,?)",
            equipos,
        )

        tecnicos = [
            ("TEC-001", "Carlos Mendoza", "Mecanica", "Mañana", 1),
            ("TEC-002", "Juan Perez", "Electrica", "Tarde", 1),
            ("TEC-003", "Luis Torres", "Instrumentacion", "Mañana", 1),
            ("TEC-004", "Maria Garcia", "Mecanica", "Noche", 1),
        ]
        c.executemany(
            "INSERT INTO tecnicos (codigo,nombre,especialidad,turno,activo) VALUES (?,?,?,?,?)",
            tecnicos,
        )

        import random
        estados = ["Cerrada", "Cerrada", "Cerrada", "En Proceso", "Pendiente"]
        tipos = ["Correctivo", "Preventivo", "Correctivo", "Preventivo", "Predictivo"]
        prioridades = ["Alta", "Media", "Critica", "Media", "Baja"]
        for i in range(1, 21):
            estado = random.choice(estados)
            tipo = random.choice(tipos)
            prioridad = random.choice(prioridades)
            equipo_id = random.randint(1, 5)
            tecnico_id = random.randint(1, 4)
            dias_atras = random.randint(1, 90)
            from datetime import timedelta
            fecha_ap = (datetime.now() - timedelta(days=dias_atras)).strftime("%Y-%m-%d %H:%M")
            fecha_ini = (datetime.now() - timedelta(days=dias_atras - 1)).strftime("%Y-%m-%d %H:%M") if estado != "Pendiente" else None
            horas = random.uniform(1, 24) if estado == "Cerrada" else None
            fecha_cie = (datetime.now() - timedelta(days=dias_atras - 2)).strftime("%Y-%m-%d %H:%M") if estado == "Cerrada" else None
            costo = round(random.uniform(50, 2000), 2) if estado == "Cerrada" else 0
            c.execute(
                """INSERT INTO ordenes_servicio
                   (numero,tipo,prioridad,estado,equipo_id,tecnico_id,descripcion,
                    fecha_apertura,fecha_inicio,fecha_cierre,tiempo_parada,costo)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    f"OS-{i:04d}", tipo, prioridad, estado, equipo_id, tecnico_id,
                    f"Mantenimiento {tipo.lower()} - Tarea #{i}",
                    fecha_ap, fecha_ini, fecha_cie,
                    round(horas, 2) if horas else 0, costo,
                ),
            )

    conn.commit()
    conn.close()


# ── KPIs ──────────────────────────────────────────────────────────────────────

def kpi_resumen():
    conn = get_db()
    c = conn.cursor()
    totales = dict(c.execute(
        "SELECT estado, COUNT(*) FROM ordenes_servicio GROUP BY estado"
    ).fetchall())
    total = sum(totales.values())
    cerradas = totales.get("Cerrada", 0)
    en_proceso = totales.get("En Proceso", 0)
    pendientes = totales.get("Pendiente", 0)

    mttr_row = c.execute(
        "SELECT AVG(tiempo_parada) FROM ordenes_servicio WHERE estado='Cerrada' AND tiempo_parada > 0"
    ).fetchone()
    mttr = round(mttr_row[0] or 0, 2)

    costo_row = c.execute(
        "SELECT SUM(costo) FROM ordenes_servicio WHERE estado='Cerrada'"
    ).fetchone()
    costo_total = round(costo_row[0] or 0, 2)

    tipos = dict(c.execute(
        "SELECT tipo, COUNT(*) FROM ordenes_servicio GROUP BY tipo"
    ).fetchall())

    conn.close()
    return {
        "total": total,
        "cerradas": cerradas,
        "en_proceso": en_proceso,
        "pendientes": pendientes,
        "mttr": mttr,
        "costo_total": costo_total,
        "tipos": tipos,
        "tasa_cierre": round((cerradas / total * 100) if total else 0, 1),
    }


def kpi_por_mes():
    conn = get_db()
    rows = conn.execute(
        """SELECT strftime('%Y-%m', fecha_apertura) as mes,
                  COUNT(*) as total,
                  SUM(CASE WHEN estado='Cerrada' THEN 1 ELSE 0 END) as cerradas,
                  AVG(CASE WHEN estado='Cerrada' AND tiempo_parada>0 THEN tiempo_parada END) as mttr
           FROM ordenes_servicio
           GROUP BY mes ORDER BY mes DESC LIMIT 6"""
    ).fetchall()
    conn.close()
    return [dict(r) for r in reversed(rows)]


def kpi_disponibilidad():
    conn = get_db()
    rows = conn.execute(
        """SELECT e.nombre,
                  SUM(os.tiempo_parada) as horas_parada,
                  COUNT(os.id) as total_os
           FROM equipos e
           LEFT JOIN ordenes_servicio os ON os.equipo_id = e.id
           GROUP BY e.id ORDER BY horas_parada DESC"""
    ).fetchall()
    conn.close()
    horas_mes = 720
    result = []
    for r in rows:
        parada = r["horas_parada"] or 0
        disp = round(max(0, (horas_mes - parada) / horas_mes * 100), 1)
        result.append({"nombre": r["nombre"], "disponibilidad": disp, "horas_parada": round(parada, 1)})
    return result


# ── CRUD Órdenes ──────────────────────────────────────────────────────────────

def listar_os(filtro_estado=None, filtro_tipo=None, filtro_equipo=None):
    conn = get_db()
    sql = """SELECT os.*, e.nombre as equipo_nombre, t.nombre as tecnico_nombre
             FROM ordenes_servicio os
             JOIN equipos e ON e.id = os.equipo_id
             LEFT JOIN tecnicos t ON t.id = os.tecnico_id
             WHERE 1=1"""
    params = []
    if filtro_estado:
        sql += " AND os.estado = ?"; params.append(filtro_estado)
    if filtro_tipo:
        sql += " AND os.tipo = ?"; params.append(filtro_tipo)
    if filtro_equipo:
        sql += " AND os.equipo_id = ?"; params.append(filtro_equipo)
    sql += " ORDER BY os.id DESC"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_os(os_id):
    conn = get_db()
    row = conn.execute(
        """SELECT os.*, e.nombre as equipo_nombre, t.nombre as tecnico_nombre
           FROM ordenes_servicio os
           JOIN equipos e ON e.id = os.equipo_id
           LEFT JOIN tecnicos t ON t.id = os.tecnico_id
           WHERE os.id = ?""", (os_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def crear_os(data):
    conn = get_db()
    c = conn.cursor()
    count = c.execute("SELECT COUNT(*) FROM ordenes_servicio").fetchone()[0]
    numero = f"OS-{count + 1:04d}"
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
    c.execute(
        """INSERT INTO ordenes_servicio
           (numero,tipo,prioridad,estado,equipo_id,tecnico_id,descripcion,observaciones,fecha_apertura)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (numero, data["tipo"], data["prioridad"], "Pendiente",
         data["equipo_id"], data.get("tecnico_id") or None,
         data["descripcion"], data.get("observaciones", ""), fecha),
    )
    os_id = c.lastrowid
    c.execute(
        "INSERT INTO historial_estados (os_id,estado,fecha,comentario) VALUES (?,?,?,?)",
        (os_id, "Pendiente", fecha, "OS creada"),
    )
    conn.commit()
    conn.close()
    return os_id


def actualizar_os(os_id, data):
    conn = get_db()
    c = conn.cursor()
    os_actual = dict(c.execute("SELECT * FROM ordenes_servicio WHERE id=?", (os_id,)).fetchone())
    nuevo_estado = data.get("estado", os_actual["estado"])
    fecha_inicio = os_actual["fecha_inicio"]
    fecha_cierre = os_actual["fecha_cierre"]
    if nuevo_estado == "En Proceso" and not fecha_inicio:
        fecha_inicio = datetime.now().strftime("%Y-%m-%d %H:%M")
    if nuevo_estado == "Cerrada" and not fecha_cierre:
        fecha_cierre = datetime.now().strftime("%Y-%m-%d %H:%M")
    c.execute(
        """UPDATE ordenes_servicio SET
           tipo=?, prioridad=?, estado=?, tecnico_id=?,
           diagnostico=?, accion_tomada=?, fecha_inicio=?,
           fecha_cierre=?, tiempo_parada=?, costo=?, observaciones=?
           WHERE id=?""",
        (data.get("tipo", os_actual["tipo"]),
         data.get("prioridad", os_actual["prioridad"]),
         nuevo_estado,
         data.get("tecnico_id") or os_actual["tecnico_id"],
         data.get("diagnostico", ""), data.get("accion_tomada", ""),
         fecha_inicio, fecha_cierre,
         float(data.get("tiempo_parada") or 0),
         float(data.get("costo") or 0),
         data.get("observaciones", ""),
         os_id),
    )
    if nuevo_estado != os_actual["estado"]:
        c.execute(
            "INSERT INTO historial_estados (os_id,estado,fecha,comentario) VALUES (?,?,?,?)",
            (os_id, nuevo_estado, datetime.now().strftime("%Y-%m-%d %H:%M"),
             data.get("comentario_estado", "")),
        )
    conn.commit()
    conn.close()


# ── CRUD Equipos ──────────────────────────────────────────────────────────────

def listar_equipos():
    conn = get_db()
    rows = conn.execute("SELECT * FROM equipos ORDER BY codigo").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_equipo(equipo_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM equipos WHERE id=?", (equipo_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def crear_equipo(data):
    conn = get_db()
    fecha = datetime.now().strftime("%Y-%m-%d")
    conn.execute(
        "INSERT INTO equipos (codigo,nombre,area,tipo,criticidad,estado,fecha_alta) VALUES (?,?,?,?,?,?,?)",
        (data["codigo"], data["nombre"], data["area"], data["tipo"],
         data.get("criticidad", "Media"), data.get("estado", "Operativo"), fecha),
    )
    conn.commit()
    conn.close()


def actualizar_equipo(equipo_id, data):
    conn = get_db()
    conn.execute(
        "UPDATE equipos SET nombre=?,area=?,tipo=?,criticidad=?,estado=? WHERE id=?",
        (data["nombre"], data["area"], data["tipo"],
         data.get("criticidad", "Media"), data.get("estado", "Operativo"), equipo_id),
    )
    conn.commit()
    conn.close()


# ── CRUD Técnicos ─────────────────────────────────────────────────────────────

def listar_tecnicos(solo_activos=False):
    conn = get_db()
    sql = "SELECT * FROM tecnicos"
    if solo_activos:
        sql += " WHERE activo=1"
    sql += " ORDER BY nombre"
    rows = conn.execute(sql).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def crear_tecnico(data):
    conn = get_db()
    conn.execute(
        "INSERT INTO tecnicos (codigo,nombre,especialidad,turno,activo) VALUES (?,?,?,?,1)",
        (data["codigo"], data["nombre"], data["especialidad"], data["turno"]),
    )
    conn.commit()
    conn.close()


def actualizar_tecnico(tec_id, data):
    conn = get_db()
    conn.execute(
        "UPDATE tecnicos SET nombre=?,especialidad=?,turno=?,activo=? WHERE id=?",
        (data["nombre"], data["especialidad"], data["turno"],
         int(data.get("activo", 1)), tec_id),
    )
    conn.commit()
    conn.close()
