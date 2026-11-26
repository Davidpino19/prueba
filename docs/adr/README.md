# Registros de Decisiones de Arquitectura (ADRs)

ADRs de `micli`. Cada ADR documenta una decisión arquitectónica importante:
su contexto, la decisión tomada y sus consecuencias. Una vez aceptado, un ADR
no se edita: si una decisión cambia, se escribe un ADR nuevo que lo reemplaza.

## Plantilla

Ver [0000-plantilla.md](0000-plantilla.md).

## Índice

| # | Título | Estado |
|---|--------|--------|
| [0001](0001-usar-click-como-base-de-la-cli.md) | Usar click como base de la CLI | Aceptado |
| [0002](0002-persistencia-en-json-bajo-config-de-usuario.md) | Persistencia en JSON bajo `~/.config/micli/` | Aceptado |
| [0003](0003-ia-multi-proveedor-via-http-directo-con-httpx.md) | IA multi-proveedor vía HTTP directo con httpx | Aceptado |
| [0004](0004-dependencias-opcionales-con-degradacion-gracial.md) | Dependencias opcionales con degradación gracial | Aceptado |
| [0005](0005-capa-de-salida-unica-testable.md) | Capa de salida única y testeable (`micli.clic`) | Aceptado |
| [0006](0006-acciones-de-shell-con-shlex-quote.md) | Acciones de shell declarativas con `shlex.quote` | Aceptado |

## Convenciones

- Nomenclatura: `NNNN-titulo-en-kebab-case.md`
- Estados propuestos: `Propuesto`, `Aceptado`, `Obsoleto`, `Reemplazado por ADR-XXXX`
- Número reservado: 0000 es la plantilla.
