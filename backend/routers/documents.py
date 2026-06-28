from fastapi import APIRouter, Request

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

@router.get("/stats")
async def get_stats(request: Request):
    pipeline = request.app.state.pipeline
    return pipeline.get_stats()
