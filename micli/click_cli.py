from pathlib import Path

import click

from micli import clic
from micli import examen as examen_mod
from micli import ia as ia_mod
from micli import ui


class MicliGroup(click.Group):
    def parse_args(self, ctx, args):
        if not args:
            raise click.UsageError("Missing command.", ctx=ctx)
        return super().parse_args(ctx, args)


@click.group(cls=MicliGroup, context_settings={"help_option_names": ["-h", "--help"]})
@click.option("--no-color", is_flag=True, help="Desactiva los colores")
@click.version_option(package_name="micli", prog_name="micli")
@click.pass_context
def app(ctx, no_color):
    """Mi primera CLI."""
    ctx.ensure_object(dict)
    if no_color:
        clic.activar_sin_color()
    else:
        clic.restaurar_color()
        ui.habilitar()
        ui._reset()


@app.command()
@click.argument("nombre")
@click.option("-v", "--verbose", is_flag=True, help="Modo verbose")
def saluda(nombre, verbose):
    """Saluda a alguien."""
    clic.imprimir(f"Hola, {nombre}!", clic.VERDE)
    if verbose:
        clic.imprimir(
            f"(verbose: comando=saluda, nombre={nombre!r})", clic.AZUL
        )


@app.command()
@click.option(
    "-t", "--tipo",
    type=click.Choice(["auto", "chiste", "frase", "saludo"]),
    default="auto", show_default=True,
    help="Qué acompañar al saludo",
)
def hola(tipo):
    """Saludo con un chiste o una frase motivadora."""
    from micli import hola as hola_mod

    saludo, etiqueta, texto = hola_mod.mensaje(tipo)
    clic.imprimir(saludo, clic.VERDE)
    if texto is not None:
        clic.imprimir(f"{etiqueta}: {texto}",
                      clic.AZUL if etiqueta == "Chiste" else clic.MAGENTA)


@app.command()
@click.argument("nombre")
def despide(nombre):
    """Se despide de alguien."""
    clic.imprimir(f"¡Hasta luego, {nombre}!", clic.AMARILLO)


@app.command()
@click.option(
    "-t", "--tipo",
    type=click.Choice(["auto", "chiste", "frase", "despedida"]),
    default="auto", show_default=True,
    help="Qué acompañar a la despedida",
)
def adios(tipo):
    """Despedida con un chiste o una frase."""
    from micli import adios as adios_mod

    despedida, etiqueta, texto = adios_mod.mensaje(tipo)
    clic.imprimir(despedida, clic.AMARILLO)
    if texto is not None:
        clic.imprimir(f"{etiqueta}: {texto}",
                      clic.AZUL if etiqueta == "Chiste" else clic.MAGENTA)


@app.command()
@click.option("-f", "--formato", default="%Y-%m-%d %H:%M:%S", show_default=True,
              help="Formato strftime")
def ahora(formato):
    """Muestra la fecha y hora actual."""
    from datetime import datetime

    clic.imprimir(datetime.now().strftime(formato), clic.MAGENTA)


@app.group()
def asignaturas():
    """Gestiona tus asignaturas."""


@asignaturas.command("add")
@click.argument("nombre")
@click.option("-c", "--creditos", type=int, default=0, show_default=True,
              help="Créditos")
def asig_add(nombre, creditos):
    """Añade una asignatura."""
    from micli import store

    try:
        store.add_asignatura(nombre, creditos)
    except ValueError as e:
        clic.imprimir(f"Error: {e}", clic.ROJO)
        raise SystemExit(1)
    clic.imprimir(f"Añadida la asignatura {nombre} ({creditos} créditos).",
                  clic.VERDE)


@asignaturas.command("list")
def asig_list():
    """Lista las asignaturas."""
    from micli import store

    datos = store.cargar()
    if not datos:
        clic.imprimir("No tienes asignaturas todavía.", clic.AZUL)
        return
    if ui.tabla_asignaturas(datos, store.estado):
        return
    for nombre, info in sorted(datos.items()):
        est = store.estado(info["nota"])
        nota_txt = "—" if info["nota"] is None else f"{info['nota']:g}"
        color = {"pendiente": clic.AMARILLO, "aprobada": clic.VERDE,
                 "suspendida": clic.ROJO}[est]
        clic.imprimir(
            f"{nombre}: {nota_txt} ({est}, {info['creditos']} créditos)", color
        )


