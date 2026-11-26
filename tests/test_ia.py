import io
import os
import unittest
from unittest import mock

import httpx

from micli import clic
from micli.click_cli import main as main_click


class TestSinRed(unittest.TestCase):
    """Sin conexión la IA debe explicar el problema y salir con 1."""

    def setUp(self):
        self._clave = os.environ.get("OPENAI_API_KEY")
        os.environ["OPENAI_API_KEY"] = "sk-finta"
        self._out = clic.out

    def tearDown(self):
        if self._clave is None:
            os.environ.pop("OPENAI_API_KEY", None)
        else:
            os.environ["OPENAI_API_KEY"] = self._clave
        clic.out = self._out

    def test_ia_sin_conexion_explica_y_sale_1(self):
        def sin_red(*a, **k):
            raise httpx.ConnectError("failed to resolve")

        clic.out = io.StringIO()
        with mock.patch.object(httpx, "post", sin_red):
            codigo = main_click(["--no-color", "ia", "hola"])
        salida = clic.out.getvalue()
        self.assertEqual(codigo, 1)
        self.assertIn("Sin conexión", salida)


if __name__ == "__main__":
    unittest.main()
