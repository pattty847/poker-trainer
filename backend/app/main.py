from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import game, reason, review, coach, range, health


def create_app() -> FastAPI:
    app = FastAPI(title="Poker Trainer MVP", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    for router in [game.router, reason.router, review.router, coach.router, range.router, health.router]:
        app.include_router(router)

    return app


app = create_app()


