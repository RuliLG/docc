from typing import List, Optional, Union
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standard error response format."""
    
    detail: str = Field(
        description="Error message describing what went wrong"
    )


class ValidationErrorResponse(BaseModel):
    """Validation error response format."""
    
    detail: list = Field(
        description="List of validation errors"
    )


class ProviderInfo(BaseModel):
    """Information about an available provider."""
    
    id: str = Field(
        description="Provider identifier"
    )
    name: str = Field(
        description="Human-readable provider name"
    )


class ProvidersResponse(BaseModel):
    """Response containing available AI and TTS providers."""
    
    ai_providers: List[ProviderInfo] = Field(
        description="List of available AI providers for code analysis"
    )
    tts_providers: List[ProviderInfo] = Field(
        description="List of available text-to-speech providers"
    )


class FileContentResponse(BaseModel):
    """Response containing file content with optional line filtering."""
    
    file_path: str = Field(
        description="Absolute path to the file"
    )
    content: str = Field(
        description="File content (filtered by line range if specified)"
    )
    total_lines: int = Field(
        description="Total number of lines in the file",
        ge=0
    )
    from_line: Optional[int] = Field(
        None,
        description="Starting line number for filtered content (1-based)"
    )
    to_line: Optional[int] = Field(
        None,
        description="Ending line number for filtered content (1-based)"
    )


class HealthResponse(BaseModel):
    """Health check response."""
    
    status: str = Field(
        description="API health status"
    )


class RootResponse(BaseModel):
    """Root endpoint response with API information."""
    
    name: str = Field(
        description="Application name"
    )
    version: str = Field(
        description="API version"
    )
    status: str = Field(
        description="Application status"
    )
    providers: dict = Field(
        description="Available providers information"
    )


class ClearCacheResponse(BaseModel):
    """Response after clearing cache."""
    
    message: str = Field(
        description="Success message"
    )