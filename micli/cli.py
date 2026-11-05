import argparse
import sys
from datetime import datetime

from colorama import Fore, Style, init as colorama_init

from micli import __version__
from micli import store

colorama_init(wrap=False, convert=False, strip=False)

out = sys.stdout

COLOR_ESTADO = {
    "pendiente": Fore.YELLOW,
    "aprobada": Fore.GREEN,
    "suspendida": Fore.RED,
}


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

    asignaturas = sub.add_parser("asignaturas", help="Gestiona tus asignaturas")
    sub_asig = asignaturas.add_subparsers(dest="subcomando", required=True)

    a_add = sub_asig.add_parser("add", help="Añade una asignatura")
    a_add.add_argument("nombre", help="Nombre de la asignatura")
    a_add.add_argument("-c", "--creditos", type=int, default=0, help="Créditos")
    a_add.set_defaults(func=cmd_asig_add)

    a_list = sub_asig.add_parser("list", help="Lista las asignaturas")
    a_list.set_defaults(func=cmd_asig_list)

    a_nota = sub_asig.add_parser("nota", help="Guarda la nota de una asignatura")
    a_nota.add_argument("nombre", help="Nombre de la asignatura")
    a_nota.add_argument("nota", type=float, help="Nota (0-10)")
    a_nota.set_defaults(func=cmd_asig_nota)

    a_remove = sub_asig.add_parser("remove", help="Elimina una asignatura")
    a_remove.add_argument("nombre", help="Nombre de la asignatura")
    a_remove.set_defaults(func=cmd_asig_remove)

    resumen = sub.add_parser("resumen", help="Resumen de tus asignaturas")
    resumen.set_defaults(func=cmd_resumen)

    return parser


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


def cmd_asig_add(args):
    try:
        store.add_asignatura(args.nombre, args.creditos)
    except ValueError as e:
        _print(f"Error: {e}", Fore.RED, args)
        return 1
    _print(f"Añadida la asignatura {args.nombre} ({args.creditos} créditos).", Fore.GREEN, args)
    return 0


def cmd_asig_list(args):
    datos = store.cargar()
    if not datos:
        _print("No tienes asignaturas todavía.", Fore.CYAN, args)
        return 0
    for nombre, info in sorted(datos.items()):
        est = store.estado(info["nota"])
        nota_txt = "—" if info["nota"] is None else f"{info['nota']:g}"
        _print(
            f"{nombre}: {nota_txt} ({est}, {info['creditos']} créditos)",
            COLOR_ESTADO[est],
            args,
        )
    return 0


def cmd_asig_nota(args):
    try:
        store.set_nota(args.nombre, args.nota)
    except KeyError:
        _print(f"Error: la asignatura {args.nombre!r} no existe.", Fore.RED, args)
        return 1
    est = store.estado(args.nota)
    _print(f"Nota de {args.nombre}: {args.nota:g} ({est}).", COLOR_ESTADO[est], args)
    return 0


def cmd_asig_remove(args):
    try:
        store.remove_asignatura(args.nombre)
    except KeyError:
        _print(f"Error: la asignatura {args.nombre!r} no existe.", Fore.RED, args)
        return 1
    _print(f"Eliminada la asignatura {args.nombre}.", Fore.YELLOW, args)
    return 0


def cmd_resumen(args):
    datos = store.cargar()
    if not datos:
        _print("No tienes asignaturas todavía.", Fore.CYAN, args)
        return 0
    estados = [store.estado(info["nota"]) for info in datos.values()]
    n = len(datos)
    aprobadas = estados.count("aprobada")
    suspendidas = estados.count("suspendida")
    pendientes = estados.count("pendiente")
    notas = [info["nota"] for info in datos.values() if info["nota"] is not None]
    media = sum(notas) / len(notas) if notas else None

    _print(f"Asignaturas: {n}", Fore.CYAN, args)
    _print(f"  Aprobadas:   {aprobadas}", Fore.GREEN, args)
    _print(f"  Suspendidas: {suspendidas}", Fore.RED, args)
    _print(f"  Pendientes:  {pendientes}", Fore.YELLOW, args)
    if media is not None:
        _print(f"Media de notas: {media:.2f}", Fore.MAGENTA, args)
    return 0


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
