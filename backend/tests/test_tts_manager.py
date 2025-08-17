import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock
from backend.core.tts_manager import TTSManager
from backend.integrations.tts_provider import TTSProvider


class MockTTSProvider(TTSProvider):
    def __init__(self, available=True):
        self._available = available

    async def generate_speech(self, text: str) -> bytes:
        return f"mock_audio_for_{text}".encode()

    def is_available(self) -> bool:
        return self._available


@pytest.fixture
def temp_cache_dir():
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def tts_manager_with_mock_provider(temp_cache_dir):
    manager = TTSManager(cache_dir=temp_cache_dir)
    manager.providers = [MockTTSProvider()]
    manager.provider = manager._get_available_provider()
    return manager


@pytest.mark.asyncio
async def test_generate_or_get_cached_audio_new_file(tts_manager_with_mock_provider):
    text = "Hello, world!"

    audio_bytes = await tts_manager_with_mock_provider.generate_or_get_cached_audio(
        text
    )

    assert audio_bytes == b"mock_audio_for_Hello, world!"

    # Check that file was cached
    cache_filename = tts_manager_with_mock_provider._get_cache_filename(text)
    cache_path = tts_manager_with_mock_provider._get_cache_path(cache_filename)
    assert cache_path.exists()


@pytest.mark.asyncio
async def test_generate_or_get_cached_audio_from_cache(tts_manager_with_mock_provider):
    text = "Cached text"

    # Generate first time
    await tts_manager_with_mock_provider.generate_or_get_cached_audio(text)

    # Mock the provider to return different data
    tts_manager_with_mock_provider.provider.generate_speech = AsyncMock(
        return_value=b"should_not_be_called"
    )

    # Get from cache
    audio_bytes = await tts_manager_with_mock_provider.generate_or_get_cached_audio(
        text
    )

    # Should return cached data, not new generation
    assert audio_bytes == b"mock_audio_for_Cached text"
    tts_manager_with_mock_provider.provider.generate_speech.assert_not_called()


@pytest.mark.asyncio
async def test_generate_or_get_cached_audio_no_provider():
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = TTSManager(cache_dir=temp_dir)
        manager.providers = [MockTTSProvider(available=False)]
        manager.provider = manager._get_available_provider()

        with pytest.raises(RuntimeError, match="No TTS providers available"):
            await manager.generate_or_get_cached_audio("test")


def test_clear_cache(tts_manager_with_mock_provider):
    # Create some mock cache files
    cache_dir = Path(tts_manager_with_mock_provider.cache_dir)
    (cache_dir / "file1.mp3").write_bytes(b"audio1")
    (cache_dir / "file2.mp3").write_bytes(b"audio2")

    assert len(list(cache_dir.glob("*.mp3"))) == 2

    tts_manager_with_mock_provider.clear_cache()

    assert len(list(cache_dir.glob("*.mp3"))) == 0


def test_get_cache_size(tts_manager_with_mock_provider):
    # Create some mock cache files
    cache_dir = Path(tts_manager_with_mock_provider.cache_dir)
    (cache_dir / "file1.mp3").write_bytes(b"audio1_12345")  # 11 bytes
    (cache_dir / "file2.mp3").write_bytes(b"audio2_678")  # 10 bytes

    cache_size = tts_manager_with_mock_provider.get_cache_size()
    assert cache_size == 21


def test_cache_filename_generation(tts_manager_with_mock_provider):
    filename1 = tts_manager_with_mock_provider._get_cache_filename("Hello")
    filename2 = tts_manager_with_mock_provider._get_cache_filename("World")
    filename3 = tts_manager_with_mock_provider._get_cache_filename("Hello")

    # Different text should create different filename
    assert filename1 != filename2

    # Same text should create same filename
    assert filename1 == filename3

    # Should end with .mp3
    assert filename1.endswith(".mp3")
