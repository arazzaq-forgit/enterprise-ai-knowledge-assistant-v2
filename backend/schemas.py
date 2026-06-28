from pydantic import BaseModel
from typing import List, Optional, Any

class UploadURLRequest(BaseModel):
    url: str

class UploadResponse(BaseModel):
    success: bool
    filename: str
    message: str
    chunks: Optional[int] = None
    error: Optional[str] = None

class ChatMessage(BaseModel):
    question: str
    answer: str

class ChatRequest(BaseModel):
    question: str
    chat_history: Optional[List[ChatMessage]] = []
    stream: bool = True

class SourceChunk(BaseModel):
    content: str
    source: str
    page: Optional[Any] = None
    similarity: Optional[float] = None

class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceChunk] = []

class SummarizeRequest(BaseModel):
    filename: str
