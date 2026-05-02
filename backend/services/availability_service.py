from datetime import datetime, timezone
from bson import ObjectId
from backend.db.client import db
from fastapi import HTTPException

# 🟢 Agregamos "huespedes: int" a los parámetros de la función
async def find_best_room_available(tipo_habitacion: str, fecha_entrada_str: str, fecha_salida_str: str, huespedes: int):
    try:
        entrada_dt = datetime.strptime(fecha_entrada_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        salida_dt = datetime.strptime(fecha_salida_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)

        if entrada_dt >= salida_dt:
            raise HTTPException(status_code=400, detail="La fecha de salida debe ser posterior a la entrada.")

        # 1. Obtener IDs de habitaciones ocupadas
        reservas_ocupadas = await db.bookings.find({
            "estado": {"$in": ["pendiente", "confirmada", "ocupada"]},
            "$and": [
                {"fecha_entrada": {"$lt": salida_dt}}, 
                {"fecha_salida": {"$gt": entrada_dt}}   
            ]
        }, {"habitacion_id": 1}).to_list(length=None)

        ids_ocupados = [reserva["habitacion_id"] for reserva in reservas_ocupadas]

        # 2. BÚSQUEDA FLEXIBLE DEL TIPO DE HABITACIÓN
        # 2. BÚSQUEDA FLEXIBLE DEL TIPO DE HABITACIÓN
        tipo_buscado = tipo_habitacion.lower()
        
        # Si la palabra "caba" o "cabin" está en la búsqueda
        if "caba" in tipo_buscado or "cabin" in tipo_buscado:
            filtro_tipo = {"$regex": "caba|cabin", "$options": "i"}
            
        # Si tiene "fami" o "family", es familiar
        elif "fami" in tipo_buscado or "family" in tipo_buscado:
            filtro_tipo = {"$regex": "fami|family", "$options": "i"}
            
        # Si no es ninguna, asumimos que es Individual
        else:
            filtro_tipo = {"$regex": "indiv", "$options": "i"}

        # ⚠️ ESTA ES LA PARTE QUE SE HABÍA BORRADO:
        query_candidatas = {
            "type": filtro_tipo,
            "_id": {"$nin": ids_ocupados}
        }

        # 3. Traemos todas las candidatas y hacemos el filtro exacto en Python
        habitaciones_candidatas = await db.rooms.find(query_candidatas).to_list(length=None)

        
        mejor_habitacion = None

        for hab in habitaciones_candidatas:
            # Forzamos la capacidad a número (por si se guardó como texto en MongoDB)
            capacidad_hab = int(hab.get("capacity", 0)) 
            
            if capacidad_hab >= huespedes:
                # Validamos que esté activa y disponible (incluso si se guardó como texto "true")
                if hab.get("active") in [True, "true", "True"] and hab.get("is_available") in [True, "true", "True"]:
                    # Si es la primera que pasa, o es más barata que la anterior, la guardamos
                    if mejor_habitacion is None or float(hab.get("price", 0)) < float(mejor_habitacion.get("price", 0)):
                        mejor_habitacion = hab

        if not mejor_habitacion:
            raise HTTPException(status_code=404, detail="No hay disponibilidad")

        return mejor_habitacion

    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido")