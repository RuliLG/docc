import json
import subprocess
from unittest.mock import Mock, patch

import pytest

from backend.integrations.opencode_provider import OpenCodeProvider


class TestOpenCodeProvider:
    @pytest.fixture
    def opencode_provider(self):
        return OpenCodeProvider()

    def test_init(self, opencode_provider):
        assert opencode_provider.opencode_command == "opencode"

    @patch("subprocess.run")
    def test_is_available_true(self, mock_run, opencode_provider):
        mock_run.return_value = Mock(returncode=0)

        assert opencode_provider.is_available() is True
        mock_run.assert_called_once_with(
            ["opencode", "--help"], capture_output=True, text=True, timeout=5
        )

    @patch("subprocess.run")
    def test_is_available_false(self, mock_run, opencode_provider):
        mock_run.return_value = Mock(returncode=1)

        assert opencode_provider.is_available() is False

    @patch("subprocess.run")
    def test_is_available_file_not_found(self, mock_run, opencode_provider):
        mock_run.side_effect = FileNotFoundError()

        assert opencode_provider.is_available() is False

    @patch("subprocess.run")
    def test_is_available_timeout(self, mock_run, opencode_provider):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="opencode", timeout=5)

        assert opencode_provider.is_available() is False

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_analyze_repository_success_with_json(
        self, mock_run, opencode_provider
    ):
        expected_json = [
            {"type": "text", "markdown": "## TL;DR\nThis is a test response"},
            {
                "type": "code",
                "file": "/test/file.py",
                "relevant_lines": [{"from": 1, "to": 10}],
                "markdown": "Test code explanation",
            },
        ]

        mock_run.return_value = Mock(
            returncode=0,
            stdout=f"Some text before\n{json.dumps(expected_json)}\nSome text after",
            stderr="",
        )

        with patch.object(opencode_provider, "is_available", return_value=True):
            result = await opencode_provider.analyze_repository(
                "/test/repo", "Test question?", "Test prompt"
            )

        assert result == json.dumps(expected_json)

        mock_run.assert_called_once_with(
            ["opencode", "run", "Test prompt"],
            capture_output=True,
            text=True,
            check=True,
            cwd="/test/repo",
            timeout=120,
        )

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_analyze_repository_success_without_json(
        self, mock_run, opencode_provider
    ):
        mock_run.return_value = Mock(
            returncode=0, stdout="This is a plain text response without JSON", stderr=""
        )

        with patch.object(opencode_provider, "is_available", return_value=True):
            result = await opencode_provider.analyze_repository(
                "/test/repo", "Test question?", "Test prompt"
            )

        assert result == "This is a plain text response without JSON"

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_analyze_repository_malformed_json(self, mock_run, opencode_provider):
        mock_run.return_value = Mock(
            returncode=0, stdout='Some text\n[{"invalid json": }]\nMore text', stderr=""
        )

        with patch.object(opencode_provider, "is_available", return_value=True):
            result = await opencode_provider.analyze_repository(
                "/test/repo", "Test question?", "Test prompt"
            )

        assert "invalid json" in result

    @pytest.mark.asyncio
    async def test_analyze_repository_not_available(self, opencode_provider):
        with patch.object(opencode_provider, "is_available", return_value=False):
            with pytest.raises(RuntimeError, match="OpenCode CLI is not available"):
                await opencode_provider.analyze_repository(
                    "/test/repo", "Test question?", "Test prompt"
                )

    @pytest.mark.asyncio
    @patch("subprocess.run")
    @patch("time.sleep")
    async def test_analyze_repository_command_failed_with_retry(
        self, mock_sleep, mock_run, opencode_provider
    ):
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd=["opencode"], stderr="Command failed: invalid prompt"
        )

        with patch.object(opencode_provider, "is_available", return_value=True):
            with pytest.raises(
                RuntimeError, match="OpenCode CLI failed with exit code 1"
            ):
                await opencode_provider.analyze_repository(
                    "/test/repo", "Test question?", "Test prompt"
                )

        assert mock_run.call_count == 3
        assert mock_sleep.call_count == 2

    @pytest.mark.asyncio
    @patch("subprocess.run")
    @patch("time.sleep")
    async def test_analyze_repository_timeout_with_retry(
        self, mock_sleep, mock_run, opencode_provider
    ):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="opencode", timeout=120)

        with patch.object(opencode_provider, "is_available", return_value=True):
            with pytest.raises(
                RuntimeError, match="OpenCode CLI timed out after all retries"
            ):
                await opencode_provider.analyze_repository(
                    "/test/repo", "Test question?", "Test prompt"
                )

        assert mock_run.call_count == 3
        assert mock_sleep.call_count == 2

    @pytest.mark.asyncio
    @patch("subprocess.run")
    @patch("time.sleep")
    async def test_analyze_repository_empty_response_with_retry(
        self, mock_sleep, mock_run, opencode_provider
    ):
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        with patch.object(opencode_provider, "is_available", return_value=True):
            with pytest.raises(
                RuntimeError, match="OpenCode returned empty response after all retries"
            ):
                await opencode_provider.analyze_repository(
                    "/test/repo", "Test question?", "Test prompt"
                )

        assert mock_run.call_count == 3
        assert mock_sleep.call_count == 2

    @pytest.mark.asyncio
    @patch("subprocess.run")
    @patch("time.sleep")
    async def test_analyze_repository_retry_then_success(
        self, mock_sleep, mock_run, opencode_provider
    ):
        expected_json = [{"type": "text", "markdown": "Success"}]

        mock_run.side_effect = [
            Mock(returncode=0, stdout="", stderr=""),
            Mock(returncode=0, stdout=json.dumps(expected_json), stderr=""),
        ]

        with patch.object(opencode_provider, "is_available", return_value=True):
            result = await opencode_provider.analyze_repository(
                "/test/repo", "Test question?", "Test prompt"
            )

        assert result == json.dumps(expected_json)
        assert mock_run.call_count == 2
        assert mock_sleep.call_count == 1

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_analyze_repository_unexpected_error(
        self, mock_run, opencode_provider
    ):
        mock_run.side_effect = Exception("Unexpected error")

        with patch.object(opencode_provider, "is_available", return_value=True):
            with pytest.raises(
                RuntimeError, match="Error running OpenCode CLI: Unexpected error"
            ):
                await opencode_provider.analyze_repository(
                    "/test/repo", "Test question?", "Test prompt"
                )
