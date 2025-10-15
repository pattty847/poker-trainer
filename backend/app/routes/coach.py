import asyncio
import json
from uuid import uuid4
from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

from ..core.sse import sse_event_stream


router = APIRouter()


@router.post("/api/coach/ask")
async def coach_ask(payload: dict, request: Request):
    question = payload.get("question", "")

    async def gen():
        # In a shared channel design, we would multiplex types; here we emit coach_suggestion
        preface = "Consider position and pot odds. "
        for token in (preface + question).split(" "):
            if await request.is_disconnected():
                break
            await asyncio.sleep(0.03)
            yield {"id": uuid4().hex, "data": json.dumps({"type": "coach_suggestion", "content": token + " "})}
        yield {"id": "z", "data": json.dumps({"type": "end", "content": ""})}

    if request.headers.get("accept", "").startswith("text/event-stream"):
        return EventSourceResponse(sse_event_stream(gen()))

    # Non-SSE simple response
    return {"suggestion": "Consider position and pot odds."}


