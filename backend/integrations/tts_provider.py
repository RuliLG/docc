from abc import ABC, abstractmethod
from typing import Optional


class TTSProvider(ABC):
    @abstractmethod
    async def generate_speech(self, text: str, voice: Optional[str] = None) -> bytes:
        """Generate speech audio from text and return audio bytes."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the TTS provider is available and configured."""
        pass

    @abstractmethod
    def get_supported_voices(self) -> list[str]:
        """Get list of supported voice names."""
        pass