@asignaturas.command("nota")
@click.argument("nombre")
@click.argument("nota", type=float)
def asig_nota(nombre, nota):
    """Guarda la nota de una asignatura."""
    from micli import store

    try:
        store.set_nota(nombre, nota)
    except KeyError:
        clic.imprimir(f"Error: la asignatura {nombre!r} no existe.", clic.ROJO)
        raise SystemExit(1)
    est = store.estado(nota)
    color = {"pendiente": clic.AMARILLO, "aprobada": clic.VERDE,
             "suspendida": clic.ROJO}[est]
    clic.imprimir(f"Nota de {nombre}: {nota:g} ({est}).", color)


@asignaturas.command("remove")
@click.argument("nombre")
def asig_remove(nombre):
    """Elimina una asignatura."""
    from micli import store

    try:
        store.remove_asignatura(nombre)
    except KeyError:
        clic.imprimir(f"Error: la asignatura {nombre!r} no existe.", clic.ROJO)
        raise SystemExit(1)
    clic.imprimir(f"Eliminada la asignatura {nombre}.", clic.AMARILLO)


@asignaturas.command("ia-consejo")
@click.option("-m", "--modelo", help="Modelo a usar (por defecto, el del proveedor)")
@click.option("-p", "--proveedor", type=click.Choice(["gemini", "openai"]),
              help="Proveedor de IA")
def asig_ia_consejo(modelo, proveedor):
    """Consejo de estudio con IA."""
    from micli import ia, store

    datos = store.cargar()
    if not datos:
        clic.imprimir("No tienes asignaturas todavía.", clic.AZUL)
        return
    clic.imprimir("Pensando...", clic.AZUL)
    try:
        consejo = ia.consejo_estudio(datos, modelo=modelo,
                                     proveedor_nombre=proveedor)
    except ia.IaError as e:
        clic.imprimir(f"Error: {e}", clic.ROJO)
        raise SystemExit(1)
    clic.imprimir(consejo, clic.MAGENTA)


@app.command()
def resumen():
    """Resumen de tus asignaturas."""
    from micli import store

    datos = store.cargar()
    if not datos:
        clic.imprimir("No tienes asignaturas todavía.", clic.AZUL)
        return
    estados = [store.estado(info["nota"]) for info in datos.values()]
    aprobadas = estados.count("aprobada")
    suspendidas = estados.count("suspendida")
    pendientes = estados.count("pendiente")
    notas = [info["nota"] for info in datos.values() if info["nota"] is not None]
    media = sum(notas) / len(notas) if notas else None

    if not ui.resumen_stats(
        len(datos), aprobadas, suspendidas, pendientes, media
    ):
        clic.imprimir(f"Asignaturas: {len(datos)}", clic.AZUL)
        clic.imprimir(f"  Aprobadas:   {aprobadas}", clic.VERDE)
        clic.imprimir(f"  Suspendidas: {suspendidas}", clic.ROJO)
        clic.imprimir(f"  Pendientes:  {pendientes}", clic.AMARILLO)
        if media is not None:
            clic.imprimir(f"Media de notas: {media:.2f}", clic.MAGENTA)


@app.command()
def acciones():
    """Lista las acciones disponibles."""
    from micli import acciones as acciones_mod

    try:
        definidas = acciones_mod.cargar_acciones()
    except acciones_mod.AccionError as e:
        clic.imprimir(f"Error: {e}", clic.ROJO)
        raise SystemExit(1)
    if not definidas:
        clic.imprimir("No hay acciones definidas.", clic.AZUL)
        return
    for nombre, acc in definidas.items():
        aviso = " (peligrosa)" if acc.get("peligrosa") else ""
        clic.imprimir(f"{nombre}: {acc.get('descripcion', '')}{aviso}", clic.AZUL)
        if acc.get("ayuda"):
            clic.imprimir(f"  {acc['ayuda']}", clic.AMARILLO)
        for ejemplo in acc.get("ejemplos", []):
            clic.imprimir(f"  {ejemplo}", clic.MAGENTA)


@app.command()
@click.option("-n", "--dry-run", is_flag=True, help="Muestra el comando sin ejecutarlo")
@click.option("-y", "--yes", is_flag=True,
              help="No pedir confirmación en acciones peligrosas")
