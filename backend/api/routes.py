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
        return ScriptResponse(script=script)
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
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audio/{audio_id}")
async def get_audio(audio_id: str):
    if audio_id not in temp_audio_files:
        raise HTTPException(status_code=404, detail="Audio file not found")

    audio_bytes = temp_audio_files[audio_id]

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
