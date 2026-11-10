import io
import json
import os
import tempfile
import unittest
from contextlib import contextmanager

from micli import cli
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


if __name__ == "__main__":
    unittest.main()
