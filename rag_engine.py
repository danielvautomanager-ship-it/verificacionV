import threading
import os

import realestate_db as rdb

_index_lock = threading.Lock()
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")


def _get_store():
    from langchain_ollama import OllamaEmbeddings
    from langchain_community.vectorstores import Chroma
    embeddings = OllamaEmbeddings(
        model="nomic-embed-text",
        base_url="http://localhost:11434",
    )
    store = Chroma(
        collection_name="propiedades_rag",
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR,
    )
    return store


def _property_card(prop: dict) -> str:
    import json
    caract = prop.get("caracteristicas", "[]")
    if isinstance(caract, str):
        try:
            caract = json.loads(caract)
        except Exception:
            caract = []
    caract_str = ", ".join(caract) if caract else "ninguna especificada"
    precio = f"{prop.get('moneda','USD')} {prop.get('precio'):,.0f}" if prop.get("precio") else "consultar"

    return (
        f"Propiedad {prop.get('codigo','')} - {prop.get('titulo','')}. "
        f"Tipo: {prop.get('tipo','')}. Operación: {prop.get('operacion','')}. "
        f"Precio: {precio}. "
        f"Dormitorios: {prop.get('dormitorios',0)}, Baños: {prop.get('banos',0)}. "
        f"Área: {prop.get('area_m2') or 'N/D'} m². "
        f"Ubicación: {prop.get('distrito','')}, {prop.get('provincia','')}, {prop.get('departamento','')}. "
        f"Estado: {prop.get('estado','')}. "
        f"Descripción: {prop.get('descripcion','') or 'Sin descripción'}. "
        f"Características: {caract_str}."
    )


def index_property(propiedad_id: int):
    prop = rdb.get_propiedad(propiedad_id)
    if not prop:
        return

    rdb.upsert_rag_doc(propiedad_id, prop["titulo"], 0, "indexando")
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        from langchain.schema import Document

        docs = []
        metadata = {
            "propiedad_id": propiedad_id,
            "codigo": prop.get("codigo", ""),
            "tipo": prop.get("tipo", ""),
            "operacion": prop.get("operacion", ""),
            "estado": prop.get("estado", ""),
            "distrito": prop.get("distrito", ""),
        }

        # Property card siempre incluida
        docs.append(Document(page_content=_property_card(prop), metadata=metadata))

        # PDFs si existen
        archivos = rdb.listar_archivos(propiedad_id)
        pdfs = [a for a in archivos if a["tipo"] == "pdf"]
        splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)

        for pdf in pdfs:
            pdf_path = os.path.join(
                os.path.dirname(__file__), "static", "uploads", "pdfs", pdf["nombre_archivo"]
            )
            if not os.path.exists(pdf_path):
                continue
            try:
                from langchain_community.document_loaders import PyPDFLoader
                loader = PyPDFLoader(pdf_path)
                pages = loader.load()
                chunks = splitter.split_documents(pages)
                for chunk in chunks:
                    chunk.metadata.update(metadata)
                docs.extend(chunks)
            except Exception:
                pass

        with _index_lock:
            store = _get_store()
            # Eliminar documentos previos de esta propiedad
            try:
                existing = store.get(where={"propiedad_id": propiedad_id})
                if existing and existing.get("ids"):
                    store.delete(ids=existing["ids"])
            except Exception:
                pass
            store.add_documents(docs)

        rdb.upsert_rag_doc(propiedad_id, prop["titulo"], len(docs), "indexado")

    except Exception as e:
        rdb.upsert_rag_doc(propiedad_id, prop["titulo"], 0, "error")
        raise


def index_all_properties():
    props = rdb.listar_propiedades()
    for p in props:
        try:
            index_property(p["id"])
        except Exception:
            pass


def consultar(pregunta: str, historial: list = []) -> str:
    from langchain_ollama import ChatOllama
    from langchain.schema import HumanMessage

    # Build context from vector store
    context_text = ""
    try:
        store = _get_store()
        retriever = store.as_retriever(search_kwargs={"k": 5})
        context_docs = retriever.invoke(pregunta)
        context_text = "\n\n".join(d.page_content for d in context_docs)
    except Exception:
        # Si ChromaDB falla, consultar directamente las propiedades
        props = rdb.listar_propiedades(filtro_estado="Disponible")
        context_text = "\n\n".join(_property_card(p) for p in props[:10])

    # Build conversation history (last 6 turns)
    history_lines = []
    for m in historial[-6:]:
        rol = "Cliente" if m["rol"] == "user" else "Asistente"
        history_lines.append(f"{rol}: {m['contenido']}")
    history_text = "\n".join(history_lines)

    system_prompt = """Eres el asistente virtual de una inmobiliaria peruana.
Tu función es responder preguntas sobre las propiedades disponibles en el catálogo.
REGLAS:
- Responde SOLO en base a la información del catálogo proporcionado.
- Si no hay propiedades que coincidan, dilo claramente y ofrece alternativas cercanas.
- Sé amable, conciso y profesional. Usa español peruano natural.
- Cuando una propiedad es de interés, anima al cliente a dejar sus datos de contacto.
- NO inventes propiedades ni precios que no estén en el catálogo.
- Si te preguntan algo no relacionado con inmuebles, redirige amablemente a propiedades."""

    full_prompt = f"""{system_prompt}

CATÁLOGO DE PROPIEDADES DISPONIBLES:
{context_text}

HISTORIAL DE CONVERSACIÓN:
{history_text}

PREGUNTA DEL CLIENTE: {pregunta}

RESPUESTA:"""

    llm = ChatOllama(
        model="llama3.2",
        base_url="http://localhost:11434",
        temperature=0.3,
    )
    response = llm.invoke([HumanMessage(content=full_prompt)])
    return response.content.strip()
