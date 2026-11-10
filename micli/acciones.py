import json
import os
import re
import shlex
from string import Formatter

RUTA_ACCIONES_POR_DEFECTO = "acciones.json"


class AccionError(Exception):
    pass


def _ruta_acciones(ruta=None):
    return ruta or os.environ.get("MICLI_ACCIONES") or RUTA_ACCIONES_POR_DEFECTO


def cargar_acciones(ruta=None):
    path = _ruta_acciones(ruta)
    if not os.path.exists(path):
        raise AccionError(
            f"No se encuentra {path}. Crea el archivo o define MICLI_ACCIONES."
        )
    try:
        with open(path, encoding="utf-8") as f:
            datos = json.load(f)
    except json.JSONDecodeError as e:
        raise AccionError(f"{path} no es JSON válido: {e}")
    acciones = datos.get("acciones")
    if not isinstance(acciones, dict):
        raise AccionError(f"{path} debe tener una clave 'acciones' con un objeto.")
    for nombre, acc in acciones.items():
        if not isinstance(acc, dict) or not acc.get("comando"):
            raise AccionError(f"La acción {nombre!r} necesita un campo 'comando'.")
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
