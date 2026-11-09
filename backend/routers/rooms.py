from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File, Form, status
from typing import Optional, List
from backend.db.client import db
from backend.services.storage_service import save_public_images, delete_public_file
from backend.models.room_model import RoomCreate, RoomUpdate
from backend.dependencies.auth import required_admin
from backend.services.room_service import (
    create_room, get_rooms, get_room, update_room, 
    delete_room, create_room_with_images, remove_room_image, add_room_images_to_db,
    get_room_logs # 🟢 IMPORTAMOS NUESTRA NUEVA FUNCIÓN
)
from backend.schemas.room_schema import room_schema, rooms_schema
from bson import ObjectId

router = APIRouter(prefix="/rooms", tags=["Gestión de Habitaciones"])

# 🟢 NUEVO ENDPOINT: Historial de movimientos (Debe ir ANTES de /{room_id})
@router.get("/logs/history")
async def room_history(page: int = 1, limit: int = 8, user=Depends(required_admin)):
    """Obtiene el registro de movimientos paginado"""
    logs = await get_room_logs(page, limit)
    return logs

# --- ENDPOINTS PÚBLICOS (Para la vista de clientes en Vue) ---
@router.get("/public")
async def get_public_rooms():
    cursor = db.rooms.find({"active": True, "is_available": True}) 
    habitaciones = await cursor.to_list(length=100)
    return rooms_schema(habitaciones)

@router.get("/public/{room_id}")
async def get_public_room_detail(room_id: str):
    habitacion = await db.rooms.find_one({
        "_id": ObjectId(room_id), 
        "active": True
    })
    if not habitacion:
        raise HTTPException(status_code=404, detail="Habitación no encontrada o inactiva")
    return room_schema(habitacion)

# 1. CREAR HABITACIÓN
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create(data: RoomCreate, user=Depends(required_admin)):
    return await create_room(data.model_dump(), user["email"])

# 2. LISTAR HABITACIONES
@router.get("/")
async def list_rooms(
    page: int = 1, limit: int = 10,
    name: Optional[str] = Query(None), active: Optional[bool] = Query(None),
):
    filters = {"name": name, "active": active}
    return await get_rooms(page, limit, filters)

# 3. VER DETALLE DE HABITACIÓN
@router.get("/{room_id}")
async def get(room_id: str):
    room = await get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Habitación no encontrada")
    return room

# 4. ACTUALIZAR HABITACIÓN
@router.put("/{room_id}")
async def update(room_id: str, data: RoomUpdate, user=Depends(required_admin)):
    updated = await update_room(
        room_id, data.model_dump(exclude_unset=True, exclude={"id"}), user["email"],
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Habitación no encontrada")
    return updated

# 5. ELIMINAR HABITACIÓN
@router.delete("/{room_id}")
async def delete(room_id: str, user=Depends(required_admin)):
    room = await get_room(room_id)
    if not room:
         raise HTTPException(status_code=404, detail="Habitación no encontrada")
         
    for image_url in room.get("images", []):
        await delete_public_file(image_url)
        
    # 🟢 Pasamos el user["email"] para el registro
    await delete_room(room_id, user["email"])
    return {"message": "Habitación y sus imágenes eliminadas correctamente"}

# 6. CREAR HABITACIÓN CON MÚLTIPLES IMÁGENES
@router.post("/create-with-images")
async def create_new_room_with_images(
    room_number: str = Form(...), name: str = Form(...), price: float = Form(...),
    capacity: int = Form(...), description: str = Form(""), active: bool = Form(True),
    type: str = Form(...), num_cuartos: int = Form(1), tipo_camas: str = Form(""),
    amenities: List[str] = Form([]), images: List[UploadFile] = File(...),
    user = Depends(required_admin)  # 5.2: antes bastaba con cualquier usuario autenticado
):
    data = {
        "room_number": room_number, "name": name, "price": price,
        "capacity": capacity, "description": description, "active": active,
        "amenities": amenities, "type": type, "num_cuartos": num_cuartos,
        "tipo_camas": tipo_camas,
    }
    
    image_urls = await save_public_images(images)

    return await create_room_with_images(data=data, images=image_urls, user_email=user["email"])

# 7. ELIMINAR UNA IMAGEN ESPECÍFICA
@router.delete("/{room_id}/delete-image")
async def delete_room_image(room_id: str, url: str, user=Depends(required_admin)):
    await remove_room_image(room_id, url, user["email"])
    await delete_public_file(url)
    return {"message": "Imagen eliminada con éxito"}

# 8. AGREGAR IMÁGENES A HABITACIÓN EXISTENTE
@router.post("/{room_id}/add-images")
async def add_images(room_id: str, files: List[UploadFile] = File(...), user=Depends(required_admin)):
    new_urls = await save_public_images(files)
    # 🟢 Pasamos el user["email"] para el registro
    exito = await add_room_images_to_db(room_id, new_urls, user["email"])
    
    if not exito:
        raise HTTPException(status_code=500, detail="Error al actualizar la base de datos")
    return {"message": "Fotos agregadas con éxito", "urls": new_urls}


@router.get("/{room_id}/booked-dates")
async def get_booked_dates(room_id: str):
    try:
       
        try:
            id_obj = ObjectId(room_id)
            condicion_id = {"$in": [room_id, id_obj]}
        except:
            condicion_id = room_id 

        query = {
            "habitacion_id": condicion_id,
            "estado": {"$ne": "cancelada"}
        }
        
        cursor = db.bookings.find(query, {"fecha_entrada": 1, "fecha_salida": 1, "_id": 0})
        reservas = await cursor.to_list(length=1000)
        
        return reservas
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching booked dates: {str(e)}")