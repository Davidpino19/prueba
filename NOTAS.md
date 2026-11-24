# Notas del desarrollo de `micli`

Resumen de todo lo que hemos construido en la CLI, para repasarlo en clase.

## Estado inicial (`b415ac1`)

CLI mínima de aprendizaje:

- `argparse` con subcomandos (`add_subparsers`).
- Subcomando `saluda <nombre>` con flag `-v/--verbose`.
- Tests con `unittest`.
- Empaquetado con `pyproject.toml` → entry point `micli = micli.cli:main`.

## Sesión 1 — Colores y nuevos comandos (`6fc4704`)

1. **Colores con `colorama`** (`Fore.GREEN`, etc.).
   - Clave: `colorama_init(wrap=False, convert=False, strip=False)` para que NO
     manipule `sys.stdout`. Sin esto, los códigos ANSI se perdían al redirigir.
2. **Capa de salida**: variable `out = sys.stdout` en `cli.py`; todos los `print`
   usan `file=out`. Los tests la sustituyen (`cli.out = io.StringIO()`) y capturan
   la salida aunque contenga códigos de color.
3. **Nuevos comandos**:
   - `despide <nombre>`
   - `ahora [-f FORMATO]` → fecha/hora con `strftime`.
4. **Flag global `--no-color`**: `_print(texto, color, args)` pinta o no según el flag.
5. `colorama` añadido a `dependencies` en `pyproject.toml`.

## Sesión 2 — Gestor de asignaturas (`0a66b0f`)

1. **`micli/store.py`** — persistencia en JSON:
   - Guardado en `~/.config/micli/asignaturas.json`.
   - La ruta se puede sobreescribir con la variable de entorno `MICLI_DATOS`
     (los tests la usan para escribir en un `tempfile` y no tocar la config real).
   - Estructura: `{"Nombre": {"creditos": 6, "nota": null}}`.
   - Funciones: `cargar`, `guardar`, `add_asignatura`, `set_nota`,
     `remove_asignatura`, `estado` (nota ≥ 5 = aprobada).
2. **Subcomando `asignaturas`** con sub-subcomandos anidados
   (`add` / `list` / `nota` / `remove`) usando `add_subparsers` dentro de otro parser.
3. **Errores manejados**: asignatura duplicada → `ValueError`, inexistente →
   `KeyError`. El CLI los pinta en rojo y devuelve código de salida `1`.
4. **`resumen`**: recuento por estado + media de notas.
5. **Colores por estado** (dict `COLOR_ESTADO`): verde aprobada, rojo suspendida,
   amarillo pendiente.
6. **Tests**: 17 tests. `setUp`/`tearDown` fijan `MICLI_DATOS` a un directorio temporal.

## Sesión 3 — Organizar archivos (`f267982`)

1. **`micli/organizar.py`** — mueve los archivos de una carpeta a subcarpetas
   según su extensión: `imagenes`, `documentos`, `videos`, `audio`, `codigo`,
   `comprimidos`, `datos` y `otros`.
   - Flags: `-n/--dry-run` (previsualizar) y `--ocultos` (incluir ocultos).
   - No sobrescribe: si hay colisión añade ` (1)`, ` (2)`, ...
   - Solo mueve archivos sueltos, no carpetas ni enlaces.
2. **`micli acciones` / `micli ejecutar`** conectados al parser, con
   `--dry-run`, placeholders `{1}`/`{nombre}` y defaults `{1:mensaje}`.
3. **Tests**: `test_organizar*` cubren clasificación, dry-run, colisión y ruta
   inválida.
4. **Uso real**: el comando se ha usado para ordenar los archivos del PC,
   comprobando que funciona con una gran cantidad de archivos reales.

## Sesión 4 — IA con OpenAI (`886df37` + esta sesión)

1. **`micli/ia.py`** — cliente de la API de chat de OpenAI con `httpx`
    (petición POST a `/v1/chat/completions`, sin la librería `openai`).
    - Soporte de **Gemini** (`gemini-2.0-flash`) con `MICLI_IA_PROVEEDOR` o
      `-p/--proveedor`: misma función `chat()` que despacha a una u otra API.
      Gemini usa `?key=...` en la URL, `contents[]` y `systemInstruction`.
   - `chat(mensajes, modelo)` → texto de la respuesta; `chatear(texto)` para
     preguntas sueltas; `consejo_estudio(datos)` construye un prompt con las
     asignaturas/notas del store.
   - Modelo por defecto `gpt-4o-mini`, configurable con `-m` o `MICLI_IA_MODELO`.
   - `httpx` se importa de forma opcional (`try/except ImportError`): sin él,
     `micli` sigue funcionando y los comandos `ia` dan un error claro. Clave:
     variable de entorno `OPENAI_API_KEY`.
2. **Nuevos comandos**: `micli ia <pregunta>` y `micli asignaturas ia-consejo`.
   Errores de API (401, etc.) → mensaje rojo + exit 1.
3. **Tests**: 5 tests nuevos con mocks de `ia.httpx` (sin tocar la red):
   chat OK, error de API, falta API key, consejo con datos y consejo sin
   asignaturas. Total: 49 tests.
4. **Nota del entorno**: en esta máquina no hay `pip` ni `ensurepip`; los
   tests de `ia` mockean `httpx` a nivel de módulo para no depender de él.

## Sesión 5 — click + Gemini

1. **`micli/clic.py`**: capa de salida compartida (`out`, `entrada`,
   `imprimir()`, `--no-color` global). `out` y `entrada` siguen siendo
   sustituibles desde los tests.
2. **`micli/click_cli.py`**: toda la CLI portada a **click** (grupo `app`,
   `--no-color`, `--version` con `package_name`, `MicliGroup` que exige
   subcomando → exit 2 como argparse). `pyproject.toml` → `micli` apunta a
   click y `micli-argparse` mantiene la versión vieja.
3. **Gemini en `ia.py`**: `-p/--proveedor` y `MICLI_IA_PROVEEDOR`
   ('openai'|'gemini'), `GEMINI_API_KEY`, modelos por defecto en `MODELOS`.
   Mismo `chat()` despachando a `_chat_openai` o `_chat_gemini`
   (`contents[]` + `systemInstruction` + `?key=`).
4. **Tests**: 54 → 58 con `tests/test_click.py` (equivalencia argparse/click:
   códigos de salida, flujo de asignaturas) y 4 tests de Gemini mockeado.

## Cómo probarla

```bash
python3 -m micli asignaturas add "Matemáticas" -c 6
python3 -m micli asignaturas nota "Matemáticas" 8
python3 -m micli asignaturas list
python3 -m micli resumen

# Tests
python3 -m unittest discover -s tests -v
```

Nota: en esta máquina `python` no existe, usa `python3`.
