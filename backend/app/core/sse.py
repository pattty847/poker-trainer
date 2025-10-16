from typing import AsyncIterator, Dict


async def sse_event_stream(source: AsyncIterator[Dict[str, str]]):
    """Deprecated helper; prefer returning EventSourceResponse(source) directly."""
    async for evt in source:
        yield evt


