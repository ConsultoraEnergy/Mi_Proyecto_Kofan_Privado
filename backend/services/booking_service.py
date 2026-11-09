from backend.db.client import db
from bson import ObjectId
from bson.errors import InvalidId
from backend.schemas.booking_schema import ReservaCreate
from datetime import datetime, timezone
from fastapi import HTTPException, status 
from backend.services.notifications_service import crear_notificacion_panel
from backend.services.pricing_service import calcular_precio_reserva, calcular_anticipo


def _habitacion_activa(habitacion: dict) -> bool:
    # Datos heredados guardan "active" como bool o como texto ("true"/"false").
    return str(habitacion.get("active", True)).strip().lower() not in ("false", "0", "no")


def comprobante_endpoint(reserva: dict):
    """URL (relativa al cliente API) para descargar el comprobante, o None si no tiene."""
    if reserva.get("comprobante_archivo") or reserva.get("comprobante_url"):
        return f"/api/reservas/{reserva['_id']}/comprobante"
    return None


async def create_booking_service(
    reserva,
    user_id: str = None,
    monto_override: float = None,
    estado_inicial: str = None,
    creado_por: str = None,
):
    """
    Crea una reserva validando disponibilidad.

    - El precio se calcula aquí a partir de la tarifa de la habitación (5.3).
    - `monto_override` solo debe pasarse desde rutas de administrador (precio negociado).
    """
    # 1. VALIDAR ID Y BUSCAR HABITACIÓN
    try:
        habitacion_obj_id = ObjectId(reserva.habitacion_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="El ID de la habitación no es válido.")

    habitacion = await db.rooms.find_one({"_id": habitacion_obj_id})
    if not habitacion or not _habitacion_activa(habitacion):
        raise HTTPException(status_code=404, detail="La habitación no existe o no está disponible para reservas.")

    # 1b. PRECIO CALCULADO EN EL SERVIDOR (valida también que salida > entrada)
    precio = calcular_precio_reserva(habitacion, reserva.fecha_entrada, reserva.fecha_salida)

    # 2. PREPARAR LAS FECHAS NUEVAS (En formato UTC para buscar en MongoDB)
    nueva_entrada = datetime.combine(reserva.fecha_entrada, datetime.min.time()).replace(tzinfo=timezone.utc)
    nueva_salida = datetime.combine(reserva.fecha_salida, datetime.min.time()).replace(tzinfo=timezone.utc)

    # 3. EL MOTOR DE DISPONIBILIDAD: Buscar choques de fechas
    reserva_existente = await db.bookings.find_one({
        "habitacion_id": habitacion_obj_id,
        "estado": {"$in": ["pendiente", "confirmada", "ocupada"]}, # Ignoramos las canceladas o finalizadas
        "$and": [
            {"fecha_entrada": {"$lt": nueva_salida}}, 
            {"fecha_salida": {"$gt": nueva_entrada}}   
        ]
    })

    if reserva_existente:
        raise HTTPException(
            status_code=400, 
            detail="Lo sentimos, la habitación ya está reservada durante esas fechas."
        )

    # 4. PREPARAR DICCIONARIO PARA GUARDAR
    reserva_dict = reserva.model_dump() if hasattr(reserva, 'model_dump') else reserva.dict()
    
    reserva_dict["fecha_entrada"] = nueva_entrada
    reserva_dict["fecha_salida"] = nueva_salida
    reserva_dict.update(precio)

    if monto_override is not None:
        reserva_dict["monto_calculado"] = precio["monto_total"]
        reserva_dict["monto_total"] = round(float(monto_override), 2)
        reserva_dict["anticipo"] = calcular_anticipo(reserva_dict["monto_total"])

    if reserva_dict.get("cliente_email"):
        reserva_dict["cliente_email"] = reserva_dict["cliente_email"].strip().lower()

    reserva_dict["estado"] = estado_inicial or "pendiente"
    if creado_por:
        reserva_dict["creado_por"] = creado_por
        
    reserva_dict["cliente_id"] = ObjectId(user_id) if user_id else None 
    reserva_dict["habitacion_id"] = habitacion_obj_id
    reserva_dict["created_at"] = datetime.now(timezone.utc)

    # 5. GUARDAR LA RESERVA
    result = await db.bookings.insert_one(reserva_dict)

    return {
        "id": str(result.inserted_id),
        "noches": reserva_dict["noches"],
        "precio_noche": reserva_dict["precio_noche"],
        "monto_total": reserva_dict["monto_total"],
        "anticipo": reserva_dict["anticipo"],
        "porcentaje_anticipo": reserva_dict["porcentaje_anticipo"],
    }


