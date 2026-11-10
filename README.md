# micli

CLI de ejemplo para gestionar asignaturas y ejecutar acciones automatizadas
definidas en `acciones.json`.

## Instalación

```bash
git clone <url-del-repositorio>
cd prueba
pip install -e .
```

Verifica la instalación:

```bash
micli --help
# o sin instalar:
python3 -m micli --help
```

## Uso

```bash
# Saludo y utilidades rápidas
micli saluda Ana
micli despide Ana
micli ahora -f "%d/%m/%Y"

# Gestor de asignaturas (persiste en ~/.config/micli/asignaturas.json)
micli asignaturas add "Matemáticas" -c 6
micli asignaturas nota "Matemáticas" 8
micli asignaturas list
micli asignaturas remove "Matemáticas"
micli resumen

# Acciones automatizadas (definidas en acciones.json)
micli acciones
micli ejecutar estado
micli ejecutar sube "fix: typo en README"
micli ejecutar --dry-run sube "fix: typo"

# Organizar archivos de una carpeta por tipo
micli organizar ~/Descargas
micli organizar --dry-run ~/Descargas
```

`micli organizar` mueve los archivos a subcarpetas según su extensión
(`imagenes`, `documentos`, `videos`, `audio`, `codigo`, `comprimidos`,
`datos`, `otros`). Ignora archivos ocultos salvo que uses `--ocultos`, y no
sobrescribe: si ya existe un archivo con el mismo nombre añade ` (1)`, ` (2)`, etc.

`--no-color` desactiva los colores en cualquier comando.

## Acciones propias

Edita `acciones.json` para añadir tus tareas automatizadas. Cada acción
declara un comando de shell con placeholders `{1}`, `{2}`, ... que se
sustituyen (citados con `shlex.quote`) por los argumentos que pases a
`micli ejecutar`.

## Tests

```bash
python3 -m unittest discover -s tests -v
```
