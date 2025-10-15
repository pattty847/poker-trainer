from __future__ import annotations

import uuid
from typing import Dict, Optional

from .poker_adapter import PokerAdapter


class GameManager:
    def __init__(self) -> None:
        self.sessions: Dict[str, PokerAdapter] = {}

    def new_game(self, *, small_blind: float, big_blind: float, stack: float, seed: int) -> Dict:
        session_id = str(uuid.uuid4())
        adapter = PokerAdapter(small_blind=small_blind, big_blind=big_blind, stack=stack, seed=seed)
        self.sessions[session_id] = adapter
        return {"sessionId": session_id, "state": adapter.get_state(session_id)}

    def apply_action(self, session_id: str, action: str, size: Optional[float]) -> Dict:
        adapter = self.sessions.get(session_id)
        if not adapter:
            return {"error": "SESSION_NOT_FOUND"}
        adapter.apply_hero_action(action, size)
        return {"state": adapter.get_state(session_id), "aiActionApplied": True}

    def get_state(self, session_id: str) -> Dict:
        adapter = self.sessions.get(session_id)
        if not adapter:
            return {"error": "SESSION_NOT_FOUND"}
        return {"state": adapter.get_state(session_id)}


game_manager = GameManager()


