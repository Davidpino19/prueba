import os

try:
    import httpx
except ImportError:
    httpx = None

URL_API = "https://api.openai.com/v1/chat/completions"
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "{modelo}:generateContent"
)
MODELOS = {
    "openai": "gpt-4o-mini",
    "gemini": "gemini-2.0-flash",
}
CLAVES = {"openai": "OPENAI_API_KEY", "gemini": "GEMINI_API_KEY"}


class IaError(Exception):
    pass


def proveedor(nombre=None):
    nombre = (nombre or os.environ.get("MICLI_IA_PROVEEDOR", "openai")).lower()
    if nombre not in MODELOS:
        raise IaError(
            f"Proveedor {nombre!r} desconocido. Usa 'openai' o 'gemini' "
            "(-p/--proveedor o MICLI_IA_PROVEEDOR)."
        )
    return nombre


def _api_key(prov):
    var = CLAVES[prov]
    clave = os.environ.get(var)
    if not clave:
        if prov == "openai":
            ayuda = (
                "Crea una clave en https://platform.openai.com/api-keys y "
                "expórtala: export OPENAI_API_KEY=..."
            )
        else:
            ayuda = (
                "Crea una clave gratis en https://aistudio.google.com/apikey y "
                "expórtala: export GEMINI_API_KEY=..."
            )
        raise IaError(f"Falta {var}. {ayuda}")
    return clave


def chat(mensajes, modelo=None, proveedor_nombre=None):
    """Envía `mensajes` a la API del proveedor elegido y devuelve el texto.

    `mensajes` es una lista de dicts {"role": ..., "content": ...}. El
    proveedor se elige con `proveedor_nombre`, la variable
    MICLI_IA_PROVEEDOR, o 'openai' por defecto.
    """
    if httpx is None:
        raise IaError(
            "Falta la librería httpx. Instálala con: pip install httpx"
        )
    prov = proveedor(proveedor_nombre)
    clave = _api_key(prov)
    modelo = modelo or os.environ.get("MICLI_IA_MODELO") or MODELOS[prov]
    if prov == "openai":
        datos, texto = _chat_openai(clave, modelo, mensajes)
    else:
        datos, texto = _chat_gemini(clave, modelo, mensajes)
    if texto is not None:
        return texto
    raise IaError(f"Respuesta inesperada de la API: {datos}")


def _respuesta_ok(respuesta):
    if respuesta.status_code != 200:
        raise IaError(
            f"La API respondió {respuesta.status_code}: "
            f"{respuesta.text[:300]}"
        )
    return respuesta.json()


def _chat_openai(clave, modelo, mensajes):
    respuesta = httpx.post(
        URL_API,
        headers={
            "Authorization": f"Bearer {clave}",
            "Content-Type": "application/json",
        },
        json={"model": modelo, "messages": mensajes},
        timeout=60,
    )
    datos = _respuesta_ok(respuesta)
    try:
        return datos, datos["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, AttributeError):
        return datos, None


def _chat_gemini(clave, modelo, mensajes):
    system = "\n".join(m["content"] for m in mensajes if m["role"] == "system")
    contenido = [
        {"role": "user" if m["role"] == "user" else "model",
         "parts": [{"text": m["content"]}]}
        for m in mensajes
        if m["role"] != "system"
    ]
    cuerpo = {"contents": contenido}
    if system:
        cuerpo["systemInstruction"] = {"parts": [{"text": system}]}
    respuesta = httpx.post(
        GEMINI_URL.format(modelo=modelo),
        params={"key": clave},
        json=cuerpo,
        timeout=60,
    )
    datos = _respuesta_ok(respuesta)
    try:
        texto = datos["candidates"][0]["content"]["parts"][0]["text"].strip()
        return datos, texto or None
    except (KeyError, IndexError, AttributeError):
        return datos, None


def chatear(texto, modelo=None, proveedor_nombre=None):
    return chat(
        [{"role": "user", "content": texto}], modelo, proveedor_nombre
    )


def resumen_asignaturas(datos):
    """Convierte el dict de asignaturas en un texto compacto para la IA."""
    if not datos:
        return "El alumno no tiene ninguna asignatura registrada."
    lineas = []
    for nombre, info in sorted(datos.items()):
        nota = info.get("nota")
        nota_txt = "sin nota" if nota is None else f"{nota:g}"
        lineas.append(
            f"- {nombre}: {info.get('creditos', 0)} créditos, nota {nota_txt}"
        )
    return "Asignaturas del alumno:\n" + "\n".join(lineas)


def consejo_estudio(datos, modelo=None, proveedor_nombre=None):
    prompt = (
        "Eres un orientador académico. A partir de los datos, da en 4-6 frases\n"
        "un consejo de estudio personalizado en español: en qué priorizar,\n"
        "qué asignatura repasar y por qué.\n\n"
        + resumen_asignaturas(datos)
    )
    return chat(
        [
            {"role": "system", "content": "Respondes en español, de forma clara y breve."},
            {"role": "user", "content": prompt},
        ],
        modelo,
        proveedor_nombre,
    )
