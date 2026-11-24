"""Capa de salida compartida: color, destino y entrada por teclado.

Los comandos (argparse o click) escriben siempre a través de estas funciones
para que los tests puedan sustituir `out` y `entrada` y capturar la salida,
y para que `--no-color` funcione en todos los subcomandos.
"""
import sys

from colorama import Fore, Style, init as colorama_init

colorama_init(wrap=False, convert=False, strip=False)

out = sys.stdout
entrada = input
_no_color = False

VERDE = Fore.GREEN
AMARILLO = Fore.YELLOW
ROJO = Fore.RED
AZUL = Fore.CYAN
MAGENTA = Fore.MAGENTA


def sin_color():
    return _no_color


def activar_sin_color():
    global _no_color
    _no_color = True


def restaurar_color():
    global _no_color
    _no_color = False


def imprimir(texto="", color=None):
    if color and not _no_color:
        texto = f"{color}{texto}{Style.RESET_ALL}"
    print(texto, file=out)
    out.flush()
