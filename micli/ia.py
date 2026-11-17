import os

import httpx

URL_API = "https://api.openai.com/v1/chat/completions"
MODELO_POR_DEFECTO = "gpt-4o-mini"


class IaError(Exception):
    pass


def _api_key():
    clave = os.environ.get("OPENAI_API_KEY")
    if not clave:
        raise IaError(
            "Falta OPENAI_API_KEY. Crea una clave en https://platform.openai.com/"
            "api-keys y expórtala: export OPENAI_API_KEY=..."
        )
    return clave


def chat(mensajes, modelo=None):
    """Envía `mensajes` a la API de chat de OpenAI y devuelve el texto.

    `mensajes` es una lista de dicts {"role": ..., "content": ...}.
    """
    clave = _api_key()
    respuesta = httpx.post(
        URL_API,
        headers={
            "Authorization": f"Bearer {clave}",
            "Content-Type": "application/json",
        },
        json={
            "model": modelo or os.environ.get("MICLI_IA_MODELO") or MODELO_POR_DEFECTO,
            "messages": mensajes,
        },
        timeout=60,
    )
    if respuesta.status_code != 200:
        raise IaError(
            f"La API respondió {respuesta.status_code}: "
            f"{respuesta.text[:300]}"
        )
    datos = respuesta.json()
    try:
        return datos["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, AttributeError):
        raise IaError(f"Respuesta inesperada de la API: {datos}")


def chatear(texto, modelo=None):
    return chat([{"role": "user", "content": texto}], modelo)


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


def consejo_estudio(datos, modelo=None):
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
    )
