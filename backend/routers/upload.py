from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from backend.schemas import UploadResponse, UploadURLRequest

router = APIRouter(tags=["Upload"])

ALLOWED = {".pdf", ".docx", ".txt", ".md", ".csv"}

@router.post("/upload", response_model=UploadResponse)
async def upload_file(request: Request, file: UploadFile = File(...)):
    pipeline = request.app.state.pipeline
    filename = file.filename or "unknown"
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED:
        raise HTTPException(status_code=400, detail=f"File type {ext} not supported")
    file_bytes = await file.read()
    if len(file_bytes) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Max 50MB")
    result = pipeline.index_file(file_bytes, filename)
    if not result["success"]:
        return UploadResponse(success=False, filename=filename, message="Failed", error=result.get("error"))
    return UploadResponse(success=True, filename=filename, message=f"Indexed {filename}", chunks=result.get("chunks", 0))

@router.post("/upload/url", response_model=UploadResponse)
async def upload_url(request: Request, body: UploadURLRequest):
    pipeline = request.app.state.pipeline
    url = body.url.strip()
    if not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="Invalid URL")
    result = pipeline.index_url(url)
    if not result["success"]:
        return UploadResponse(success=False, filename=url, message="Failed", error=result.get("error"))
    return UploadResponse(success=True, filename=url, message=f"Indexed {url}", chunks=result.get("chunks", 0))
