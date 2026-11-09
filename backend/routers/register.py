from fastapi import APIRouter, HTTPException, status
from backend.services.user_service import get_user_by_email, get_user_by_document, create_user_service
from backend.schemas.user_schema import UserCreate, UserRole

router = APIRouter(
    prefix="/register",
    tags=["register"]
)

MIN_PASSWORD_LENGTH = 8


@router.post("/", status_code=201)
async def register_user(new_user: UserCreate):
    # En el registro público la contraseña es obligatoria: sin ella el servicio usaría
    # el número de documento (dato semipúblico) como contraseña (5.10).
    if not new_user.password or len(new_user.password) < MIN_PASSWORD_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La contraseña es obligatoria y debe tener al menos {MIN_PASSWORD_LENGTH} caracteres.",
        )

    if await get_user_by_email(new_user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya está registrado."
        )

    if await get_user_by_document(new_user.number_document):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El número de documento ya está registrado."
        )

    new_user.role = UserRole.CLIENT
    new_user.is_active = True
    new_id = await create_user_service(new_user)

    # 5.5: NO se vinculan automáticamente reservas de invitado por correo.
    # Se habilitará con verificación de email (ver link_guest_bookings_to_user).

    return {
        "message": "Usuario registrado exitosamente en Kofán Hospedaje",
        "user_id": new_id,
    }
