from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes.feed import router as feed_router
from .routes.reflection import router as reflection_router
from .routes.resonance import router as resonance_router
from .routes.profile import router as profile_router


def create_app() -> FastAPI:
    app = FastAPI(title="Liminal-You API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(feed_router, prefix="/api", tags=["feed"])
    app.include_router(reflection_router, prefix="/api", tags=["reflections"])
    app.include_router(profile_router, prefix="/api", tags=["profiles"])
    app.include_router(resonance_router, tags=["resonance"])

    return app


app = create_app()
