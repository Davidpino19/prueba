# ADR-0008: Capas separadas con `ProveedorIA` y flujo de examen en el dominio

- **Fecha:** 2026-11-26
- **Estado:** Aceptado
- **Relacionado con:** ADR-0001, ADR-0003, ADR-0005

## Contexto

La auditoría de responsabilidades detectó tres fugas: el flujo interactivo
del examen vivía en el frontend (duplicado en click y argparse), los
proveedores de IA se elegían con if/else dentro de una función suelta, y
hubo accesos a internals privados entre módulos (`ui._reset`,
`store._rutas`).

## Decisión

- `examen.jugar()` (dominio) ejecuta el flujo completo; los frontends solo
  cablean opciones y lo llaman. La E/S se inyecta (`imprimir`, `entrada`,
  `panel_fn`) con valores por defecto en `micli.clic`, respetando ADR-0005.
- `ProveedorIA` con fábrica estática `desde_config(nombre, modelo)`:
  argumentos > variables de entorno > por defecto; `ia.chat()` sigue siendo
  la función pública de siempre, ahora delegada.
- Internals hechos públicos: `ui.reset()` y `store.carpeta_datos()`;
  proscrito llamar a `._algo` de otro módulo.

## Consecuencias

- Positivo: un solo sitio para el examen; añadir un proveedor es crear una
  rama en `ProveedorIA.chat` + una entrada en `MODELOS/CLAVES/FALLBACKS`.
- Positivo: la fábrica centraliza la resolución de configuración (antes
  repartida por `chat()`, `proveedor()` y `_api_key()`).
- Negativo: una clase más donde antes bastaban funciones; justificado por la
  duplicación eliminada (~120 líneas fuera del frontend argparse).
- Revisar: si hay tercer proveedor, extraer `_chat_openai/_chat_gemini` a
  subclases en vez de if/else.
