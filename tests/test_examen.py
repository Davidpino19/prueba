import io
import json
import os
import tempfile
import unittest
from contextlib import contextmanager

from micli import clic
from micli import examen as examen_mod
from micli import ia
from micli.click_cli import main


@contextmanager
def capture_out():
    buf = io.StringIO()
    antiguo = clic.out
    clic.out = buf
    try:
        yield buf
    finally:
        clic.out = antiguo


class TestExamen(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        os.environ["MICLI_DATOS"] = os.path.join(self.dir, "asignaturas.json")
        os.environ["MICLI_UI_CONF"] = os.path.join(self.dir, "ui.json")
        self.ruta_resumen = os.path.join(self.dir, "tema.txt")
        with open(self.ruta_resumen, "w", encoding="utf-8") as f:
            f.write("Las plantas hacen la fotosíntesis usando luz, agua y CO2.")
        from micli import ui as ui_mod

        self.addCleanup(ui_mod.reset)
        ui_mod.reset()

    def tearDown(self):
        for var in ("MICLI_DATOS", "MICLI_UI_CONF", "MICLI_IA_PROVEEDOR",
                    "GEMINI_API_KEY", "OPENAI_API_KEY"):
            os.environ.pop(var, None)

    def _mock_ia(self, respuestas):
        """Sustituye ia.chat por una cola de respuestas."""
        it = iter(respuestas)
        antiguo = ia.chat
        ia.chat = lambda *a, **k: next(it)
        self.addCleanup(setattr, ia, "chat", antiguo)

    def test_leer_resumen_txt(self):
        texto = examen_mod.leer_resumen(self.ruta_resumen)
        self.assertIn("fotosíntesis", texto)

    def test_leer_resumen_no_existe(self):
        with self.assertRaises(examen_mod.ExamenError):
            examen_mod.leer_resumen(os.path.join(self.dir, "nada.txt"))

    def test_leer_resumen_formato_no_soportado(self):
        ruta = os.path.join(self.dir, "tema.docx")
        open(ruta, "w").close()
        with self.assertRaises(examen_mod.ExamenError):
            examen_mod.leer_resumen(ruta)

    def test_crear_preguntas_json(self):
        self._mock_ia([
            json.dumps({"preguntas": [
                {"pregunta": "¿Qué hacen las plantas?", "tipo": "corto"},
                {"pregunta": "La fotosíntesis usa...", "tipo": "test",
                 "opciones": ["a) luz", "b) piedra"]},
            ]})
        ])
        preguntas = examen_mod.crear("texto del resumen", num=2)
        self.assertEqual(len(preguntas), 2)
        self.assertEqual(preguntas[1]["tipo"], "test")
        self.assertEqual(len(preguntas[1]["opciones"]), 2)

    def test_crear_dificultad_invalida(self):
        with self.assertRaises(examen_mod.ExamenError):
            examen_mod.crear("texto", dificultad="imposible")

    def test_extraer_json_con_bloque(self):
        datos = examen_mod._extraer_json(
            '```json\n{"preguntas": [{"pregunta": "x", "tipo": "corto"}]}\n```'
        )
        self.assertEqual(len(datos["preguntas"]), 1)

    def test_extraer_json_invalido(self):
        with self.assertRaises(examen_mod.ExamenError):
            examen_mod._extraer_json("no hay json aquí")

    def test_corregir(self):
        self._mock_ia([
            json.dumps({"nota": 7.5, "respuestas": [
                {"numero": 1, "nota": 9, "acertada": True,
                 "feedback": "Bien"},
            ]})
        ])
        nota, corr = examen_mod.corregir(
            "contenido",
            [{"pregunta": "p1", "tipo": "corto"}],
            {1: "fotosíntesis"},
        )
        self.assertEqual(nota, 7.5)
        self.assertEqual(corr[0]["numero"], 1)

    def test_guardar_e_historial(self):
        ruta = examen_mod.guardar("Tema1", "media", 8.0, [])
        self.assertTrue(os.path.exists(ruta))
        historial = examen_mod.historial()
        self.assertEqual(historial[0]["nombre"], "Tema1")
        self.assertEqual(historial[0]["nota"], 8.0)

    def test_flujo_crear_y_corregir_por_cli(self):
        self._mock_ia([
            json.dumps({"preguntas": [
                {"pregunta": "¿Qué hacen las plantas?", "tipo": "corto"},
                {"pregunta": "La fotosíntesis usa...", "tipo": "test",
                 "opciones": ["a) luz", "b) piedra"]},
            ]}),
            json.dumps({"nota": 6.0, "respuestas": [
                {"numero": 1, "nota": 8, "acertada": True,
                 "feedback": "Correcta"},
                {"numero": 2, "nota": 4, "acertada": False,
                 "feedback": "Falta CO2"},
            ]}),
        ])
        antiguo_entrada = clic.entrada
        respuestas = iter(["Hacen la fotosíntesis", "a) luz"])
        clic.entrada = lambda _p="": next(respuestas)
        self.addCleanup(setattr, clic, "entrada", antiguo_entrada)
        os.environ["GEMINI_API_KEY"] = "AQ.clave-test"

        with capture_out() as buf:
            codigo = main([
                "examen", "crear", self.ruta_resumen,
                "-t", "Biología", "-p", "gemini",
            ])
        salida = buf.getvalue()
        self.assertEqual(codigo, 0)
        self.assertIn("Examen de Biología", salida)
        self.assertIn("6.00", salida)
        self.assertIn("✔ Pregunta 1", salida)
        self.assertIn("✘ Pregunta 2", salida)
        self.assertIn("Guardado en", salida)

    def test_examen_list_vacio(self):
        with capture_out() as buf:
            codigo = main(["--no-color", "examen", "list"])
        self.assertEqual(codigo, 0)
        self.assertIn("no has hecho ningún examen", buf.getvalue())

    def test_crear_sin_fuente(self):
        with capture_out() as buf:
            codigo = main(["--no-color", "examen", "crear"])
        self.assertEqual(codigo, 1)
        self.assertIn("Indica un fichero", buf.getvalue())

    def test_jugar_flujo_completo(self):
        correccion = json.dumps({
            "nota": 8.5,
            "respuestas": [
                {"numero": 1, "nota": 8.5, "acertada": True,
                 "feedback": "Bien"},
            ],
        })
        self._mock_ia([correccion])
        lineas = []
        nota, ruta = examen_mod.jugar(
            "Tema", "contenido del resumen",
            [{"pregunta": "¿Qué es la fotosíntesis?", "tipo": "corto"}],
            "media",
            imprimir=lambda t, c=None: lineas.append(t),
            entrada=lambda p: "Convertir luz en energía",
        )
        self.assertEqual(nota, 8.5)
        self.assertTrue(ruta and ruta.exists())
        self.assertIn("Nota: 8.50", "\n".join(lineas))
        self.assertIn("✔ P1 (8.5/10)", "\n".join(lineas))

    def test_proveedor_desde_config(self):
        os.environ["GEMINI_API_KEY"] = "AQ.finta"
        os.environ["MICLI_IA_PROVEEDOR"] = "gemini"
        prov = ia.ProveedorIA.desde_config()
        self.assertEqual(prov.nombre, "gemini")
        self.assertFalse(prov.modelo_fijo)
        self.assertEqual(prov.modelos[0], ia.MODELOS["gemini"])

        os.environ["OPENAI_API_KEY"] = "sk-finta"
        fijo = ia.ProveedorIA.desde_config("openai", "gpt-4o")
        self.assertTrue(fijo.modelo_fijo)
        self.assertEqual(fijo.modelos, ["gpt-4o"])

        with self.assertRaises(ia.IaError):
            ia.ProveedorIA.desde_config("otro")


if __name__ == "__main__":
    unittest.main()
