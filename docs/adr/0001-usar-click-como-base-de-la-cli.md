# ADR-0001: Usar click como base de la CLI

- **Fecha:** 2026-11-24
- **Estado:** Aceptado

## Contexto

La CLI nació con `argparse` (stdlib) y un único parser con subcomandos a mano.
Con el crecimiento (asignaturas, examen, ia, ui, acciones) el parser en
argparse se volvió difícil de extender: anidación de subcomandos, help
autogenerado, grupos y tests requerían mucho código propio.

Alternativas consideradas:

- Seguir con `argparse`: sin dependencias, pero más boilerplate por comando.
- `click`: declarativo, subcomandos naturales, amplíamente usado en el ecosistema.
- `typer`: más moderno y tipado, pero añade dependencia sobre click y menos
  control del output compartido.

## Decisión

Usar **click** como framework principal. La entrada publicada es
`micli = micli.click_cli:main`. La versión argparse se conserva como
`micli-argparse = micli.cli:main` para no romper a quien ya la usa y como
referencia de la capa de salida compartida.

## Consecuencias

- Añadir comandos es barato: una función con `@micli.command()`.
- El comportamiento de salida (colores, `--no-color`, captura en tests) no
  depende del framework: ambos frontends pasan por `micli.clic` (ADR-0005).
- Nueva dependencia de runtime (`click`) en `pyproject.toml`.
- Duplication temporal de dos frontends; cuando `micli-argparse` ya no se use,
  se podrá eliminar borrando `micli/cli.py` y su entrada.
