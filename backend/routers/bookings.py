from typing import Optional
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, Form, File, UploadFile, HTTPException, status
from fastapi.responses import FileResponse
from backend.db.client import db
from backend.dependencies.auth import get_current_user, required_admin
from backend.schemas.booking_schema import ReservaCreate, UpdateEstadoReserva, ReservaPublicCreate, UpdateReservaDetalles, ReservaAdminCreate
from backend.services.booking_service import create_booking_service, get_all_bookings_service, get_user_bookings_service, update_booking_status_service, update_booking_details_service
from backend.services.storage_service import (
    save_private_receipt,
    delete_private_receipt,
    private_receipt_path,
    legacy_public_path,
    media_type_for,
)
from datetime import datetime, timezone

router = APIRouter(
    prefix="/api/reservas", 
    tags=["api/reservas"]
)


async def _crear_reserva_con_comprobante(reserva_datos, comprobante: UploadFile, **kwargs) -> dict:
    """Guarda el comprobante en almacenamiento privado y crea la reserva.
    Si la reserva falla (fechas ocupadas, habitación inválida...), borra el comprobante."""
    clave = await save_private_receipt(comprobante)
    reserva_datos.comprobante_archivo = clave
    try:
        return await create_booking_service(reserva_datos, **kwargs)
    except Exception:
        await delete_private_receipt(clave)
        raise


# PARA CREAR UNA RESERVA, SOLO USUARIOS AUTENTICADOS
# Nota: cualquier "monto_total" que envíe el cliente se ignora; el backend calcula el precio (5.3).
@router.post("/")
async def registrar_reserva(
    habitacion_id: str = Form(...),
    fecha_entrada: str = Form(...),
    fecha_salida: str = Form(...),
    cliente_nombre: str = Form(...),
    cliente_email: str = Form(...),
    cliente_celular: str = Form(...),
    observaciones: str = Form(None),
    comprobante: UploadFile = File(...),  # RN-05: toda reserva web exige comprobante
    user = Depends(get_current_user) # 🔒 Requiere Token
):
    reserva_datos = ReservaCreate(
        habitacion_id=habitacion_id,
        fecha_entrada=fecha_entrada,
        fecha_salida=fecha_salida,
        cliente_nombre=cliente_nombre,
        cliente_email=cliente_email,
        cliente_celular=cliente_celular,
        tipo_persona="natural",
        tipo_documento="CC", 
        cliente_documento="0",
        observaciones=observaciones,
    )

    reserva = await _crear_reserva_con_comprobante(reserva_datos, comprobante, user_id=str(user["_id"]))
    
    return {
        "message": "Reserva creada exitosamente",
        "reserva_id": reserva["id"],
        "monto_total": reserva["monto_total"],
        "anticipo": reserva["anticipo"],
        "noches": reserva["noches"],
        "usuario_que_reservo": user["email"] 
    }

@router.post("/invitado")
async def registrar_reserva_publica(
    habitacion_id: str = Form(...),
    fecha_entrada: str = Form(...),
    fecha_salida: str = Form(...),
    cliente_nombre: str = Form(...),
    cliente_email: str = Form(...),
    cliente_celular: str = Form(...),
    observaciones: str = Form(None),
    comprobante: UploadFile = File(...),  # RN-05: toda reserva web exige comprobante
):
    reserva_datos = ReservaPublicCreate(
        habitacion_id=habitacion_id,
        fecha_entrada=fecha_entrada,
        fecha_salida=fecha_salida,
        cliente_nombre=cliente_nombre,
        cliente_email=cliente_email,
        cliente_celular=cliente_celular,
        tipo_persona="natural",
        tipo_documento="CC",
        cliente_documento="0",
        observaciones=observaciones,
    )

    reserva = await _crear_reserva_con_comprobante(reserva_datos, comprobante, user_id=None)
    
    return {
        "message": "¡Reserva y comprobante recibidos con éxito!",
        "reserva_id": reserva["id"],
        "monto_total": reserva["monto_total"],
        "anticipo": reserva["anticipo"],
        "noches": reserva["noches"],
        "cliente": cliente_nombre
    }


# RESERVA MANUAL DESDE EL PANEL (recepción / admin)
@router.post("/admin", status_code=status.HTTP_201_CREATED)
async def registrar_reserva_admin(datos: ReservaAdminCreate, admin_user = Depends(required_admin)):
    reserva_datos = ReservaPublicCreate(
        habitacion_id=datos.habitacion_id,
        fecha_entrada=datos.fecha_entrada,
        fecha_salida=datos.fecha_salida,
        cliente_nombre=datos.cliente_nombre,
        cliente_email=datos.cliente_email,
        cliente_celular=datos.cliente_celular,
        tipo_persona="natural",
        observaciones=datos.observaciones or "Reserva manual desde Panel Admin",
    )

    reserva = await create_booking_service(
        reserva_datos,
        user_id=None,
        monto_override=datos.monto_total,
        estado_inicial="confirmada",
        creado_por=admin_user["email"],
    )

    return {
        "message": "Reserva registrada y confirmada",
        "reserva_id": reserva["id"],
        "monto_total": reserva["monto_total"],
        "anticipo": reserva["anticipo"],
        "noches": reserva["noches"],
    }


