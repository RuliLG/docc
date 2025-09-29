import io
import logging
import time
import uuid
from collections import OrderedDict
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from backend.api import system_check
from backend.core.config import get_settings
from backend.core.script_generator import ScriptGenerator
from backend.core.tts_manager import TTSManager
from backend.integrations.claude_provider import ClaudeProvider
from backend.integrations.elevenlabs_provider import ElevenLabsProvider
from backend.integrations.openai_tts_provider import OpenAITTSProvider
from backend.integrations.opencode_provider import OpenCodeProvider
from backend.models.script import ScriptRequest, ScriptResponse
from backend.models.tts import CacheStatsResponse, TTSRequest, TTSResponse
# Define response models inline for documentation
from typing import Dict, List, Optional, Any
from models.errors import (
    ProvidersResponse,
    SystemCheckResponse,
    QuickSystemCheckResponse,
    HealthResponse,
    ClearCacheResponse,
    FileContentResponse,
)

router = APIRouter()
logger = logging.getLogger(__name__)

# Include system check routes
router.include_router(system_check.router, tags=["system"])

# Store audio files temporarily with TTL (time-to-live)
# Using OrderedDict for LRU-like behavior
temp_audio_files = OrderedDict()
AUDIO_FILE_TTL = 3600  # 1 hour in seconds
MAX_AUDIO_FILES = 100  # Maximum number of cached audio files

# Lazy initialization of services
_script_generator = None
_tts_manager = None


def get_script_generator():
    global _script_generator
    if _script_generator is None:
        _script_generator = ScriptGenerator()
    return _script_generator


def get_tts_manager():
    global _tts_manager
    if _tts_manager is None:
        _tts_manager = TTSManager()
    return _tts_manager


def _cleanup_old_audio_files():
    """Remove expired audio files and enforce max cache size."""
    current_time = time.time()

    # Remove expired files
    expired_keys = [
        audio_id
        for audio_id, entry in temp_audio_files.items()
        if current_time - entry["timestamp"] > AUDIO_FILE_TTL
    ]
    for key in expired_keys:
        del temp_audio_files[key]
        logger.debug(f"Removed expired audio file: {key}")

    # Enforce max cache size (LRU: remove oldest)
    while len(temp_audio_files) > MAX_AUDIO_FILES:
        oldest_key = next(iter(temp_audio_files))
        del temp_audio_files[oldest_key]
        logger.debug(f"Removed oldest audio file to maintain cache limit: {oldest_key}")


@router.post(
    "/generate-script",
    response_model=ScriptResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate documentation script",
    description="Analyzes a repository and generates a structured script explaining the codebase with audio files",
    responses={
        200: {"description": "Script generated successfully with audio files"},
        400: {"description": "Invalid request parameters (repository path, question, etc.)"},
        404: {"description": "Repository not found or inaccessible"},
        500: {"description": "Internal server error (AI provider unavailable, TTS generation failed, etc.)"},
    }
)
async def generate_script(request: ScriptRequest):
    """
    Generate a comprehensive documentation script for a repository.
    
    This endpoint analyzes the provided repository using AI providers (Claude Code or OpenCode)
    to answer the user's question about the codebase. It returns a structured script with
    text and code blocks, along with pre-generated audio files for narration.
    
    The script follows a storytelling format that can be used to create automated video
    explanations of the codebase.
    """
    try:
        script_generator = get_script_generator()
        script = await script_generator.generate(
            repository_path=request.repository_path,
            question=request.question,
            ai_provider=request.ai_provider,
        )

        # Pre-generate audio for all script blocks
        # Create a new TTSManager with the preferred provider
        tts_manager = TTSManager(preferred_provider=request.tts_provider)
        audio_urls = []

        # Check if TTS is available
        if not tts_manager.provider:
            logger.warning("No TTS provider available, skipping audio generation")
            return ScriptResponse(script=script, audio_files=None)

        for i, block in enumerate(script):
            # Generate audio for the markdown content
            logger.info(f"Generating audio for block {i}: {block.markdown[:50]}...")
            audio_bytes = await tts_manager.generate_or_get_cached_audio(
                text=block.markdown
            )

            # Validate audio data
            if not audio_bytes or len(audio_bytes) == 0:
                logger.warning(f"Empty audio generated for block {i}")
                raise HTTPException(
                    status_code=500, detail=f"Failed to generate audio for block {i}"
                )

            # Generate unique ID for this audio
            audio_id = str(uuid.uuid4())
            _cleanup_old_audio_files()
            temp_audio_files[audio_id] = {"data": audio_bytes, "timestamp": time.time()}
            logger.info(f"Generated audio {audio_id}, size: {len(audio_bytes)} bytes")

            # Add the audio URL to the list
            audio_urls.append(f"/api/v1/audio/{audio_id}")

        return ScriptResponse(script=script, audio_files=audio_urls)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/generate-audio",
    response_model=TTSResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate audio from text",
    description="Converts text to speech using available TTS providers (ElevenLabs or OpenAI)",
    responses={
        200: {"description": "Audio generated successfully"},
        400: {"description": "Invalid text input (empty, too long, etc.)"},
        500: {"description": "TTS provider unavailable or generation failed"},
    }
)
async def generate_audio(request: TTSRequest):
    """
    Generate audio file from text input.
    
    Converts the provided text to speech using the configured TTS provider.
    The audio is cached temporarily and can be accessed via the returned URL.
    """
    try:
        tts_manager = get_tts_manager()
        audio_bytes = await tts_manager.generate_or_get_cached_audio(text=request.text)

        # Generate unique ID for this audio
        audio_id = str(uuid.uuid4())
        _cleanup_old_audio_files()
        temp_audio_files[audio_id] = {"data": audio_bytes, "timestamp": time.time()}

        return TTSResponse(
            audio_url=f"/api/v1/audio/{audio_id}",
            cache_hit=False,  # TODO: Implement cache hit detection
        )
    except Exception as e:
        logger.error(f"Error generating audio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/audio/{audio_id}",
    status_code=status.HTTP_200_OK,
    summary="Stream audio file",
    description="Retrieves and streams a temporarily cached audio file",
    responses={
        200: {"description": "Audio file streamed successfully", "content": {"audio/mpeg": {}}},
        404: {"description": "Audio file not found or expired"},
    }
)
async def get_audio(audio_id: str):
    """
    Stream a cached audio file.
    
    Retrieves a temporarily stored audio file by its UUID. Audio files are automatically
    cleaned up after 1 hour or when the cache exceeds the maximum size limit.
    """
    if audio_id not in temp_audio_files:
        raise HTTPException(status_code=404, detail="Audio file not found")

    audio_entry = temp_audio_files[audio_id]
    audio_bytes = audio_entry["data"]

    # Debug logging
    logger.debug(f"Serving audio {audio_id}, size: {len(audio_bytes)} bytes")

    return StreamingResponse(
        io.BytesIO(audio_bytes),
        media_type="audio/mpeg",
        headers={"Content-Disposition": "inline; filename=audio.mp3"},
    )


