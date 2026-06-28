import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.pipeline.rag_pipeline import RAGPipeline
from backend.routers import upload, chat, documents

pipeline = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global pipeline
    print("Starting RAG pipeline...")
    pipeline = RAGPipeline(
     llm_model=os.getenv("LLM_MODEL", "llama3-8b-8192"),
)
    app.state.pipeline = pipeline
    print("Pipeline ready!")
    yield
    print("Shutting down...")

app = FastAPI(title="DocMind AI API", version="2.0.0", lifespan=lifespan)

app.add_middleware(CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"])

app.include_router(upload.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(documents.router, prefix="/api")

@app.get("/api/health")
async def health():
    global pipeline
    stats = pipeline.get_stats() if pipeline else {}
    return {"status": "ok", "stats": stats}

@app.get("/")
async def root():
    return {"message": "DocMind AI API", "docs": "/docs"}
