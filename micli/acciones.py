import json
import os
import re
import shlex
from string import Formatter

RUTA_ACCIONES_POR_DEFECTO = "acciones.json"


class AccionError(Exception):
    pass


class AccionNoValida(AccionError):
    """La definición de una acción concreta está mal escrita."""


class ConfigError(AccionError):
    """El archivo de configuración (acciones.json) no es usable."""


def _ruta_acciones(ruta=None):
    return ruta or os.environ.get("MICLI_ACCIONES") or RUTA_ACCIONES_POR_DEFECTO


def cargar_acciones(ruta=None):
    path = _ruta_acciones(ruta)
    if not os.path.exists(path):
        raise ConfigError(
            f"No se encuentra {path}. Crea el archivo o define MICLI_ACCIONES."
        )
    try:
        with open(path, encoding="utf-8") as f:
            datos = json.load(f)
    except json.JSONDecodeError as e:
        raise ConfigError(
            f"{path} no es JSON válido (línea {e.lineno}, columna "
            f"{e.colno}): revisa las llaves y las comas."
        )
    except OSError as e:
        raise ConfigError(f"No puedo leer {path}: {e.strerror or e}")
    acciones = datos.get("acciones")
    if not isinstance(acciones, dict):
        raise ConfigError(
            f"{path} debe tener una clave 'acciones' con un objeto "
            '{"nombre": {...}, ...}.'
        )
    for nombre, acc in acciones.items():
        if not isinstance(acc, dict) or not acc.get("comando"):
            raise AccionNoValida(
                f"La acción {nombre!r} necesita un campo 'comando' de texto."
            )
        if not isinstance(acc["comando"], str):
            raise AccionNoValida(f"El 'comando' de {nombre!r} debe ser texto.")
        if "peligrosa" in acc and not isinstance(acc["peligrosa"], bool):
            raise AccionNoValida(
                f"El campo 'peligrosa' de {nombre!r} debe ser true o false."
            )
    return acciones


def placeholders(comando):
    """Lista de (clave, default) declarados en el comando, sin duplicados.

    Solo se consideran placeholders los nombres posicionales (`{1}`) y los
    identificadores simples (`{nombre}`). Las llaves de shell (`{}`, `${VAR}`)
    se dejan intactas.
    """
    resultado = []
    for literal, clave, espec, _ in Formatter().parse(comando):
        if not clave or literal.endswith("$"):
            continue
        nombre, sep, default = clave.partition(":")
        if not sep and espec:
            default = espec
        if not (nombre.isdigit() and int(nombre) > 0 or nombre.isidentifier()):
            continue
        par = (nombre, default if (sep or espec) else None)
        if par not in resultado:
            resultado.append(par)
    return resultado


def construir(comando, argumentos):
    """Sustituye los placeholders de `comando` citando los valores con shlex.

    `argumentos` es la lista de argumentos que llegan a `micli ejecutar`
    (todos como str). Los `{n}` toman la posición n (1-indexada); los
    `{nombre}` se pasan como `--nombre=valor`. Un placeholder con default
    (`{1:mensaje}`) se resuelve con el default si no se pasa valor.
    """
    posicionales = [a for a in argumentos if not a.startswith("--")]
    declarados = placeholders(comando)

    valores = {}
    for clave, default in declarados:
        if clave.isdigit():
            idx = int(clave) - 1
            valores[clave] = posicionales[idx] if 0 <= idx < len(posicionales) else default
        else:
            valor = default
            for a in argumentos:
                if a.startswith("--") and "=" in a:
                    k, v = a[2:].split("=", 1)
                    if k == clave:
                        valor = v
                        break
            valores[clave] = valor

    faltan = [
        c for c, d in declarados
        if d is None and (valores.get(c) is None or valores.get(c) == "")
    ]
    if faltan:
        raise AccionError(
            "Faltan parámetros: " + ", ".join("{" + c + "}" for c in faltan)
        )

    plantilla = comando.replace("{{", "\x00").replace("}}", "\x01")
    for clave, _ in declarados:
        patron = re.compile(r"\{" + re.escape(clave) + r"(?::[^}]*)?\}")
        plantilla = patron.sub(
            lambda _, valor=valores[clave]: shlex.quote(str(valor)),
            plantilla,
        )
    return plantilla.replace("\x00", "{").replace("\x01", "}")


def segmentar(accion, argumentos):
    """Divide `accion + argumentos` en segmentos separados por `+`.

    Cada segmento es [nombre-accion, args...]. Permite encadenar:
    `micli ejecutar prueba + estado`.
    """
    segmentos = [[]]
    for token in [accion] + list(argumentos):
        if token == "+":
            segmentos.append([])
        else:
            segmentos[-1].append(token)
    if any(not s for s in segmentos):
        raise AccionError(
            "Encadenado inválido. Uso: micli ejecutar acc1 + acc2 [args]."
        )
    assert all(s and isinstance(s[0], str) for s in segmentos), \
        "segmentar(): cada segmento debe empezar por el nombre de acción"
    return segmentos


def es_peligrosa(acc):
    return bool(acc.get("peligrosa"))


def confirmar(nombre, acc, entrada_fn):
    """Pide confirmación al usuario para acciones peligrosas."""
    aviso = acc.get("aviso", "puede borrar o sobreescribir archivos")
    respuesta = entrada_fn(
        f"La acción {nombre!r} es peligrosa ({aviso}). "
        "¿Ejecutarla? (escribe sí): "
    )
    return (respuesta or "").strip().lower() in ("si", "sí", "s", "yes", "y")
