"""
Almacenamiento de archivos (interfaz única, 5.6 / 5.11 / Fase 3).

Dos tipos de archivo:
- PÚBLICOS (fotos de habitaciones, galería, logo): solo imágenes JPEG/PNG/WebP reales, re-codificadas
  (sin EXIF/GPS ni contenido incrustado). Cada foto lleva una miniatura WebP en `thumbs/<uuid>.webp`.
- PRIVADOS (comprobantes de pago): nunca accesibles por URL pública; se entregan por un endpoint
  autenticado que lee el archivo desde aquí.

Dos backends, elegidos con STORAGE_BACKEND:
- `local`: disco (`upload_dir` servido en /static/uploads; `private_upload_dir` no servido).
- `s3`:    bucket S3 compatible (DigitalOcean Spaces / R2 / S3) bajo `<S3_KEY_PREFIX>/`:
             public/<uuid>.<ext>          ACL public-read, caché inmutable (sirve el CDN)
             public/thumbs/<uuid>.webp    ídem
             receipts/<uuid>.<ext>        ACL private, solo la API puede leerlos

El tipo se detecta por el contenido; la extensión se deriva del tipo; el tamaño se limita leyendo
como máximo N+1 bytes; los nombres son uuid4().hex + extensión de una lista blanca.
"""

import logging
import re
import uuid
from dataclasses import dataclass
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from typing import Protocol

from fastapi import UploadFile
from fastapi.concurrency import run_in_threadpool
from PIL import Image, ImageOps, UnidentifiedImageError

from backend.app.core.errors import PayloadTooLarge, ServiceUnavailable, ValidationFailed
from backend.app.core.settings import Settings, get_settings

logger = logging.getLogger(__name__)

PUBLIC_URL_PREFIX = "/static/uploads/"
THUMBS_DIR = "thumbs"
PUBLIC_CACHE_CONTROL = "public, max-age=31536000, immutable"  # los nombres nunca se reutilizan

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


@dataclass(frozen=True)
class ReceiptContent:
    content: bytes
    content_type: str
    extension: str


@dataclass(frozen=True)
class _ProcessedImage:
    content: bytes
    ext: str
    thumbnail: bytes  # WebP


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


def _reencode(data: bytes, *, thumbnail_px: int | None) -> tuple[bytes, str, bytes | None]:
    try:
        with Image.open(BytesIO(data)) as probe:
            fmt = probe.format
            if fmt not in _IMAGE_FORMATS:
                raise ValidationFailed(_INVALID_IMAGE)
            probe.verify()

        with Image.open(BytesIO(data)) as source:
            source.load()
            img: Image.Image = ImageOps.exif_transpose(source)  # aplica la rotación antes de descartar EXIF
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

            thumb_bytes = None
            if thumbnail_px:
                thumb = img.copy()
                if thumb.mode not in ("RGB", "RGBA"):
                    thumb = thumb.convert("RGBA" if "A" in thumb.getbands() else "RGB")
                thumb.thumbnail((thumbnail_px, thumbnail_px), Image.Resampling.LANCZOS)
                thumb_out = BytesIO()
                thumb.save(thumb_out, "WEBP", quality=80, method=4, **save_kwargs)
                thumb_bytes = thumb_out.getvalue()
    except ValidationFailed:
        raise
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, SyntaxError, ValueError):
        raise ValidationFailed(_INVALID_IMAGE) from None
    return out.getvalue(), _IMAGE_FORMATS[fmt][0], thumb_bytes


def _process_image(data: bytes, thumbnail_px: int) -> _ProcessedImage:
    content, ext, thumb = _reencode(data, thumbnail_px=thumbnail_px)
    assert thumb is not None  # noqa: S101 - siempre se pide miniatura
    return _ProcessedImage(content=content, ext=ext, thumbnail=thumb)


def _process_receipt(data: bytes) -> tuple[bytes, str]:
    if data.startswith(b"%PDF-"):
        if any(marker in data for marker in _PDF_FORBIDDEN_MARKERS):
            raise ValidationFailed("El PDF contiene elementos no permitidos (scripts o archivos incrustados).")
        return data, "pdf"
    try:
        content, ext, _ = _reencode(data, thumbnail_px=None)
    except ValidationFailed:
        raise ValidationFailed("Comprobante no válido. Solo se permiten imágenes JPEG, PNG, WebP o PDF.") from None
    return content, ext


def _valid_name(name: str | None) -> bool:
    return bool(name) and bool(_STORED_NAME_RE.match(name or ""))


def _thumb_name(name: str) -> str:
    return f"{THUMBS_DIR}/{name.rsplit('.', 1)[0]}.webp"


