from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from backend.schemas import ChatRequest, ChatResponse, SourceChunk, SummarizeRequest
import json

router = APIRouter(tags=["Chat"])

def make_token_event(token):
    data = json.dumps({"token": token})
    return f"data: {data}\n\n"

def make_done_event():
    data = json.dumps({"done": True})
    return f"data: {data}\n\n"

def make_error_event(error):
    data = json.dumps({"error": str(error)})
    return f"data: {data}\n\n"

@router.post("/chat")
async def chat(request: Request, body: ChatRequest):
    """Stream AI response via Server-Sent Events."""
    pipeline = request.app.state.pipeline
    history = [
        {"question": m.question, "answer": m.answer}
        for m in (body.chat_history or [])
    ]

    async def generate():
        try:
            for chunk in pipeline.ask(
                question=body.question,
                chat_history=history,
                stream=True
            ):
                yield make_token_event(chunk)
            yield make_done_event()
        except Exception as e:
            yield make_error_event(e)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        }
    )

@router.post("/chat/evaluate")
async def chat_with_evaluation(request: Request, body: ChatRequest):
    """Ask a question and get answer with confidence + hallucination scores."""
    pipeline = request.app.state.pipeline
    history = [
        {"question": m.question, "answer": m.answer}
        for m in (body.chat_history or [])
    ]
    result = pipeline.ask_with_evaluation(
        question=body.question,
        chat_history=history
    )
    return result

@router.post("/chat/sources")
async def get_sources(request: Request, body: ChatRequest):
    """Get source chunks for a question."""
    pipeline = request.app.state.pipeline
    sources_raw = pipeline.get_sources(body.question)
    sources = [
        SourceChunk(
            content=s.get("content", ""),
            source=s.get("metadata", {}).get("source", "Unknown"),
            page=s.get("metadata", {}).get("page_number"),
            similarity=s.get("similarity"),
        )
        for s in sources_raw
    ]
    return {"sources": sources, "count": len(sources)}

@router.post("/summarize")
async def summarize(request: Request, body: SummarizeRequest):
    """Summarize a document via streaming."""
    pipeline = request.app.state.pipeline

    async def generate():
        try:
            for chunk in pipeline.summarize(body.filename):
                yield make_token_event(chunk)
            yield make_done_event()
        except Exception as e:
            yield make_error_event(e)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        }
    )
