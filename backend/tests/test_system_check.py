import subprocess
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestSystemCheckEndpoints:
    @pytest.mark.asyncio
    async def test_check_command_exists_success(self):
        from backend.api.system_check import check_command_exists

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)

            result = await check_command_exists("claude")

            assert result is True
            mock_run.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_command_exists_failure(self):
        from backend.api.system_check import check_command_exists

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=1)

            result = await check_command_exists("nonexistent")

            assert result is False

    @pytest.mark.asyncio
    async def test_check_command_exists_exception(self):
        from backend.api.system_check import check_command_exists

        with patch("subprocess.run", side_effect=Exception("Error")):
            result = await check_command_exists("claude")

            assert result is False

    @pytest.mark.asyncio
    async def test_check_claude_code_installed_and_configured(self):
        from backend.api.system_check import check_claude_code

        with patch("backend.api.system_check.check_command_exists", return_value=True):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock(
                    returncode=0, stdout="claude version 1.0.0"
                )

                result = await check_claude_code()

                assert result["installed"] is True
                assert result["configured"] is True
                assert result["version"] == "claude version 1.0.0"
                assert result["error"] is None

    @pytest.mark.asyncio
    async def test_check_claude_code_not_installed(self):
        from backend.api.system_check import check_claude_code

        with patch("backend.api.system_check.check_command_exists", return_value=False):
            result = await check_claude_code()

            assert result["installed"] is False
            assert result["configured"] is False
            assert result["error"] == "Claude Code not found in PATH"

    @pytest.mark.asyncio
    async def test_check_claude_code_version_error(self):
        from backend.api.system_check import check_claude_code

        with patch("backend.api.system_check.check_command_exists", return_value=True):
            with patch("subprocess.run", side_effect=Exception("Version check failed")):
                result = await check_claude_code()

                assert result["installed"] is True
                assert "Could not get Claude Code version" in result["error"]

    @pytest.mark.asyncio
    async def test_check_opencode_installed_and_configured(self):
        from backend.api.system_check import check_opencode

        with patch("backend.api.system_check.check_command_exists", return_value=True):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock(
                    returncode=0, stdout="opencode version 2.0.0"
                )

                result = await check_opencode()

                assert result["installed"] is True
                assert result["configured"] is True
                assert result["version"] == "opencode version 2.0.0"

    @pytest.mark.asyncio
    async def test_check_opencode_not_installed(self):
        from backend.api.system_check import check_opencode

        with patch("backend.api.system_check.check_command_exists", return_value=False):
            result = await check_opencode()

            assert result["installed"] is False
            assert result["error"] == "OpenCode not found in PATH"

    @pytest.mark.asyncio
    async def test_check_elevenlabs_configured_and_accessible(self):
        from backend.api.system_check import check_elevenlabs

        mock_response = Mock(status_code=200)

        with patch("backend.core.config.get_settings") as mock_settings:
            mock_settings.return_value.elevenlabs_api_key = "test_key"

            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                    return_value=mock_response
                )

                result = await check_elevenlabs()

                assert result["configured"] is True
                assert result["accessible"] is True
                assert result["api_key_set"] is True
                assert result["error"] is None

    @pytest.mark.asyncio
    async def test_check_elevenlabs_invalid_key(self):
        from backend.api.system_check import check_elevenlabs

        mock_response = Mock(status_code=401)

        with patch("backend.core.config.get_settings") as mock_settings:
            mock_settings.return_value.elevenlabs_api_key = "invalid_key"

            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                    return_value=mock_response
                )

                result = await check_elevenlabs()

                assert result["configured"] is True
                assert result["accessible"] is False
                assert result["error"] == "Invalid ElevenLabs API key"

    @pytest.mark.asyncio
    async def test_check_elevenlabs_not_configured(self):
        from backend.api.system_check import check_elevenlabs

        with patch("backend.api.system_check.get_settings") as mock_settings:
            mock_settings.return_value.elevenlabs_api_key = None

            result = await check_elevenlabs()

            assert result["configured"] is False
            assert result["error"] == "ElevenLabs API key not configured"

    @pytest.mark.asyncio
    async def test_check_elevenlabs_connection_error(self):
        import httpx

        from backend.api.system_check import check_elevenlabs

        with patch("backend.core.config.get_settings") as mock_settings:
            mock_settings.return_value.elevenlabs_api_key = "test_key"

            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                    side_effect=httpx.RequestError("Connection failed")
                )

                result = await check_elevenlabs()

                assert result["configured"] is True
                assert result["accessible"] is False
                assert "Could not connect to ElevenLabs API" in result["error"]

    @pytest.mark.asyncio
    async def test_check_openai_tts_configured_and_accessible(self):
        from backend.api.system_check import check_openai_tts

        mock_response = Mock(status_code=200)
        mock_response.json.return_value = {"data": [{"id": "tts-1"}]}

        with patch("backend.core.config.get_settings") as mock_settings:
            mock_settings.return_value.openai_api_key = "test_key"

            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                    return_value=mock_response
                )

                result = await check_openai_tts()

                assert result["configured"] is True
                assert result["accessible"] is True
                assert result["api_key_set"] is True

    @pytest.mark.asyncio
    async def test_check_openai_tts_invalid_key(self):
        from backend.api.system_check import check_openai_tts

        mock_response = Mock(status_code=401)

        with patch("backend.core.config.get_settings") as mock_settings:
            mock_settings.return_value.openai_api_key = "invalid_key"

            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                    return_value=mock_response
                )

                result = await check_openai_tts()

                assert result["configured"] is True
                assert result["accessible"] is False
                assert result["error"] == "Invalid OpenAI API key"

    @pytest.mark.asyncio
    async def test_check_openai_tts_not_configured(self):
        from backend.api.system_check import check_openai_tts

        with patch("backend.api.system_check.get_settings") as mock_settings:
            mock_settings.return_value.openai_api_key = None

            result = await check_openai_tts()

            assert result["configured"] is False
            assert result["error"] == "OpenAI API key not configured"

    def test_system_check_endpoint_all_services_available(self, client):
        with patch(
            "backend.api.system_check.check_claude_code", new_callable=AsyncMock
        ) as mock_claude:
            with patch(
                "backend.api.system_check.check_opencode", new_callable=AsyncMock
            ) as mock_opencode:
                with patch(
                    "backend.api.system_check.check_elevenlabs", new_callable=AsyncMock
                ) as mock_elevenlabs:
                    with patch(
                        "backend.api.system_check.check_openai_tts",
                        new_callable=AsyncMock,
                    ) as mock_openai:
                        mock_claude.return_value = {
                            "installed": True,
                            "configured": True,
                            "version": "1.0.0",
                            "error": None,
                        }
                        mock_opencode.return_value = {
                            "installed": False,
                            "configured": False,
                            "version": None,
                            "error": "Not installed",
                        }
                        mock_elevenlabs.return_value = {
                            "configured": True,
                            "accessible": True,
                            "api_key_set": True,
                            "error": None,
                        }
                        mock_openai.return_value = {
                            "configured": False,
                            "accessible": False,
                            "api_key_set": False,
                            "error": "Not configured",
                        }

                        response = client.get("/api/v1/system-check")

                        assert response.status_code == 200
                        data = response.json()

                        assert data["system_ready"] is True
                        assert data["requirements_met"]["ai_cli"] is True
                        assert data["requirements_met"]["tts_service"] is True
                        assert data["services"]["claude_code"]["installed"] is True
                        assert data["services"]["elevenlabs"]["accessible"] is True

    def test_system_check_endpoint_no_ai_cli(self, client):
        with patch(
            "backend.api.system_check.check_claude_code", new_callable=AsyncMock
        ) as mock_claude:
            with patch(
                "backend.api.system_check.check_opencode", new_callable=AsyncMock
            ) as mock_opencode:
                with patch(
                    "backend.api.system_check.check_elevenlabs", new_callable=AsyncMock
                ) as mock_elevenlabs:
                    with patch(
                        "backend.api.system_check.check_openai_tts",
                        new_callable=AsyncMock,
                    ) as mock_openai:
                        mock_claude.return_value = {
                            "installed": False,
                            "configured": False,
                            "version": None,
                            "error": "Not installed",
                        }
                        mock_opencode.return_value = {
                            "installed": False,
                            "configured": False,
                            "version": None,
                            "error": "Not installed",
                        }
                        mock_elevenlabs.return_value = {
                            "configured": True,
                            "accessible": True,
                            "api_key_set": True,
                            "error": None,
                        }
                        mock_openai.return_value = {
                            "configured": False,
                            "accessible": False,
                            "api_key_set": False,
                            "error": "Not configured",
                        }

                        response = client.get("/api/v1/system-check")

                        assert response.status_code == 200
                        data = response.json()

                        assert data["system_ready"] is False
                        assert data["requirements_met"]["ai_cli"] is False
                        assert data["requirements_met"]["tts_service"] is True
                        assert len(data["recommendations"]) > 0
                        assert any(
                            "Claude Code" in rec or "OpenCode" in rec
                            for rec in data["recommendations"]
                        )

    def test_system_check_endpoint_no_tts(self, client):
        with patch(
            "backend.api.system_check.check_claude_code", new_callable=AsyncMock
        ) as mock_claude:
            with patch(
                "backend.api.system_check.check_opencode", new_callable=AsyncMock
            ) as mock_opencode:
                with patch(
                    "backend.api.system_check.check_elevenlabs", new_callable=AsyncMock
                ) as mock_elevenlabs:
                    with patch(
                        "backend.api.system_check.check_openai_tts",
                        new_callable=AsyncMock,
                    ) as mock_openai:
                        mock_claude.return_value = {
                            "installed": True,
                            "configured": True,
                            "version": "1.0.0",
                            "error": None,
                        }
                        mock_opencode.return_value = {
                            "installed": False,
                            "configured": False,
                            "version": None,
                            "error": "Not installed",
                        }
                        mock_elevenlabs.return_value = {
                            "configured": False,
                            "accessible": False,
                            "api_key_set": False,
                            "error": "Not configured",
                        }
                        mock_openai.return_value = {
                            "configured": False,
                            "accessible": False,
                            "api_key_set": False,
                            "error": "Not configured",
                        }

                        response = client.get("/api/v1/system-check")

                        assert response.status_code == 200
                        data = response.json()

                        assert data["system_ready"] is False
                        assert data["requirements_met"]["ai_cli"] is True
                        assert data["requirements_met"]["tts_service"] is False
                        assert len(data["recommendations"]) > 0
                        assert any(
                            "ELEVENLABS_API_KEY" in rec or "OPENAI_API_KEY" in rec
                            for rec in data["recommendations"]
                        )

    def test_quick_system_check_all_available(self, client):
        with patch(
            "backend.api.system_check.check_command_exists", new_callable=AsyncMock
        ) as mock_check:
            mock_check.side_effect = [True, False]

            with patch("backend.core.config.get_settings") as mock_settings:
                mock_settings.return_value.elevenlabs_api_key = "test_key"
                mock_settings.return_value.openai_api_key = None

                response = client.get("/api/v1/system-check/quick")

                assert response.status_code == 200
                data = response.json()

                assert data["system_ready"] is True
                assert data["has_ai_cli"] is True
                assert data["has_tts"] is True

    def test_quick_system_check_nothing_available(self, client):
        with patch(
            "backend.api.system_check.check_command_exists", new_callable=AsyncMock
        ) as mock_check:
            mock_check.side_effect = [False, False]

            with patch("backend.api.system_check.get_settings") as mock_settings:
                mock_settings.return_value.elevenlabs_api_key = None
                mock_settings.return_value.openai_api_key = None

                response = client.get("/api/v1/system-check/quick")

                assert response.status_code == 200
                data = response.json()

                assert data["system_ready"] is False
                assert data["has_ai_cli"] is False
                assert data["has_tts"] is False
