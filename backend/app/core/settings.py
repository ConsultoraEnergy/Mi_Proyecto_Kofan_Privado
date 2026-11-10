"""
Configuración única de la aplicación (pydantic-settings).

Todas las variables se leen de entorno o de `backend/.env`. Los campos sin valor por defecto son
obligatorios: si faltan, la aplicación no arranca.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import Field, SecretStr, field_validator, model_validator
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

    @model_validator(mode="after")
    def _smtp_requires_host(self) -> "Settings":
        if self.email_backend == "smtp" and not self.smtp_host:
            raise ValueError("EMAIL_BACKEND=smtp requiere SMTP_HOST.")
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


@lru_cache
def get_settings() -> Settings:
    return Settings()
