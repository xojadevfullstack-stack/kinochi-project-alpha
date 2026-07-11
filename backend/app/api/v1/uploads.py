from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
import os
import uuid
import shutil
from app.api.deps import get_current_admin

router = APIRouter(prefix="/uploads", tags=["uploads"])

UPLOAD_DIR = "uploads/posters"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/poster", status_code=status.HTTP_201_CREATED)
async def upload_poster(
    file: UploadFile = File(...),
    admin: dict = Depends(get_current_admin)
):
    """Upload a poster image (Admin only). Returns the URL path to the image."""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Faqat rasm fayllari ruxsat etiladi (MIME turi image/* bo'lishi kerak).")
        
    # Check extension
    ext = file.filename.split(".")[-1].lower() if file.filename and "." in file.filename else "jpg"
    if ext not in ["jpg", "jpeg", "png", "webp"]:
        raise HTTPException(status_code=400, detail="Faqat JPG, PNG yoki WEBP formatidagi rasmlar ruxsat etiladi.")
        
    # Generate unique filename
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    # Save file
    try:
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Faylni saqlashda xatolik: {str(e)}")
        
    # Return the URL path
    # In a real production setup with Render, local files are ephemeral. 
    # But for this phase, we'll serve it statically.
    return {"url": f"/static/posters/{filename}"}
