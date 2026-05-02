from fastapi import APIRouter, HTTPException, status
from backend.services.user_service import get_user_by_email, get_user_by_document, create_user_service, link_guest_bookings_to_user
from backend.schemas.user_schema import UserCreate

router = APIRouter(
    prefix="/register",
    tags=["register"]
)

@router.post("/", status_code=201)
async def register_user(new_user: UserCreate):
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
        
    new_user.role = "client"
    new_id = await create_user_service(new_user)
    
    # 🟢 2. LA MAGIA: Vinculamos las reservas pasadas al nuevo ID
    reservas_vinculadas = await link_guest_bookings_to_user(new_user.email, new_id)
    
    return {
        "message": "Usuario registrado exitosamente en Kofán Hospedaje",
        "user_id": new_id,
        "reservas_recuperadas": reservas_vinculadas # 🟢 Opcional: te dice cuántas rescató
    }