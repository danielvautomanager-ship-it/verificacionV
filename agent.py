import json
import os
import anthropic
import database as db

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))

SYSTEM_PROMPT = """Eres un asistente experto en el sistema ERP de mantenimiento industrial.
Tienes acceso a herramientas para consultar órdenes de servicio, equipos, técnicos y KPIs.
Responde siempre en español, de forma clara y concisa.
Cuando el usuario pregunte sobre datos, usa las herramientas disponibles para obtener información actualizada.
Puedes ayudar con:
- Consultar y analizar órdenes de servicio (pendientes, en proceso, cerradas)
- Revisar el estado y disponibilidad de equipos
- Ver información de técnicos
- Analizar indicadores KPI de mantenimiento
- Generar resúmenes y recomendaciones basadas en los datos
"""

TOOLS = [
    {
        "name": "listar_ordenes",
        "description": "Lista las órdenes de servicio del sistema, con filtros opcionales por estado, tipo y equipo.",
        "input_schema": {
            "type": "object",
            "properties": {
                "estado": {
                    "type": "string",
                    "description": "Filtrar por estado: Pendiente, En Proceso, Cerrada, Cancelada",
                    "enum": ["Pendiente", "En Proceso", "Cerrada", "Cancelada"]
                },
                "tipo": {
                    "type": "string",
                    "description": "Filtrar por tipo: Correctivo, Preventivo, Predictivo",
                    "enum": ["Correctivo", "Preventivo", "Predictivo"]
                },
                "limite": {
                    "type": "integer",
                    "description": "Número máximo de órdenes a retornar (default 10)",
                    "default": 10
                }
            }
        }
    },
    {
        "name": "obtener_kpis",
        "description": "Obtiene los indicadores KPI de mantenimiento: total de órdenes, tasa de cierre, MTTR, costo total, distribución por tipo.",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "listar_equipos",
        "description": "Lista todos los equipos registrados con su estado actual, área y criticidad.",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "listar_tecnicos",
        "description": "Lista los técnicos disponibles con su especialidad y turno.",
        "input_schema": {
            "type": "object",
            "properties": {
                "solo_activos": {
                    "type": "boolean",
                    "description": "Si es true, retorna solo técnicos activos",
                    "default": True
                }
            }
        }
    },
    {
        "name": "obtener_disponibilidad",
        "description": "Obtiene el indicador de disponibilidad de cada equipo basado en horas de parada.",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "obtener_kpis_por_mes",
        "description": "Obtiene los KPIs agrupados por mes (últimos 6 meses): total de órdenes, cerradas y MTTR promedio.",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    }
]


def ejecutar_herramienta(nombre: str, parametros: dict) -> str:
    if nombre == "listar_ordenes":
        ordenes = db.listar_os(
            filtro_estado=parametros.get("estado"),
            filtro_tipo=parametros.get("tipo")
        )
        limite = parametros.get("limite", 10)
        ordenes = ordenes[:limite]
        if not ordenes:
            return "No se encontraron órdenes de servicio con los filtros especificados."
        filas = []
        for o in ordenes:
            filas.append(
                f"OS {o['numero']} | {o['tipo']} | Prioridad: {o['prioridad']} | "
                f"Estado: {o['estado']} | Equipo: {o['equipo_nombre']} | "
                f"Técnico: {o.get('tecnico_nombre') or 'Sin asignar'} | "
                f"Fecha: {o['fecha_apertura']}"
            )
        return f"Se encontraron {len(filas)} órdenes:\n" + "\n".join(filas)

    elif nombre == "obtener_kpis":
        kpi = db.kpi_resumen()
        return (
            f"KPIs de Mantenimiento:\n"
            f"- Total órdenes: {kpi['total']}\n"
            f"- Cerradas: {kpi['cerradas']} ({kpi['tasa_cierre']}%)\n"
            f"- En Proceso: {kpi['en_proceso']}\n"
            f"- Pendientes: {kpi['pendientes']}\n"
            f"- MTTR promedio: {kpi['mttr']} horas\n"
            f"- Costo total: S/. {kpi['costo_total']}\n"
            f"- Por tipo: {', '.join(f'{k}: {v}' for k, v in kpi['tipos'].items())}"
        )

    elif nombre == "listar_equipos":
        equipos = db.listar_equipos()
        if not equipos:
            return "No hay equipos registrados."
        filas = [
            f"{e['codigo']} | {e['nombre']} | Área: {e['area']} | "
            f"Tipo: {e['tipo']} | Criticidad: {e['criticidad']} | Estado: {e['estado']}"
            for e in equipos
        ]
        return f"{len(filas)} equipos registrados:\n" + "\n".join(filas)

    elif nombre == "listar_tecnicos":
        solo_activos = parametros.get("solo_activos", True)
        tecnicos = db.listar_tecnicos(solo_activos=solo_activos)
        if not tecnicos:
            return "No hay técnicos registrados."
        filas = [
            f"{t['codigo']} | {t['nombre']} | Especialidad: {t['especialidad']} | "
            f"Turno: {t['turno']} | {'Activo' if t['activo'] else 'Inactivo'}"
            for t in tecnicos
        ]
        return f"{len(filas)} técnicos:\n" + "\n".join(filas)

    elif nombre == "obtener_disponibilidad":
        datos = db.kpi_disponibilidad()
        if not datos:
            return "No hay datos de disponibilidad."
        filas = [
            f"{d['nombre']}: {d['disponibilidad']}% disponible ({d['horas_parada']}h parada)"
            for d in datos
        ]
        return "Disponibilidad por equipo:\n" + "\n".join(filas)

    elif nombre == "obtener_kpis_por_mes":
        meses = db.kpi_por_mes()
        if not meses:
            return "No hay datos mensuales disponibles."
        filas = [
            f"{m['mes']}: {m['total']} órdenes, {m['cerradas']} cerradas, "
            f"MTTR: {round(m['mttr'] or 0, 1)}h"
            for m in meses
        ]
        return "KPIs por mes (últimos 6 meses):\n" + "\n".join(filas)

    return f"Herramienta '{nombre}' no reconocida."


def stream_respuesta(historial: list):
    """
    Genera una respuesta en streaming con manejo de tool use.
    Yields líneas SSE: 'data: <texto>\n\n'
    """
    messages = list(historial)

    while True:
        with client.messages.stream(
            model="claude-opus-4-6",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
            thinking={"type": "adaptive"},
            cache_control={"type": "ephemeral"},
        ) as stream:
            tool_uses = []
            text_accumulated = []

            for event in stream:
                if event.type == "content_block_delta":
                    if event.delta.type == "text_delta":
                        chunk = event.delta.text
                        text_accumulated.append(chunk)
                        yield f"data: {json.dumps({'type': 'text', 'content': chunk})}\n\n"

            final_msg = stream.get_final_message()

        # Collect tool use blocks
        for block in final_msg.content:
            if block.type == "tool_use":
                tool_uses.append(block)

        if final_msg.stop_reason != "tool_use" or not tool_uses:
            break

        # Execute tools and continue
        messages.append({"role": "assistant", "content": final_msg.content})
        tool_results = []
        for tu in tool_uses:
            yield f"data: {json.dumps({'type': 'tool', 'name': tu.name})}\n\n"
            resultado = ejecutar_herramienta(tu.name, tu.input)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tu.id,
                "content": resultado,
            })
        messages.append({"role": "user", "content": tool_results})

    yield f"data: {json.dumps({'type': 'done'})}\n\n"
