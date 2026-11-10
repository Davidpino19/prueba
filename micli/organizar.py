import shutil
from pathlib import Path

CATEGORIAS = {
    "imagenes": {
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".ico",
        ".tif", ".tiff", ".heic", ".raw",
    },
    "documentos": {
        ".pdf", ".doc", ".docx", ".odt", ".rtf", ".txt", ".md", ".markdown",
        ".tex", ".epub", ".xls", ".xlsx", ".ods", ".ppt", ".pptx", ".odp",
    },
    "videos": {
        ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v",
        ".mpeg", ".mpg",
    },
    "audio": {
        ".mp3", ".wav", ".flac", ".ogg", ".oga", ".m4a", ".aac", ".wma", ".opus",
    },
    "codigo": {
        ".py", ".ipynb", ".js", ".jsx", ".ts", ".tsx", ".html", ".htm",
        ".css", ".scss", ".sass", ".less", ".java", ".kt", ".c", ".h", ".cpp",
        ".hpp", ".cc", ".cs", ".go", ".rs", ".rb", ".php", ".pl", ".lua",
        ".sh", ".bash", ".zsh", ".ps1", ".bat", ".sql", ".r", ".swift",
        ".vue", ".svelte", ".toml", ".yaml", ".yml", ".ini", ".cfg", ".conf",
    },
    "comprimidos": {
        ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".tgz",
    },
    "datos": {
        ".csv", ".tsv", ".parquet", ".feather", ".db", ".sqlite", ".sqlite3",
        ".xml", ".json", ".dat", ".bin",
    },
}


class OrganizarError(Exception):
    pass


def categoria(nombre):
    ext = Path(nombre).suffix.lower()
    for nombre_categoria, extensiones in CATEGORIAS.items():
        if ext in extensiones:
            return nombre_categoria
    return "otros"


def _destino_libre(carpeta, nombre):
    destino = carpeta / nombre
    if not destino.exists():
        return destino
    base, ext = destino.stem, destino.suffix
    i = 1
    while True:
        candidato = carpeta / f"{base} ({i}){ext}"
        if not candidato.exists():
            return candidato
        i += 1


def organizar(ruta=".", dry_run=False, ocultos=False):
    raiz = Path(ruta)
    if not raiz.is_dir():
        raise OrganizarError(f"{raiz} no es un directorio.")

    movidos = []
    for origen in sorted(raiz.iterdir(), key=lambda p: p.name.lower()):
        if not origen.is_file() or origen.is_symlink():
            continue
        if not ocultos and origen.name.startswith("."):
            continue

        destino = _destino_libre(raiz / categoria(origen.name), origen.name)
        movidos.append((origen, destino))

        if not dry_run:
            try:
                destino.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(origen), str(destino))
            except OSError as e:
                raise OrganizarError(f"No se pudo mover {origen.name}: {e}")
    return movidos
