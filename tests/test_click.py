import os
import unittest

from micli import clic
from micli.cli import main as main_argparse
from micli.click_cli import main as main_click


class TestEquivalencia(unittest.TestCase):
    """La versión click debe comportarse como la de argparse."""

    def setUp(self):
        self.dir = os.path.dirname(__file__)
        self.ruta = os.path.join(self.dir, "datos-equivalencia.json")
        os.environ["MICLI_DATOS"] = self.ruta

    def tearDown(self):
        os.environ.pop("MICLI_DATOS", None)
        if os.path.exists(self.ruta):
            os.remove(self.ruta)

    def test_sin_comando_es_2(self):
        with self.assertRaises(SystemExit) as ctx:
            main_argparse([])
        self.assertEqual(ctx.exception.code, 2)
        self.assertEqual(main_click([]), 2)

    def test_argumento_faltante_es_2(self):
        with self.assertRaises(SystemExit) as ctx:
            main_argparse(["saluda"])
        self.assertEqual(ctx.exception.code, 2)
        self.assertEqual(main_click(["saluda"]), 2)

    def test_proveedor_invalido_es_2(self):
        with self.assertRaises(SystemExit) as ctx:
            main_argparse(["--no-color", "ia", "-p", "malo", "hola"])
        self.assertEqual(ctx.exception.code, 2)
        self.assertEqual(main_click(["--no-color", "ia", "-p", "malo", "hola"]), 2)

    def test_asignaturas_flujo(self):
        self.assertEqual(main_click(["asignaturas", "add", "Matemáticas", "-c", "6"]), 0)
        self.assertEqual(main_click(["asignaturas", "nota", "Matemáticas", "8"]), 0)
        self.assertEqual(main_click(["resumen"]), 0)
        self.assertEqual(main_click(["asignaturas", "remove", "Matemáticas"]), 0)
        self.assertEqual(main_click(["asignaturas", "remove", "Nada"]), 1)


if __name__ == "__main__":
    unittest.main()
