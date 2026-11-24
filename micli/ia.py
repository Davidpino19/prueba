import os
import time

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
    "gemini": "gemini-flash-lite-latest",
}
CLAVES = {"openai": "OPENAI_API_KEY", "gemini": "GEMINI_API_KEY"}
FALLBACKS = {
    "openai": ["gpt-4o"],
    "gemini": ["gemini-3.8-flash", "gemini-2.5-flash"],
}


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

    Con un modelo sin `-m`, si la API falla con 404 (modelo retirado) o 503
    (saturación) se reintenta con los modelos de `FALLBACKS`.
    """
    if httpx is None:
        raise IaError(
            "Falta la librería httpx. Instálala con: pip install httpx"
        )
    prov = proveedor(proveedor_nombre)
    clave = _api_key(prov)
    fijo = bool(modelo or os.environ.get("MICLI_IA_MODELO"))
    modelos = ([modelo or os.environ.get("MICLI_IA_MODELO") or MODELOS[prov]]
               if fijo else [MODELOS[prov], *FALLBACKS[prov]])
    ultimo = None
    for m in modelos:
        try:
            if prov == "openai":
                datos, texto = _chat_openai(clave, m, mensajes)
            else:
                datos, texto = _chat_gemini(clave, m, mensajes)
            if texto is not None:
                return texto
            ultimo = IaError(f"Respuesta inesperada de la API: {datos}")
        except IaError as e:
            ultimo = e
            if fijo:
                raise
            error = str(e)
            if "503" not in error and "404" not in error and "truncated" not in error.lower():
                raise
    raise ultimo


def _respuesta_ok(respuesta, reintentos=3, reintentar=None):
    ultimo = None
    for intento in range(reintentos + 1):
        if respuesta.status_code == 200:
            return respuesta.json()
        ultimo = IaError(
            f"La API respondió {respuesta.status_code}: "
            f"{respuesta.text[:300]}"
        )
        if respuesta.status_code != 503 or intento == reintentos:
            raise ultimo
        time.sleep(2 * (intento + 1))
        respuesta = reintentar() if reintentar else respuesta
    raise ultimo


def _chat_openai(clave, modelo, mensajes):
    def enviar():
        return httpx.post(
            URL_API,
            headers={
                "Authorization": f"Bearer {clave}",
                "Content-Type": "application/json",
            },
            json={"model": modelo, "messages": mensajes},
            timeout=120,
        )

    datos = _respuesta_ok(enviar(), reintentar=enviar)
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
    cuerpo = {
        "contents": contenido,
        "generationConfig": {
            "maxOutputTokens": 8192,
            "responseMimeType": "application/json",
        },
    }
    if system:
        cuerpo["systemInstruction"] = {"parts": [{"text": system}]}
    cabeceras = {"x-goog-api-key": clave}
    params = {} if clave.startswith("AQ.") else {"key": clave}
    def enviar():
        return httpx.post(
            GEMINI_URL.format(modelo=modelo),
            params=params or None,
            headers=cabeceras,
            json=cuerpo,
            timeout=120,
        )

    datos = _respuesta_ok(enviar(), reintentar=enviar)
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
