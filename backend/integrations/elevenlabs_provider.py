import os
from typing import Optional
from elevenlabs import generate
from backend.integrations.tts_provider import TTSProvider


class ElevenLabsProvider(TTSProvider):
    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.default_voice = "Rachel"  # ElevenLabs default voice

    async def generate_speech(self, text: str, voice: Optional[str] = None) -> bytes:
        if not self.is_available():
            raise RuntimeError("ElevenLabs API key not available")

        try:
            voice_name = voice or self.default_voice

            # Generate speech using ElevenLabs
            audio = generate(
                text=text, voice=voice_name, model="eleven_monolingual_v1"
            )

            return audio
        except Exception as e:
            raise RuntimeError(f"ElevenLabs TTS failed: {str(e)}")

    def is_available(self) -> bool:
        return self.api_key is not None

    def get_supported_voices(self) -> list[str]:
        # Common ElevenLabs voices - in production, this could be fetched from their API
        return [
            "Rachel",
            "Drew",
            "Clyde",
            "Paul",
            "Domi",
            "Dave",
            "Fin",
            "Sarah",
            "Antoni",
            "Thomas",
            "Charlie",
            "Emily",
            "Elli",
            "Callum",
        ]
