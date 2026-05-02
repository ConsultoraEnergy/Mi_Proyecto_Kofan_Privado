from fastapi import APIRouter, Query, HTTPException
from backend.services.availability_service import find_best_room_available
from backend.schemas.room_schema import room_schema

router = APIRouter(prefix="/busqueda", tags=["Búsqueda Pública"])

@router.get("/disponibilidad")
async def check_availability(
    tipo: str = Query(..., description="Categoría de habitación"),
    entrada: str = Query(..., description="Fecha entrada YYYY-MM-DD"),
    salida: str = Query(..., description="Fecha salida YYYY-MM-DD"),
    huespedes: int = Query(1, description="Número de huéspedes") # 🟢 Recibimos el dato
):
    # 🟢 Se lo pasamos al servicio
    habitacion = await find_best_room_available(tipo, entrada, salida, huespedes)
    
    if not habitacion:
        raise HTTPException(
            status_code=404, 
            detail=f"No hay habitaciones disponibles tipo '{tipo}' para {huespedes} huéspedes en estas fechas."
        )
    
    return room_schema(habitacion)