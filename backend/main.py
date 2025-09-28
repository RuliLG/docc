import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router
from backend.core.config import get_settings

API_VERSION = "1.0.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    settings = get_settings()
    logger = logging.getLogger(__name__)

    # Startup
    logger.info(f"Starting {settings.app_name}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"CORS origins: {settings.docc_cors_origins}")

    # Create cache directory
    settings.get_cache_path().mkdir(exist_ok=True)
    logger.info(f"Audio cache directory: {settings.get_cache_path()}")

    # Check provider availability
    providers = settings.get_available_providers()
    logger.info(f"Available providers: {providers}")

    if not settings.has_ai_provider() and not settings.has_tts_provider():
        logger.warning("No AI or TTS providers configured. Some features may not work.")

    yield

    # Shutdown
    logger.info(f"Shutting down {settings.app_name}")


def create_app():
    """Create and configure the FastAPI application."""
    settings = get_settings()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(settings.log_file), logging.StreamHandler()],
    )

    app = FastAPI(
        title=settings.app_name,
        description="AI-powered repository documentation tool API",
        version=API_VERSION,
        debug=settings.debug,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.docc_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router, prefix="/api/v1")

    @app.get("/")
    async def root():
        """Root endpoint with API information."""
        return {
            "name": settings.app_name,
            "version": API_VERSION,
            "status": "running",
            "providers": settings.get_available_providers(),
        }

    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=app.extra.get("settings", get_settings()).api_host,
        port=app.extra.get("settings", get_settings()).api_port,
        log_level=get_settings().log_level.lower(),
    )
