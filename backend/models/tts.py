from pydantic import BaseModel, Field


class TTSRequest(BaseModel):
    """Request to generate audio from text."""
    
    text: str = Field(
        description="Text content to convert to speech",
        min_length=1,
        max_length=5000
    )


class TTSResponse(BaseModel):
    """Response containing audio URL and cache information."""
    
    audio_url: str = Field(
        description="URL to access the generated audio file"
    )
    cache_hit: bool = Field(
        description="Whether the audio was served from cache"
    )


class CacheStatsResponse(BaseModel):
    """Statistics about the audio cache."""
    
    cache_size_bytes: int = Field(
        description="Total cache size in bytes",
        ge=0
    )
    cache_size_mb: float = Field(
        description="Total cache size in megabytes",
        ge=0
    )
    cached_files_count: int = Field(
        description="Number of files currently cached",
        ge=0
    )