@click.argument("accion")
@click.argument("argumentos", nargs=-1, type=click.UNPROCESSED)
def ejecutar(dry_run, yes, accion, argumentos):
    """Ejecuta una o varias acciones de acciones.json (separadas por +)."""
    import subprocess

    from micli import acciones as acciones_mod

    try:
        definidas = acciones_mod.cargar_acciones()
        segmentos = acciones_mod.segmentar(accion, argumentos)
    except acciones_mod.AccionError as e:
        clic.imprimir(f"Error: {e}", clic.ROJO)
        raise SystemExit(1)

    for seg in segmentos:
        nombre, args = seg[0], seg[1:]
        acc = definidas.get(nombre)
        if acc is None:
            clic.imprimir(f"Error: la acción {nombre!r} no existe.", clic.ROJO)
            raise SystemExit(1)
        try:
            comando = acciones_mod.construir(acc["comando"], args)
        except acciones_mod.AccionError as e:
            clic.imprimir(f"Error: {e}", clic.ROJO)
            raise SystemExit(1)

        if dry_run:
            clic.imprimir(comando, clic.MAGENTA)
            if acciones_mod.es_peligrosa(acc):
                clic.imprimir("  (acción peligrosa: borrará/sobrescribirá)",
                              clic.AMARILLO)
            continue

        if acciones_mod.es_peligrosa(acc) and not yes:
            if not acciones_mod.confirmar(nombre, acc, clic.entrada):
                clic.imprimir(f"Cancelada: {nombre}.", clic.AMARILLO)
                return

        clic.imprimir(f"$ {comando}", clic.AZUL)
        resultado = subprocess.run(
            comando, shell=True, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )
        if resultado.stdout:
            print(resultado.stdout, end="", file=clic.out)
            clic.out.flush()
        if resultado.returncode != 0:
            clic.imprimir(f"La acción terminó con código {resultado.returncode}.",
                          clic.ROJO)
            raise SystemExit(resultado.returncode)


@app.command("organizar")
@click.argument("ruta", default=".")
@click.option("-n", "--dry-run", is_flag=True, help="Muestra los movimientos sin hacerlos")
@click.option("--ocultos", is_flag=True, help="Incluye también los archivos ocultos")
def organizar_cmd(ruta, dry_run, ocultos):
    """Organiza archivos en carpetas por tipo."""
    from micli import organizar

    try:
        movidos = organizar.organizar(ruta, dry_run=dry_run, ocultos=ocultos)
    except organizar.OrganizarError as e:
        clic.imprimir(f"Error: {e}", clic.ROJO)
        raise SystemExit(1)
    if not movidos:
        clic.imprimir("No hay archivos que organizar.", clic.AZUL)
        return
    raiz = Path(ruta)
    color = clic.MAGENTA if dry_run else clic.VERDE
    for origen, destino in movidos:
        clic.imprimir(f"{origen.name} -> {destino.relative_to(raiz)}", color)
    if dry_run:
        clic.imprimir(f"Se moverían {len(movidos)} archivo(s).", clic.AMARILLO)
    else:
        clic.imprimir(f"Organizados {len(movidos)} archivo(s).", clic.VERDE)


@asignaturas.command("organizar")
@click.argument("ruta", default=".")
@click.option("-d", "--destino",
              default=str(Path.home() / "Asignaturas"), show_default=True,
              help="Carpeta base de las asignaturas")
