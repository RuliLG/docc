from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from backend.models.script import ScriptRequest, ScriptResponse
from backend.models.tts import (
    TTSRequest,
    TTSResponse,
    VoicesResponse,
    CacheStatsResponse,
)
from backend.core.script_generator import ScriptGenerator
from backend.core.tts_manager import TTSManager
import io
import uuid
import os
from pathlib import Path

router = APIRouter()

# Store audio files temporarily for serving
temp_audio_files = {}

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


@router.post("/generate-script", response_model=ScriptResponse)
async def generate_script(request: ScriptRequest):
    try:
        script_generator = get_script_generator()
        script = await script_generator.generate(
            repository_path=request.repository_path, question=request.question
        )
        
        # Pre-generate audio for all script blocks
        tts_manager = get_tts_manager()
        audio_urls = []
        
        # Check if TTS is available
        if not tts_manager.provider:
            print("WARNING: No TTS provider available, skipping audio generation")
            return ScriptResponse(script=script, audio_files=None)
        
        for i, block in enumerate(script):
            # Generate audio for the markdown content
            print(f"Generating audio for block {i}: {block.markdown[:50]}...")
            audio_bytes = await tts_manager.generate_or_get_cached_audio(
                text=block.markdown, voice=None  # Use default voice
            )
            
            # Validate audio data
            if not audio_bytes or len(audio_bytes) == 0:
                print(f"WARNING: Empty audio generated for block {i}")
                raise HTTPException(status_code=500, detail=f"Failed to generate audio for block {i}")
            
            # Generate unique ID for this audio
            audio_id = str(uuid.uuid4())
            temp_audio_files[audio_id] = audio_bytes
            print(f"Generated audio {audio_id}, size: {len(audio_bytes)} bytes")
            
            # Add the audio URL to the list
            audio_urls.append(f"/api/v1/audio/{audio_id}")
        
        return ScriptResponse(script=script, audio_files=audio_urls)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-audio", response_model=TTSResponse)
async def generate_audio(request: TTSRequest):
    try:
        tts_manager = get_tts_manager()
        audio_bytes = await tts_manager.generate_or_get_cached_audio(
            text=request.text, voice=request.voice
        )

        # Generate unique ID for this audio
        audio_id = str(uuid.uuid4())
        temp_audio_files[audio_id] = audio_bytes

        return TTSResponse(
            audio_url=f"/api/v1/audio/{audio_id}",
            cache_hit=False,  # TODO: Implement cache hit detection
        )
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audio/{audio_id}")
async def get_audio(audio_id: str):
    if audio_id not in temp_audio_files:
        raise HTTPException(status_code=404, detail="Audio file not found")

    audio_bytes = temp_audio_files[audio_id]
    
    # Debug logging
    print(f"Serving audio {audio_id}, size: {len(audio_bytes)} bytes")

    return StreamingResponse(
        io.BytesIO(audio_bytes),
        media_type="audio/mpeg",
        headers={"Content-Disposition": "inline; filename=audio.mp3"},
    )


@router.get("/voices", response_model=VoicesResponse)
async def get_voices():
    tts_manager = get_tts_manager()
    voices = tts_manager.get_supported_voices()
    provider_name = (
        type(tts_manager.provider).__name__ if tts_manager.provider else "None"
    )

    return VoicesResponse(voices=voices, provider=provider_name)


@router.get("/cache/stats", response_model=CacheStatsResponse)
async def get_cache_stats():
    tts_manager = get_tts_manager()
    cache_size = tts_manager.get_cache_size()
    cache_files_count = len(list(tts_manager.cache_dir.glob("*.mp3")))

    return CacheStatsResponse(
        cache_size_bytes=cache_size,
        cache_size_mb=cache_size / (1024 * 1024),
        cached_files_count=cache_files_count,
    )


@router.delete("/cache")
async def clear_cache():
    tts_manager = get_tts_manager()
    tts_manager.clear_cache()
    return {"message": "Cache cleared successfully"}


@router.get("/health")
async def health_check():
    return {"status": "healthy"}


@router.get("/file-content")
async def get_file_content(file_path: str, from_line: int = None, to_line: int = None):
    """Get content of a file with optional line range filtering."""
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
            with open(path, 'r', encoding='utf-8') as f:
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
            "content": ''.join(filtered_lines),
            "total_lines": len(lines),
            "from_line": from_line,
            "to_line": to_line
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
