"""
Servicio único de almacenamiento de archivos (5.6 y 5.11).

- Archivos PÚBLICOS (fotos de habitaciones, galería, logo): se guardan en UPLOAD_DIR y se
  sirven en /static/uploads. Solo se aceptan imágenes JPEG/PNG/WebP reales, que además se
  re-codifican (elimina EXIF/GPS y cualquier contenido incrustado).
- Archivos PRIVADOS (comprobantes de pago): se guardan en PRIVATE_UPLOAD_DIR, que NO se monta
  como estático. Solo se entregan a través de un endpoint autenticado.

Reglas comunes:
- El tipo se detecta por el CONTENIDO (firma mágica / Pillow), nunca por el nombre ni por el
  content-type que declara el cliente.
- La extensión del archivo guardado se deriva del tipo detectado.
- Límite de tamaño leyendo como máximo N+1 bytes (no se confía en Content-Length).
- Nombres generados: uuid4().hex + extensión de la lista blanca.
"""
import logging
import os
import re
import uuid
from io import BytesIO
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from PIL import Image, ImageOps, UnidentifiedImageError

from backend.core.config import (
    MAX_IMAGE_SIZE_MB,
    MAX_RECEIPT_SIZE_MB,
    PRIVATE_UPLOAD_DIR,
    UPLOAD_DIR,
)

logger = logging.getLogger(__name__)

PUBLIC_URL_PREFIX = "/static/uploads/"

# Formato detectado por Pillow -> (extensión, media type)
_IMAGE_FORMATS = {
    "JPEG": ("jpg", "image/jpeg"),
    "PNG": ("png", "image/png"),
    "WEBP": ("webp", "image/webp"),
}
MEDIA_TYPES = {ext: media for ext, media in _IMAGE_FORMATS.values()}
MEDIA_TYPES["jpeg"] = "image/jpeg"  # archivos antiguos guardados con extensión .jpeg
MEDIA_TYPES["pdf"] = "application/pdf"

# Nombre válido de un archivo generado por este servicio (protege contra path traversal).
_STORED_NAME_RE = re.compile(r"^[0-9a-f]{32}\.(jpg|jpeg|png|webp|pdf)$")

# Protección contra "bombas de descompresión" (imágenes diminutas que ocupan GB en memoria).
_MAX_IMAGE_PIXELS = 50_000_000
Image.MAX_IMAGE_PIXELS = _MAX_IMAGE_PIXELS

_PDF_FORBIDDEN_MARKERS = (b"/JavaScript", b"/Launch", b"/EmbeddedFile")


# ---------------------------------------------------------------------------
# Validación y procesamiento (síncrono: se ejecuta en un hilo aparte)
# ---------------------------------------------------------------------------

def _read_limited(file: UploadFile, max_mb: int) -> bytes:
    max_bytes = max_mb * 1024 * 1024
    file.file.seek(0)
    data = file.file.read(max_bytes + 1)
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El archivo está vacío.")
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"El archivo supera el tamaño máximo permitido ({max_mb} MB).",
        )
    return data


def _invalid_image() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Archivo no válido. Solo se permiten imágenes JPEG, PNG o WebP.",
    )


def _process_image(data: bytes) -> tuple[bytes, str]:
    """Valida que `data` sea una imagen real y la re-codifica. Devuelve (bytes, extensión)."""
    try:
        with Image.open(BytesIO(data)) as probe:
            fmt = probe.format
            if fmt not in _IMAGE_FORMATS:
                raise _invalid_image()
            probe.verify()

        with Image.open(BytesIO(data)) as img:
            img.load()
            # Aplica la rotación EXIF antes de descartar los metadatos.
            img = ImageOps.exif_transpose(img)
            icc_profile = img.info.get("icc_profile")
            img.info = {}

            save_kwargs = {}
            if icc_profile:
                save_kwargs["icc_profile"] = icc_profile

            out = BytesIO()
            if fmt == "JPEG":
                if img.mode not in ("RGB", "L"):
                    img = img.convert("RGB")
                img.save(out, "JPEG", quality=88, optimize=True, **save_kwargs)
            elif fmt == "PNG":
                img.save(out, "PNG", **save_kwargs)
            else:  # WEBP
                img.save(out, "WEBP", quality=88, **save_kwargs)
    except HTTPException:
        raise
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, SyntaxError, ValueError):
        raise _invalid_image()

    return out.getvalue(), _IMAGE_FORMATS[fmt][0]