@click.option("-n", "--dry-run", is_flag=True, help="Muestra los movimientos sin hacerlos")
@click.option("--ocultos", is_flag=True, help="Incluye también los archivos ocultos")
def asig_organizar(ruta, destino, dry_run, ocultos):
    """Mueve archivos a carpetas de asignaturas (interactivo)."""
    from micli import organizar, store

    try:
        archivos = organizar.archivos_sueltos(ruta, ocultos=ocultos)
    except organizar.OrganizarError as e:
        clic.imprimir(f"Error: {e}", clic.ROJO)
        raise SystemExit(1)
    if not archivos:
        clic.imprimir("No hay archivos que organizar.", clic.AZUL)
        return

    opciones = []
    for nombre in organizar.ASIGNATURAS_POR_DEFECTO + list(store.cargar()):
        if nombre not in opciones:
            opciones.append(nombre)

    base = Path(destino).expanduser()
    clic.imprimir(f"Destino: {base}", clic.AZUL)
    clic.imprimir("Asignaturas:", clic.AZUL)
    for i, nombre in enumerate(opciones, 1):
        clic.imprimir(f"  {i}) {nombre}", clic.AZUL)
    clic.imprimir("  0) Omitir   q) Salir", clic.AMARILLO)

    movidos = 0
    omitidos = 0
    for i, origen in enumerate(archivos, 1):
        clic.imprimir(f"\nArchivo {i}/{len(archivos)}: {origen.name}",
                      clic.MAGENTA)
        salir = False
        while True:
            try:
                respuesta = clic.entrada(
                    f"Asignatura [0-{len(opciones)}, q]: "
                ).strip().lower()
            except EOFError:
                respuesta = "q"

            if respuesta == "q":
                salir = True
                break
            if respuesta in ("", "0"):
                omitidos += 1
                clic.imprimir(f"Omitido: {origen.name}", clic.AMARILLO)
                break
            if respuesta.isdigit() and 1 <= int(respuesta) <= len(opciones):
                asignatura = opciones[int(respuesta) - 1]
                carpeta = base / organizar.nombre_carpeta(asignatura)
                if dry_run:
                    clic.imprimir(
                        f"{origen.name} -> {carpeta / origen.name} (dry-run)",
                        clic.MAGENTA,
                    )
                else:
                    try:
                        destino_ok = organizar.mover_a(origen, carpeta)
                    except organizar.OrganizarError as e:
                        clic.imprimir(f"Error: {e}", clic.ROJO)
                        raise SystemExit(1)
                    clic.imprimir(f"{origen.name} -> {destino_ok}", clic.VERDE)
                movidos += 1
                break
            clic.imprimir("Opción no válida.", clic.ROJO)

        if salir:
            clic.imprimir("Saliendo sin organizar el resto.", clic.AMARILLO)
            break

    if dry_run:
        clic.imprimir(
            f"\nSe moverían {movidos} archivo(s) y se omitirían {omitidos}.",
            clic.AMARILLO,
        )
    else:
        clic.imprimir(
            f"\nOrganizados {movidos} archivo(s) y omitidos {omitidos}.",
            clic.VERDE,
        )


@app.group()
def examen():
    """Genera y corrige exámenes con IA a partir de tus resúmenes."""


@examen.command("crear")
@click.argument("fuente", required=False)
@click.option("-t", "--tema", help="Nombre o tema del examen")
@click.option("--texto", help="Contenido del resumen pegado directamente")
@click.option("-d", "--dificultad",
              type=click.Choice(examen_mod.DIFICULTADES), default="media",
              show_default=True, help="Nivel de las preguntas")
@click.option("-n", "--num", default=5, show_default=True,
              help="Número de preguntas")
@click.option("-m", "--modelo", help="Modelo a usar (por defecto, el del proveedor)")
@click.option("-p", "--proveedor", type=click.Choice(["gemini", "openai"]),
              help="Proveedor de IA")
