import random

from micli import hola

DESPEDIDAS = [
    "¡Hasta luego! Que tengas un buen día.",
    "¡Nos vemos pronto!",
    "¡Cuídate! Aquí estaré cuando vuelvas.",
    "¡Adiós! Que el código te acompañe.",
    "¡Hasta la próxima! Descansa un poco.",
    "¡Nos leemos! Buen trabajo hoy.",
    "¡Chao! Que todo te salga bien.",
    "¡Hasta pronto! No olvides guardar los cambios.",
]


def mensaje(tipo="auto", rng=random):
    despedida = rng.choice(DESPEDIDAS)
    if tipo == "despedida":
        return despedida, None, None
    etiqueta, texto = hola.extra(tipo, rng)
    return despedida, etiqueta, texto
