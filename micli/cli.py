import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from colorama import Fore, Style, init as colorama_init

from micli import __version__
from micli import acciones
from micli import adios
from micli import hola
from micli import organizar
from micli import store

colorama_init(wrap=False, convert=False, strip=False)

out = sys.stdout
entrada = input

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

    hola_p = sub.add_parser("hola", help="Saludo con un chiste o una frase motivadora")
    hola_p.add_argument(
        "-t", "--tipo",
        choices=["auto", "chiste", "frase", "saludo"],
        default="auto",
        help="Qué acompañar al saludo (por defecto: chiste o frase al azar)",
    )
    hola_p.set_defaults(func=cmd_hola)

    despide = sub.add_parser("despide", help="Se despide de alguien")
    despide.add_argument("nombre", help="Nombre a despedir")
    despide.set_defaults(func=cmd_despide)

    adios_p = sub.add_parser("adios", help="Despedida con un chiste o una frase")
    adios_p.add_argument(
        "-t", "--tipo",
        choices=["auto", "chiste", "frase", "despedida"],
        default="auto",
        help="Qué acompañar a la despedida (por defecto: chiste o frase al azar)",
    )
    adios_p.set_defaults(func=cmd_adios)

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

    a_org = sub_asig.add_parser(
        "organizar", help="Mueve archivos a carpetas de asignaturas (interactivo)"
    )
    a_org.add_argument(
        "ruta", nargs="?", default=".",
        help="Carpeta con los archivos (por defecto: el directorio actual)",
    )
    a_org.add_argument(
        "-d", "--destino", default=str(Path.home() / "Asignaturas"),
        help="Carpeta base de las asignaturas (por defecto: ~/Asignaturas)",
    )
    a_org.add_argument(
        "-n", "--dry-run", action="store_true",
        help="Muestra los movimientos sin hacerlos",
    )
    a_org.add_argument(
        "--ocultos", action="store_true",
        help="Incluye también los archivos ocultos",
    )
    a_org.set_defaults(func=cmd_asig_organizar)

    resumen = sub.add_parser("resumen", help="Resumen de tus asignaturas")
    resumen.set_defaults(func=cmd_resumen)

    acciones_p = sub.add_parser("acciones", help="Lista las acciones disponibles")
    acciones_p.set_defaults(func=cmd_acciones)

    ejecutar = sub.add_parser("ejecutar", help="Ejecuta una acción de acciones.json")
    ejecutar.add_argument(
        "-n", "--dry-run", action="store_true",
        help="Muestra el comando sin ejecutarlo",
    )
    ejecutar.add_argument("accion", help="Nombre de la acción")
    ejecutar.add_argument(
        "argumentos", nargs=argparse.REMAINDER,
        help="Argumentos para la acción",
    )
    ejecutar.set_defaults(func=cmd_ejecutar)

    organizar_p = sub.add_parser(
        "organizar", help="Organiza archivos en carpetas por tipo"
    )
    organizar_p.add_argument(
        "ruta", nargs="?", default=".",
        help="Carpeta a organizar (por defecto: el directorio actual)",
    )
    organizar_p.add_argument(
        "-n", "--dry-run", action="store_true",
        help="Muestra los movimientos sin hacerlos",
    )
    organizar_p.add_argument(
        "--ocultos", action="store_true",
        help="Incluye también los archivos ocultos",
    )
    organizar_p.set_defaults(func=cmd_organizar)

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


def cmd_hola(args):
    saludo, etiqueta, texto = hola.mensaje(args.tipo)
    _print(saludo, Fore.GREEN, args)
    if texto is not None:
        color = Fore.CYAN if etiqueta == "Chiste" else Fore.MAGENTA
        _print(f"{etiqueta}: {texto}", color, args)
    return 0


def cmd_despide(args):
    _print(f"¡Hasta luego, {args.nombre}!", Fore.YELLOW, args)
    return 0


def cmd_adios(args):
    despedida, etiqueta, texto = adios.mensaje(args.tipo)
    _print(despedida, Fore.YELLOW, args)
    if texto is not None:
        color = Fore.CYAN if etiqueta == "Chiste" else Fore.MAGENTA
        _print(f"{etiqueta}: {texto}", color, args)
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


