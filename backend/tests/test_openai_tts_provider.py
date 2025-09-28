from unittest.mock import MagicMock, Mock, patch

import pytest

from backend.integrations.openai_tts_provider import OpenAITTSProvider


class TestOpenAITTSProvider:
    @pytest.fixture
    def provider_with_key(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test_openai_key"}):
            provider = OpenAITTSProvider()
            return provider

    @pytest.fixture
    def provider_without_key(self):
        with patch.dict("os.environ", {}, clear=True):
            provider = OpenAITTSProvider()
            return provider

    def test_init_with_api_key(self, provider_with_key):
        assert provider_with_key.api_key == "test_openai_key"
        assert provider_with_key.default_voice == "alloy"
        assert provider_with_key.default_model == "tts-1"

    def test_init_with_custom_env_vars(self):
        with patch.dict(
            "os.environ",
            {
                "OPENAI_API_KEY": "custom_key",
                "OPENAI_VOICE": "nova",
                "OPENAI_TTS_MODEL": "tts-1-hd",
            },
        ):
            provider = OpenAITTSProvider()
            assert provider.api_key == "custom_key"
            assert provider.default_voice == "nova"
            assert provider.default_model == "tts-1-hd"

    def test_init_without_api_key(self, provider_without_key):
        assert provider_without_key.api_key is None

    def test_is_available_with_key(self, provider_with_key):
        assert provider_with_key.is_available() is True

    def test_is_available_without_key(self, provider_without_key):
        assert provider_without_key.is_available() is False

    @pytest.mark.asyncio
    async def test_generate_speech_success(self, provider_with_key):
        mock_response = Mock()
        mock_response.content = b"mock_audio_data"

        with patch(
            "openai.audio.speech.create", return_value=mock_response
        ) as mock_create:
            result = await provider_with_key.generate_speech("Test text")

            assert result == b"mock_audio_data"
            mock_create.assert_called_once_with(
                model="tts-1", voice="alloy", input="Test text"
            )

    @pytest.mark.asyncio
    async def test_generate_speech_not_available(self, provider_without_key):
        with pytest.raises(RuntimeError, match="OpenAI API key not available"):
            await provider_without_key.generate_speech("Test text")

    @pytest.mark.asyncio
    async def test_generate_speech_api_error(self, provider_with_key):
        with patch("openai.audio.speech.create", side_effect=Exception("API Error")):
            with pytest.raises(RuntimeError, match="OpenAI TTS failed: API Error"):
                await provider_with_key.generate_speech("Test text")

    @pytest.mark.asyncio
    async def test_generate_speech_empty_text(self, provider_with_key):
        mock_response = Mock()
        mock_response.content = b""

        with patch("openai.audio.speech.create", return_value=mock_response):
            result = await provider_with_key.generate_speech("")

            assert result == b""

    @pytest.mark.asyncio
    async def test_generate_speech_with_custom_voice_and_model(self):
        with patch.dict(
            "os.environ",
            {
                "OPENAI_API_KEY": "test_key",
                "OPENAI_VOICE": "shimmer",
                "OPENAI_TTS_MODEL": "tts-1-hd",
            },
        ):
            provider = OpenAITTSProvider()
            mock_response = Mock()
            mock_response.content = b"audio_data"

            with patch(
                "openai.audio.speech.create", return_value=mock_response
            ) as mock_create:
                result = await provider.generate_speech("Test text")

                assert result == b"audio_data"
                mock_create.assert_called_once_with(
                    model="tts-1-hd", voice="shimmer", input="Test text"
                )

    @pytest.mark.asyncio
    async def test_generate_speech_long_text(self, provider_with_key):
        long_text = "This is a long text. " * 100
        mock_response = Mock()
        mock_response.content = b"long_audio_data"

        with patch(
            "openai.audio.speech.create", return_value=mock_response
        ) as mock_create:
            result = await provider_with_key.generate_speech(long_text)

            assert result == b"long_audio_data"
            mock_create.assert_called_once_with(
                model="tts-1", voice="alloy", input=long_text
            )

    @pytest.mark.asyncio
    async def test_api_key_set_in_openai_module(self, provider_with_key):
        with patch("openai.api_key", None):
            assert provider_with_key.api_key == "test_openai_key"
