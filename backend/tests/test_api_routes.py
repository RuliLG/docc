from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

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
    from backend.models.script import CodeBlock, LineRange, TextBlock

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

    with patch(
        "backend.api.routes.get_script_generator", return_value=mock_script_generator
    ):
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

    with patch(
        "backend.api.routes.get_script_generator", return_value=mock_script_generator
    ):
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
            "/api/v1/generate-audio", json={"text": "Hello, world!"},
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
            "/api/v1/generate-audio", json={"text": "Hello, world!"},
        )

    assert response.status_code == 500
    assert "TTS failed" in response.json()["detail"]


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


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "status" in data
    assert data["status"] == "running"
    assert "providers" in data


def test_available_providers(client):
    with patch("backend.api.routes.ClaudeProvider") as mock_claude:
        with patch("backend.api.routes.OpenCodeProvider") as mock_opencode:
            with patch("backend.api.routes.ElevenLabsProvider") as mock_elevenlabs:
                with patch("backend.api.routes.OpenAITTSProvider") as mock_openai:
                    mock_claude.return_value.is_available.return_value = True
                    mock_opencode.return_value.is_available.return_value = False
                    mock_elevenlabs.return_value.is_available.return_value = True
                    mock_openai.return_value.is_available.return_value = False

                    response = client.get("/api/v1/available-providers")

                    assert response.status_code == 200
                    data = response.json()
                    assert "ai_providers" in data
                    assert "tts_providers" in data
                    assert len(data["ai_providers"]) == 1
                    assert data["ai_providers"][0]["id"] == "claude_code"
                    assert len(data["tts_providers"]) == 1
                    assert data["tts_providers"][0]["id"] == "elevenlabs"


def test_available_providers_none_available(client):
    with patch("backend.api.routes.ClaudeProvider") as mock_claude:
        with patch("backend.api.routes.OpenCodeProvider") as mock_opencode:
            with patch("backend.api.routes.ElevenLabsProvider") as mock_elevenlabs:
                with patch("backend.api.routes.OpenAITTSProvider") as mock_openai:
                    mock_claude.return_value.is_available.return_value = False
                    mock_opencode.return_value.is_available.return_value = False
                    mock_elevenlabs.return_value.is_available.return_value = False
                    mock_openai.return_value.is_available.return_value = False

                    response = client.get("/api/v1/available-providers")

                    assert response.status_code == 200
                    data = response.json()
                    assert len(data["ai_providers"]) == 0
                    assert len(data["tts_providers"]) == 0


def test_file_content_success(client, temp_file_for_test):
    response = client.get(f"/api/v1/file-content?file_path={temp_file_for_test}")

    assert response.status_code == 200
    data = response.json()
    assert "content" in data
    assert "total_lines" in data
    assert "def hello()" in data["content"]
    assert data["total_lines"] == 3


def test_file_content_with_line_range(client, temp_file_for_test):
    response = client.get(
        f"/api/v1/file-content?file_path={temp_file_for_test}&from_line=1&to_line=2"
    )

    assert response.status_code == 200
    data = response.json()
    assert "def hello()" in data["content"]
    assert "return 42" not in data["content"]
    assert data["from_line"] == 1
    assert data["to_line"] == 2


def test_file_content_not_absolute_path(client):
    response = client.get("/api/v1/file-content?file_path=relative/path.py")

    assert response.status_code == 400
    assert "must be absolute" in response.json()["detail"]


def test_file_content_not_found(client):
    response = client.get("/api/v1/file-content?file_path=/nonexistent/file.py")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_file_content_is_directory(client, tmp_path):
    response = client.get(f"/api/v1/file-content?file_path={tmp_path}")

    assert response.status_code == 400
    assert "not a file" in response.json()["detail"]


def test_generate_script_with_tts_provider_none(client, mock_script_generator):
    from backend.models.script import TextBlock

    mock_blocks = [TextBlock(markdown="Test")]
    mock_script_generator.generate.return_value = mock_blocks

    with patch(
        "backend.api.routes.get_script_generator", return_value=mock_script_generator
    ):
        with patch("backend.api.routes.TTSManager") as mock_tts_class:
            mock_tts = Mock()
            mock_tts.provider = None
            mock_tts_class.return_value = mock_tts

            response = client.post(
                "/api/v1/generate-script",
                json={
                    "repository_path": "/test/repo",
                    "question": "Test?",
                    "tts_provider": None,
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["audio_files"] is None


def test_generate_script_with_empty_audio(client, mock_script_generator):
    from backend.models.script import TextBlock

    mock_blocks = [TextBlock(markdown="Test")]
    mock_script_generator.generate.return_value = mock_blocks

    with patch(
        "backend.api.routes.get_script_generator", return_value=mock_script_generator
    ):
        with patch("backend.api.routes.TTSManager") as mock_tts_class:
            mock_tts = Mock()
            mock_tts.provider = Mock()
            mock_tts.generate_or_get_cached_audio = AsyncMock(return_value=b"")
            mock_tts_class.return_value = mock_tts

            response = client.post(
                "/api/v1/generate-script",
                json={"repository_path": "/test/repo", "question": "Test?"},
            )

            assert response.status_code == 500
            assert "Failed to generate audio" in response.json()["detail"]
