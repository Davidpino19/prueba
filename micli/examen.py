"""Generación y corrección de exámenes con IA.

Soporta resúmenes en TXT/MD (lectura directa), PDF (pypdf o `pdftotext`
como fallback) y texto pegado directamente. Usa `micli.ia` para crear las
preguntas y corregirlas.
"""
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from micli import ia


class ExamenError(Exception):
    pass


DIFICULTADES = ("facil", "media", "dificil")
DIFICULTAD_TEXTO = {
    "facil": "fácil: preguntas conceptuales y de definición sencilla",
    "media": "media: mezcla de definición, aplicación y algún caso práctico",
    "dificil": "difícil: aplicación, análisis y casos prácticos con matices",
}


def leer_resumen(fichero):
    """Devuelve el texto de un resumen (txt/md leídos tal, PDF extraído)."""
    ruta = Path(fichero).expanduser()
    if not ruta.exists():
        raise ExamenError(f"No existe el fichero: {ruta}")
    sufijo = ruta.suffix.lower()
    if sufijo in (".txt", ".md", ".markdown"):
        return ruta.read_text(encoding="utf-8", errors="replace")
    if sufijo == ".pdf":
        return _leer_pdf(ruta)
    raise ExamenError(f"Formato no soportado: {sufijo} (usa txt, md o pdf)")


def _leer_pdf(ruta):
    try:
        from pypdf import PdfReader

        lector = PdfReader(str(ruta))
        texto = "\n".join(
            pagina.extract_text() or "" for pagina in lector.pages
        )
        if texto.strip():
            return texto
    except ImportError:
        pass
    except Exception:
        pass
    pdftotext = shutil.which("pdftotext")
    if pdftotext:
        resultado = subprocess.run(
            [pdftotext, str(ruta), "-"], capture_output=True, text=True
        )
        if resultado.returncode == 0 and resultado.stdout.strip():
            return resultado.stdout
        raise ExamenError(
            "No se ha podido extraer texto del PDF (¿está escaneado?)"
        )
    raise ExamenError(
        "No hay forma de leer el PDF: instala pypdf o pdftotext, o pega el "
        "texto con --texto"
    )


def crear(contenido, dificultad="media", num=5, modelo=None,
          proveedor=None):
    """Pide a la IA `num` preguntas de nivel `dificultad` sobre `contenido`.

    Devuelve una lista de dicts {"pregunta": str, "tipo": str}.
    """
    dificultad = dificultad.lower()
    if dificultad not in DIFICULTADES:
        raise ExamenError(
            f"Dificultad {dificultad!r} inválida. Usa: "
            + ", ".join(DIFICULTADES)
        )
    contenido = contenido.strip()
    if not contenido:
        raise ExamenError("El resumen está vacío.")
    tipos = "test (opciones a-d), corto o desarrollo"
    prompt = (
        "Eres un profesor universitario. A partir del material, crea "
        f"{num} preguntas de examen de dificultad {DIFICULTAD_TEXTO[dificultad]} "
        f"sobre el material (tipos variados: {tipos}).\n\n"
        "Devuelve EXCLUSIVAMENTE un JSON válido con la forma:\n"
        '{"preguntas": [{"pregunta": "...", "tipo": "test|corto|desarrollo", '
        '"opciones": ["a) ...", "b) ...", "c) ...", "d) ..."]}]}\n'
        'El campo "opciones" solo va en las preguntas de tipo test.\n'
        "JSON compacto, sin saltos de línea.\n\n"
        "Material:\n" + contenido
    )
    respuesta = ia.chat(
        [
            {
                "role": "system",
                "content": (
                    "Respondes en español. Solo devuelves JSON válido, "
                    "sin texto alrededor."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        modelo=modelo,
        proveedor_nombre=proveedor,
    )
    datos = _extraer_json(respuesta)
    preguntas = datos.get("preguntas")
    if not isinstance(preguntas, list) or not preguntas:
        raise ExamenError("La IA no devolvió preguntas válidas.")
    limpieza = []
    for p in preguntas:
        if isinstance(p, dict) and p.get("pregunta"):
            entrada = {
                "pregunta": str(p["pregunta"]).strip(),
                "tipo": str(p.get("tipo", "desarrollo")).strip(),
            }
            if entrada["tipo"] == "test" and isinstance(p.get("opciones"), list):
                entrada["opciones"] = [str(o) for o in p["opciones"]]
            limpieza.append(entrada)
    if not limpieza:
        raise ExamenError("La IA devolvió preguntas sin campo 'pregunta'.")
    return limpieza


def _extraer_json(texto):
    texto = texto.strip()
    if texto.startswith("```"):
        inicio = texto.find("`")
        fin = texto.rfind("`")
        texto = texto[inicio + 1 : fin].strip()
        if texto.lower().startswith("json"):
            texto = texto[4:]
        texto = texto.strip()
    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        inicio = texto.find("{")
        fin = texto.rfind("}")
        if inicio != -1 and fin > inicio:
            try:
                return json.loads(texto[inicio : fin + 1])
            except json.JSONDecodeError:
                pass
    raise ExamenError(
        "La IA no devolvió JSON válido:\n"
        + texto[:1000]
        + ("\n[...truncado]" if len(texto) > 1000 else "")
    )


def corregir(contenido, preguntas, respuestas, modelo=None, proveedor=None):
    """Corrige las respuestas y devuelve (nota, [dicts por pregunta])."""
    conversacion = [
        {
            "numero": i,
            "pregunta": p.get("pregunta"),
            "tipo": p.get("tipo"),
            "respuesta_alumno": respuestas.get(i, ""),
        }
        for i, p in enumerate(preguntas, 1)
    ]
    prompt = (
        "Eres un profesor corrigiendo un examen. Valora cada respuesta "
        "0-10 según lo bien que responda a la pregunta, y da un feedback "
        "breve (1-2 frases) y una nota global 0-10.\n\n"
        "Material de referencia:\n" + contenido[:12000] + "\n\n"
        "Examen y respuestas del alumno:\n"
        + json.dumps(conversacion, ensure_ascii=False)
        + '\n\nDevuelve EXCLUSIVAMENTE JSON: {"nota": 7.5, "respuestas": '
        '[{"numero": 1, "nota": 8, "acertada": true, "feedback": "..."}]}'
    )
    respuesta = ia.chat(
        [
            {
                "role": "system",
                "content": (
                    "Respondes en español. Solo devuelves JSON válido, "
                    "sin texto alrededor."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        modelo=modelo,
        proveedor_nombre=proveedor,
    )
    datos = _extraer_json(respuesta)
    nota = float(datos.get("nota", 0))
    correcciones = datos.get("respuestas", [])
    if not isinstance(correcciones, list):
        correcciones = []
    return nota, correcciones


def ruta_examenes():
    from micli import store

    return Path(store._rutas()).parent / "examenes"


def guardar(nombre, dificultad, nota, correcciones):
    """Guarda el resultado del examen y devuelve la ruta."""
    carpeta = ruta_examenes()
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / (
        f"{datetime.now():%Y%m%d-%H%M%S}-{nombre}.json"
    )
    ruta.write_text(
        json.dumps(
            {
                "nombre": nombre,
                "fecha": datetime.now().isoformat(timespec="seconds"),
                "dificultad": dificultad,
                "nota": nota,
                "correcciones": correcciones,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return ruta


def historial():
    """Lista los exámenes guardados, más nuevos primero."""
    carpeta = ruta_examenes()
    if not carpeta.exists():
        return []
    examenes = []
    for fichero in sorted(carpeta.glob("*.json"), reverse=True):
        try:
            examenes.append(json.loads(fichero.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            continue
    return examenes