# ---------------------------------------------------------------------------
# Backends
# ---------------------------------------------------------------------------


class _Backend(Protocol):
    def public_url(self, name: str) -> str: ...
    def public_name(self, url: str) -> str | None: ...
    def put_public(self, name: str, content: bytes, content_type: str) -> None: ...
    def delete_public(self, name: str) -> bool: ...
    def put_private(self, name: str, content: bytes, content_type: str) -> None: ...
    def get_private(self, name: str) -> bytes | None: ...
    def delete_private(self, name: str) -> bool: ...


class _LocalBackend:
    def __init__(self, settings: Settings):
        self.public_dir = settings.upload_dir
        self.private_dir = settings.private_upload_dir

    @staticmethod
    def _safe_path(directory: Path, name: str) -> Path | None:
        """Ruta dentro de `directory` (anti path traversal); `name` ya pasó por `_valid_name`."""
        base = directory.resolve()
        path = (base / name).resolve()
        return path if base in path.parents else None

    @staticmethod
    def _write(path: Path | None, content: bytes) -> None:
        if path is None:  # pragma: no cover - los nombres los genera este módulo
            raise ValidationFailed("Nombre de archivo no válido.")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    @staticmethod
    def _unlink(path: Path | None) -> bool:
        if path is None or not path.exists():
            return False
        try:
            path.unlink()
            return True
        except OSError as exc:
            logger.warning("No se pudo eliminar %s: %s", path.name, exc)
            return False

    def public_url(self, name: str) -> str:
        return PUBLIC_URL_PREFIX + name

    def public_name(self, url: str) -> str | None:
        return url[len(PUBLIC_URL_PREFIX) :] if url.startswith(PUBLIC_URL_PREFIX) else None

    def put_public(self, name: str, content: bytes, content_type: str) -> None:
        self._write(self._safe_path(self.public_dir, name), content)

    def delete_public(self, name: str) -> bool:
        return self._unlink(self._safe_path(self.public_dir, name))

    def put_private(self, name: str, content: bytes, content_type: str) -> None:
        self._write(self._safe_path(self.private_dir, name), content)

    def get_private(self, name: str) -> bytes | None:
        path = self._safe_path(self.private_dir, name)
        return path.read_bytes() if path is not None and path.is_file() else None

    def delete_private(self, name: str) -> bool:
        return self._unlink(self._safe_path(self.private_dir, name))


class _S3Backend:
    def __init__(self, settings: Settings):
        import boto3
        from botocore.config import Config

        assert settings.s3_access_key_id and settings.s3_secret_access_key  # noqa: S101 - validado en Settings
        self.bucket = settings.s3_bucket
        prefix = settings.s3_key_prefix
        self.public_prefix = f"{prefix}/public/" if prefix else "public/"
        self.private_prefix = f"{prefix}/receipts/" if prefix else "receipts/"
        self.public_base = f"{settings.s3_public_base}/{self.public_prefix}"
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.s3_client_endpoint,
            region_name=settings.s3_region,
            aws_access_key_id=settings.s3_access_key_id.get_secret_value(),
            aws_secret_access_key=settings.s3_secret_access_key.get_secret_value(),
            config=Config(
                signature_version="s3v4",
                s3={"addressing_style": "virtual"},
                retries={"max_attempts": 3, "mode": "standard"},
                connect_timeout=5,
                read_timeout=30,
            ),
        )

    def _call(self, operation: str, **kwargs):
        from botocore.exceptions import BotoCoreError, ClientError

        try:
            return getattr(self.client, operation)(Bucket=self.bucket, **kwargs)
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in ("NoSuchKey", "404"):
                return None
            logger.error("Error de almacenamiento en %s(%s): %s", operation, kwargs.get("Key"), exc)
            raise ServiceUnavailable("El almacenamiento de archivos no está disponible. Intenta más tarde.") from exc
        except BotoCoreError as exc:
            logger.error("Error de conexión con el almacenamiento en %s: %s", operation, exc)
            raise ServiceUnavailable("El almacenamiento de archivos no está disponible. Intenta más tarde.") from exc

    def public_url(self, name: str) -> str:
        return self.public_base + name

    def public_name(self, url: str) -> str | None:
        return url[len(self.public_base) :] if url.startswith(self.public_base) else None

    def put_public(self, name: str, content: bytes, content_type: str) -> None:
        self._call(
            "put_object",
            Key=self.public_prefix + name,
            Body=content,
            ContentType=content_type,
            ACL="public-read",
            CacheControl=PUBLIC_CACHE_CONTROL,
        )

    def delete_public(self, name: str) -> bool:
        self._call("delete_object", Key=self.public_prefix + name)
        return True

    def put_private(self, name: str, content: bytes, content_type: str) -> None:
        self._call(
            "put_object",
            Key=self.private_prefix + name,
            Body=content,
            ContentType=content_type,
            ACL="private",
            CacheControl="private, no-store",
        )

    def get_private(self, name: str) -> bytes | None:
        response = self._call("get_object", Key=self.private_prefix + name)
        return response["Body"].read() if response else None

    def delete_private(self, name: str) -> bool:
        self._call("delete_object", Key=self.private_prefix + name)
        return True


