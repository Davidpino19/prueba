# Changelog

Formato [Keep a Changelog](https://keepachangelog.com/es/1.1.0/),
versionado según [SemVer](https://semver.org/lang/es/).

## [1.0.0] - 2026-11-26

Primer release estable de `micli`.

### Añadido

- CLI completa con **click** (`micli`) y variante legada argparse
  (`micli-argparse`, misma salida a través de `micli.clic`).
- Gestor de asignaturas con persistencia JSON en `~/.config/micli/`
  (`asignaturas add/list/nota/remove`, `resumen`).
- **IA multi-proveedor** (OpenAI y Gemini) por HTTP con `httpx`: `micli ia`,
  `micli asignaturas ia-consejo` y fábrica `ProveedorIA.desde_config()` con
  reintentos y fallbacks de modelo.
- **Exámenes con IA** (`micli examen crear/list`): desde txt/md/pdf o
  `--texto`, corrección con nota 0-10 y feedback por pregunta; histórico
  guardado. Flujo interactivo en el dominio (`examen.jugar()`).
- **Motor de acciones** declarativas (`acciones.json`) con 9 acciones incluidas
  (`estado`, `sube`, `limpia`, `prueba`, `pendientes`, `respaldo` y 3 con IA):
  placeholders citados con `shlex.quote`, encadenado con `+`, `--dry-run` y
  confirmación para acciones `"peligrosa"` (con `--yes` para saltarla).
- **Organización de archivos**: `micli organizar` (por tipo, sin sobrescribir:
  añade ` (1)`, ` (2)`, ...) y `micli asignaturas organizar` (interactivo).
- **TUI opcional con `rich`** (`pip install 'micli[ui]'`): tablas y paneles,
  controlable con `micli ui on/off`.
- **Errores humanos**: excepciones propias (`IaError`, `AccionError` +
  `AccionNoValida`/`ConfigError`, `StoreError`, `OrganizarError`,
  `ExamenError`, `AsignaturaInexistente`/`AsignaturaDuplicada`), mensajes en
  español, salida 1/130 y nunca traceback ante errores previsibles (sin red,
  config corrupta, Ctrl+C, permisos).
- **89 tests unittest** (camino feliz + casos feos; la IA se mockea) que pasan
  sin dependencias opcionales.
- **CI en GitHub Actions** (Python 3.10 y 3.12 en cada push/PR).
- **8 ADRs** en `docs/adr/` explicando las decisiones de arquitectura.
- Instalación de pip alternativa vía `scripts/instalar-ia.sh` para sistemas sin
  `pip`.

### Cambiado

- `--no-color` y la capa `clic.py` unifican salida y color en ambos frontends.
- El flujo del examen se movió del frontend al dominio (menos duplicación).

## [0.3.0] - 2026-11-24

- Comando `examen` (crear/corregir) y modo JSON para `ia`.
- Proveedor Gemini (`x-goog-api-key`) y modelo por defecto
  `gemini-flash-lite-latest`.

## [0.2.0] - 2026-11-17

- Acciones automatizadas (`micli acciones`/`ejecutar`) con `shlex.quote`.
- `micli organizar` por tipo de archivo.

## [0.1.0] - 2026-10-26

- Primera CLI con argparse: saludos, asignaturas y resumen.
