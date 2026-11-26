# ADR-0007: Encadenado con `+` y confirmación de acciones peligrosas

- **Fecha:** 2026-11-26
- **Estado:** Aceptado
- **Reemplaza a:** amplía ADR-0006

## Contexto

`micli ejecutar` solo corría una acción por invocación y ninguna acción
destructiva pedía confirmación (`limpia` borra directamente). Para cubrir el
flujo "varias acciones a la vez" y "sin efectos sorpresa" hacían falta
encadenado y una barrera antes de borrar o sobrescribir.

## Decisión

Dos reglas:

1. **Encadenado:** `micli ejecutar acc1 [args] + acc2 [args]` ejecuta las
   acciones en orden y se detiene al primer fallo (`segmentar()` en
   `micli/acciones.py`; implementado por igual en el frontend click y en el
   argparse).
2. **Confirmación:** una acción declarada con `"peligrosa": true` en
   `acciones.json` pide confirmación explícita (`confirmar()`), salvo con
   `--yes`. Con `--dry-run` no se pregunta: solo se marca el aviso
   `(acción peligrosa)`. `micli acciones` etiqueta estas acciones con
   `(peligrosa)`.

## Consecuencias

- Positivo: el criterio "+" es inequívoco (un argumento literal `+` no es
  válido para ninguna acción actual); la salida de `ejecutar` explica qué se
  va a ejecutar (`$ comando`) antes de hacerlo.
- Positivo: `limpia` ya no borra sin avisar.
- Negativo: encadenar acciones que comparten argumentos es confuso (los args
  van ligados a su acción); la alternativa de ficheros de "recetas" quedó
  fuera por simplicidad.
- Negativo: `--yes` anula la barrera; asumido por ser una CLI interactiva.
- Revisar: si aparecen más acciones destructivas, valorar una papelera en vez
  de `rm -rf` en `limpia`.
