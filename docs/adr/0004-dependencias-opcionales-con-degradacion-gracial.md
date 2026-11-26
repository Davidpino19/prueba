# ADR-0004: Dependencias opcionales con degradación gracial

- **Fecha:** 2026-11-24
- **Estado:** Aceptado

## Contexto

Algunas funciones mejoran la experiencia pero no son esenciales: `rich`
(tablas y paneles en `asignaturas list`, `resumen`, `examen list`), `pypdf`
(lectura de resúmenes en PDF) y `httpx` solo se necesita para la IA. Si
fueran dependencias obligatorias, la instalación base sería más pesada y
fallaría en entornos restringidos.

## Decisión

Mantener como dependencias base solo `click`, `colorama` y `httpx`, y declarar
el resto como **extras** en `pyproject.toml` (`pip install 'micli[ui]'`,
`pip install 'micli[pdf]'`). El código importa estos extras dentro de
`try/except ImportError` y degrada: sin `rich` se imprimen tablas de texto plano, sin
`pypdf` se prueba `pdftotext` y si tampoco existe se pide el contenido con
`--texto`. La TUI además se puede apagar con `micli ui off` o `--no-color`.

## Consecuencias

- Positivo: instalación base mínima; la CLI nunca falla por faltar un extra,
  solo pierde la mejora.
- Positivo: el usuario decide qué instala.
- Negativo: más ramas de `try/except ImportError` y dos rutas de prueba por
  función (con y sin extra).
- Revisar: `httpx` es base aunque solo lo use IA; si se separa, moverlo a un
  extra `ia`.
