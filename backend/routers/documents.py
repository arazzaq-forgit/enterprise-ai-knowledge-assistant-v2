from fastapi import APIRouter, Request, HTTPException

router = APIRouter(tags=["Documents"])

@router.get("/documents")
async def get_documents(request: Request):
    pipeline = request.app.state.pipeline
    stats = pipeline.get_stats()
    return {"documents": stats.get("document_names", []), "total_chunks": stats.get("total_chunks", 0), "total_docs": stats.get("loaded_documents", 0)}

@router.delete("/documents")
async def clear_documents(request: Request):
    pipeline = request.app.state.pipeline
    pipeline.vector_store.clear()
    return {"success": True, "message": "Knowledge base cleared"}

@router.delete("/documents/{filename:path}")
async def delete_document(filename: str, request: Request):
    """
    Delete a single document (and all its chunks) from the knowledge base.
    filename must match exactly what /api/documents lists (the 'source'
    it was uploaded/indexed under). Using :path so URL-sourced documents
    (which may contain '/') work too, not just local filenames.
    """
    pipeline = request.app.state.pipeline
    result = pipeline.delete_document(filename)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=f"Document '{filename}' not found")
    return result

@router.get("/stats")
async def get_stats(request: Request):
    pipeline = request.app.state.pipeline
    return pipeline.get_stats()