def examen_crear(fuente, tema, texto, dificultad, num, modelo, proveedor):
    """Crea un examen interactivo desde un resumen (txt, md o pdf)."""
    if bool(fuente) == bool(texto):
        clic.imprimir("Indica un fichero o --texto (no ambos, ni ninguno).",
                      clic.ROJO)
        raise SystemExit(1)
    try:
        contenido = examen_mod.leer_resumen(fuente) if fuente else texto
        preguntas = examen_mod.crear(
            contenido, dificultad=dificultad, num=num, modelo=modelo,
            proveedor=proveedor,
        )
    except examen_mod.ExamenError as e:
        clic.imprimir(f"Error: {e}", clic.ROJO)
        raise SystemExit(1)
    except ia_mod.IaError as e:
        clic.imprimir(f"Error: {e}", clic.ROJO)
        raise SystemExit(1)

    nombre = tema or (Path(fuente).stem if fuente else "examen")
    ui.panel(
        f"{len(preguntas)} preguntas · dificultad {dificultad}\n"
        "Responde pregunta a pregunta; respuesta vacía para terminar.",
        titulo=f"Examen de {nombre}",
    ) or clic.imprimir(
        f"Examen de {nombre} · {len(preguntas)} preguntas "
        f"({dificultad}). Responde; vacío para terminar.",
        clic.AZUL,
    )

    respuestas = {}
    for i, pregunta in enumerate(preguntas, 1):
        clic.imprimir(f"\n{i}. ({pregunta['tipo']}) {pregunta['pregunta']}",
                      clic.MAGENTA)
        for opcion in pregunta.get("opciones", []):
            clic.imprimir(f"   {opcion}", clic.AMARILLO)
        respuestas[i] = clic.entrada("Tu respuesta: ").strip()
        if not respuestas[i]:
            clic.imprimir("Sin respuesta: termino aquí.", clic.AMARILLO)
            break

    clic.imprimir("Corrigendo...", clic.AZUL)
    try:
        nota, correcciones = examen_mod.corregir(
            contenido, preguntas, respuestas, modelo=modelo,
            proveedor=proveedor,
        )
    except (examen_mod.ExamenError, ia_mod.IaError) as e:
        clic.imprimir(f"Error: {e}", clic.ROJO)
        raise SystemExit(1)

    color = clic.VERDE if nota >= 5 else clic.ROJO
    ui.panel(
        f"[bold]{nota:.2f}[/bold] sobre 10",
        titulo="Nota",
        estilo="green" if nota >= 5 else "red",
    ) or clic.imprimir(f"\nNota: {nota:.2f}", color)
    for correccion in correcciones:
        numero = correccion.get("numero")
        nota_q = correccion.get("nota")
        bien = correccion.get("acertada")
        marca = "✔" if bien else "✘"
        color = clic.VERDE if bien else clic.ROJO
        ui.panel(
            f"P{numero} — {nota_q}/10\n{correccion.get('feedback', '')}",
            titulo=f"{marca} Pregunta {numero}",
            estilo="green" if bien else "red",
        ) or clic.imprimir(
            f"  {marca} P{numero} ({nota_q}/10): {correccion.get('feedback', '')}",
            color,
        )
    try:
        ruta = examen_mod.guardar(nombre, dificultad, nota, correcciones)
        clic.imprimir(f"Guardado en {ruta}", clic.AZUL)
    except OSError as e:
        clic.imprimir(f"No se pudo guardar: {e}", clic.AMARILLO)


@examen.command("list")
def examen_list():
    """Muestra el histórico de exámenes corregidos."""
    examenes = examen_mod.historial()
    if not examenes:
        clic.imprimir("Todavía no has hecho ningún examen.", clic.AZUL)
        return
    if ui.tabla_examenes(examenes):
        return
    for ex in examenes:
        fecha = str(ex.get("fecha", ""))[:10]
        nota = ex.get("nota")
        color = clic.VERDE if (nota or 0) >= 5 else clic.ROJO
        clic.imprimir(
            f"{fecha}  {ex['nombre']} ({ex.get('dificultad')}) — {nota}/10",
            color,
        )


@app.command()
@click.argument("pregunta")
@click.option("-m", "--modelo", help="Modelo a usar (por defecto, el del proveedor)")
@click.option("-p", "--proveedor", type=click.Choice(["gemini", "openai"]),
              help="Proveedor de IA")
def ia(pregunta, modelo, proveedor):
    """Pregunta algo a la IA (OpenAI o Gemini)."""
    clic.imprimir("Pensando...", clic.AZUL)
    try:
        respuesta = ia_mod.chatear(pregunta, modelo=modelo,
                                   proveedor_nombre=proveedor)
    except ia_mod.IaError as e:
        clic.imprimir(f"Error: {e}", clic.ROJO)
        raise SystemExit(1)
    clic.imprimir(respuesta, clic.VERDE)


@app.group(name="ui")
def ui_grupo():
    """Activa o desactiva la interfaz con tablas y paneles."""


@ui_grupo.command("on")
def ui_on():
    """Activa la interfaz rica."""
    ui.activar(True)
    clic.imprimir(
        "Interfaz activada."
        if ui.RICH else "rich no instalado: instala `pip install rich`.",
        clic.VERDE if ui.RICH else clic.AMARILLO,
    )
    if ui.RICH:
        ui.habilitar()


@ui_grupo.command("off")
def ui_off():
    """Desactiva la interfaz rica."""
    ui.activar(False)
    clic.imprimir("Interfaz desactivada.", clic.AMARILLO)


def main(argv=None):
    args = list(argv) if argv is not None else None
    try:
        app.main(args=args, prog_name="micli", standalone_mode=False)
    except SystemExit as e:
        return e.code or 0
    except click.UsageError as e:
        e.show()
        return e.exit_code
    except click.ClickException as e:
        e.show()
        return e.exit_code
    except click.Abort:
        return 130
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
