from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, status
from typing import Optional
from backend.services.gallery_service import get_all_photos, upload_photo, delete_photo
from backend.dependencies.auth import required_admin

router = APIRouter(prefix="/gallery", tags=["Gallery"])

@router.get("/")
async def get_gallery(categoria: Optional[str] = None):
    # 🟢 1. DELEGAMOS LA BÚSQUEDA AL SERVICIO
    return await get_all_photos(categoria)

@router.post("/")
async def upload_gallery_image(
    file: UploadFile = File(...),
    categoria: str = Form("general"),
    user = Depends(required_admin)  # Protege la ruta y nos dice quién subió la foto
):
    # El servicio valida el archivo y responde 400/413 con un mensaje claro si no es válido.
    # Nota: el título inicial será el nombre del archivo
    return await upload_photo(file, titulo=file.filename, categoria=categoria, uploader_email=user["email"])
            
@router.delete("/{image_id}", dependencies=[Depends(required_admin)])
async def delete_gallery_image(image_id: str):
    # 🟢 3. DELEGAMOS EL BORRADO (Físico y de BD) AL SERVICIO
    exito = await delete_photo(image_id)
    
    if not exito:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Imagen no encontrada")
    
    return {"message": "Imagen y archivo eliminados exitosamente"}