"""Capa de presentación opcional con `rich`.

Si `rich` está instalado y el modo UI está activado (`micli ui on`, por
defecto), `habilitar()` sustituye el renderizado básico por consolas con
tablas y paneles. Con `--no-color` o `micli ui off` se usa el básico.
"""
import json
import os

from micli import clic

try:
    from rich import box
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    RICH = True
except ImportError:
    RICH = False

_RUTA_POR_DEFECTO = os.path.expanduser(
    os.path.join("~", ".config", "micli", "ui.json")
)


def _ruta():
    return os.environ.get("MICLI_UI_CONF") or _RUTA_POR_DEFECTO


def activado():
    if clic.sin_color():
        return False
    try:
        with open(_ruta(), encoding="utf-8") as f:
            return bool(json.load(f).get("ui", True))
    except (OSError, ValueError):
        return True


def activar(valor=True):
    ruta = _ruta()
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump({"ui": bool(valor)}, f)


def reset():
    """Descarta la consola cacheada (tras cambiar destino o preferencias)."""
    global _consola
    _consola = None


_reset = reset  # compatibilidad con usos y tests anteriores


_consola = None


def habilitar():
    """Activa rich si está disponible. Devuelve True si tiene efecto."""
    global _consola
    if not RICH or not activado():
        _consola = None
        return False
    _consola = Console(file=clic.out)
    return True


def consola():
    global _consola
    if not activado():
        _consola = None
        return None
    if _consola is None or _consola.file is not clic.out:
        _reconectar()
    return _consola


def _reconectar():
    global _consola
    _consola = Console(file=clic.out)


def tabla_asignaturas(datos, estado):
    if not RICH or not consola():
        return False
    tabla = Table(title="Asignaturas", box=box.SIMPLE_HEAVY)
    tabla.add_column("Asignatura")
    tabla.add_column("Nota", justify="right")
    tabla.add_column("Estado")
    tabla.add_column("Créditos", justify="right")
    for nombre, info in sorted(datos.items()):
        est = estado(info["nota"])
        color = {"aprobada": "green", "suspendida": "red",
                 "pendiente": "yellow"}[est]
        nota = "—" if info["nota"] is None else f"{info['nota']:g}"
        tabla.add_row(
            nombre, nota, Text(est, style=color), str(info["creditos"])
        )
    consola().print(tabla)
    return True


def tabla_examenes(examenes):
    if not RICH or not consola():
        return False
    tabla = Table(title="Histórico de exámenes", box=box.SIMPLE_HEAVY)
    tabla.add_column("Fecha")
    tabla.add_column("Tema")
    tabla.add_column("Dificultad")
    tabla.add_column("Nota", justify="right")
    for ex in examenes:
        nota = ex.get("nota") or 0
        color = "green" if nota >= 5 else "red"
        tabla.add_row(
            str(ex.get("fecha", ""))[:10],
            str(ex.get("nombre", "")),
            str(ex.get("dificultad", "")),
            Text(f"{nota}/10", style=color),
        )
    consola().print(tabla)
    return True


def panel(texto, titulo=None, estilo="cyan"):
    if not RICH or not consola():
        return False
    consola().print(Panel(texto, title=titulo, border_style=estilo))
    return True


def resumen_stats(n, aprobadas, suspendidas, pendientes, media):
    if not RICH or not consola():
        return False
    tabla = Table(box=box.SIMPLE)
    tabla.add_column("Total", justify="right")
    tabla.add_column("Aprobadas", style="green", justify="right")
    tabla.add_column("Suspendidas", style="red", justify="right")
    tabla.add_column("Pendientes", style="yellow", justify="right")
    tabla.add_column("Media", style="magenta", justify="right")
    tabla.add_row(
        str(n), str(aprobadas), str(suspendidas), str(pendientes),
        "—" if media is None else f"{media:.2f}",
    )
    consola().print(tabla)
    return True
