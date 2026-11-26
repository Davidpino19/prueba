# ADR-0003: IA multi-proveedor vía HTTP directo con httpx

- **Fecha:** 2026-11-24
- **Estado:** Aceptado

## Contexto

`micli ia`, `ia-consejo` y `examen` necesitan llamar a un LLM. Se usará
OpenAI y Gemini, y podría añadirse más adelante cualquier API compatible con
el formato de OpenAI. Alternativas: los SDK oficiales (`openai`,
`google-generativeai`), o llamadas HTTP directas.

Restricciones: instalación ligera (es una CLI de ejemplo), Python >= 3.8 y
que la clave sea siempre variable del entorno (`OPENAI_API_KEY`,
`GEMINI_API_KEY`).

## Decisión

Llamar a las APIs por **HTTP directo con `httpx`**, encapsulando cada
proveedor detrás de una función común en `micli/ia.py`. El proveedor se
elige con `-p/--proveedor` o la variable `MICLI_IA_PROVEEDOR`; los modelos
por defecto se pueden sobrescribir con `-m` o `MICLI_IA_MODELO`. Detalles
resueltos: Gemini usa la cabecera `x-goog-api-key` y por defecto
`gemini-flash-lite-latest`; el modo JSON de los exámenes pide salida
estructurada al proveedor. Si un modelo por defecto falla con 404/503 se
reintenta con la lista de `FALLBACKS` del proveedor, salvo que el usuario lo
fije explícitamente.

## Consecuencias

- Positivo: una sola dependencia (`httpx`) sirve para ambos proveedores y
  para añadir un tercero compatible con OpenAI (solo base URL y cabecera).
- Positivo: sin acoplamiento a versiones de SDKs que cambian rápido.
- Negativo: hay que mantener a mano el formato de cada API (autenticación,
  respuesta, errores); una rotura de API se detecta en runtime, no por el
  tipado del SDK.
- Revisar: si el número de proveedores crece a 3-4, extraer una interfaz
  `Proveedor` explícita o revisar los SDKs.
