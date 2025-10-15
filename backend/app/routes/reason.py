import asyncio
import json
from uuid import uuid4
from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

from ..core.sse import sse_event_stream


router = APIRouter()


@router.get("/api/reason/stream")
async def reason_stream(sessionId: str, archetype: str, request: Request):
    async def gen():
        # Emit initial skill tag (mocked intermediate)
        yield {"id": "0", "data": json.dumps({"type": "tag", "content": "intermediate"})}
        # Mock streamed tokens
        text = "On this flop, range advantage favors the preflop raiser. We can c-bet small."
        for token in text.split(" "):
            if await request.is_disconnected():
                break
            await asyncio.sleep(0.03)
            yield {"id": uuid4().hex, "data": json.dumps({"type": "token", "content": token + " "})}
        yield {"id": "z", "data": json.dumps({"type": "end", "content": ""})}

    async def with_heartbeat():
        # Simple heartbeat every 10s emitting empty token to keep connection alive
        async for evt in gen():
            yield evt
        # Note: in real impl we'd push periodic heartbeats while stream is open

    return EventSourceResponse(sse_event_stream(with_heartbeat()))


