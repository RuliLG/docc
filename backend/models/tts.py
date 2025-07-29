from typing import Optional, List
from pydantic import BaseModel


class TTSRequest(BaseModel):
    text: str
    voice: Optional[str] = None


class TTSResponse(BaseModel):
    audio_url: str
    cache_hit: bool


class VoicesResponse(BaseModel):
    voices: List[str]
    provider: str


class CacheStatsResponse(BaseModel):
    cache_size_bytes: int
    cache_size_mb: float
    cached_files_count: int
