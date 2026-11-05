import argparse
import sys
from datetime import datetime

from colorama import Fore, Style, init as colorama_init

from micli import __version__

colorama_init(wrap=False, convert=False, strip=False)


def build_parser():
    parser = argparse.ArgumentParser(
        prog="micli",
        description="Mi primera CLI",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--no-color", action="store_true", help="Desactiva los colores")
    sub = parser.add_subparsers(dest="comando", required=True)

    saluda = sub.add_parser("saluda", help="Saluda a alguien")
    saluda.add_argument("nombre", help="Nombre a saludar")
    saluda.add_argument("-v", "--verbose", action="store_true", help="Modo verbose")
    saluda.set_defaults(func=cmd_saluda)

    despide = sub.add_parser("despide", help="Se despide de alguien")
    despide.add_argument("nombre", help="Nombre a despedir")
    despide.set_defaults(func=cmd_despide)

    ahora = sub.add_parser("ahora", help="Muestra la fecha y hora actual")
    ahora.add_argument(
        "-f", "--formato", default="%Y-%m-%d %H:%M:%S",
        help="Formato strftime (por defecto: %Y-%m-%d %H:%M:%S)",
    )
    ahora.set_defaults(func=cmd_ahora)

    return parser


out = sys.stdout


def _print(texto, color, args):
    if getattr(args, "no_color", False):
        print(texto, file=out)
    else:
        print(f"{color}{texto}{Style.RESET_ALL}", file=out)


def cmd_saluda(args):
    _print(f"Hola, {args.nombre}!", Fore.GREEN, args)
    if args.verbose:
        _print(f"(verbose: comando={args.comando}, nombre={args.nombre!r})", Fore.CYAN, args)
    return 0


def cmd_despide(args):
    _print(f"¡Hasta luego, {args.nombre}!", Fore.YELLOW, args)
    return 0


def cmd_ahora(args):
    ahora = datetime.now().strftime(args.formato)
    _print(ahora, Fore.MAGENTA, args)
    return 0


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