# 5.6: los comprobantes ya no son públicos. Solo el admin o el dueño de la reserva los ven.
@router.get("/{reserva_id}/comprobante")
async def descargar_comprobante(reserva_id: str, user = Depends(get_current_user)):
    no_encontrado = HTTPException(status_code=404, detail="Comprobante no encontrado")
    try:
        reserva_oid = ObjectId(reserva_id)
    except InvalidId:
        raise no_encontrado

    reserva = await db.bookings.find_one(
        {"_id": reserva_oid},
        {"cliente_id": 1, "comprobante_archivo": 1, "comprobante_url": 1},
    )
    if not reserva:
        raise no_encontrado

    es_admin = user.get("role") == "admin"
    es_dueno = reserva.get("cliente_id") is not None and str(reserva.get("cliente_id")) == str(user["_id"])
    if not (es_admin or es_dueno):
        # 404 (no 403) para no revelar que la reserva existe.
        raise no_encontrado

    path = None
    if reserva.get("comprobante_archivo"):
        path = private_receipt_path(reserva["comprobante_archivo"])
    elif reserva.get("comprobante_url"):
        # Comprobantes antiguos que aún no se han migrado a almacenamiento privado.
        path = legacy_public_path(reserva["comprobante_url"])

    if path is None:
        raise no_encontrado

    return FileResponse(
        path,
        media_type=media_type_for(path),
        filename=f"comprobante-{reserva_id}{path.suffix}",
        content_disposition_type="inline",
        headers={
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


# 🟢 SOLO ADMIN PUEDE CAMBIAR EL ESTADO DE UNA RESERVA (AQUÍ ESTÁ LA CORRECCIÓN)
@router.patch("/{reserva_id}/estado")
async def cambiar_estado_reserva(
    reserva_id: str, 
    datos_actualizacion: UpdateEstadoReserva, 
    admin_user = Depends(required_admin) 
):
    exito = await update_booking_status_service(
        reserva_id=reserva_id, 
        nuevo_estado=datos_actualizacion.estado.value, 
        motivo=datos_actualizacion.motivo_actualizacion,
        admin_email=admin_user["email"],
        admin_id=str(admin_user["_id"]) # 🟢 LE PASAMOS EL ID AL SERVICIO PARA QUE CREE LA NOTIFICACIÓN
    )
    
    if not exito:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
        
    return {
        "message": "Estado de la reserva actualizado exitosamente",
        "admin_que_autorizo": admin_user["email"],
        "nuevo_estado": datos_actualizacion.estado.value,
        "motivo": datos_actualizacion.motivo_actualizacion
    }


@router.get("/mis-reservas")
async def listar_mis_reservas(user = Depends(get_current_user)):
    try:
        # 1. Extraemos el ID del usuario de forma segura
        user_id = str(user["_id"])
        
        # 2. Vamos a la base de datos a buscar sus reservas
        reservas = await get_user_bookings_service(user_id)
        
        # 3. Validamos que SIEMPRE devuelva una lista (incluso si está vacía)
        if not reservas:
            return []
            
        return reservas

    except Exception as e:
        # 4. Si algo explota en la BD, se lo decimos educadamente al frontend
        print(f"Error interno al buscar reservas: {e}") 
        raise HTTPException(
            status_code=500, 
            detail="Tuvimos un problema interno al cargar tus reservas. Intenta de nuevo."
        )


@router.get("/admin/todas")
async def get_all_bookings(
    estados: Optional[str] = None, 
    page: int = 1,     
    limit: int = 10,   
    admin_user = Depends(required_admin)
):
    return await get_all_bookings_service(estados_filtro=estados, page=page, limit=limit)


@router.put("/{reserva_id}/detalles")
async def actualizar_detalles_reserva(
    reserva_id: str, 
    detalles: UpdateReservaDetalles, 
    admin_user = Depends(required_admin) 
):
    # Convertimos el modelo a diccionario
    datos_actualizados = detalles.model_dump()
    
    # Convertimos los strings del frontend a datetime UTC para MongoDB
    try:
        entrada_dt = datetime.strptime(datos_actualizados["fecha_entrada"], "%Y-%m-%d")
        salida_dt = datetime.strptime(datos_actualizados["fecha_salida"], "%Y-%m-%d")
        
        # Inyectamos los objetos datetime con zona horaria UTC de vuelta al diccionario
        datos_actualizados["fecha_entrada"] = entrada_dt.replace(tzinfo=timezone.utc)
        datos_actualizados["fecha_salida"] = salida_dt.replace(tzinfo=timezone.utc)
        
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail="Formato de fecha inválido. Por favor usa el formato YYYY-MM-DD."
        )
    
    # Enviamos los datos limpios y en el formato correcto a MongoDB
    exito = await update_booking_details_service(reserva_id, datos_actualizados)
    
    if not exito:
        raise HTTPException(status_code=404, detail="Reserva no encontrada o no hubo cambios")
        
    return {
        "message": "Detalles de la reserva y acompañantes actualizados exitosamente",
        "admin": admin_user["email"]
    }