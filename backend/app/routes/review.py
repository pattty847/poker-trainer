from typing import Dict
from fastapi import APIRouter


router = APIRouter()


@router.get("/api/review/hand")
def review_hand(sessionId: str):
    # Minimal stub for hand review payload
    return {
        "handId": sessionId,
        "timeline": [],
        "alternateLines": [],
    }