def _process_receipt(data: bytes) -> tuple[bytes, str]:
    """Comprobante de pago: imagen (re-codificada) o PDF sin contenido activo."""
    if data.startswith(b"%PDF-"):
        if any(marker in data for marker in _PDF_FORBIDDEN_MARKERS):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El PDF contiene elementos no permitidos (scripts o archivos incrustados).",
            )
        return data, "pdf"

    try:
        return _process_image(data)
    except HTTPException as exc:
        if exc.status_code == status.HTTP_400_BAD_REQUEST:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Comprobante no válido. Solo se permiten imágenes JPEG, PNG, WebP o PDF.",
            )
        raise


def _write(directory: str, content: bytes, ext: str) -> str:
    os.makedirs(directory, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.{ext}"
    with open(os.path.join(directory, filename), "wb") as buffer:
        buffer.write(content)
    return filename


def _safe_path(directory: str, filename: str) -> Path | None:
    """Ruta absoluta dentro de `directory` o None si el nombre no es uno generado por nosotros."""
    if not filename or not _STORED_NAME_RE.match(filename):
        return None
    base = Path(directory).resolve()
    path = (base / filename).resolve()
    if path.parent != base:
        return None
    return path


def _save_public_images_sync(files: list[UploadFile]) -> list[str]:
    # Primero se valida TODO; solo si todas las imágenes son válidas se escriben en disco
    # (evita archivos huérfanos cuando falla la 3.ª de 5 imágenes).
    processed = [_process_image(_read_limited(f, MAX_IMAGE_SIZE_MB)) for f in files]
    return [PUBLIC_URL_PREFIX + _write(UPLOAD_DIR, content, ext) for content, ext in processed]


def _save_receipt_sync(file: UploadFile) -> str:
    content, ext = _process_receipt(_read_limited(file, MAX_RECEIPT_SIZE_MB))
    return _write(PRIVATE_UPLOAD_DIR, content, ext)


def _delete_public_sync(url: str) -> bool:
    if not url or not url.startswith(PUBLIC_URL_PREFIX):
        return False
    path = _safe_path(UPLOAD_DIR, url[len(PUBLIC_URL_PREFIX):])
    if path is None or not path.exists():
        return False
    try:
        path.unlink()
        return True
    except OSError as exc:
        logger.warning("No se pudo eliminar %s: %s", path.name, exc)
        return False


# ---------------------------------------------------------------------------
# API pública (async: el trabajo pesado corre fuera del event loop)
# ---------------------------------------------------------------------------

async def save_public_image(file: UploadFile) -> str:
    """Guarda una imagen pública y devuelve su URL relativa (/static/uploads/...)."""
    urls = await run_in_threadpool(_save_public_images_sync, [file])
    return urls[0]


async def save_public_images(files: list[UploadFile]) -> list[str]:
    files = [f for f in files if f and f.filename]
    if not files:
        return []
    return await run_in_threadpool(_save_public_images_sync, files)


async def delete_public_file(url: str) -> bool:
    return await run_in_threadpool(_delete_public_sync, url)


async def save_private_receipt(file: UploadFile) -> str:
    """Guarda un comprobante en almacenamiento privado y devuelve su clave (nombre interno)."""
    return await run_in_threadpool(_save_receipt_sync, file)


def _delete_private_sync(key: str) -> bool:
    path = _safe_path(PRIVATE_UPLOAD_DIR, key)
    if path is None or not path.exists():
        return False
    try:
        path.unlink()
        return True
    except OSError as exc:
        logger.warning("No se pudo eliminar el comprobante %s: %s", path.name, exc)
        return False


async def delete_private_receipt(key: str) -> bool:
    return await run_in_threadpool(_delete_private_sync, key)


def private_receipt_path(key: str) -> Path | None:
    """Ruta del comprobante privado, o None si la clave no es válida o el archivo no existe."""
    path = _safe_path(PRIVATE_UPLOAD_DIR, key)
    return path if path is not None and path.exists() else None


def legacy_public_path(url: str) -> Path | None:
    """Ruta de un comprobante antiguo guardado en /static/uploads (antes de 5.6)."""
    if not url or not url.startswith(PUBLIC_URL_PREFIX):
        return None
    path = _safe_path(UPLOAD_DIR, url[len(PUBLIC_URL_PREFIX):])
    return path if path is not None and path.exists() else None


def media_type_for(path: Path) -> str:
    return MEDIA_TYPES.get(path.suffix.lstrip(".").lower(), "application/octet-stream")
