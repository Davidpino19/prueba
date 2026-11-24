#!/bin/sh
# Instala pip (si falta) y las dependencias de micli en modo usuario.
# Uso: sh scripts/instalar-ia.sh
set -e

PY=python3

if ! $PY -m pip --version >/dev/null 2>&1; then
    echo "[1/3] pip no encontrado: instalándolo con get-pip.py..."
    TMP=$(mktemp)
    if command -v curl >/dev/null 2>&1; then
        curl -fsSL https://bootstrap.pypa.io/get-pip.py -o "$TMP"
    elif command -v wget >/dev/null 2>&1; then
        wget -q https://bootstrap.pypa.io/get-pip.py -O "$TMP"
    else
        echo "Error: necesito curl o wget para descargar get-pip.py" >&2
        exit 1
    fi
    $PY "$TMP" --user
    rm -f "$TMP"
else
    echo "[1/3] pip ya está disponible."
fi

echo "[2/3] Instalando micli y sus dependencias (httpx, colorama)..."
"$PY" -m pip install --user --upgrade -e .

RUTA_USUARIO=$(dirname "$(command -v python3)")/..
export PATH="$HOME/.local/bin:$PATH"

echo "[3/3] Comprobando la instalación..."
$PY -c "import httpx; print('httpx', httpx.__version__)"
micli --version

if [ -z "$OPENAI_API_KEY" ]; then
    echo ""
    echo "Falta la API key. Crea una en https://platform.openai.com/api-keys y ejecuta:"
    echo "  export OPENAI_API_KEY=sk-..."
else
    echo "OPENAI_API_KEY detectada. Ya puedes usar: micli ia \"tu pregunta\""
fi
