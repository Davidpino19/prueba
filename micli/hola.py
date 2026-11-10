import random

SALUDOS = [
    "¡Hola! Me alegra verte por aquí.",
    "¡Buenas! ¿Qué tal va el día?",
    "¡Hola de nuevo! Vamos a por ello.",
    "¡Hey! Aquí estoy para animarte un poco.",
    "¡Hola! Espero que tengas un gran día.",
    "¡Saludos! ¿Listo para seguir aprendiendo?",
    "¡Hola! Me encanta que hayas venido a saludar.",
    "¡Buenas y bienvenido!",
]

CHISTES = [
    "¿Qué le dice un bit a otro? Nos vemos en el bus.",
    "¿Por qué los programadores prefieren el modo oscuro? Porque la luz atrae bugs.",
    "¿Qué hace una abeja en el gimnasio? ¡Zum-ba!",
    "¿Cómo se despiden los químicos? Ácido un placer.",
    "¿Qué le dijo el 0 al 8? Bonito cinturón.",
    "¿Por qué el libro de matemáticas estaba triste? Porque tenía muchos problemas.",
    "—Doctor, me duele aquí. —Pues no toque ahí.",
    "¿Cuál es el colmo de un informático? Que le digan que no funciona el ratón y responda: ¿lo has apagado y encendido?",
    "—¿Qué tal la dieta? —Muy bien, ya perdí la cuenta de las veces que la empiezo.",
    "¿Sabes cuál es el animal más antiguo? La cebra, porque está en blanco y negro.",
]

FRASES = [
    "Hoy no tienes que poder con todo: solo con lo siguiente.",
    "El progreso más pequeño sigue siendo progreso.",
    "No esperes a tener ganas; empieza y las ganas aparecen.",
    "Cada línea de código que entiendes es una puerta que se abre.",
    "Los errores son solo pistas disfrazadas.",
    "No se trata de ir rápido, sino de no parar.",
    "Hazlo con miedo, pero hazlo.",
    "La constancia le gana al talento cuando el talento descansa.",
    "Un paso pequeño hoy vale más que un plan perfecto mañana.",
    "Tu yo de dentro de un año te agradecerá lo que hagas hoy.",
]


def extra(tipo="auto", rng=random):
    if tipo in ("saludo", "despedida"):
        return None, None
    if tipo == "chiste":
        categoria = "chiste"
    elif tipo == "frase":
        categoria = "frase"
    else:
        categoria = rng.choice(["chiste", "frase"])

    if categoria == "chiste":
        return "Chiste", rng.choice(CHISTES)
    return "Frase", rng.choice(FRASES)


def mensaje(tipo="auto", rng=random):
    saludo = rng.choice(SALUDOS)
    etiqueta, texto = extra(tipo, rng)
    return saludo, etiqueta, texto
