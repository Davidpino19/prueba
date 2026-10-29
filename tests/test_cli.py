import io
import unittest
from contextlib import redirect_stdout

from micli.cli import main


class TestSaluda(unittest.TestCase):
    def run_cli(self, argv):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(argv)
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


if __name__ == "__main__":
    unittest.main()
