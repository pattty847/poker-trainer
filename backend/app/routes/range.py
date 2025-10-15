from typing import Literal
from fastapi import APIRouter


router = APIRouter()


@router.get("/api/range/estimate")
def estimate_range(sessionId: str, perspective: Literal["hero", "villain"]):
    # Simple uniform grid placeholder
    val = 1.0 / 169.0
    grid = [[val for _ in range(13)] for _ in range(13)]
    return {"grid": grid}


