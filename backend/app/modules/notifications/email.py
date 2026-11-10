"""
Envío de correos. Backends:
- console: escribe el correo en el log (desarrollo y pruebas).
- smtp: cualquier servidor SMTP (Gmail, Zoho, hosting, Brevo...) configurado por .env.

Los correos se envían en segundo plano (BackgroundTasks) para no bloquear la petición; un fallo de
envío se registra pero no rompe el flujo del usuario.
"""

import logging
import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import make_msgid

from fastapi.concurrency import run_in_threadpool

from backend.app.core.settings import get_settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Email:
    to: str
    subject: str
    text: str
    html: str | None = None


# Bandeja en memoria para las pruebas (solo backend console).
outbox: list[Email] = []


def _build_message(email: Email) -> EmailMessage:
    settings = get_settings()
    message = EmailMessage()
    message["From"] = settings.email_from
    message["To"] = email.to
    message["Subject"] = email.subject
    message["Message-ID"] = make_msgid()
    message.set_content(email.text)
    if email.html:
        message.add_alternative(email.html, subtype="html")
    return message


def _send_smtp(email: Email) -> None:
    settings = get_settings()
    message = _build_message(email)
    password = settings.smtp_password.get_secret_value() if settings.smtp_password else None
    context = ssl.create_default_context()
    host = settings.smtp_host
    if not host:  # Settings ya lo exige con EMAIL_BACKEND=smtp; defensa adicional
        raise RuntimeError("SMTP_HOST no está configurado.")
    server: smtplib.SMTP
    if settings.smtp_ssl:
        server = smtplib.SMTP_SSL(host, settings.smtp_port, timeout=settings.smtp_timeout_seconds, context=context)
    else:
        server = smtplib.SMTP(host, settings.smtp_port, timeout=settings.smtp_timeout_seconds)
    with server:
        if settings.smtp_starttls and not settings.smtp_ssl:
            server.starttls(context=context)
        if settings.smtp_user and password:
            server.login(settings.smtp_user, password)
        server.send_message(message)


async def send_email(email: Email) -> None:
    settings = get_settings()
    try:
        if settings.email_backend == "smtp":
            await run_in_threadpool(_send_smtp, email)
        else:
            outbox.append(email)
            logger.info("EMAIL (console) para %s | %s\n%s", email.to, email.subject, email.text)
    except Exception:
        logger.exception("No se pudo enviar el correo '%s' a %s", email.subject, email.to)