# 🟢 ACTUALIZADO: Capta el estado anterior y notifica a Cliente y Admin con el nombre real de la habitación
# 🟢 ACTUALIZADO: Capta el estado anterior y notifica a Cliente y Admin con el nombre real de la habitación
async def update_booking_status_service(reserva_id: str, nuevo_estado: str, motivo: str = None, admin_email: str = None, admin_id: str = None):
    estado_str = str(nuevo_estado).lower()

    # 1. CAPTURAMOS EL ESTADO Y DATOS ANTES DEL CAMBIO
    reserva_previa = await db.bookings.find_one({"_id": ObjectId(reserva_id)})
    if not reserva_previa:
        return False
        
    estado_anterior = reserva_previa.get("estado", "desconocido")
    cliente_id = reserva_previa.get("cliente_id")
    
    # 2. PREPARAMOS LOS DATOS DE ACTUALIZACIÓN
    update_data = {
        "estado": estado_str,
        "updated_at": datetime.now(timezone.utc)
    }
    
    if motivo:
        update_data["motivo_actualizacion"] = motivo
    if admin_email:
        update_data["actualizado_por"] = admin_email
        
    # 3. EJECUTAMOS LA ACTUALIZACIÓN EN MONGODB
    result = await db.bookings.update_one(
        {"_id": ObjectId(reserva_id)}, 
        {"$set": update_data}
    )
    
    # 4. LÓGICA DE NOTIFICACIONES
    if result.matched_count > 0:
        
        # A) LÓGICA BLINDADA PARA BUSCAR EL NOMBRE DE LA HABITACIÓN
        habitacion_id = reserva_previa.get("habitacion_id")
        nombre_hab = "nuestras instalaciones"
        
        if habitacion_id:
            try:
                habitacion = await db.rooms.find_one({"_id": ObjectId(str(habitacion_id))})
                if habitacion:
                    nombre_oficial = habitacion.get("name")
                    if nombre_oficial:
                        nombre_hab = nombre_oficial
                    else:
                        numero = habitacion.get("room_number", "S/N")
                        tipo = habitacion.get("type", "Cabaña").capitalize()
                        nombre_hab = f"Hab. {numero} - {tipo}"
            except Exception as e:
                print(f"Error silencioso al buscar habitación: {e}")

        # B) ARMAMOS LOS MENSAJES Y COLORES
        config = {
            "confirmada": ("¡Reserva Confirmada!", "success", "bi-check-circle-fill"),
            "ocupada": ("¡Check-in Realizado!", "info", "bi-house-door-fill"),
            "finalizada": ("¡Check-out Exitoso!", "secondary", "bi-check2-all"),
            "cancelada": ("Reserva Cancelada", "danger", "bi-x-circle-fill")
        }
        
        titulo, tipo, icono = config.get(estado_str, ("Actualización de Reserva", "primary", "bi-info-circle-fill"))

        # C) NOTIFICAR AL CLIENTE (Si tiene cuenta)
        if cliente_id:
            mensaje_cliente = f"Tu reserva para '{nombre_hab}' ahora está: {estado_str.upper()}."
            if estado_str == "confirmada":
                mensaje_cliente = f"Tu estancia en '{nombre_hab}' ha sido aprobada. ¡Te esperamos!"
            
            await crear_notificacion_panel(
                user_id=str(cliente_id),
                titulo=titulo,
                mensaje=mensaje_cliente,
                tipo=tipo,
                icono=icono
            )
            
        # D) NOTIFICAR AL ADMIN (Para que salga en el historial del Dashboard)
        if admin_id:
            # Buscamos el nombre del cliente para el historial
            nombre_cliente = reserva_previa.get("cliente_nombre")
            if not nombre_cliente and cliente_id:
                cliente_db = await db.users.find_one({"_id": ObjectId(str(cliente_id))})
                if cliente_db:
                    nombre_cliente = cliente_db.get("full_name")
            if not nombre_cliente:
                nombre_cliente = "un cliente"

            # 🟢 AQUÍ ESTÁ LA MAGIA: Incluimos el correo de quien autorizó el cambio
            quien_cambio = admin_email if admin_email else "un administrador"
            mensaje_historial = f"La reserva de {nombre_cliente} ({nombre_hab}) pasó de '{estado_anterior.upper()}' a '{estado_str.upper()}' (Modificado por: {quien_cambio})."
            
            await crear_notificacion_panel(
                user_id=admin_id,
                titulo=f"Movimiento: {titulo}",
                mensaje=mensaje_historial,
                tipo=tipo,
                icono=icono
            )
            
    return result.matched_count > 0


