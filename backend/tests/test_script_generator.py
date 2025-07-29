import pytest
import json
import os
from unittest.mock import Mock, AsyncMock, patch, mock_open
from backend.core.script_generator import ScriptGenerator
from backend.models.script import TextBlock, CodeBlock
from backend.integrations.claude_provider import ClaudeProvider
from backend.integrations.openai_ai_provider import OpenAIProvider
from backend.integrations.opencode_provider import OpenCodeProvider


@pytest.fixture
def mock_ai_provider():
    provider = Mock()
    provider.is_available.return_value = True
    provider.analyze_repository = AsyncMock()
    return provider


@pytest.fixture
def script_generator(mock_ai_provider):
    generator = ScriptGenerator()
    generator.ai_provider = mock_ai_provider
    return generator


class TestScriptGenerator:
    @pytest.mark.asyncio
    async def test_generate_script_success(self, script_generator, mock_ai_provider):
        """Test successful script generation with valid JSON response."""
        mock_response = json.dumps(
            [
                {"type": "text", "markdown": "## TL;DR\nThis explains how pricing works"},
                {
                    "type": "code",
                    "file": "/path/to/pricing.py",
                    "relevant_lines": [{"from": 10, "to": 15}],
                    "markdown": "This code handles pricing calculations",
                },
            ]
        )

        mock_ai_provider.analyze_repository.return_value = mock_response

        result = await script_generator.generate("/fake/repo", "How does pricing work?")

        assert len(result) == 2
        assert isinstance(result[0], TextBlock)
        assert isinstance(result[1], CodeBlock)
        assert result[0].markdown == "## TL;DR\nThis explains how pricing works"
        assert result[1].file == "/path/to/pricing.py"
        assert len(result[1].relevant_lines) == 1
        assert result[1].relevant_lines[0].from_line == 10
        assert result[1].relevant_lines[0].to_line == 15

    @pytest.mark.asyncio
    async def test_generate_script_with_single_line_references(self, script_generator, mock_ai_provider):
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

        result = await script_generator.generate("/fake/repo", "Test question")

        assert len(result) == 1
        assert isinstance(result[0], CodeBlock)
        assert len(result[0].relevant_lines) == 2
        assert result[0].relevant_lines[0].line == 42
        assert result[0].relevant_lines[1].from_line == 10

    @pytest.mark.asyncio
    async def test_generate_script_invalid_json(self, script_generator, mock_ai_provider):
        """Test error handling for invalid JSON response."""
        mock_ai_provider.analyze_repository.return_value = "Invalid JSON response"

        with pytest.raises(ValueError, match="Failed to parse AI response as JSON"):
            await script_generator.generate("/fake/repo", "How does pricing work?")

    @pytest.mark.asyncio
    async def test_generate_script_malformed_blocks(self, script_generator, mock_ai_provider):
        """Test error handling for malformed block structure."""
        mock_response = json.dumps(
            [
                {"type": "code", "file": "/test.py"}  # Missing required fields
            ]
        )

        mock_ai_provider.analyze_repository.return_value = mock_response

        with pytest.raises(ValueError, match="Failed to parse script blocks"):
            await script_generator.generate("/fake/repo", "Test question")

    @patch('builtins.open', new_callable=mock_open, read_data='# Test System Prompt')
    def test_load_system_prompt_success(self, mock_file):
        """Test loading system prompt from file."""
        generator = ScriptGenerator()
        assert 'Test System Prompt' in generator.system_prompt

    @patch('builtins.open', side_effect=FileNotFoundError())
    def test_load_system_prompt_fallback(self, mock_file):
        """Test fallback when system prompt file is not found."""
        generator = ScriptGenerator()
        assert 'You are an expert code analyst' in generator.system_prompt

    def test_build_prompt(self, script_generator):
        """Test prompt building with repository path and question."""
        prompt = script_generator._build_prompt("/test/repo", "How does it work?")
        
        assert "/test/repo" in prompt
        assert "How does it work?" in prompt
        assert script_generator.system_prompt in prompt

    @patch.object(ClaudeProvider, 'is_available', return_value=True)
    @patch.object(OpenAIProvider, 'is_available', return_value=False)
    @patch.object(OpenCodeProvider, 'is_available', return_value=False)
    def test_get_available_provider_claude(self, mock_opencode, mock_openai, mock_claude):
        """Test provider selection when Claude is available."""
        generator = ScriptGenerator()
        provider = generator.ai_provider
        
        assert isinstance(provider, ClaudeProvider)

    @patch.object(ClaudeProvider, 'is_available', return_value=False)
    @patch.object(OpenAIProvider, 'is_available', return_value=True)
    @patch.object(OpenCodeProvider, 'is_available', return_value=False)
    def test_get_available_provider_openai(self, mock_opencode, mock_openai, mock_claude):
        """Test provider selection when only OpenAI is available."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            generator = ScriptGenerator()
            provider = generator.ai_provider
            
            assert isinstance(provider, OpenAIProvider)

    @patch.object(ClaudeProvider, 'is_available', return_value=False)
    @patch.object(OpenAIProvider, 'is_available', return_value=False)
    @patch.object(OpenCodeProvider, 'is_available', return_value=False)
    def test_get_available_provider_none(self, mock_opencode, mock_openai, mock_claude):
        """Test error when no providers are available."""
        with pytest.raises(RuntimeError, match="No AI providers are available"):
            generator = ScriptGenerator()

    @pytest.mark.asyncio
    async def test_parse_ai_response_empty_array(self, script_generator, mock_ai_provider):
        """Test handling of empty array response."""
        mock_ai_provider.analyze_repository.return_value = json.dumps([])

        result = await script_generator.generate("/fake/repo", "Test question")

        assert result == []
        assert len(result) == 0
