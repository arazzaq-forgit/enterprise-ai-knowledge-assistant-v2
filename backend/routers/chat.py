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

def make_eval_event(sources, confidence, hallucination_check):
    data = json.dumps({
        "eval": True,
        "sources": sources,
        "confidence": confidence,
        "hallucination_check": hallucination_check,
    })
    return f"data: {data}\n\n"

def make_error_event(error):
    data = json.dumps({"error": str(error)})
    return f"data: {data}\n\n"

@router.post("/chat")
async def chat(request: Request, body: ChatRequest):
    """
    Stream AI response via Server-Sent Events.

    Single LLM call: tokens stream as they're generated, then one final
    "eval" event carries confidence + hallucination scores (computed from
    the already-retrieved chunks and the now-complete answer — no second
    LLM round-trip, no separate /chat/evaluate call needed from the client).
    """
    pipeline = request.app.state.pipeline
    history = [
        {"question": m.question, "answer": m.answer}
        for m in (body.chat_history or [])
    ]

    async def generate():
        try:
            for event in pipeline.ask_stream_with_evaluation(
                question=body.question,
                chat_history=history,
            ):
                if event["type"] == "token":
                    yield make_token_event(event["token"])
                elif event["type"] == "eval":
                    yield make_eval_event(
                        event["sources"],
                        event["confidence"],
                        event["hallucination_check"],
                    )
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
    """
    Non-streaming: ask a question and get the answer with confidence +
    hallucination scores in one blocking response. Kept for callers that
    want a single non-streaming call (e.g. Phase 3 batch evaluation script).
    Not used by the main chat UI anymore — that uses the single-call
    streaming /chat endpoint above instead.
    """
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