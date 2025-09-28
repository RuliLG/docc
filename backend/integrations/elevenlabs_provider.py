import os

from backend.integrations.tts_provider import TTSProvider

try:
    from elevenlabs import ElevenLabs

    ELEVENLABS_AVAILABLE = True
except:
    ELEVENLABS_AVAILABLE = False


class ElevenLabsProvider(TTSProvider):
    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.default_voice = os.getenv("ELEVENLABS_VOICE", "Rachel")
        self.default_model = os.getenv("ELEVENLABS_MODEL", "eleven_turbo_v2_5")
        self.client = ElevenLabs(api_key=self.api_key) if ELEVENLABS_AVAILABLE else None

    async def generate_speech(self, text: str) -> bytes:
        if not self.is_available():
            raise RuntimeError(
                "ElevenLabs API key not available or library not installed"
            )

        try:
            audio_generator = self.client.text_to_speech.convert(
                text=text, voice_id=self.default_voice, model_id=self.default_model
            )

            audio_bytes = b"".join(chunk for chunk in audio_generator)
            return audio_bytes
        except Exception as e:
            raise RuntimeError(f"ElevenLabs TTS failed: {str(e)}")

    def is_available(self) -> bool:
        return self.api_key is not None and self.client is not None
