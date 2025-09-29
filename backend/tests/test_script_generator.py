import json
import os
from unittest.mock import AsyncMock, Mock, mock_open, patch

import pytest

from backend.core.script_generator import ScriptGenerator
from backend.integrations.claude_provider import ClaudeProvider
from backend.integrations.opencode_provider import OpenCodeProvider
from backend.models.script import CodeBlock, TextBlock


@pytest.fixture
def mock_ai_provider():
    provider = Mock()
    provider.is_available.return_value = True
    provider.analyze_repository = AsyncMock()
    return provider


@pytest.fixture
def script_generator(mock_ai_provider):
    # Patch subprocess.run throughout the test
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0)
        generator = ScriptGenerator()
        generator.ai_provider = mock_ai_provider
        # Replace the providers list with just the mock provider
        generator.providers = [mock_ai_provider]
        yield generator


@pytest.fixture
def script_generator_with_real_providers():
    # Patch subprocess.run throughout the test
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0)
        generator = ScriptGenerator()
        yield generator


class TestScriptGenerator:
    @pytest.mark.asyncio
    async def test_generate_script_success(
        self, script_generator, mock_ai_provider, tmp_path
    ):
        """Test successful script generation with valid JSON response."""
        mock_response = json.dumps(
            [
                {
                    "type": "text",
                    "markdown": "## TL;DR\nThis explains how pricing works",
                },
                {
                    "type": "code",
                    "file": "/path/to/pricing.py",
                    "relevant_lines": [{"from": 10, "to": 15}],
                    "markdown": "This code handles pricing calculations",
                },
            ]
        )

        mock_ai_provider.analyze_repository.return_value = mock_response

        result = await script_generator.generate(
            str(tmp_path), "How does pricing work?"
        )

        assert len(result) == 2
        assert isinstance(result[0], TextBlock)
        assert isinstance(result[1], CodeBlock)
        assert result[0].markdown == "## TL;DR\nThis explains how pricing works"
        assert result[1].file == "/path/to/pricing.py"
        assert len(result[1].relevant_lines) == 1
        assert result[1].relevant_lines[0].from_line == 10
        assert result[1].relevant_lines[0].to_line == 15

    @pytest.mark.asyncio
    async def test_generate_script_with_single_line_references(
        self, script_generator, mock_ai_provider, tmp_path
    ):
        """Test script generation with single line references."""
        mock_response = json.dumps(
            [
                {
                    "type": "code",
                    "file": "/test.py",
                    "relevant_lines": [{"line": 42}, {"from": 10, "to": 15}],
                    "markdown": "Mixed line references",
                }
            ]
        )

        mock_ai_provider.analyze_repository.return_value = mock_response

        result = await script_generator.generate(str(tmp_path), "Test question")

        assert len(result) == 1
        assert isinstance(result[0], CodeBlock)
        assert len(result[0].relevant_lines) == 2
        assert result[0].relevant_lines[0].line == 42
        assert result[0].relevant_lines[1].from_line == 10

    @pytest.mark.asyncio
    async def test_generate_script_invalid_json(
        self, script_generator, mock_ai_provider, tmp_path
    ):
        """Test error handling for invalid JSON response."""
        mock_ai_provider.analyze_repository.return_value = "Invalid JSON response"

        with pytest.raises(
            RuntimeError,
            match="All AI providers failed.*Failed to parse AI response as JSON",
        ):
            await script_generator.generate(str(tmp_path), "How does pricing work?")

    @pytest.mark.asyncio
    async def test_generate_script_malformed_blocks(
        self, script_generator, mock_ai_provider, tmp_path
    ):
        """Test error handling for malformed block structure."""
        mock_response = json.dumps(
            [{"type": "code", "file": "/test.py"}]  # Missing required fields
        )

        mock_ai_provider.analyze_repository.return_value = mock_response

        with pytest.raises(
            RuntimeError, match="All AI providers failed.*Failed to parse script blocks"
        ):
            await script_generator.generate(str(tmp_path), "Test question")

    @patch("builtins.open", new_callable=mock_open, read_data="# Test System Prompt")
    def test_load_system_prompt_success(self, mock_file):
        """Test loading system prompt from file."""
        generator = ScriptGenerator()
        assert "Test System Prompt" in generator.system_prompt

    @patch("builtins.open", side_effect=FileNotFoundError())
    def test_load_system_prompt_fallback(self, mock_file):
        """Test fallback when system prompt file is not found."""
        generator = ScriptGenerator()
        assert "You are an expert code analyst" in generator.system_prompt

    def test_build_prompt(self, script_generator):
        """Test prompt building with repository path and question."""
        prompt = script_generator._build_prompt("/test/repo", "How does it work?")

        assert "/test/repo" in prompt
        assert "How does it work?" in prompt
        assert script_generator.system_prompt in prompt

    @patch.object(ClaudeProvider, "is_available", return_value=True)
    @patch.object(OpenCodeProvider, "is_available", return_value=False)
    def test_get_available_provider_claude(self, mock_opencode, mock_claude):
        """Test provider selection when Claude is available."""
        with patch("builtins.print"):
            generator = ScriptGenerator()
            provider = generator.ai_provider

            assert isinstance(provider, ClaudeProvider)

    @patch.object(ClaudeProvider, "is_available", return_value=False)
    @patch.object(OpenCodeProvider, "is_available", return_value=False)
    def test_get_available_provider_none(self, mock_opencode, mock_claude):
        """Test error when no providers are available."""
        with pytest.raises(RuntimeError, match="No local CLI agents are available"):
            generator = ScriptGenerator()

    @pytest.mark.asyncio
    async def test_parse_ai_response_empty_array(
        self, script_generator, mock_ai_provider, tmp_path
    ):
        """Test handling of empty array response."""
        mock_ai_provider.analyze_repository.return_value = json.dumps([])

        result = await script_generator.generate(str(tmp_path), "Test question")

        assert result == []
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_generate_with_provider_fallback(self):
        """Test that generator falls back to next provider if first fails."""
        with patch.object(ClaudeProvider, "is_available", return_value=False):
            with patch.object(OpenCodeProvider, "is_available", return_value=True):
                with patch.object(
                    OpenCodeProvider, "analyze_repository", new=AsyncMock()
                ) as mock_analyze:
                    mock_analyze.return_value = json.dumps(
                        [{"type": "text", "markdown": "Test"}]
                    )

                    generator = ScriptGenerator()
                    result = await generator.generate("/fake/repo", "Test question")

                    assert len(result) == 1
                    mock_analyze.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_with_specific_provider(self):
        """Test generating with a specific AI provider."""
        with patch.object(ClaudeProvider, "is_available", return_value=True):
            with patch.object(
                ClaudeProvider, "analyze_repository", new=AsyncMock()
            ) as mock_analyze:
                mock_analyze.return_value = json.dumps(
                    [{"type": "text", "markdown": "Test"}]
                )

                generator = ScriptGenerator()
                result = await generator.generate(
                    "/fake/repo", "Test question", ai_provider="claude_code"
                )

                assert len(result) == 1
                mock_analyze.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_all_providers_fail(self):
        """Test error when all providers fail."""
        with patch.object(ClaudeProvider, "is_available", return_value=True):
            with patch.object(OpenCodeProvider, "is_available", return_value=True):
                with patch.object(
                    ClaudeProvider,
                    "analyze_repository",
                    new=AsyncMock(side_effect=Exception("Claude failed")),
                ):
                    with patch.object(
                        OpenCodeProvider,
                        "analyze_repository",
                        new=AsyncMock(side_effect=Exception("OpenCode failed")),
                    ):
                        generator = ScriptGenerator()

                        with pytest.raises(
                            RuntimeError, match="All AI providers failed"
                        ):
                            await generator.generate("/fake/repo", "Test question")

    @pytest.mark.asyncio
    async def test_generate_provider_returns_empty(self):
        """Test error when provider returns empty response."""
        with patch.object(ClaudeProvider, "is_available", return_value=True):
            with patch.object(OpenCodeProvider, "is_available", return_value=False):
                with patch.object(
                    ClaudeProvider, "analyze_repository", new=AsyncMock(return_value="")
                ):
                    generator = ScriptGenerator()

                    with pytest.raises(RuntimeError):
                        await generator.generate("/fake/repo", "Test question")

    @pytest.mark.asyncio
    async def test_generate_with_unknown_provider(self):
        """Test generating with unknown provider name falls back to all."""
        with patch.object(ClaudeProvider, "is_available", return_value=True):
            with patch.object(
                ClaudeProvider, "analyze_repository", new=AsyncMock()
            ) as mock_analyze:
                mock_analyze.return_value = json.dumps(
                    [{"type": "text", "markdown": "Test"}]
                )

                generator = ScriptGenerator()
                result = await generator.generate(
                    "/fake/repo", "Test question", ai_provider="unknown_provider"
                )

                assert len(result) == 1

    def test_get_providers_to_try_no_preference(
        self, script_generator_with_real_providers
    ):
        """Test getting all providers when no preference specified."""
        providers = script_generator_with_real_providers._get_providers_to_try(None)
        assert len(providers) == 2

    def test_get_providers_to_try_with_preference(
        self, script_generator_with_real_providers
    ):
        """Test getting specific provider when preference specified."""
        providers = script_generator_with_real_providers._get_providers_to_try(
            "claude_code"
        )
        assert len(providers) == 1
        assert isinstance(providers[0], ClaudeProvider)
