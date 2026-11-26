# micli

CLI de ejemplo para gestionar asignaturas y ejecutar acciones automatizadas
definidas en `acciones.json`.

## Instalación

```bash
git clone <url-del-repositorio>
cd prueba
pip install -e .
```

Si tu sistema no tiene `pip` instalado, usa el script de ayuda (instala pip
vía `get-pip.py` en modo usuario y luego las dependencias):

```bash
sh scripts/instalar-ia.sh
```

Verifica la instalación:

```bash
micli --help
# o sin instalar:
python3 -m micli --help
```

## Uso

La CLI está escrita con **click** (entrada: `micli`). La versión antigua con
`argparse` sigue disponible como `micli-argparse` o `python3 -m micli`.

```bash
# Saludo y utilidades rápidas
micli saluda Ana
micli hola
micli hola --tipo chiste
micli despide Ana
micli adios
micli adios --tipo frase
micli ahora -f "%d/%m/%Y"

# Gestor de asignaturas (persiste en ~/.config/micli/asignaturas.json)
micli asignaturas add "Matemáticas" -c 6
micli asignaturas nota "Matemáticas" 8
micli asignaturas list
micli asignaturas remove "Matemáticas"
micli resumen

# Organizar archivos en carpetas de asignaturas (interactivo)
micli asignaturas organizar ~/Descargas
micli asignaturas organizar ~/Descargas --destino ~/Asignaturas --dry-run

# Acciones automatizadas (definidas en acciones.json)
micli acciones
micli ejecutar estado
micli ejecutar sube "fix: typo en README"
micli ejecutar --dry-run sube "fix: typo"

# Organizar archivos de una carpeta por tipo
micli organizar ~/Descargas
micli organizar --dry-run ~/Descargas

# IA (OpenAI o Gemini) — necesita OPENAI_API_KEY o GEMINI_API_KEY
export OPENAI_API_KEY=sk-...
micli ia "Explícame qué es una base de datos"
micli ia -m gpt-4o "Resume el teorema de Pitágoras"
MICLI_IA_PROVEEDOR=gemini micli ia "Explícame qué es una base de datos"
micli ia -p gemini "Explícame qué es una base de datos"
micli asignaturas ia-consejo

# Exámenes con IA (desde tus resúmenes txt/md/pdf, o texto con --texto)
micli examen crear ~/apuntes/tema4.pdf -t "Tema 4" -n 10 -d dificil -p gemini
micli examen crear --texto "La fotosíntesis convierte luz en energía..."
micli examen list
```

## Exámenes (`micli examen`)

`micli examen crear <resumen>` (txt, md o pdf; o `--texto "..."`) pide a la IA
que te haga un examen interactivo: preguntas de tipo test, corto o desarrollo,
con `-d facil|media|dificil` y `-n` número de preguntas. Respondes una a una y
al terminar la IA corrige, te da nota 0-10 y feedback por pregunta. El
resultado se guarda en `~/.config/micli/examenes/`; `micli examen list` muestra
el histórico con fechas y notas.

La lectura de PDF usa `pypdf` (opcional: `pip install 'micli[pdf]'`) o
`pdftotext` si lo tienes; si no, pega el contenido con `--texto`.

## IA

`micli ia <pregunta>` envía tu pregunta a la API de chat de OpenAI (por defecto
`gpt-4o-mini`; cámbiala con `-m` o con la variable `MICLI_IA_MODELO`).

Con `-p/--proveedor gemini` (o `MICLI_IA_PROVEEDOR=gemini`) usa la API de
Gemini (`gemini-flash-lite-latest` por defecto) con tu `GEMINI_API_KEY`.

`micli asignaturas ia-consejo` pasa tus asignaturas y notas a la IA y devuelve
un consejo de estudio personalizado en 4-6 frases.

Necesitas una API key ([OpenAI](https://platform.openai.com/api-keys) o
[Gemini](https://aistudio.google.com/apikey)) y exportarla como
`OPENAI_API_KEY` o `GEMINI_API_KEY`. Si falta la key o la librería `httpx`, o
no hay red, el comando lo explica con un mensaje claro (p. ej. `Sin conexión
con la API...`) y sale con código 1; el resto de comandos no necesita red.

## Organizar archivos

`micli organizar` mueve los archivos a subcarpetas según su extensión
(`imagenes`, `documentos`, `videos`, `audio`, `codigo`, `comprimidos`,
`datos`, `otros`). Ignora archivos ocultos salvo que uses `--ocultos`, y no
sobrescribe: si ya existe un archivo con el mismo nombre añade ` (1)`, ` (2)`, etc.

`micli asignaturas organizar` pregunta a qué asignatura pertenece cada archivo y
lo mueve a `~/Asignaturas/<Asignatura>/` (o a la carpeta de `--destino`). Las
asignaturas por defecto son Programación, Base de datos, Lenguajes, Entornos de
desarrollo y Sistemas informáticos, además de las que tengas registradas. Usa
`--dry-run` para verlo sin mover nada; los archivos ocultos se ignoran salvo
que uses `--ocultos`.

## Más utilidades

- `micli hola`: saludo con un chiste o una frase motivadora al azar (`--tipo
  chiste|frase|saludo`). El contenido está en `micli/hola.py`: puedes añadir el
  tuyo.
- `micli adios`: lo mismo al despedirte (`--tipo chiste|frase|despedida`); las
  despedidas están en `micli/adios.py`.
- `micli ahora`: fecha y hora actuales; `-f` acepta un formato strftime
  (ej. `-f "%d/%m/%Y"`).
- `--no-color`: desactiva los colores en cualquier comando.

## Interfaz (TUI con rich)

Si tienes `rich` instalado (`pip install 'micli[ui]'`), `asignaturas list`,
`resumen` y `examen list` se muestran como tablas, y los exámenes como paneles
con bordes de color. Controla con `micli ui on` / `micli ui off` (se guarda en
`~/.config/micli/ui.json`); `--no-color` también la desactiva.

## Acciones propias

Edita `acciones.json` para añadir tus tareas automatizadas. Cada acción
declara un comando de shell con placeholders `{1}`, `{2}`, ... que se
sustituyen (citados con `shlex.quote`) por los argumentos que pases a
`micli ejecutar`.

Incluye 6 acciones listas: `estado`, `sube`, `limpia` (peligrosa), `prueba`,
`pendientes` y `respaldo`.

```bash
micli acciones                          # lista con descripción y ejemplos
micli ejecutar pendientes               # TODO/FIXME del código
micli ejecutar prueba + estado          # encadena acciones con + (para si una falla)
micli ejecutar --dry-run limpia         # simula antes de ejecutar
micli ejecutar limpia                   # pide confirmación (acción "peligrosa")
micli ejecutar --yes limpia             # salta la confirmación
```

Reglas anti-sorpresa: `--dry-run` muestra el comando exacto (y avisa si la
acción es peligrosa) sin ejecutarlo; las acciones con `"peligrosa": true`
piden confirmación explícita antes de ejecutarse; al encadenar con `+` la
ejecución se detiene si una acción falla.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

## Decisiones de arquitectura

Las ADRs (Architectural Decision Records) están en [docs/adr/](docs/adr/).
