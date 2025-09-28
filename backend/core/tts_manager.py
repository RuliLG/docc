import hashlib
import logging
from pathlib import Path
from typing import Optional

from backend.core.config import get_settings
from backend.integrations.elevenlabs_provider import ElevenLabsProvider
from backend.integrations.openai_tts_provider import OpenAITTSProvider
from backend.integrations.tts_provider import TTSProvider

logger = logging.getLogger(__name__)


class TTSManager:
    def __init__(
        self, cache_dir: Optional[str] = None, preferred_provider: Optional[str] = None
    ):
        settings = get_settings()

        self.providers = [ElevenLabsProvider(), OpenAITTSProvider()]
        self.preferred_provider = preferred_provider

        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = settings.get_cache_path()

        self.cache_dir.mkdir(exist_ok=True)
        self.max_cache_size_mb = settings.audio_cache_max_size_mb
        self.provider = self._get_available_provider()

        logger.info(f"TTS Manager initialized with cache dir: {self.cache_dir}")
        if self.provider:
            logger.info(f"Using TTS provider: {type(self.provider).__name__}")
        else:
            logger.warning("No TTS providers available")

    def _get_available_provider(self) -> Optional[TTSProvider]:
        """Get the first available TTS provider based on preference."""
        # If a preferred provider is specified, try to use it first
        if self.preferred_provider:
            provider_map = {
                "elevenlabs": ElevenLabsProvider,
                "openai": OpenAITTSProvider,
            }

            if self.preferred_provider in provider_map:
                for provider in self.providers:
                    if (
                        isinstance(provider, provider_map[self.preferred_provider])
                        and provider.is_available()
                    ):
                        logger.info(
                            f"Using preferred TTS provider: {self.preferred_provider}"
                        )
                        return provider
                logger.warning(
                    f"Preferred provider {self.preferred_provider} not available, trying all"
                )

        # Fall back to first available provider
        for provider in self.providers:
            if provider.is_available():
                return provider
        return None

    def _get_cache_filename(self, text: str) -> str:
        """Generate a cache filename based on text."""
        hash_obj = hashlib.md5(text.encode())
        return f"{hash_obj.hexdigest()}.mp3"

    def _get_cache_path(self, filename: str) -> Path:
        """Get the full cache file path."""
        return self.cache_dir / filename

    async def generate_or_get_cached_audio(self, text: str) -> bytes:
        """Generate audio or return cached version if available."""
        if not self.provider:
            raise RuntimeError(
                "No TTS providers available. Please set ELEVENLABS_API_KEY or OPENAI_API_KEY environment variable."
            )

        # Check cache first
        cache_filename = self._get_cache_filename(text)
        cache_path = self._get_cache_path(cache_filename)

        if cache_path.exists():
            with open(cache_path, "rb") as f:
                return f.read()

        # Generate new audio
        audio_bytes = await self.provider.generate_speech(text)

        # Cache the audio
        with open(cache_path, "wb") as f:
            f.write(audio_bytes)

        return audio_bytes

    def clear_cache(self) -> None:
        """Clear all cached audio files."""
        for file_path in self.cache_dir.glob("*.mp3"):
            file_path.unlink()

    def get_cache_size(self) -> int:
        """Get total size of cached audio files in bytes."""
        total_size = 0
        for file_path in self.cache_dir.glob("*.mp3"):
            total_size += file_path.stat().st_size
        return total_size
