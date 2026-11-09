"""
Almacenamiento de archivos (interfaz única, 5.6 / 5.11).

- PÚBLICOS (fotos de habitaciones, galería, logo): `settings.upload_dir`, servidos en /static/uploads.
  Solo imágenes JPEG/PNG/WebP reales, re-codificadas (sin EXIF/GPS ni contenido incrustado).
- PRIVADOS (comprobantes de pago): `settings.private_upload_dir`, nunca servidos como estáticos.

El tipo se detecta por el contenido; la extensión se deriva del tipo; el tamaño se limita leyendo
como máximo N+1 bytes; los nombres son uuid4().hex + extensión de una lista blanca.

Fase 3: reemplazar la implementación local por object storage (R2/S3) manteniendo estas funciones.
"""
import logging
import re
import uuid
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from fastapi import UploadFile
from fastapi.concurrency import run_in_threadpool
from PIL import Image, ImageOps, UnidentifiedImageError

from backend.app.core.errors import PayloadTooLarge, ValidationFailed
from backend.app.core.settings import get_settings

logger = logging.getLogger(__name__)

PUBLIC_URL_PREFIX = "/static/uploads/"

_IMAGE_FORMATS = {
    "JPEG": ("jpg", "image/jpeg"),
    "PNG": ("png", "image/png"),
    "WEBP": ("webp", "image/webp"),
}
MEDIA_TYPES = {ext: media for ext, media in _IMAGE_FORMATS.values()}
MEDIA_TYPES["pdf"] = "application/pdf"

_STORED_NAME_RE = re.compile(r"^[0-9a-f]{32}\.(jpg|png|webp|pdf)$")
_PDF_FORBIDDEN_MARKERS = (b"/JavaScript", b"/Launch", b"/EmbeddedFile")

Image.MAX_IMAGE_PIXELS = 50_000_000  # protección contra bombas de descompresión


@dataclass(frozen=True)
class StoredFile:
    key: str  # nombre interno (uuid.ext)
    content_type: str


# ---------------------------------------------------------------------------
# Validación (síncrona; se ejecuta en un hilo aparte)
# ---------------------------------------------------------------------------

def _read_limited(file: UploadFile, max_mb: int) -> bytes:
    max_bytes = max_mb * 1024 * 1024
    file.file.seek(0)
    data = file.file.read(max_bytes + 1)
    if not data:
        raise ValidationFailed("El archivo está vacío.")
    if len(data) > max_bytes:
        raise PayloadTooLarge(f"El archivo supera el tamaño máximo permitido ({max_mb} MB).")
    return data


_INVALID_IMAGE = "Archivo no válido. Solo se permiten imágenes JPEG, PNG o WebP."


def _process_image(data: bytes) -> tuple[bytes, str]:
    try:
        with Image.open(BytesIO(data)) as probe:
            fmt = probe.format
            if fmt not in _IMAGE_FORMATS:
                raise ValidationFailed(_INVALID_IMAGE)
            probe.verify()

        with Image.open(BytesIO(data)) as img:
            img.load()
            img = ImageOps.exif_transpose(img)  # aplica la rotación antes de descartar EXIF
            icc_profile = img.info.get("icc_profile")
            img.info = {}
            save_kwargs = {"icc_profile": icc_profile} if icc_profile else {}

            out = BytesIO()
            if fmt == "JPEG":
                if img.mode not in ("RGB", "L"):
                    img = img.convert("RGB")
                img.save(out, "JPEG", quality=88, optimize=True, **save_kwargs)
            elif fmt == "PNG":
                img.save(out, "PNG", **save_kwargs)
            else:
                img.save(out, "WEBP", quality=88, **save_kwargs)
    except ValidationFailed:
        raise
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, SyntaxError, ValueError):
        raise ValidationFailed(_INVALID_IMAGE)
    return out.getvalue(), _IMAGE_FORMATS[fmt][0]


def _process_receipt(data: bytes) -> tuple[bytes, str]:
    if data.startswith(b"%PDF-"):
        if any(marker in data for marker in _PDF_FORBIDDEN_MARKERS):
            raise ValidationFailed("El PDF contiene elementos no permitidos (scripts o archivos incrustados).")
        return data, "pdf"
    try:
        return _process_image(data)
    except ValidationFailed:
        raise ValidationFailed("Comprobante no válido. Solo se permiten imágenes JPEG, PNG, WebP o PDF.")


def _write(directory: Path, content: bytes, ext: str) -> str:
    directory.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.{ext}"
    (directory / filename).write_bytes(content)
    return filename


def _safe_path(directory: Path, filename: str | None) -> Path | None:
    """Ruta dentro de `directory`, o None si el nombre no lo generó este servicio (anti path traversal)."""
    if not filename or not _STORED_NAME_RE.match(filename):
        return None
    base = directory.resolve()
    path = (base / filename).resolve()
    return path if path.parent == base else None


def _unlink(path: Path | None) -> bool:
    if path is None or not path.exists():
        return False
    try:
        path.unlink()
        return True
    except OSError as exc:
        logger.warning("No se pudo eliminar %s: %s", path.name, exc)
        return False


def _save_public_images_sync(files: list[UploadFile]) -> list[str]:
    settings = get_settings()
    # Se valida todo antes de escribir: si una imagen falla no quedan archivos huérfanos.
    processed = [_process_image(_read_limited(f, settings.max_image_size_mb)) for f in files]
    return [PUBLIC_URL_PREFIX + _write(settings.upload_dir, content, ext) for content, ext in processed]


def _save_receipt_sync(file: UploadFile) -> StoredFile:
    settings = get_settings()
    content, ext = _process_receipt(_read_limited(file, settings.max_receipt_size_mb))
    return StoredFile(key=_write(settings.private_upload_dir, content, ext), content_type=MEDIA_TYPES[ext])


def _public_path(url: str | None) -> Path | None:
    if not url or not url.startswith(PUBLIC_URL_PREFIX):
        return None
    return _safe_path(get_settings().upload_dir, url[len(PUBLIC_URL_PREFIX):])


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

async def save_public_image(file: UploadFile) -> str:
    """Guarda una imagen pública y devuelve su URL relativa (/static/uploads/...)."""
    return (await run_in_threadpool(_save_public_images_sync, [file]))[0]


async def save_public_images(files: list[UploadFile]) -> list[str]:
    files = [f for f in files if f is not None and f.filename]
    if not files:
        return []
    return await run_in_threadpool(_save_public_images_sync, files)


async def delete_public_file(url: str | None) -> bool:
    return await run_in_threadpool(_unlink, _public_path(url))


async def save_private_receipt(file: UploadFile) -> StoredFile:
    return await run_in_threadpool(_save_receipt_sync, file)


async def delete_private_receipt(key: str | None) -> bool:
    return await run_in_threadpool(_unlink, _safe_path(get_settings().private_upload_dir, key))


def private_receipt_path(key: str | None) -> Path | None:
    path = _safe_path(get_settings().private_upload_dir, key)
    return path if path is not None and path.exists() else None


def media_type_for(path: Path) -> str:
    return MEDIA_TYPES.get(path.suffix.lstrip(".").lower(), "application/octet-stream")