def cmd_asig_organizar(args):
    try:
        archivos = organizar.archivos_sueltos(args.ruta, ocultos=args.ocultos)
    except organizar.OrganizarError as e:
        _print(f"Error: {e}", Fore.RED, args)
        return 1
    if not archivos:
        _print("No hay archivos que organizar.", Fore.CYAN, args)
        return 0

    opciones = []
    for nombre in organizar.ASIGNATURAS_POR_DEFECTO + list(store.cargar()):
        if nombre not in opciones:
            opciones.append(nombre)

    base = Path(args.destino).expanduser()
    _print(f"Destino: {base}", Fore.CYAN, args)
    _print("Asignaturas:", Fore.CYAN, args)
    for i, nombre in enumerate(opciones, 1):
        _print(f"  {i}) {nombre}", Fore.CYAN, args)
    _print("  0) Omitir   q) Salir", Fore.YELLOW, args)

    movidos = 0
    omitidos = 0
    for i, origen in enumerate(archivos, 1):
        _print(f"\nArchivo {i}/{len(archivos)}: {origen.name}", Fore.MAGENTA, args)
        salir = False
        while True:
            try:
                respuesta = entrada(
                    f"Asignatura [0-{len(opciones)}, q]: "
                ).strip().lower()
            except EOFError:
                respuesta = "q"

            if respuesta == "q":
                salir = True
                break
            if respuesta in ("", "0"):
                omitidos += 1
                _print(f"Omitido: {origen.name}", Fore.YELLOW, args)
                break
            if respuesta.isdigit() and 1 <= int(respuesta) <= len(opciones):
                asignatura = opciones[int(respuesta) - 1]
                carpeta = base / organizar.nombre_carpeta(asignatura)
                if args.dry_run:
                    _print(
                        f"{origen.name} -> {carpeta / origen.name} (dry-run)",
                        Fore.MAGENTA, args,
                    )
                else:
                    try:
                        destino = organizar.mover_a(origen, carpeta)
                    except organizar.OrganizarError as e:
                        _print(f"Error: {e}", Fore.RED, args)
                        return 1
                    _print(f"{origen.name} -> {destino}", Fore.GREEN, args)
                movidos += 1
                break
            _print("Opción no válida.", Fore.RED, args)

        if salir:
            _print("Saliendo sin organizar el resto.", Fore.YELLOW, args)
            break

    if args.dry_run:
        _print(
            f"\nSe moverían {movidos} archivo(s) y se omitirían {omitidos}.",
            Fore.YELLOW, args,
        )
    else:
        _print(
            f"\nOrganizados {movidos} archivo(s) y omitidos {omitidos}.",
            Fore.GREEN, args,
        )
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


def cmd_acciones(args):
    try:
        definidas = acciones.cargar_acciones()
    except acciones.AccionError as e:
        _print(f"Error: {e}", Fore.RED, args)
        return 1
    if not definidas:
        _print("No hay acciones definidas.", Fore.CYAN, args)
        return 0
    for nombre, acc in definidas.items():
        _print(f"{nombre}: {acc.get('descripcion', '')}", Fore.CYAN, args)
        if acc.get("ayuda"):
            _print(f"  {acc['ayuda']}", Fore.YELLOW, args)
        for ejemplo in acc.get("ejemplos", []):
            _print(f"  {ejemplo}", Fore.MAGENTA, args)
    return 0


def cmd_ejecutar(args):
    try:
        definidas = acciones.cargar_acciones()
    except acciones.AccionError as e:
        _print(f"Error: {e}", Fore.RED, args)
        return 1
    accion = definidas.get(args.accion)
    if accion is None:
        _print(f"Error: la acción {args.accion!r} no existe.", Fore.RED, args)
        return 1
    try:
        comando = acciones.construir(accion["comando"], args.argumentos)
    except acciones.AccionError as e:
        _print(f"Error: {e}", Fore.RED, args)
        return 1

    if args.dry_run:
        _print(comando, Fore.MAGENTA, args)
        return 0

    _print(f"$ {comando}", Fore.CYAN, args)
    out.flush()
    resultado = subprocess.run(
        comando, shell=True, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    if resultado.stdout:
        print(resultado.stdout, end="", file=out)
    if resultado.returncode != 0:
        _print(
            f"La acción terminó con código {resultado.returncode}.",
            Fore.RED, args,
        )
    return resultado.returncode


def cmd_organizar(args):
    try:
        movidos = organizar.organizar(
            args.ruta, dry_run=args.dry_run, ocultos=args.ocultos
        )
    except organizar.OrganizarError as e:
        _print(f"Error: {e}", Fore.RED, args)
        return 1

    if not movidos:
        _print("No hay archivos que organizar.", Fore.CYAN, args)
        return 0

    raiz = Path(args.ruta)
    color = Fore.MAGENTA if args.dry_run else Fore.GREEN
    for origen, destino in movidos:
        _print(f"{origen.name} -> {destino.relative_to(raiz)}", color, args)

    if args.dry_run:
        _print(f"Se moverían {len(movidos)} archivo(s).", Fore.YELLOW, args)
    else:
        _print(f"Organizados {len(movidos)} archivo(s).", Fore.GREEN, args)
    return 0


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
