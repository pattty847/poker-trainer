from typing import AsyncIterator, Protocol


class ReasoningEngine(Protocol):
    async def stream(self, game_state: dict, archetype: str) -> AsyncIterator[str]:
        ...


