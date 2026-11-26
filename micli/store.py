import json
import os

RUTA_POR_DEFECTO = os.path.expanduser(os.path.join("~", ".config", "micli", "asignaturas.json"))


class StoreError(Exception):
    """Error de lectura/escritura de los datos (fichero corrupto, permisos)."""


class AsignaturaInexistente(KeyError):
    pass


class AsignaturaDuplicada(ValueError):
    pass


def _ruta(ruta=None):
    return ruta or os.environ.get("MICLI_DATOS") or RUTA_POR_DEFECTO


def carpeta_datos(ruta=None):
    """Directorio de configuración (~/.config/micli) derivado de la ruta."""
    return os.path.dirname(_ruta(ruta))


def cargar(ruta=None):
    path = _ruta(ruta)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            datos = json.load(f)
    except json.JSONDecodeError as e:
        raise StoreError(
            f"{path} no es JSON válido (línea {e.lineno}, columna "
            f"{e.colno}). Edítalo o bórralo para empezar de cero."
        )
    except OSError as e:
        raise StoreError(f"No puedo leer {path}: {e.strerror or e}")
    assert isinstance(datos, dict), f"{path} debe contener un objeto JSON"
    return datos


def guardar(datos, ruta=None):
    assert isinstance(datos, dict), "guardar() espera un dict"
    path = _ruta(ruta)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
    except OSError as e:
        raise StoreError(f"No puedo escribir {path}: {e.strerror or e}")


def add_asignatura(nombre, creditos=0, ruta=None):
    datos = cargar(ruta)
    if nombre in datos:
        raise AsignaturaDuplicada(f"La asignatura {nombre!r} ya existe")
    datos[nombre] = {"creditos": creditos, "nota": None}
    guardar(datos, ruta)
    return datos


def set_nota(nombre, nota, ruta=None):
    datos = cargar(ruta)
    if nombre not in datos:
        raise AsignaturaInexistente(nombre)
    datos[nombre]["nota"] = nota
    guardar(datos, ruta)
    return datos


def remove_asignatura(nombre, ruta=None):
    datos = cargar(ruta)
    if nombre not in datos:
        raise AsignaturaInexistente(nombre)
    del datos[nombre]
    guardar(datos, ruta)
    return datos


def estado(nota):
    if nota is None:
        return "pendiente"
    return "aprobada" if nota >= 5 else "suspendida"