@router.get(
    "/cache/stats",
    response_model=CacheStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get cache statistics",
    description="Returns information about the current state of the audio cache",
    responses={
        200: {"description": "Cache statistics retrieved successfully"},
    }
)
async def get_cache_stats():
    """
    Get audio cache statistics.
    
    Returns detailed information about the audio cache including size, 
    number of cached files, and storage usage.
    """
    tts_manager = get_tts_manager()
    cache_size = tts_manager.get_cache_size()
    cache_files_count = len(list(tts_manager.cache_dir.glob("*.mp3")))

    return CacheStatsResponse(
        cache_size_bytes=cache_size,
        cache_size_mb=cache_size / (1024 * 1024),
        cached_files_count=cache_files_count,
    )


@router.delete(
    "/cache",
    response_model=ClearCacheResponse,
    status_code=status.HTTP_200_OK,
    summary="Clear audio cache",
    description="Removes all cached audio files to free up storage space",
    responses={
        200: {"description": "Cache cleared successfully"},
    }
)
async def clear_cache():
    """
    Clear all cached audio files.
    
    Removes all audio files from the cache directory to free up storage space.
    This operation cannot be undone.
    """
    tts_manager = get_tts_manager()
    tts_manager.clear_cache()
    return {"message": "Cache cleared successfully"}


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Simple health check endpoint to verify API is running",
    responses={
        200: {"description": "API is healthy and running"},
    }
)
async def health_check():
    """
    Health check endpoint.
    
    Returns a simple status message indicating the API is running and responsive.
    """
    return {"status": "healthy"}


@router.get(
    "/available-providers",
    response_model=ProvidersResponse,
    status_code=status.HTTP_200_OK,
    summary="Get available providers",
    description="Returns list of currently available and configured AI and TTS providers",
    responses={
        200: {"description": "Provider list retrieved successfully"},
    }
)
async def get_available_providers():
    """
    Get list of available AI and TTS providers.
    Returns which providers are currently configured and available.
    """
    # Check AI providers
    ai_providers = []
    claude_provider = ClaudeProvider()
    opencode_provider = OpenCodeProvider()

    if claude_provider.is_available():
        ai_providers.append({"id": "claude_code", "name": "Claude Code"})
    if opencode_provider.is_available():
        ai_providers.append({"id": "opencode", "name": "OpenCode"})

    # Check TTS providers
    tts_providers = []
    elevenlabs_provider = ElevenLabsProvider()
    openai_provider = OpenAITTSProvider()

    if elevenlabs_provider.is_available():
        tts_providers.append({"id": "elevenlabs", "name": "ElevenLabs"})
    if openai_provider.is_available():
        tts_providers.append({"id": "openai", "name": "OpenAI TTS"})

    return {"ai_providers": ai_providers, "tts_providers": tts_providers}


@router.get(
    "/file-content",
    response_model=FileContentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get file content",
    description="Retrieves content of a file with optional line range filtering for code display",
    responses={
        200: {"description": "File content retrieved successfully"},
        400: {"description": "Invalid file path or line range"},
        404: {"description": "File not found"},
        500: {"description": "Error reading file"},
    }
)
async def get_file_content(
    file_path: str = Query(..., description="Absolute path to the file to read"),
    from_line: int = Query(None, description="Starting line number (1-based)", ge=1),
    to_line: int = Query(None, description="Ending line number (1-based)", ge=1)
):
    """
    Get file content with optional line filtering.
    
    Safely reads a file's content with optional line range filtering. This is used
    by the frontend to display code blocks with highlighted sections. Includes
    security checks to prevent unauthorized file access.
    """
    try:
        # Security check - ensure the path is absolute and exists
        path = Path(file_path)
        if not path.is_absolute():
            raise HTTPException(status_code=400, detail="File path must be absolute")

        if not path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        if not path.is_file():
            raise HTTPException(status_code=400, detail="Path is not a file")

        # Read the file
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")

        # Apply line range filtering if specified
        if from_line is not None and to_line is not None:
            # Convert to 0-based indexing
            start = max(0, from_line - 1)
            end = min(len(lines), to_line)
            filtered_lines = lines[start:end]
        else:
            filtered_lines = lines

        return {
            "file_path": str(path),
            "content": "".join(filtered_lines),
            "total_lines": len(lines),
            "from_line": from_line,
            "to_line": to_line,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
