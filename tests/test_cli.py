import io
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


class TestSaluda(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
