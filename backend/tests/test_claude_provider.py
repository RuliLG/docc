import json
import subprocess
from unittest.mock import MagicMock, Mock, patch

import pytest

from backend.integrations.claude_provider import ClaudeProvider


class TestClaudeProvider:
    @pytest.fixture
    def claude_provider(self):
        return ClaudeProvider()

    def test_init(self, claude_provider):
        assert claude_provider.claude_command == "claude"

    @patch("subprocess.run")
    def test_is_available_true(self, mock_run, claude_provider):
        """Test when Claude CLI is available."""
        mock_run.return_value = Mock(returncode=0)

        assert claude_provider.is_available() is True
        mock_run.assert_called_once_with(
            ["claude", "--version"], capture_output=True, text=True
        )

    @patch("subprocess.run")
    def test_is_available_false(self, mock_run, claude_provider):
        """Test when Claude CLI is not available."""
        mock_run.return_value = Mock(returncode=1)

        assert claude_provider.is_available() is False

    @patch("subprocess.run")
    def test_is_available_file_not_found(self, mock_run, claude_provider):
        """Test when Claude CLI is not installed."""
        mock_run.side_effect = FileNotFoundError()

        assert claude_provider.is_available() is False

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_analyze_repository_success_with_json(
        self, mock_run, claude_provider, tmp_path
    ):
        """Test successful analysis with valid JSON response."""
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

        # Mock is_available to return True
        with patch.object(claude_provider, "is_available", return_value=True):
            result = await claude_provider.analyze_repository(
                str(tmp_path), "Test question?", "Test prompt"
            )

        # Should extract just the JSON part
        assert result == json.dumps(expected_json)

        mock_run.assert_called_once_with(
            ["claude", "--print", "--output-format", "text", "Test prompt"],
            capture_output=True,
            text=True,
            check=True,
            cwd=str(tmp_path),
            timeout=120,
        )

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_analyze_repository_success_without_json(
        self, mock_run, claude_provider
    ):
        """Test when response doesn't contain valid JSON."""
        mock_run.return_value = Mock(
            returncode=0, stdout="This is a plain text response without JSON", stderr=""
        )

        with patch.object(claude_provider, "is_available", return_value=True):
            result = await claude_provider.analyze_repository(
                "/test/repo", "Test question?", "Test prompt"
            )

        # Should return the entire output
        assert result == "This is a plain text response without JSON"

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_analyze_repository_malformed_json(self, mock_run, claude_provider):
        """Test when JSON is malformed."""
        mock_run.return_value = Mock(
            returncode=0, stdout='Some text\n[{"invalid json": }]\nMore text', stderr=""
        )

        with patch.object(claude_provider, "is_available", return_value=True):
            result = await claude_provider.analyze_repository(
                "/test/repo", "Test question?", "Test prompt"
            )

        # Should return the entire output when JSON is malformed
        assert "invalid json" in result

    @pytest.mark.asyncio
    async def test_analyze_repository_not_available(self, claude_provider):
        """Test when Claude CLI is not available."""
        with patch.object(claude_provider, "is_available", return_value=False):
            with pytest.raises(RuntimeError, match="Claude Code CLI is not available"):
                await claude_provider.analyze_repository(
                    "/test/repo", "Test question?", "Test prompt"
                )

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_analyze_repository_command_failed(
        self, mock_run, claude_provider, tmp_path
    ):
        """Test when Claude CLI command fails."""
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd=["claude"], stderr="Command failed: invalid prompt"
        )

        with patch.object(claude_provider, "is_available", return_value=True):
            with pytest.raises(
                RuntimeError,
                match="Error running Claude Code CLI:.*returned non-zero exit status 1",
            ):
                await claude_provider.analyze_repository(
                    str(tmp_path), "Test question?", "Test prompt"
                )

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_analyze_repository_unexpected_error(self, mock_run, claude_provider):
        """Test when an unexpected error occurs."""
        mock_run.side_effect = Exception("Unexpected error")

        with patch.object(claude_provider, "is_available", return_value=True):
            with pytest.raises(
                RuntimeError, match="Error running Claude Code CLI: Unexpected error"
            ):
                await claude_provider.analyze_repository(
                    "/test/repo", "Test question?", "Test prompt"
                )
