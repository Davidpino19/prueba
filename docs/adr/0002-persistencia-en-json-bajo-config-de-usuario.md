# ADR-0002: Persistencia en JSON bajo `~/.config/micli/`

- **Fecha:** 2026-11-24
- **Estado:** Aceptado

## Contexto

La CLI necesita guardar estado: asignaturas y notas, resultados de exámenes, y
preferencias de UI. Opciones valoradas: base de datos (SQLite), un formato
compacto binario, o ficheros JSON de texto plano.

Restricciones: Python >= 3.8 sin servidor, orientación a que el usuario pueda
inspeccionar y editar su configuración a mano, y cero configuración adicional.

## Decisión

Guardar todo el estado como **JSON de texto plano** bajo
`~/.config/micli/`: `asignaturas.json`, `ui.json` y una carpeta `examenes/`
con un archivo por examen. La escritura centralizada en `micli/store.py`
crea el directorio si no existe.

## Consecuencias

- Positivo: legible y editable a mano, fácil de respaldar o versionar, sin
  dependencias extra; un archivo por examen evita un único fichero gigante.
- Negativo: sin transacciones ni concurrencia; dos procesos escribiendo a la
  vez pueden corromper `asignaturas.json` (aceptable para una CLI de un solo
  usuario).
- Revisar: si el volumen de exámenes crece, añadir rotación o un índice; si se
  necesitan consultas, migrar a SQLite tras `store.py`, que ya aísla el acceso.
