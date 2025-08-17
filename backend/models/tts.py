from typing import Optional
from pydantic import BaseModel


class TTSRequest(BaseModel):
    text: str


class TTSResponse(BaseModel):
    audio_url: str
    cache_hit: bool


class CacheStatsResponse(BaseModel):
    cache_size_bytes: int
    cache_size_mb: float
    cached_files_count: int
