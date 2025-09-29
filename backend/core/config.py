from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from pydantic import field_validator
from pydantic_settings import BaseSettings

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    # Application settings
    app_name: str = "Docc - AI Documentation Tool"
    debug: bool = False
    development: bool = True

    # Server settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # CORS settings
    cors_origins: Optional[List[str]] = None

    # Security
    secret_key: str = "default-secret-key-change-in-production"

    # TTS Provider settings
    elevenlabs_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None

    # Audio cache settings
    audio_cache_dir: str = "audio_cache"
    audio_cache_max_size_mb: int = 500

    # Logging settings
    log_level: str = "INFO"
    log_file: str = "docc.log"

    # Frontend settings
    react_app_api_base_url: str = "http://localhost:8000/api/v1"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if v is None or v == "":
            return ["http://localhost:3000", "http://127.0.0.1:3000"]
        if isinstance(v, str) and v.strip():
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, str) and not v.strip():
            # Empty string, use default
            return ["http://localhost:3000", "http://127.0.0.1:3000"]
        elif isinstance(v, list):
            return v if v else ["http://localhost:3000", "http://127.0.0.1:3000"]
        return ["http://localhost:3000", "http://127.0.0.1:3000"]

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed_levels:
            raise ValueError(f"log_level must be one of {allowed_levels}")
        return v.upper()

    @field_validator("audio_cache_max_size_mb")
    @classmethod
    def validate_cache_size(cls, v):
        if v < 10:
            raise ValueError("audio_cache_max_size_mb must be at least 10MB")
        if v > 10000:
            raise ValueError("audio_cache_max_size_mb must be less than 10GB")
        return v

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "validate_default": True,
        "env_ignore_empty": True,  # Ignore empty environment variables
    }

    def get_cache_path(self) -> Path:
        """Get the cache directory path as a Path object."""
        return Path(self.audio_cache_dir)

    def has_ai_provider(self) -> bool:
        """Check if at least one AI provider is configured."""
        # Import here to avoid circular imports
        from backend.integrations.claude_provider import ClaudeProvider
        from backend.integrations.opencode_provider import OpenCodeProvider

        claude = ClaudeProvider()
        opencode = OpenCodeProvider()
        return claude.is_available() or opencode.is_available()

    def has_tts_provider(self) -> bool:
        """Check if at least one TTS provider is configured."""
        from backend.integrations.elevenlabs_provider import ElevenLabsProvider
        from backend.integrations.openai_tts_provider import OpenAITTSProvider

        elevenlabs = ElevenLabsProvider()
        openai = OpenAITTSProvider()
        return elevenlabs.is_available() or openai.is_available()

    def get_available_providers(self) -> dict:
        """Get information about available providers."""
        # Import here to avoid circular imports
        from backend.integrations.claude_provider import ClaudeProvider
        from backend.integrations.opencode_provider import OpenCodeProvider
        from backend.integrations.elevenlabs_provider import ElevenLabsProvider
        from backend.integrations.openai_tts_provider import OpenAITTSProvider

        claude = ClaudeProvider()
        opencode = OpenCodeProvider()
        elevenlabs = ElevenLabsProvider()
        openai = OpenAITTSProvider()

        return {
            "ai_providers": {
                "claude": claude.is_available(),
                "opencode": opencode.is_available(),
            },
            "tts_providers": {
                "elevenlabs": elevenlabs.is_available(),
                "openai": openai.is_available(),
            },
        }


# Global settings instance (lazy initialization)
_settings = None


def get_settings() -> Settings:
    """Get application settings."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
