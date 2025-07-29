import pytest
import json
import os
from unittest.mock import Mock, patch, MagicMock, mock_open
from backend.integrations.openai_ai_provider import OpenAIProvider


class TestOpenAIProvider:
    @pytest.fixture
    def openai_provider_with_key(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key'}):
            provider = OpenAIProvider()
            return provider

    @pytest.fixture
    def openai_provider_without_key(self):
        with patch.dict(os.environ, {}, clear=True):
            provider = OpenAIProvider()
            return provider

    def test_init_with_api_key(self, openai_provider_with_key):
        assert openai_provider_with_key.api_key == 'test-api-key'

    def test_init_without_api_key(self, openai_provider_without_key):
        assert openai_provider_without_key.api_key is None

    def test_is_available_with_key(self, openai_provider_with_key):
        assert openai_provider_with_key.is_available() is True

    def test_is_available_without_key(self, openai_provider_without_key):
        assert openai_provider_without_key.is_available() is False

    @patch('builtins.open', new_callable=mock_open, read_data='# Test System Prompt\nYou are a code analyzer.')
    def test_load_system_prompt_from_file(self, mock_file):
        provider = OpenAIProvider()
        assert 'Test System Prompt' in provider.system_prompt
        assert 'You are a code analyzer' in provider.system_prompt

    @patch('builtins.open', side_effect=FileNotFoundError())
    def test_load_system_prompt_fallback(self, mock_file):
        provider = OpenAIProvider()
        assert 'You are an expert code analyst' in provider.system_prompt

    @pytest.mark.asyncio
    @patch('openai.chat.completions.create')
    async def test_analyze_repository_success(self, mock_openai_create, openai_provider_with_key):
        """Test successful repository analysis."""
        expected_response = [
            {
                "type": "text",
                "markdown": "## TL;DR\nThis is how authentication works"
            },
            {
                "type": "code",
                "file": "/auth/login.py",
                "relevant_lines": [{"from": 10, "to": 20}],
                "markdown": "Login implementation"
            }
        ]
        
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = f"Here is the analysis:\n{json.dumps(expected_response)}\nThat's all!"
        mock_openai_create.return_value = mock_response
        
        # Mock repository context
        with patch.object(openai_provider_with_key, '_get_repository_context', return_value='Mock repo context'):
            result = await openai_provider_with_key.analyze_repository(
                "/test/repo",
                "How does authentication work?",
                "Test prompt"
            )
        
        # Should extract the JSON
        assert result == json.dumps(expected_response)
        
        # Verify OpenAI was called correctly
        mock_openai_create.assert_called_once()
        call_args = mock_openai_create.call_args
        assert call_args[1]['model'] == 'gpt-4-turbo-preview'
        assert call_args[1]['temperature'] == 0.3
        assert len(call_args[1]['messages']) == 2  # system + user

    @pytest.mark.asyncio
    @patch('openai.chat.completions.create')
    async def test_analyze_repository_no_json_in_response(self, mock_openai_create, openai_provider_with_key):
        """Test when OpenAI response doesn't contain JSON."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "This is a plain text response without any JSON"
        mock_openai_create.return_value = mock_response
        
        with patch.object(openai_provider_with_key, '_get_repository_context', return_value='Mock repo context'):
            result = await openai_provider_with_key.analyze_repository(
                "/test/repo",
                "Test question?",
                "Test prompt"
            )
        
        # Should return the entire content
        assert result == "This is a plain text response without any JSON"

    @pytest.mark.asyncio
    async def test_analyze_repository_no_api_key(self, openai_provider_without_key):
        """Test when API key is not available."""
        with pytest.raises(RuntimeError, match="OpenAI API key not available"):
            await openai_provider_without_key.analyze_repository(
                "/test/repo",
                "Test question?",
                "Test prompt"
            )

    @pytest.mark.asyncio
    @patch('openai.chat.completions.create')
    async def test_analyze_repository_api_error(self, mock_openai_create, openai_provider_with_key):
        """Test when OpenAI API throws an error."""
        mock_openai_create.side_effect = Exception("API Error: Rate limit exceeded")
        
        with patch.object(openai_provider_with_key, '_get_repository_context', return_value='Mock repo context'):
            with pytest.raises(RuntimeError, match="OpenAI API failed: API Error: Rate limit exceeded"):
                await openai_provider_with_key.analyze_repository(
                    "/test/repo",
                    "Test question?",
                    "Test prompt"
                )

    @patch('os.walk')
    def test_get_repository_context(self, mock_walk, openai_provider_with_key):
        """Test repository context generation."""
        # Mock os.walk to return a simple structure
        mock_walk.return_value = [
            ('/test/repo', ['src', '.git'], ['README.md', 'setup.py']),
            ('/test/repo/src', [], ['main.py', 'utils.py', '.hidden.py'])
        ]
        
        # Mock file reading
        with patch('builtins.open', mock_open(read_data='# Test README\nThis is a test project')):
            context = openai_provider_with_key._get_repository_context('/test/repo', max_files=5)
        
        assert 'README.md' in context
        assert 'Test README' in context
        assert 'setup.py' in context
        assert 'src/main.py' in context
        assert '.hidden.py' not in context  # Hidden files should be excluded
        assert '.git' not in context  # Hidden directories should be excluded

    @patch('os.walk')
    def test_get_repository_context_max_files(self, mock_walk, openai_provider_with_key):
        """Test that max_files limit is respected."""
        # Mock os.walk to return many files
        mock_walk.return_value = [
            ('/test/repo', [], [f'file{i}.py' for i in range(30)])
        ]
        
        context = openai_provider_with_key._get_repository_context('/test/repo', max_files=10)
        
        # Count the number of files in context
        file_count = context.count('file')
        assert file_count == 10  # Should stop at max_files