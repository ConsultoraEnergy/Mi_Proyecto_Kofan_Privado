from backend.db.client import db
from backend.services.storage_service import save_public_image, delete_public_file
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime, timezone
from fastapi import UploadFile

async def get_all_photos(categoria: str = None):
    query = {}
    if categoria and categoria != "todos":
        query["categoria"] = categoria 

    cursor = db.gallery.find(query).sort("created_at", -1)
    photos = []

    async for photo in cursor:
        # 🟢 SALVAVIDAS: Si no tiene fecha, no explota, solo devuelve vacío
        fecha_creacion = photo.get("created_at")
        fecha_str = fecha_creacion.isoformat() if fecha_creacion else ""

        photos.append({
            "id": str(photo["_id"]),
            "url": photo["url"],
            "titulo": photo.get("titulo", ""),
            "categoria": photo.get("categoria", "general"),
            "created_at": fecha_str,
        })

    return photos

async def upload_photo(file: UploadFile, titulo: str, categoria: str, uploader_email: str):
    # Valida el contenido real, re-codifica y guarda fuera del event loop
    url = await save_public_image(file)

    doc = {
        "url": url,
        "titulo": titulo,
        "categoria": categoria,
        "uploaded_by": uploader_email,
        "created_at": datetime.now(timezone.utc),
    }

    result = await db.gallery.insert_one(doc)
    return {"id": str(result.inserted_id), "url": url, "titulo": titulo, "categoria": categoria}

async def delete_photo(photo_id: str):
    try:
        photo_oid = ObjectId(photo_id)
    except InvalidId:
        return False

    photo = await db.gallery.find_one({"_id": photo_oid})

    if not photo:
        return False

    if "url" in photo:
        # 🟢 BORRADO FÍSICO SEGURO
        await delete_public_file(photo["url"])

    result = await db.gallery.delete_one({"_id": photo_oid})
    return result.deleted_count > 0