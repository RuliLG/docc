from unittest.mock import MagicMock, Mock, patch

import pytest

from backend.integrations.elevenlabs_provider import ElevenLabsProvider


class TestElevenLabsProvider:
    @pytest.fixture
    def provider_with_key(self):
        mock_elevenlabs_class = Mock()
        mock_client = MagicMock()
        mock_elevenlabs_class.return_value = mock_client

        with patch(
            "backend.integrations.elevenlabs_provider.ELEVENLABS_AVAILABLE", True
        ), patch.dict(
            "backend.integrations.elevenlabs_provider.__dict__",
            {"ElevenLabs": mock_elevenlabs_class},
        ), patch.dict(
            "os.environ", {"ELEVENLABS_API_KEY": "test_key"}
        ):
            provider = ElevenLabsProvider()
            yield provider

    @pytest.fixture
    def provider_without_key(self):
        mock_elevenlabs_class = Mock()
        mock_client = MagicMock()
        mock_elevenlabs_class.return_value = mock_client

        with patch.dict("os.environ", {}, clear=True), patch(
            "backend.integrations.elevenlabs_provider.ELEVENLABS_AVAILABLE", True
        ), patch.dict(
            "backend.integrations.elevenlabs_provider.__dict__",
            {"ElevenLabs": mock_elevenlabs_class},
        ):
            provider = ElevenLabsProvider()
            yield provider

    @pytest.fixture
    def provider_without_library(self):
        with patch.dict("os.environ", {"ELEVENLABS_API_KEY": "test_key"}), patch(
            "backend.integrations.elevenlabs_provider.ELEVENLABS_AVAILABLE", False
        ):
            provider = ElevenLabsProvider()
            yield provider

    def test_init_with_api_key(self, provider_with_key):
        assert provider_with_key.api_key == "test_key"
        assert provider_with_key.default_voice == "Rachel"
        assert provider_with_key.default_model == "eleven_turbo_v2_5"
        assert provider_with_key.client is not None

    def test_init_with_custom_env_vars(self):
        mock_elevenlabs_class = Mock()
        mock_client = MagicMock()
        mock_elevenlabs_class.return_value = mock_client

        with patch(
            "backend.integrations.elevenlabs_provider.ELEVENLABS_AVAILABLE", True
        ), patch.dict(
            "backend.integrations.elevenlabs_provider.__dict__",
            {"ElevenLabs": mock_elevenlabs_class},
        ), patch.dict(
            "os.environ",
            {
                "ELEVENLABS_API_KEY": "custom_key",
                "ELEVENLABS_VOICE": "CustomVoice",
                "ELEVENLABS_MODEL": "custom_model",
            },
        ):
            provider = ElevenLabsProvider()
            assert provider.api_key == "custom_key"
            assert provider.default_voice == "CustomVoice"
            assert provider.default_model == "custom_model"

    def test_init_without_api_key(self, provider_without_key):
        assert provider_without_key.api_key is None

    def test_is_available_with_key_and_library(self, provider_with_key):
        assert provider_with_key.is_available() is True

    def test_is_available_without_key(self, provider_without_key):
        assert provider_without_key.is_available() is False

    def test_is_available_without_library(self, provider_without_library):
        assert provider_without_library.is_available() is False

    @pytest.mark.asyncio
    async def test_generate_speech_success(self, provider_with_key):
        mock_audio_chunks = [b"audio", b"chunk", b"data"]
        provider_with_key.client.text_to_speech.convert = Mock(
            return_value=iter(mock_audio_chunks)
        )

        result = await provider_with_key.generate_speech("Test text")

        assert result == b"audiochunkdata"
        provider_with_key.client.text_to_speech.convert.assert_called_once_with(
            text="Test text", voice_id="Rachel", model_id="eleven_turbo_v2_5"
        )

    @pytest.mark.asyncio
    async def test_generate_speech_not_available(self, provider_without_key):
        with pytest.raises(
            RuntimeError,
            match="ElevenLabs API key not available or library not installed",
        ):
            await provider_without_key.generate_speech("Test text")

    @pytest.mark.asyncio
    async def test_generate_speech_api_error(self, provider_with_key):
        provider_with_key.client.text_to_speech.convert = Mock(
            side_effect=Exception("API Error")
        )

        with pytest.raises(RuntimeError, match="ElevenLabs TTS failed: API Error"):
            await provider_with_key.generate_speech("Test text")

    @pytest.mark.asyncio
    async def test_generate_speech_empty_text(self, provider_with_key):
        mock_audio_chunks = [b""]
        provider_with_key.client.text_to_speech.convert = Mock(
            return_value=iter(mock_audio_chunks)
        )

        result = await provider_with_key.generate_speech("")

        assert result == b""
        provider_with_key.client.text_to_speech.convert.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_speech_with_custom_voice_and_model(self):
        mock_elevenlabs_class = Mock()
        mock_client = MagicMock()
        mock_elevenlabs_class.return_value = mock_client
        mock_client.text_to_speech.convert = Mock(return_value=iter([b"audio"]))

        with patch(
            "backend.integrations.elevenlabs_provider.ELEVENLABS_AVAILABLE", True
        ), patch.dict(
            "backend.integrations.elevenlabs_provider.__dict__",
            {"ElevenLabs": mock_elevenlabs_class},
        ), patch.dict(
            "os.environ",
            {
                "ELEVENLABS_API_KEY": "test_key",
                "ELEVENLABS_VOICE": "Nicole",
                "ELEVENLABS_MODEL": "eleven_multilingual_v2",
            },
        ):
            provider = ElevenLabsProvider()
            result = await provider.generate_speech("Test text")

            assert result == b"audio"
            mock_client.text_to_speech.convert.assert_called_once_with(
                text="Test text",
                voice_id="Nicole",
                model_id="eleven_multilingual_v2",
            )
