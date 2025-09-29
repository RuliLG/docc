import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router
from backend.core.config import get_settings
from backend.models.errors import RootResponse

API_VERSION = "1.0.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    settings = get_settings()
    logger = logging.getLogger(__name__)

    # Startup
    logger.info(f"Starting {settings.app_name}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"CORS origins: {settings.cors_origins}")

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
        description="""
This API analyzes code repositories and generates comprehensive documentation
scripts with audio narration. Perfect for creating automated video explanations
of codebases.

## Features

* **AI-Powered Analysis**: Uses Claude Code or OpenCode to understand repositories
* **Structured Scripts**: Generates text and code blocks for storytelling
* **Audio Generation**: Creates narration using ElevenLabs or OpenAI TTS
* **File Content API**: Safely retrieves code with line highlighting
* **Cache Management**: Efficient audio caching with automatic cleanup

## Getting Started

1. Ensure you have AI providers configured (Claude Code/OpenCode)
2. Configure TTS providers (ElevenLabs/OpenAI) for audio generation
3. Use `/generate-script` to analyze repositories and create documentation

## Provider Configuration

Check `/available-providers` to see which providers are currently configured
and available for use.
        """,
        version=API_VERSION,
        debug=settings.debug,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router, prefix="/api/v1")

    @app.get(
        "/",
        response_model=RootResponse,
        summary="API Information",
        description="Get basic information about the API including version and available providers",
        tags=["info"],
    )
    async def root():
        """
        Root endpoint with API information.

        Returns basic API metadata including the application name, version,
        current status, and information about available AI and TTS providers.
        """
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