async def get_user_bookings_service(user_id: str) -> list:
    """
    Obtiene las reservas de un usuario específico (mis reservas)
    """
    pipeline = [
        {"$match": {"cliente_id": ObjectId(user_id)}},
        {"$lookup": {
            "from": "rooms",
            "localField": "habitacion_id",
            "foreignField": "_id",
            "as": "habitacion_info"
        }},
        {"$unwind": {"path": "$habitacion_info", "preserveNullAndEmptyArrays": True}}
    ]

    cursor = db.bookings.aggregate(pipeline)
    mis_reservas = []

    async for reserva in cursor:
        habitacion = reserva.get("habitacion_info")
        
        if habitacion:
            nombre_oficial = habitacion.get("name")
            if nombre_oficial:
                info_habitacion = nombre_oficial
            else:
                numero = habitacion.get("room_number", "S/N")
                tipo = habitacion.get("type", "Cabaña").capitalize()
                info_habitacion = f"Hab. {numero} - {tipo}"
        else:
            info_habitacion = "Habitación no encontrada"
            
        fecha_ent = reserva.get("fecha_entrada")
        fecha_sal = reserva.get("fecha_salida")
        fecha_crea = reserva.get("created_at", reserva.get("fecha_creacion")) 

        mis_reservas.append({
            "id": str(reserva["_id"]),
            "habitacion_nombre": info_habitacion, 
            "habitacion_id": str(reserva.get("habitacion_id", "")),
            "fecha_entrada": fecha_ent.strftime("%Y-%m-%d") if hasattr(fecha_ent, 'strftime') else str(fecha_ent)[:10],
            "fecha_salida": fecha_sal.strftime("%Y-%m-%d") if hasattr(fecha_sal, 'strftime') else str(fecha_sal)[:10],
            "fecha_creacion": fecha_crea.strftime("%Y-%m-%d") if hasattr(fecha_crea, 'strftime') else str(fecha_crea)[:10],
            "monto_total": reserva.get("monto_total", 0),
            "estado": reserva.get("estado", "pendiente"),
            "observaciones": reserva.get("observaciones", "")
        })
    
    return mis_reservas


async def get_all_bookings_service(estados_filtro: str = None, page: int = 1, limit: int = 10) -> dict:
    """
    Obtiene todas las reservas con soporte para filtros de múltiples estados (pestañas) y paginación.
    """
    pipeline = []
    query_count = {}
    
    if estados_filtro:
        lista_estados = estados_filtro.split(",")
        filtro_match = {"estado": {"$in": lista_estados}}
        pipeline.append({"$match": filtro_match})
        query_count = filtro_match

    skip = (page - 1) * limit
    total_documentos = await db.bookings.count_documents(query_count)
    total_paginas = (total_documentos + limit - 1) // limit if limit > 0 else 1

    pipeline.extend([
        {"$sort": {"fecha_entrada": -1}}, 
        {"$skip": skip},
        {"$limit": limit},
        {"$lookup": {"from": "rooms", "localField": "habitacion_id", "foreignField": "_id", "as": "habitacion_info"}},
        {"$lookup": {"from": "clients", "localField": "cliente_id", "foreignField": "_id", "as": "cliente_info"}},
        {"$unwind": {"path": "$habitacion_info", "preserveNullAndEmptyArrays": True}},
        {"$unwind": {"path": "$cliente_info", "preserveNullAndEmptyArrays": True}}
    ])

    cursor = db.bookings.aggregate(pipeline)
    lista_global = []
    conteo_pendientes = 0

    async for reserva in cursor:
        habitacion = reserva.get("habitacion_info", {})
        cliente = reserva.get("cliente_info", {})
        
        estado = reserva.get("estado", "pendiente")
        if estado == "pendiente":
            conteo_pendientes += 1

        nombre_cliente = cliente.get("full_name", reserva.get("cliente_nombre", "Desconocido"))
        correo_cliente = reserva.get("cliente_email", cliente.get("email", ""))
        celular_cliente = reserva.get("cliente_celular", cliente.get("phone", "")) 

        numero_hab = habitacion.get('room_number', habitacion.get('numero_unidad', 'S/N'))

        lista_global.append({
            "id": str(reserva["_id"]),
            "habitacion_id": str(habitacion.get("_id", "")) if habitacion else None, 
            "cliente": nombre_cliente,
            "cliente_email": correo_cliente,
            "cliente_celular": celular_cliente,
            "tipo_documento": reserva.get("tipo_documento", ""),
            "cliente_documento": reserva.get("cliente_documento", ""),
            "acompanantes": reserva.get("acompanantes", []),
            "consumos_extras": reserva.get("consumos_extras", []),
            "habitacion": f"Hab. {numero_hab}" if habitacion else "N/A",
            "monto": reserva.get("monto_total", 0),
            "estado": estado,
            "fecha_entrada": str(reserva.get("fecha_entrada", "N/A"))[:10],
            "fecha_salida": str(reserva.get("fecha_salida", "N/A"))[:10],
            # 5.6: ya no se expone la ruta del archivo; solo el endpoint autenticado.
            "comprobante_url": comprobante_endpoint(reserva),
        })

    habitaciones_ocupadas = await db.rooms.count_documents({"is_available": False})
    total_habitaciones = await db.rooms.count_documents({})

    return {
        "resumen": {
            "total_encontradas": total_documentos, 
            "pendientes_por_aprobar": conteo_pendientes,
            "ocupacion_actual": f"{habitaciones_ocupadas}/{total_habitaciones}",
            "porcentaje_ocupacion": f"{(habitaciones_ocupadas/total_habitaciones)*100:.1f}%" if total_habitaciones > 0 else "0%",
            "total_paginas": total_paginas,        
            "pagina_actual": page                
        },
        "reservas": lista_global
    }
    

async def update_booking_details_service(reserva_id: str, datos: dict) -> bool:
    try:
        id_obj = ObjectId(reserva_id)
        resultado = await db.bookings.update_one(
            {"_id": id_obj},
            {"$set": datos}
        )
        return resultado.matched_count > 0
    except Exception as e:
        print(f"Error actualizando detalles de reserva: {e}")
        return False