from backend.db.client import db
from backend.services.storage_service import save_public_image, delete_public_file
from fastapi import UploadFile

async def get_site_config():
    # Buscamos la configuración, excluyendo el ID de Mongo
    return await db.settings.find_one({}, {"_id": 0})

async def update_site_config(data_dict: dict):
    # Actualizamos los datos. upsert=True crea el documento si no existe
    await db.settings.update_one({}, {"$set": data_dict}, upsert=True)
    return {"message": "Configuración de Kofán actualizada"}

async def update_site_logo(file: UploadFile):
    # 1. Buscamos el logo viejo
    config_actual = await db.settings.find_one({})
    logo_viejo = config_actual.get("logo_url") if config_actual else None

    # 2. Guardamos el nuevo archivo (validado y re-codificado)
    file_url = await save_public_image(file)
    
    # 3. Actualizamos la BD
    await db.settings.update_one({}, {"$set": {"logo_url": file_url}}, upsert=True)

    # 4. Limpiamos la basura del disco duro
    if logo_viejo:
        await delete_public_file(logo_viejo)

    return {"logo_url": file_url}