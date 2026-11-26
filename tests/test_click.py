import io
import json
import os
import shutil
import tempfile
import unittest
from unittest import mock

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


class TestEjecutar(unittest.TestCase):
    """Encadenado con `+` y confirmación de acciones peligrosas (click)."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.ruta = os.path.join(self.dir, "acciones.json")
        with open(self.ruta, "w", encoding="utf-8") as f:
            json.dump({"acciones": {
                "eco": {"comando": "echo hola {1}"},
                "mal": {"comando": "exit 3"},
                "borra": {"comando": "echo borrando", "peligrosa": True},
            }}, f)
        os.environ["MICLI_ACCIONES"] = self.ruta
        self._out = clic.out
        clic.out = io.StringIO()

    def tearDown(self):
        clic.out = self._out
        os.environ.pop("MICLI_ACCIONES", None)
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_encadenado_con_confirmacion(self):
        with mock.patch.object(clic, "entrada", lambda _p="": "sí"):
            code = main_click(
                ["--no-color", "ejecutar", "eco", "x", "+", "borra"])
        salida = clic.out.getvalue()
        self.assertEqual(code, 0)
        self.assertIn("hola x", salida)
        self.assertIn("borrando", salida)

    def test_peligrosa_cancela_sin_ejecutar(self):
        with mock.patch.object(clic, "entrada", lambda _p="": "no"):
            code = main_click(["--no-color", "ejecutar", "borra"])
        salida = clic.out.getvalue()
        self.assertEqual(code, 0)
        self.assertIn("Cancelada", salida)
        self.assertNotIn("borrando", salida)

    def test_encadenado_para_al_fallar(self):
        code = main_click(["--no-color", "ejecutar", "mal", "+", "eco", "y"])
        self.assertEqual(code, 3)
        self.assertNotIn("hola y", clic.out.getvalue())

    def test_encadenado_invalido_es_1(self):
        code = main_click(["--no-color", "ejecutar", "+", "eco", "y"])
        self.assertEqual(code, 1)
        self.assertIn("Encadenado inválido", clic.out.getvalue())


if __name__ == "__main__":
    unittest.main()
