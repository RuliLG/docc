import os
import openai
from backend.integrations.tts_provider import TTSProvider


class OpenAITTSProvider(TTSProvider):
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.default_voice = os.getenv("OPENAI_VOICE", "alloy")
        self.default_model = os.getenv("OPENAI_TTS_MODEL", "tts-1")
        if self.api_key:
            openai.api_key = self.api_key

    async def generate_speech(self, text: str) -> bytes:
        if not self.is_available():
            raise RuntimeError("OpenAI API key not available")

        try:
            response = openai.audio.speech.create(
                model=self.default_model, voice=self.default_voice, input=text
            )

            return response.content
        except Exception as e:
            raise RuntimeError(f"OpenAI TTS failed: {str(e)}")

    def is_available(self) -> bool:
        return self.api_key is not None
