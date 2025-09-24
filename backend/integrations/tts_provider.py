from abc import ABC, abstractmethod


class TTSProvider(ABC):
    @abstractmethod
    async def generate_speech(self, text: str) -> bytes:
        """Generate speech audio from text and return audio bytes."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the TTS provider is available and configured."""
        pass