@lru_cache(maxsize=4)
def _backend_for(settings_id: int, kind: str) -> _Backend:
    settings = get_settings()
    return _S3Backend(settings) if kind == "s3" else _LocalBackend(settings)


def _backend() -> _Backend:
    settings = get_settings()
    if settings.storage_backend == "s3":
        return _backend_for(id(settings), "s3")
    return _LocalBackend(settings)  # barato; respeta cambios de directorio en pruebas


def reset_backend_cache() -> None:
    """Para pruebas: obliga a crear de nuevo el cliente S3."""
    _backend_for.cache_clear()


# ---------------------------------------------------------------------------
# Operaciones síncronas (en hilo aparte)
# ---------------------------------------------------------------------------


def _save_public_images_sync(files: list[UploadFile]) -> list[str]:
    settings = get_settings()
    backend = _backend()
    # Se valida todo antes de escribir: si una imagen falla no quedan archivos huérfanos.
    processed = [_process_image(_read_limited(f, settings.max_image_size_mb), settings.thumbnail_max_px) for f in files]
    written: list[str] = []
    try:
        for image in processed:
            name = f"{uuid.uuid4().hex}.{image.ext}"
            backend.put_public(name, image.content, MEDIA_TYPES[image.ext])
            written.append(name)
            backend.put_public(_thumb_name(name), image.thumbnail, "image/webp")
    except Exception:
        for name in written:
            _delete_public_sync(backend, name)
        raise
    return [backend.public_url(name) for name in written]


def _delete_public_sync(backend: _Backend, name: str) -> bool:
    deleted = backend.delete_public(name)
    backend.delete_public(_thumb_name(name))
    return deleted


def _delete_public_url_sync(url: str | None) -> bool:
    if not url:
        return False
    backend = _backend()
    name = backend.public_name(url)
    if name is None and url.startswith(PUBLIC_URL_PREFIX):
        # Foto guardada en disco antes de pasar a S3.
        backend = _LocalBackend(get_settings())
        name = backend.public_name(url)
    if not _valid_name(name):
        return False
    assert name is not None  # noqa: S101
    return _delete_public_sync(backend, name)


def _save_receipt_sync(file: UploadFile) -> StoredFile:
    settings = get_settings()
    content, ext = _process_receipt(_read_limited(file, settings.max_receipt_size_mb))
    name = f"{uuid.uuid4().hex}.{ext}"
    _backend().put_private(name, content, MEDIA_TYPES[ext])
    return StoredFile(key=name, content_type=MEDIA_TYPES[ext])


def _read_receipt_sync(key: str) -> ReceiptContent | None:
    content = _backend().get_private(key)
    if content is None:
        return None
    ext = key.rsplit(".", 1)[-1]
    return ReceiptContent(content=content, content_type=MEDIA_TYPES[ext], extension=ext)


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------


async def save_public_image(file: UploadFile) -> str:
    """Guarda una imagen pública (más su miniatura) y devuelve su URL."""
    return (await run_in_threadpool(_save_public_images_sync, [file]))[0]


async def save_public_images(files: list[UploadFile]) -> list[str]:
    files = [f for f in files if f is not None and f.filename]
    if not files:
        return []
    return await run_in_threadpool(_save_public_images_sync, files)


async def delete_public_file(url: str | None) -> bool:
    """Elimina una foto pública y su miniatura. Ignora URLs que no generó este servicio."""
    return await run_in_threadpool(_delete_public_url_sync, url)


async def save_private_receipt(file: UploadFile) -> StoredFile:
    return await run_in_threadpool(_save_receipt_sync, file)


async def delete_private_receipt(key: str | None) -> bool:
    if not _valid_name(key):
        return False
    assert key is not None  # noqa: S101
    return await run_in_threadpool(_backend().delete_private, key)


async def read_private_receipt(key: str | None) -> ReceiptContent | None:
    if not _valid_name(key):
        return None
    assert key is not None  # noqa: S101
    return await run_in_threadpool(_read_receipt_sync, key)
