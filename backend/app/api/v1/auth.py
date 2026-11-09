from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Cookie, Depends, Response, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, ConfigDict, Field

from backend.app.api.deps import CurrentUser
from backend.app.core.errors import Unauthorized
from backend.app.core.settings import get_settings
from backend.app.modules.auth import service
from backend.app.modules.auth.service import TokenOut, VerifyEmailOut
from backend.app.modules.users import service as users_service
from backend.app.modules.users.schemas import NormalizedEmail, Password, RegisterIn, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])

COOKIE_PATH = "/api/v1/auth"


class TokenIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str = Field(min_length=10, max_length=200)


class ForgotPasswordIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: NormalizedEmail


class ResetPasswordIn(TokenIn):
    password: Password


class MessageOut(BaseModel):
    message: str


def _set_refresh_cookie(response: Response, raw: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=raw,
        max_age=settings.refresh_token_expire_days * 24 * 3600,
        httponly=True,  # inaccesible para JavaScript (mitiga XSS)
        secure=settings.cookie_secure,
        samesite=settings.refresh_cookie_samesite,
        path=COOKIE_PATH,  # solo viaja a los endpoints de auth
    )


def _clear_refresh_cookie(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(settings.refresh_cookie_name, path=COOKIE_PATH,
                           secure=settings.cookie_secure, samesite=settings.refresh_cookie_samesite)


RefreshCookie = Annotated[str | None, Cookie(alias=get_settings().refresh_cookie_name)]


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterIn, background: BackgroundTasks):
    return await users_service.register(data, background)


@router.post("/login", response_model=TokenOut)
async def login(response: Response, form: Annotated[OAuth2PasswordRequestForm, Depends()]):
    session = await service.login(form.username, form.password)
    _set_refresh_cookie(response, session.refresh_token)
    return session.token


@router.post("/refresh", response_model=TokenOut)
async def refresh(response: Response, refresh_token: RefreshCookie = None):
    try:
        session = await service.refresh(refresh_token)
    except Unauthorized as exc:
        # Sesión inválida: además del 401, se borra la cookie del navegador.
        error = JSONResponse(status_code=401, content={"detail": exc.message, "code": exc.code})
        _clear_refresh_cookie(error)
        return error
    _set_refresh_cookie(response, session.refresh_token)
    return session.token


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response, refresh_token: RefreshCookie = None):
    await service.logout(refresh_token)
    _clear_refresh_cookie(response)


@router.post("/verify-email", response_model=VerifyEmailOut)
async def verify_email(data: TokenIn):
    return await service.verify_email(data.token)


@router.post("/resend-verification", response_model=MessageOut, status_code=status.HTTP_202_ACCEPTED)
async def resend_verification(user: CurrentUser, background: BackgroundTasks):
    await users_service.resend_verification(user, background)
    return MessageOut(message="Te enviamos un nuevo enlace de verificación.")


@router.post("/forgot-password", response_model=MessageOut, status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(data: ForgotPasswordIn, background: BackgroundTasks):
    await service.forgot_password(data.email, background)
    return MessageOut(message="Si el correo está registrado, recibirás un enlace para restablecer tu contraseña.")


@router.post("/reset-password", response_model=MessageOut)
async def reset_password(data: ResetPasswordIn):
    await service.reset_password(data.token, data.password)
    return MessageOut(message="Contraseña actualizada. Ya puedes iniciar sesión.")
