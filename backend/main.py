import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import router
from backend.core.config import get_settings

def create_app():
    """Create and configure the FastAPI application."""
    settings = get_settings()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(settings.log_file), logging.StreamHandler()],
    )
    
    logger = logging.getLogger(__name__)
    
    app = FastAPI(
        title=settings.app_name,
        description="AI-powered repository documentation tool API",
        version="1.0.0",
        debug=settings.debug,
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.docc_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.include_router(router, prefix="/api/v1")
    
    @app.on_event("startup")
    async def startup_event():
        """Application startup event."""
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
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Application shutdown event."""
        logger.info(f"Shutting down {settings.app_name}")
    
    @app.get("/")
    async def root():
        """Root endpoint with API information."""
        return {
            "name": settings.app_name,
            "version": "1.0.0",
            "status": "running",
            "providers": settings.get_available_providers(),
        }
    
    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower(),
    )
