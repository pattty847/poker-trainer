from typing import AsyncIterator, Dict


async def sse_event_stream(source: AsyncIterator[Dict[str, str]]):
    """Wrap an async iterator of {id, data} dicts into SSE wire format."""
    # Initial open event for some clients
    yield "event: open\n\n"
    async for evt in source:
        evt_id = evt.get("id", "")
        data = evt.get("data", "")
        if evt_id:
            yield f"id: {evt_id}\n"
        yield f"data: {data}\n\n"


