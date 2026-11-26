# ADR-0006: Acciones de shell declarativas con `shlex.quote`

- **Fecha:** 2026-11-26
- **Estado:** Aceptado

## Contexto

`micli acciones` / `micli ejecutar` permiten definir tareas automatizadas
(commit+push, estado del repo, etc.) en `acciones.json` en la raíz del
proyecto, sin escribir código Python por tarea. El riesgo evidente es la
inyección de comandos al interpolar argumentos del usuario en una orden de
shell.

Alternativas: scripts Python registrados por código (más seguro pero menos
inmediato), o plantillas de shell en JSON (lo elegido).

## Decisión

Cada acción en `acciones.json` declara un comando de shell con
placeholders `{1}`, `{2}`, ... que se sustituyen citando cada argumento con
`shlex.quote` antes de ejecutarlo con `subprocess` a través del shell. Se
ofrece `--dry-run` para previsualizar el comando sin ejecutarlo.

## Consecuencias

- Positivo: añadir una tarea es editar un JSON; los placeholders posicionales
  son simples y cubren los casos habituales.
- Positivo: `shlex.quote` neutraliza la inyección desde los argumentos.
- Negativo: el propio `acciones.json` es de confianza plena (quien lo edita
  puede ejecutar cualquier cosa): es un fichero del proyecto, no del usuario,
  y así se documenta.
- Negativo: depende de un shell POSIX; en Windows requeriría ajuste.
- Revisar: si hace falta, validar el esquema de `acciones.json` al cargar y
  permitir nombres de acción con argumentos con nombre.
