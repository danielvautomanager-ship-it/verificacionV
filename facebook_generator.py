import json
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2"


def _build_prompt(prop: dict, plataforma: str) -> str:
    caract = prop.get("caracteristicas", "[]")
    if isinstance(caract, str):
        try:
            caract = json.loads(caract)
        except Exception:
            caract = []
    caract_str = ", ".join(caract) if caract else "No especificadas"

    precio_str = ""
    if prop.get("precio"):
        precio_str = f"{prop.get('moneda','USD')} {prop.get('precio'):,.0f}"

    base_info = f"""
PROPIEDAD:
- Tipo: {prop.get('tipo','Casa')} en {prop.get('operacion','Venta')}
- Título: {prop.get('titulo','')}
- Precio: {precio_str or 'Consultar'}
- Dormitorios: {prop.get('dormitorios',0)} | Baños: {prop.get('banos',0)}
- Área construida: {prop.get('area_m2') or 'N/D'} m² | Terreno: {prop.get('area_terreno_m2') or 'N/D'} m²
- Ubicación: {prop.get('distrito','')} {', ' + prop.get('provincia','') if prop.get('provincia') else ''}
- Descripción: {prop.get('descripcion','') or 'Sin descripción'}
- Características: {caract_str}
""".strip()

    if plataforma == "facebook_marketplace":
        rules = """
REGLAS para Facebook Marketplace:
1. El campo "titulo" debe ser máximo 100 caracteres, incluir: tipo + ubicación + precio si aplica. Ejemplo: "Casa 3 dorm. en Miraflores - USD 180,000"
2. El campo "cuerpo" debe tener 200-350 palabras. Párrafo 1: presentación impactante. Párrafo 2: características detalladas. Párrafo 3: ubicación y accesos.
3. NO usar más de 3 emojis en todo el texto.
4. Incluir el precio de forma explícita si está disponible.
5. El campo "llamada_accion" debe ser una frase corta de contacto (max 80 caracteres).
6. El campo "hashtags" debe tener entre 5 y 8 hashtags relevantes separados por espacios. Usar hashtags en español peruano como: #inmueblesLima #casaenVenta #bienesraicesPeru.
"""
    else:
        rules = """
REGLAS para Facebook Perfil/Página:
1. El campo "titulo" es el primer párrafo del post (1-2 líneas llamativas con 1-2 emojis relevantes). Max 120 caracteres.
2. El campo "cuerpo" debe tener 250-400 palabras. Usar storytelling emocional: imagina vivir aquí, estilo de vida, beneficios. Incluir características clave. Terminar con pregunta al lector.
3. Usar hasta 5 emojis estratégicamente.
4. El campo "llamada_accion" debe invitar a contactar con emoji de WhatsApp/teléfono. Max 100 caracteres.
5. El campo "hashtags" debe tener entre 10 y 15 hashtags. Mezclar: #inmueblesLima #PropiedadesLima #CasasDeLujo #InversionInmobiliaria #BienesRaicesPeru y hashtags del distrito.
"""

    prompt = f"""Eres un experto en marketing inmobiliario digital para el mercado peruano.
Genera contenido optimizado para {plataforma.replace('_', ' ')} para la siguiente propiedad.

{base_info}

{rules}

IMPORTANTE: Responde ÚNICAMENTE con un objeto JSON válido con estas claves exactas:
{{"titulo": "...", "cuerpo": "...", "hashtags": "...", "llamada_accion": "..."}}

No incluyas texto adicional fuera del JSON."""

    return prompt


def generar_publicacion(prop: dict, plataforma: str) -> dict:
    prompt = _build_prompt(prop, plataforma)
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        raw = response.json().get("response", "{}")
        result = json.loads(raw)
        # Validar claves mínimas
        for key in ("titulo", "cuerpo", "hashtags", "llamada_accion"):
            if key not in result:
                result[key] = ""
        return result
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "Ollama no está disponible. Asegúrate de que Ollama está corriendo "
            "con: ollama serve"
        )
    except json.JSONDecodeError:
        raise RuntimeError("La IA no retornó JSON válido. Intente nuevamente.")
