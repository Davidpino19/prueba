# ADR-0005: Capa de salida única y testeable (`micli.clic`)

- **Fecha:** 2026-11-24
- **Estado:** Aceptado

## Contexto

Existen dos frontends (click y el heredado argparse, ver ADR-0001) y se
quiere que `--no-color` funcione en todos los subcomandos y que los tests
puedan capturar la salida sin parchear `print`/`input` en cada módulo.

## Decisión

Todos los comandos escriben y leen **solo a través de `micli/clic.py`**:
`imprimir()`, `preguntar()`, los colores predefinidos y los punteables
`out` (stdout) y `entrada` (input). El flag `--no-color` invoca
`activar_sin_color()`. `micli/ui.py` (rich) es una capa superior que, si está
desactivada o falta la librería, cae de vuelta a `clic.imprimir()`.

## Consecuencias

- Positivo: los tests sustituyen `clic.out` y `clic.entrada` y prueban ambos
  frontends con el mismo código; el soporte de color se cambia en un sitio.
- Positivo: independencia del framework de CLI, lo que permitió migrar de
  argparse a click sin tocar los comandos.
- Negativo: los comandos no pueden usar `print` directamente; hay que recordar
  la convención (fácil de verificar en code review).
- Revisar: si la salida rica crece, `ui.py` podría absorber parte de la lógica
  de formateo de `clic.py`.
