from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings

logger = logging.getLogger(__name__)
from .routes.analytics import router as analytics_router
from .routes.auth import router as auth_router
from .routes.emotions import router as emotions_router
from .routes.feed import router as feed_router
from .routes.i18n import router as i18n_router
from .routes.reflection import router as reflection_router
from .routes.profile import router as profile_router
from .routes.feedback_ws import router as feedback_ws_router

# Import LiminalDB storage if enabled
if settings.liminaldb_enabled:
    from .liminaldb.storage import get_storage


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    if settings.liminaldb_enabled:
        # Initialize LiminalDB storage
        storage = await get_storage()
        app.state.storage = storage
        logger.info("LiminalDB storage initialized at %s", settings.liminaldb_url)

    yield

    # Shutdown
    if settings.liminaldb_enabled and hasattr(app.state, "storage"):
        await app.state.storage.close()
        logger.info("LiminalDB storage closed")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Liminal-You API",
        version="0.2.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins if settings.cors_origins else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(analytics_router, prefix="/api", tags=["analytics"])
    app.include_router(auth_router, prefix="/api", tags=["auth"])
    app.include_router(emotions_router, prefix="/api", tags=["emotions"])
    app.include_router(feed_router, prefix="/api", tags=["feed"])
    app.include_router(i18n_router, prefix="/api", tags=["i18n"])
    app.include_router(reflection_router, prefix="/api", tags=["reflections"])
    app.include_router(profile_router, prefix="/api", tags=["profiles"])
    app.include_router(feedback_ws_router, tags=["feedback"])

    return app


app = create_app()
