import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
from backend.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_script_generator():
    mock = Mock()
    mock.generate = AsyncMock()
    return mock


@pytest.fixture
def mock_tts_manager():
    mock = Mock()
    mock.generate_or_get_cached_audio = AsyncMock()
    mock.get_supported_voices = Mock()
    mock.get_cache_size = Mock()
    mock.clear_cache = Mock()
    mock.cache_dir = Mock()
    mock.provider = Mock()
    return mock


def test_health_check(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_generate_script_success(client, mock_script_generator):
    from backend.models.script import TextBlock, CodeBlock, LineRange

    # Mock successful script generation
    mock_blocks = [
        TextBlock(markdown="## Test\nThis is a test"),
        CodeBlock(
            file="/test/file.py",
            relevant_lines=[LineRange(line=10)],
            markdown="Test code explanation",
        ),
    ]
    mock_script_generator.generate.return_value = mock_blocks

    with patch("backend.api.routes.get_script_generator", return_value=mock_script_generator):
        response = client.post(
            "/api/v1/generate-script",
            json={"repository_path": "/test/repo", "question": "How does it work?"},
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data["script"]) == 2
    assert data["script"][0]["type"] == "text"
    assert data["script"][1]["type"] == "code"


def test_generate_script_failure(client, mock_script_generator):
    mock_script_generator.generate.side_effect = Exception("AI provider failed")

    with patch("backend.api.routes.get_script_generator", return_value=mock_script_generator):
        response = client.post(
            "/api/v1/generate-script",
            json={"repository_path": "/test/repo", "question": "How does it work?"},
        )

    assert response.status_code == 500
    assert "AI provider failed" in response.json()["detail"]


@pytest.mark.asyncio
async def test_generate_audio_success(client, mock_tts_manager):
    mock_tts_manager.generate_or_get_cached_audio.return_value = b"mock_audio_data"

    with patch("backend.api.routes.get_tts_manager", return_value=mock_tts_manager):
        response = client.post(
            "/api/v1/generate-audio",
            json={"text": "Hello, world!", "voice": "test_voice"},
        )

    assert response.status_code == 200
    data = response.json()
    assert "audio_url" in data
    assert data["audio_url"].startswith("/api/v1/audio/")
    assert "cache_hit" in data


def test_generate_audio_failure(client, mock_tts_manager):
    mock_tts_manager.generate_or_get_cached_audio.side_effect = Exception("TTS failed")

    with patch("backend.api.routes.get_tts_manager", return_value=mock_tts_manager):
        response = client.post(
            "/api/v1/generate-audio",
            json={"text": "Hello, world!", "voice": "test_voice"},
        )

    assert response.status_code == 500
    assert "TTS failed" in response.json()["detail"]


def test_get_voices(client, mock_tts_manager):
    mock_tts_manager.get_supported_voices.return_value = ["voice1", "voice2", "voice3"]
    mock_tts_manager.provider.__class__.__name__ = "MockProvider"

    with patch("backend.api.routes.get_tts_manager", return_value=mock_tts_manager):
        response = client.get("/api/v1/voices")

    assert response.status_code == 200
    data = response.json()
    assert data["voices"] == ["voice1", "voice2", "voice3"]
    assert data["provider"] == "MockProvider"


def test_get_cache_stats(client, mock_tts_manager):
    mock_tts_manager.get_cache_size.return_value = 1024 * 1024  # 1MB
    mock_tts_manager.cache_dir.glob.return_value = ["file1.mp3", "file2.mp3"]

    with patch("backend.api.routes.get_tts_manager", return_value=mock_tts_manager):
        response = client.get("/api/v1/cache/stats")

    assert response.status_code == 200
    data = response.json()
    assert data["cache_size_bytes"] == 1024 * 1024
    assert data["cache_size_mb"] == 1.0
    assert data["cached_files_count"] == 2


def test_clear_cache(client, mock_tts_manager):
    with patch("backend.api.routes.get_tts_manager", return_value=mock_tts_manager):
        response = client.delete("/api/v1/cache")

    assert response.status_code == 200
    assert response.json()["message"] == "Cache cleared successfully"
    mock_tts_manager.clear_cache.assert_called_once()


def test_get_audio_not_found(client):
    response = client.get("/api/v1/audio/nonexistent-id")
    assert response.status_code == 404
    assert response.json()["detail"] == "Audio file not found"


def test_get_audio_success(client, mock_tts_manager):
    # First, create an audio file by calling generate-audio
    mock_tts_manager.generate_or_get_cached_audio.return_value = b"test_audio_data"

    with patch("backend.api.routes.get_tts_manager", return_value=mock_tts_manager):
        # Generate audio to get an ID
        response = client.post("/api/v1/generate-audio", json={"text": "test"})

        audio_url = response.json()["audio_url"]
        audio_id = audio_url.split("/")[-1]

        # Now get the audio file
        response = client.get(f"/api/v1/audio/{audio_id}")

        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/mpeg"
