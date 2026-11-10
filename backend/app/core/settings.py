"""
Configuración única de la aplicación (pydantic-settings).

Todas las variables se leen de entorno o de `backend/.env`. Los campos sin valor por defecto son
obligatorios: si faltan, la aplicación no arranca.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from pydantic import AliasChoices, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]

_INSECURE_SECRETS = {"mysecretkey", "secret", "changeme", "change-me", "secret-key"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Entorno ---
    app_env: Literal["development", "test", "production"] = "development"

    # --- Identidad del hotel (valores iniciales; el contenido editable vive en la colección settings) ---
    hotel_name: str = "Hotel Kawari"
    timezone: str = "America/Bogota"
    currency: str = "COP"

    # --- Base de datos ---
    mongo_uri: SecretStr
    mongo_db_name: str = "kawari"

    # --- Seguridad ---
    secret_key: SecretStr
    access_token_expire_minutes: int = Field(default=15, ge=1, le=120)
    refresh_token_expire_days: int = Field(default=7, ge=1, le=60)
    refresh_cookie_name: str = "kawari_refresh"
    refresh_cookie_secure: bool | None = None  # None = True en producción, False en desarrollo
    refresh_cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    email_verification_expire_hours: int = 48
    password_reset_expire_minutes: int = 60
    set_password_expire_hours: int = 72

    # --- Reservas ---
    deposit_percent: int = Field(default=50, ge=0, le=100)
    booking_payment_deadline_hours: int = Field(default=48, ge=1)
    booking_expiration_check_minutes: int = Field(default=15, ge=1)
    booked_dates_window_days: int = Field(default=540, ge=30)
    booking_code_prefix: str = Field(default="KW", pattern=r"^[A-Z]{1,4}$")

    # --- Archivos ---
    upload_dir: Path = BACKEND_DIR / "static" / "uploads"
    private_upload_dir: Path = BACKEND_DIR / "private_uploads"
    max_image_size_mb: int = Field(default=8, ge=1)
    max_receipt_size_mb: int = Field(default=5, ge=1)
    thumbnail_max_px: int = Field(default=800, ge=100, le=2000)

    # --- Object storage (S3 compatible: DigitalOcean Spaces, Cloudflare R2, AWS S3) ---
    # local = disco (desarrollo y pruebas) | s3 = bucket. Se aceptan también los nombres DO_* de DigitalOcean.
    storage_backend: Literal["local", "s3"] = "local"
    s3_endpoint_url: str | None = Field(
        default=None, validation_alias=AliasChoices("S3_ENDPOINT_URL", "DO_S3_ENDPOINT_URL")
    )
    s3_region: str = Field(default="us-east-1", validation_alias=AliasChoices("S3_REGION", "DO_AWS_REGION"))
    s3_bucket: str | None = Field(default=None, validation_alias=AliasChoices("S3_BUCKET", "DO_AWS_BUCKET_NAME"))
    s3_access_key_id: SecretStr | None = Field(
        default=None, validation_alias=AliasChoices("S3_ACCESS_KEY_ID", "DO_AWS_ACCESS_KEY_ID")
    )
    s3_secret_access_key: SecretStr | None = Field(
        default=None, validation_alias=AliasChoices("S3_SECRET_ACCESS_KEY", "DO_AWS_SECRET_ACCESS_KEY")
    )
    # Carpeta raíz dentro del bucket (permite compartir el bucket con otros proyectos).
    s3_key_prefix: str = "kawari"
    # URL pública de las fotos, idealmente el CDN: https://<bucket>.<region>.cdn.digitaloceanspaces.com
    # Si se omite se usa el endpoint de origen del bucket (sin CDN).
    s3_public_base_url: str | None = None

    # --- Email ---
    email_backend: Literal["console", "smtp"] = "console"
    email_from: str = "Hotel Kawari <no-reply@localhost>"
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: SecretStr | None = None
    smtp_starttls: bool = True
    smtp_ssl: bool = False
    smtp_timeout_seconds: int = 15
    frontend_url: str = "http://localhost:5173"

    # --- Tareas programadas ---
    scheduler_enabled: bool = True

    # --- Observabilidad ---
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_format: Literal["json", "text"] | None = None  # None = json en producción, text en desarrollo
    sentry_dsn: SecretStr | None = None  # vacío = Sentry desactivado
    sentry_traces_sample_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    app_release: str | None = None  # p. ej. el SHA del commit; se reporta a Sentry

    @field_validator("secret_key")
    @classmethod
    def _secret_key_must_be_strong(cls, value: SecretStr) -> SecretStr:
        raw = value.get_secret_value()
        if len(raw) < 32 or raw.lower() in _INSECURE_SECRETS:
            raise ValueError(
                "SECRET_KEY es insegura. Usa al menos 32 caracteres aleatorios: "
                'python -c "import secrets; print(secrets.token_urlsafe(48))"'
            )
        return value

    @field_validator("timezone")
    @classmethod
    def _timezone_must_exist(cls, value: str) -> str:
        ZoneInfo(value)  # lanza error si la zona no existe
        return value

    @field_validator("frontend_url")
    @classmethod
    def _strip_trailing_slash(cls, value: str) -> str:
        return value.rstrip("/")

    @field_validator("s3_key_prefix")
    @classmethod
    def _normalize_prefix(cls, value: str) -> str:
        value = value.strip("/")
        if value and not all(part.replace("-", "").replace("_", "").isalnum() for part in value.split("/")):
            raise ValueError("S3_KEY_PREFIX solo admite letras, números, guiones y '/'.")
        return value

    @model_validator(mode="after")
    def _smtp_requires_host(self) -> "Settings":
        if self.email_backend == "smtp" and not self.smtp_host:
            raise ValueError("EMAIL_BACKEND=smtp requiere SMTP_HOST.")
        return self

    @model_validator(mode="after")
    def _s3_requires_credentials(self) -> "Settings":
        if self.storage_backend == "s3":
            missing = [
                name
                for name, value in (
                    ("S3_BUCKET", self.s3_bucket),
                    ("S3_ACCESS_KEY_ID", self.s3_access_key_id),
                    ("S3_SECRET_ACCESS_KEY", self.s3_secret_access_key),
                )
                if not value
            ]
            if missing:
                raise ValueError(f"STORAGE_BACKEND=s3 requiere: {', '.join(missing)}.")
        return self

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def effective_log_format(self) -> str:
        if self.log_format is not None:
            return self.log_format
        return "json" if self.is_production else "text"

    @property
    def cookie_secure(self) -> bool:
        if self.refresh_cookie_secure is not None:
            return self.refresh_cookie_secure
        return self.is_production

    @property
    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.timezone)

    @property
    def s3_client_endpoint(self) -> str | None:
        """Endpoint regional para boto3. Acepta también el "Origin Endpoint" de DigitalOcean
        (https://<bucket>.<region>.digitaloceanspaces.com) quitándole el nombre del bucket."""
        if not self.s3_endpoint_url:
            return None
        parts = urlsplit(self.s3_endpoint_url.rstrip("/"))
        host = parts.hostname or ""
        if self.s3_bucket and host.startswith(f"{self.s3_bucket}."):
            host = host[len(self.s3_bucket) + 1 :]
        return f"{parts.scheme or 'https'}://{host}"

    @property
    def s3_public_base(self) -> str:
        """Origen público de las fotos (CDN si se configuró), sin barra final."""
        if self.s3_public_base_url:
            return self.s3_public_base_url.rstrip("/")
        endpoint = self.s3_client_endpoint
        if endpoint:
            parts = urlsplit(endpoint)
            return f"{parts.scheme}://{self.s3_bucket}.{parts.hostname}"
        return f"https://{self.s3_bucket}.s3.{self.s3_region}.amazonaws.com"


@lru_cache
def get_settings() -> Settings:
    return Settings()
