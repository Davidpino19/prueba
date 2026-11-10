import io
import json
import os
import tempfile
import unittest
from contextlib import contextmanager

from micli import cli
from micli import hola
from micli.cli import main


@contextmanager
def capture_out():
    buf = io.StringIO()
    antiguo = cli.out
    cli.out = buf
    try:
        yield buf
    finally:
        cli.out = antiguo


class TestCli(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.ruta = os.path.join(self.dir, "asignaturas.json")
        os.environ["MICLI_DATOS"] = self.ruta

        self.ruta_acciones = os.path.join(self.dir, "acciones.json")
        with open(self.ruta_acciones, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "acciones": {
                        "eco": {
                            "descripcion": "Eco de prueba",
                            "comando": "echo hola {1}",
                        },
                        "nombrado": {
                            "descripcion": "Acción con nombre",
                            "comando": "echo {nombre}",
                            "ayuda": "micli ejecutar nombrado",
                            "ejemplos": ["micli ejecutar nombrado --nombre=Ana"],
                        },
                        "falla": {"descripcion": "Falla", "comando": "exit 3"},
                    }
                },
                f,
            )
        os.environ["MICLI_ACCIONES"] = self.ruta_acciones

    def tearDown(self):
        del os.environ["MICLI_DATOS"]
        del os.environ["MICLI_ACCIONES"]

    def run_cli(self, argv):
        with capture_out() as buf:
            code = main(["--no-color"] + argv)
        return code, buf.getvalue()

    def run_cli_entrada(self, argv, respuestas):
        it = iter(respuestas)
        antiguo = cli.entrada
        cli.entrada = lambda _prompt="": next(it)
        try:
            with capture_out() as buf:
                code = main(["--no-color"] + argv)
        finally:
            cli.entrada = antiguo
        return code, buf.getvalue()

    def test_saludo_simple(self):
        code, out = self.run_cli(["saluda", "Ana"])
        self.assertEqual(code, 0)
        self.assertEqual(out, "Hola, Ana!\n")

    def test_saludo_verbose(self):
        code, out = self.run_cli(["saluda", "Ana", "-v"])
        self.assertEqual(code, 0)
        self.assertIn("Hola, Ana!", out)
        self.assertIn("verbose", out)

    def test_falta_nombre(self):
        with self.assertRaises(SystemExit):
            main(["saluda"])

    def test_sin_comando(self):
        with self.assertRaises(SystemExit):
            main([])

    def test_ahora(self):
        code, out = self.run_cli(["ahora"])
        self.assertEqual(code, 0)
        self.assertRegex(out.strip(), r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")

    def test_ahora_formato(self):
        code, out = self.run_cli(["ahora", "-f", "%Y"])
        self.assertEqual(code, 0)
        self.assertRegex(out.strip(), r"\d{4}")

    def test_despide(self):
        code, out = self.run_cli(["despide", "Luis"])
        self.assertEqual(code, 0)
        self.assertEqual(out, "¡Hasta luego, Luis!\n")

    def test_hola_chiste(self):
        code, out = self.run_cli(["hola", "--tipo", "chiste"])
        self.assertEqual(code, 0)
        self.assertTrue(any(saludo in out for saludo in hola.SALUDOS))
        self.assertIn("Chiste:", out)
        self.assertTrue(any(chiste in out for chiste in hola.CHISTES))

    def test_hola_frase(self):
        code, out = self.run_cli(["hola", "--tipo", "frase"])
        self.assertEqual(code, 0)
        self.assertTrue(any(saludo in out for saludo in hola.SALUDOS))
        self.assertIn("Frase:", out)
        self.assertTrue(any(frase in out for frase in hola.FRASES))

    def test_hola_saludo(self):
        code, out = self.run_cli(["hola", "--tipo", "saludo"])
        self.assertEqual(code, 0)
        self.assertIn(out.strip(), hola.SALUDOS)
        self.assertNotIn("Chiste:", out)
        self.assertNotIn("Frase:", out)

    def test_hola_auto(self):
        code, out = self.run_cli(["hola"])
        self.assertEqual(code, 0)
        self.assertTrue("Chiste:" in out or "Frase:" in out)

    def test_colores_activos(self):
        with capture_out() as buf:
            code = main(["saluda", "Ana"])
        self.assertEqual(code, 0)
        self.assertIn("\033[", buf.getvalue())

    def test_asig_add_y_list(self):
        code, out = self.run_cli(["asignaturas", "add", "Matemáticas", "-c", "6"])
        self.assertEqual(code, 0)
        self.assertIn("Matemáticas", out)
        code, out = self.run_cli(["asignaturas", "list"])
        self.assertEqual(code, 0)
        self.assertIn("Matemáticas: — (pendiente, 6 créditos)", out)

    def test_asig_add_duplicada(self):
        self.run_cli(["asignaturas", "add", "Física"])
        code, out = self.run_cli(["asignaturas", "add", "Física"])
        self.assertEqual(code, 1)
        self.assertIn("ya existe", out)

    def test_asig_nota_aprobada(self):
        self.run_cli(["asignaturas", "add", "Historia"])
        code, out = self.run_cli(["asignaturas", "nota", "Historia", "7"])
        self.assertEqual(code, 0)
        self.assertIn("aprobada", out)
        code, out = self.run_cli(["asignaturas", "list"])
        self.assertIn("Historia: 7 (aprobada", out)

    def test_asig_nota_suspendida(self):
        self.run_cli(["asignaturas", "add", "Química"])
        code, out = self.run_cli(["asignaturas", "nota", "Química", "3"])
        self.assertEqual(code, 0)
        self.assertIn("suspendida", out)

    def test_asig_nota_inexistente(self):
        code, out = self.run_cli(["asignaturas", "nota", "NoExiste", "8"])
        self.assertEqual(code, 1)
        self.assertIn("no existe", out)

    def test_asig_remove(self):
        self.run_cli(["asignaturas", "add", "Biología"])
        code, out = self.run_cli(["asignaturas", "remove", "Biología"])
        self.assertEqual(code, 0)
        code, out = self.run_cli(["asignaturas", "list"])
        self.assertIn("No tienes asignaturas", out)

    def test_asig_remove_inexistente(self):
        code, out = self.run_cli(["asignaturas", "remove", "Nada"])
        self.assertEqual(code, 1)

    def test_resumen(self):
        self.run_cli(["asignaturas", "add", "A"])
        self.run_cli(["asignaturas", "add", "B"])
        self.run_cli(["asignaturas", "add", "C"])
        self.run_cli(["asignaturas", "nota", "A", "8"])
        self.run_cli(["asignaturas", "nota", "B", "2"])
        code, out = self.run_cli(["resumen"])
        self.assertEqual(code, 0)
        self.assertIn("Asignaturas: 3", out)
        self.assertIn("Aprobadas:   1", out)
        self.assertIn("Suspendidas: 1", out)
        self.assertIn("Pendientes:  1", out)
        self.assertIn("Media de notas: 5.00", out)

    def test_resumen_vacio(self):
        code, out = self.run_cli(["resumen"])
        self.assertEqual(code, 0)
        self.assertIn("No tienes asignaturas", out)

    def test_acciones_lista(self):
        code, out = self.run_cli(["acciones"])
        self.assertEqual(code, 0)
        self.assertIn("eco: Eco de prueba", out)
        self.assertIn("micli ejecutar nombrado", out)
        self.assertIn("micli ejecutar nombrado --nombre=Ana", out)

    def test_ejecutar_dry_run(self):
        code, out = self.run_cli(["ejecutar", "--dry-run", "eco", "mundo"])
        self.assertEqual(code, 0)
        self.assertEqual(out, "echo hola mundo\n")

    def test_ejecutar_dry_run_cita(self):
        code, out = self.run_cli(["ejecutar", "--dry-run", "eco", "hola mundo"])
        self.assertEqual(code, 0)
        self.assertEqual(out, "echo hola 'hola mundo'\n")

    def test_ejecutar_nombrado(self):
        code, out = self.run_cli(
            ["ejecutar", "--dry-run", "nombrado", "--nombre=Ana"]
        )
        self.assertEqual(code, 0)
        self.assertEqual(out, "echo Ana\n")

    def test_ejecutar_ejecuta(self):
        code, out = self.run_cli(["ejecutar", "eco", "mundo"])
        self.assertEqual(code, 0)
        self.assertIn("$ echo hola mundo", out)
        self.assertIn("hola mundo", out)

    def test_ejecutar_inexistente(self):
        code, out = self.run_cli(["ejecutar", "nada"])
        self.assertEqual(code, 1)
        self.assertIn("no existe", out)

    def test_ejecutar_falta_parametro(self):
        code, out = self.run_cli(["ejecutar", "eco"])
        self.assertEqual(code, 1)
        self.assertIn("Faltan parámetros", out)

    def test_ejecutar_codigo_de_salida(self):
        code, out = self.run_cli(["ejecutar", "falla"])
        self.assertEqual(code, 3)
        self.assertIn("código 3", out)

    def _carpeta_temporal(self, nombres):
        carpeta = tempfile.mkdtemp()
        for nombre in nombres:
            with open(os.path.join(carpeta, nombre), "w"):
                pass
        return carpeta

    def test_organizar(self):
        carpeta = self._carpeta_temporal(
            ["foto.JPG", "notas.txt", "script.py", "raro.xyz", "datos.csv", ".oculto"]
        )
        os.makedirs(os.path.join(carpeta, "subdir"))
        code, out = self.run_cli(["organizar", carpeta])
        self.assertEqual(code, 0)
        self.assertTrue(os.path.isfile(os.path.join(carpeta, "imagenes", "foto.JPG")))
        self.assertTrue(os.path.isfile(os.path.join(carpeta, "documentos", "notas.txt")))
        self.assertTrue(os.path.isfile(os.path.join(carpeta, "codigo", "script.py")))
        self.assertTrue(os.path.isfile(os.path.join(carpeta, "datos", "datos.csv")))
        self.assertTrue(os.path.isfile(os.path.join(carpeta, "otros", "raro.xyz")))
        self.assertTrue(os.path.isfile(os.path.join(carpeta, ".oculto")))
        self.assertTrue(os.path.isdir(os.path.join(carpeta, "subdir")))
        self.assertIn("Organizados 5 archivo(s).", out)

    def test_organizar_dry_run(self):
        carpeta = self._carpeta_temporal(["notas.txt"])
        code, out = self.run_cli(["organizar", "--dry-run", carpeta])
        self.assertEqual(code, 0)
        self.assertIn("notas.txt -> documentos", out)
        self.assertIn("Se moverían 1 archivo(s).", out)
        self.assertTrue(os.path.isfile(os.path.join(carpeta, "notas.txt")))

    def test_organizar_colision(self):
        carpeta = self._carpeta_temporal(["foto.jpg"])
        os.makedirs(os.path.join(carpeta, "imagenes"))
        open(os.path.join(carpeta, "imagenes", "foto.jpg"), "w").close()
        code, _ = self.run_cli(["organizar", carpeta])
        self.assertEqual(code, 0)
        self.assertTrue(
            os.path.isfile(os.path.join(carpeta, "imagenes", "foto (1).jpg"))
        )

    def test_organizar_ruta_inexistente(self):
        ruta = os.path.join(tempfile.mkdtemp(), "no-existe")
        code, out = self.run_cli(["organizar", ruta])
        self.assertEqual(code, 1)
        self.assertIn("no es un directorio", out)

    def test_asig_organizar_interactivo(self):
        carpeta = self._carpeta_temporal(["apuntes.txt", "bd.pdf"])
        destino = tempfile.mkdtemp()
        code, out = self.run_cli_entrada(
            ["asignaturas", "organizar", carpeta, "--destino", destino],
            ["1", "2"],
        )
        self.assertEqual(code, 0)
        self.assertIn("1) Programación", out)
        self.assertIn("5) Sistemas informáticos", out)
        self.assertTrue(
            os.path.isfile(
                os.path.join(destino, "Programación", "apuntes.txt")
            )
        )
        self.assertTrue(
            os.path.isfile(
                os.path.join(destino, "Base de datos", "bd.pdf")
            )
        )
        self.assertIn("Organizados 2 archivo(s)", out)

    def test_asig_organizar_omitir(self):
        carpeta = self._carpeta_temporal(["suelto.txt"])
        code, out = self.run_cli_entrada(
            ["asignaturas", "organizar", carpeta], ["0"]
        )
        self.assertEqual(code, 0)
        self.assertIn("Omitido: suelto.txt", out)
        self.assertTrue(os.path.isfile(os.path.join(carpeta, "suelto.txt")))

    def test_asig_organizar_invalida_luego_valida(self):
        carpeta = self._carpeta_temporal(["redes.txt"])
        destino = tempfile.mkdtemp()
        code, out = self.run_cli_entrada(
            ["asignaturas", "organizar", carpeta, "--destino", destino],
            ["99", "5"],
        )
        self.assertEqual(code, 0)
        self.assertIn("Opción no válida", out)
        self.assertTrue(
            os.path.isfile(
                os.path.join(destino, "Sistemas informáticos", "redes.txt")
            )
        )

    def test_asig_organizar_salir(self):
        carpeta = self._carpeta_temporal(["a.txt", "b.txt"])
        destino = tempfile.mkdtemp()
        code, out = self.run_cli_entrada(
            ["asignaturas", "organizar", carpeta, "--destino", destino],
            ["q"],
        )
        self.assertEqual(code, 0)
        self.assertIn("Saliendo sin organizar el resto", out)
        self.assertTrue(os.path.isfile(os.path.join(carpeta, "a.txt")))
        self.assertTrue(os.path.isfile(os.path.join(carpeta, "b.txt")))

    def test_asig_organizar_dry_run(self):
        carpeta = self._carpeta_temporal(["notas.txt"])
        destino = tempfile.mkdtemp()
        code, out = self.run_cli_entrada(
            ["asignaturas", "organizar", carpeta, "--destino", destino,
             "--dry-run"],
            ["1"],
        )
        self.assertEqual(code, 0)
        self.assertIn("(dry-run)", out)
        self.assertIn("Se moverían 1 archivo(s)", out)
        self.assertTrue(os.path.isfile(os.path.join(carpeta, "notas.txt")))

    def test_asig_organizar_colision(self):
        carpeta = self._carpeta_temporal(["foto.jpg"])
        destino = tempfile.mkdtemp()
        os.makedirs(os.path.join(destino, "Programación"))
        open(os.path.join(destino, "Programación", "foto.jpg"), "w").close()
        code, _ = self.run_cli_entrada(
            ["asignaturas", "organizar", carpeta, "--destino", destino],
            ["1"],
        )
        self.assertEqual(code, 0)
        self.assertTrue(
            os.path.isfile(
                os.path.join(destino, "Programación", "foto (1).jpg")
            )
        )

    def test_asig_organizar_ignora_ocultos(self):
        carpeta = self._carpeta_temporal([".oculto", "visible.txt"])
        destino = tempfile.mkdtemp()
        code, _ = self.run_cli_entrada(
            ["asignaturas", "organizar", carpeta, "--destino", destino],
            ["1"],
        )
        self.assertEqual(code, 0)
        self.assertTrue(os.path.isfile(os.path.join(carpeta, ".oculto")))
        self.assertTrue(
            os.path.isfile(
                os.path.join(destino, "Programación", "visible.txt")
            )
        )


if __name__ == "__main__":
    unittest.main()
