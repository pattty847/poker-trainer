from typing import Dict
from fastapi import APIRouter
from ..domain.game_manager import game_manager


router = APIRouter()

_sessions: Dict[str, Dict] = {}


@router.post("/api/game/new")
def new_game(payload: Dict):
    # TODO: Add variable new game options
    return game_manager.new_game(
        small_blind=float(payload.get("smallBlind", 0.5)),
        big_blind=float(payload.get("bigBlind", 1.0)),
        stack=float(payload.get("stack", 100)),
        seed=int(payload.get("seed", 42)),
        num_players=int(payload.get("numPlayers", 2)),
    )


@router.post("/api/game/action")
def apply_action(payload: Dict):
    return game_manager.apply_action(
        session_id=payload["sessionId"],
        action=payload["action"],
        size=payload.get("size"),
    )


@router.get("/api/game/state")
def get_state(sessionId: str):
    return game_manager.get_state(sessionId)


@router.post("/api/game/reset")
def reset_game(payload: Dict):
    return game_manager.reset_game(session_id=payload["sessionId"], seed=payload.get("seed"))

