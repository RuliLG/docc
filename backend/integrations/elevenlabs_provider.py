import os
from elevenlabs import generate
from backend.integrations.tts_provider import TTSProvider


class ElevenLabsProvider(TTSProvider):
    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.default_voice = "Rachel"  # ElevenLabs default voice

    async def generate_speech(self, text: str) -> bytes:
        if not self.is_available():
            raise RuntimeError("ElevenLabs API key not available")

        try:
            # Generate speech using ElevenLabs with default voice
            audio = generate(
                api_key=self.api_key,
                text=text,
                voice=self.default_voice,
                model="eleven_flash_v2_5",
            )
            
            # Convert to bytes if it's a generator
            if hasattr(audio, '__iter__') and not isinstance(audio, (bytes, bytearray)):
                audio_bytes = b''.join(audio)
                return audio_bytes
            
            return audio
        except Exception as e:
            raise RuntimeError(f"ElevenLabs TTS failed: {str(e)}")

    def is_available(self) -> bool:
        return self.api_key is not None

