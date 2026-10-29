import argparse
import sys

from micli import __version__


def build_parser():
    parser = argparse.ArgumentParser(
        prog="micli",
        description="Mi primera CLI",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="comando", required=True)

    saluda = sub.add_parser("saluda", help="Saluda a alguien")
    saluda.add_argument("nombre", help="Nombre a saludar")
    saluda.add_argument("-v", "--verbose", action="store_true", help="Modo verbose")
    saluda.set_defaults(func=cmd_saluda)

    return parser


def cmd_saluda(args):
    print(f"Hola, {args.nombre}!")
    if args.verbose:
        print(f"(verbose: comando={args.comando}, nombre={args.nombre!r})")
    return 0


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
