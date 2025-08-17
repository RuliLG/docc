import os
import openai
from backend.integrations.tts_provider import TTSProvider


class OpenAITTSProvider(TTSProvider):
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.default_voice = "alloy"
        if self.api_key:
            openai.api_key = self.api_key

    async def generate_speech(self, text: str) -> bytes:
        if not self.is_available():
            raise RuntimeError("OpenAI API key not available")

        try:
            # Generate speech using OpenAI TTS with default voice
            response = openai.audio.speech.create(
                model="tts-1", voice=self.default_voice, input=text
            )

            return response.content
        except Exception as e:
            raise RuntimeError(f"OpenAI TTS failed: {str(e)}")

    def is_available(self) -> bool:
        return self.api_key is not None

