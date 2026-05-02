from backend.db.client import db
from backend.core.security import hash_password
from bson import ObjectId
from pymongo import ReturnDocument

async def create_user_service(user_data):
    if not isinstance(user_data, dict):
        user_data = user_data.model_dump()
    raw_password = user_data.get("password") or user_data.get("number_document")
    
    if not raw_password:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Se requiere contraseña o número de documento")
    user_data["password"] = hash_password(raw_password)
    # 🟢 CAMBIO: db.clients -> db.users
    result = await db.users.insert_one(user_data)
    return str(result.inserted_id)

async def update_user_service(user_id: str, update_data: dict):
    # 🟢 CAMBIO: db.clients -> db.users
    return await db.users.find_one_and_update(
        {"_id": ObjectId(user_id)},
        {"$set": update_data},
        return_document=ReturnDocument.AFTER
    )

async def delete_user_service(user_id: str):
    # 🟢 CAMBIO: db.clients -> db.users
    result = await db.users.delete_one({"_id": ObjectId(user_id)})
    return result.deleted_count > 0

async def get_user_by_email(email: str):
    # 🟢 CAMBIO: db.clients -> db.users
    return await db.users.find_one({"email": email})

async def get_user_by_document(doc: str):
    # 🟢 CAMBIO: db.clients -> db.users
    return await db.users.find_one({"number_document": doc})

async def get_user_by_id(user_id: str):
    # 🟢 CAMBIO: db.clients -> db.users
    return await db.users.find_one({"_id": ObjectId(user_id)})

async def deactivate_user_service(user_id: str):
    # 🟢 CAMBIO: db.clients -> db.users
    result = await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"is_active": False}}
    )
    return result.matched_count > 0

async def toggle_user_status_service(user_id: str):
    # 🟢 CAMBIO: db.clients -> db.users
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return None
    
    new_status = not user.get("is_active", True)
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"is_active": new_status}}
    )
    return new_status

async def get_all_users_service(skip: int = 0, limit: int = 50):
    # 🟢 CAMBIO: db.clients -> db.users
    cursor = db.users.find().skip(skip).limit(limit)
    users = await cursor.to_list(length=limit)
    
    for user in users:
        user["_id"] = str(user["_id"])
        user.pop("password", None) 
        
    return users



async def link_guest_bookings_to_user(email: str, user_id: str):
    """
    Busca todas las reservas hechas con este correo que no tengan 
    un usuario asignado y las vincula al nuevo user_id.
    """
   
    email_limpio = email.strip().lower()

    filtro_correo = {"$regex": f"^{email_limpio}$", "$options": "i"}

    result = await db.bookings.update_many(
        {
            "cliente_email": filtro_correo,  # 🟢 Usamos el campo correcto de tu BD
            "cliente_id": {"$in": [None, ""]} # 🟢 Usamos el campo correcto de tu BD
        },
        {
            "$set": {
                "cliente_id": ObjectId(user_id)        # 🟢 Inyectamos el nuevo ID aquí
            }
        }
    )
    return result.modified_count