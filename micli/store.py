import json
import os

RUTA_POR_DEFECTO = os.path.expanduser(os.path.join("~", ".config", "micli", "asignaturas.json"))


def _rutas(ruta=None):
    return ruta or os.environ.get("MICLI_DATOS") or RUTA_POR_DEFECTO


def cargar(ruta=None):
    path = _rutas(ruta)
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def guardar(datos, ruta=None):
    path = _rutas(ruta)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)


def add_asignatura(nombre, creditos=0, ruta=None):
    datos = cargar(ruta)
    if nombre in datos:
        raise ValueError(f"La asignatura {nombre!r} ya existe")
    datos[nombre] = {"creditos": creditos, "nota": None}
    guardar(datos, ruta)
    return datos


def set_nota(nombre, nota, ruta=None):
    datos = cargar(ruta)
    if nombre not in datos:
        raise KeyError(nombre)
    datos[nombre]["nota"] = nota
    guardar(datos, ruta)
    return datos


def remove_asignatura(nombre, ruta=None):
    datos = cargar(ruta)
    if nombre not in datos:
        raise KeyError(nombre)
    del datos[nombre]
    guardar(datos, ruta)
    return datos


def estado(nota):
    if nota is None:
        return "pendiente"
    return "aprobada" if nota >= 5 else "suspendida"
