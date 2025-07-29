import pytest
import json
import os
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, mock_open
from click.testing import CliRunner
from cli.main import docc


class TestCLI:
    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def mock_script_generator(self):
        with patch('cli.main.ScriptGenerator') as mock:
            instance = Mock()
            instance.generate = AsyncMock()
            mock.return_value = instance
            yield instance

    @pytest.fixture
    def mock_tts_manager(self):
        with patch('cli.main.TTSManager') as mock:
            instance = Mock()
            instance.generate_or_get_cached_audio = AsyncMock()
            mock.return_value = instance
            yield instance

    def test_cli_help(self, runner):
        """Test CLI help command."""
        result = runner.invoke(docc, ['--help'])
        assert result.exit_code == 0
        assert 'Generate documentation script for a repository question' in result.output
        assert 'REPOSITORY_PATH' in result.output
        assert 'QUESTION' in result.output

    def test_cli_invalid_repository(self, runner):
        """Test CLI with invalid repository path."""
        result = runner.invoke(docc, ['/nonexistent/path', 'Test question?'])
        assert result.exit_code == 2
        assert 'does not exist' in result.output

    @patch('os.path.isdir', return_value=True)
    @patch('os.path.abspath', side_effect=lambda x: f"/absolute{x}")
    @patch('webbrowser.open')
    def test_cli_success_with_default_output(
        self, mock_browser, mock_abspath, mock_isdir, 
        runner, mock_script_generator, mock_tts_manager, tmp_path
    ):
        """Test successful CLI execution with default output."""
        # Mock script generation
        mock_blocks = [
            Mock(dict=lambda: {
                "type": "text", 
                "markdown": "## TL;DR\nTest response"
            }),
            Mock(dict=lambda: {
                "type": "code",
                "file": "/test.py",
                "relevant_lines": [],
                "markdown": "Code explanation"
            })
        ]
        
        # Set markdown attribute for the mock blocks
        mock_blocks[0].markdown = "## TL;DR\nTest response"
        mock_blocks[1].markdown = "Code explanation"
        
        mock_script_generator.generate.return_value = mock_blocks
        mock_tts_manager.generate_or_get_cached_audio.return_value = b"fake audio"

        with patch('pathlib.Path.mkdir'), \
             patch('builtins.open', mock_open()), \
             patch('pathlib.Path.cwd', return_value=tmp_path):
            
            result = runner.invoke(docc, ['/test/repo', 'How does it work?'])
        
        assert result.exit_code == 0
        assert 'Session generated successfully' in result.output
        
        # Verify browser was opened
        mock_browser.assert_called_once()
        browser_url = mock_browser.call_args[0][0]
        assert 'http://localhost:3000?session=' in browser_url

    @patch('os.path.isdir', return_value=True)
    @patch('os.path.abspath', side_effect=lambda x: f"/absolute{x}")
    def test_cli_with_custom_output(
        self, mock_abspath, mock_isdir,
        runner, mock_script_generator, mock_tts_manager
    ):
        """Test CLI with custom output directory."""
        mock_script_generator.generate.return_value = []
        
        with patch('pathlib.Path.mkdir'), \
             patch('builtins.open', mock_open()):
            
            result = runner.invoke(docc, [
                '/test/repo', 
                'Test question?',
                '--output', '/custom/output'
            ])
        
        assert result.exit_code == 0

    @patch('os.path.isdir', return_value=True)
    @patch('os.path.abspath', side_effect=lambda x: f"/absolute{x}")
    def test_cli_no_browser_flag(
        self, mock_abspath, mock_isdir,
        runner, mock_script_generator, mock_tts_manager
    ):
        """Test CLI with --no-browser flag."""
        mock_script_generator.generate.return_value = []
        
        with patch('pathlib.Path.mkdir'), \
             patch('builtins.open', mock_open()), \
             patch('webbrowser.open') as mock_browser:
            
            result = runner.invoke(docc, [
                '/test/repo',
                'Test question?',
                '--no-browser'
            ])
        
        assert result.exit_code == 0
        mock_browser.assert_not_called()

    @patch('os.path.isdir', return_value=True)
    @patch('os.path.abspath', side_effect=lambda x: f"/absolute{x}")
    def test_cli_verbose_output(
        self, mock_abspath, mock_isdir,
        runner, mock_script_generator, mock_tts_manager
    ):
        """Test CLI with verbose flag."""
        mock_script_generator.generate.return_value = []
        
        with patch('pathlib.Path.mkdir'), \
             patch('builtins.open', mock_open()):
            
            result = runner.invoke(docc, [
                '/test/repo',
                'Test question?',
                '--verbose'
            ])
        
        assert result.exit_code == 0
        assert 'Analyzing repository: /absolute/test/repo' in result.output
        assert 'Question: Test question?' in result.output
        assert 'Initializing script generator...' in result.output

    @patch('os.path.isdir', return_value=True)
    @patch('os.path.abspath', side_effect=lambda x: f"/absolute{x}")
    def test_cli_script_generation_error(
        self, mock_abspath, mock_isdir,
        runner, mock_script_generator
    ):
        """Test CLI when script generation fails."""
        mock_script_generator.generate.side_effect = Exception("AI provider failed")
        
        with patch('pathlib.Path.mkdir'):
            result = runner.invoke(docc, ['/test/repo', 'Test question?'])
        
        assert result.exit_code == 1
        assert 'Error: AI provider failed' in result.output

    @patch('os.path.isdir', return_value=True)
    @patch('os.path.abspath', side_effect=lambda x: f"/absolute{x}")
    def test_cli_audio_generation_warning(
        self, mock_abspath, mock_isdir,
        runner, mock_script_generator, mock_tts_manager
    ):
        """Test CLI when audio generation fails but continues."""
        mock_blocks = [Mock(dict=lambda: {"type": "text", "markdown": "Test"})]
        mock_blocks[0].markdown = "Test"
        
        mock_script_generator.generate.return_value = mock_blocks
        mock_tts_manager.generate_or_get_cached_audio.side_effect = Exception("TTS failed")
        
        with patch('pathlib.Path.mkdir'), \
             patch('builtins.open', mock_open()), \
             patch('webbrowser.open'):
            
            result = runner.invoke(docc, [
                '/test/repo',
                'Test question?',
                '--verbose'
            ])
        
        assert result.exit_code == 0
        assert 'Warning: Could not generate audio' in result.output

    def test_cli_with_file_path_instead_of_directory(self, runner):
        """Test CLI when given a file path instead of directory."""
        with patch('os.path.exists', return_value=True), \
             patch('os.path.isdir', return_value=False):
            
            result = runner.invoke(docc, ['/test/file.py', 'Test question?'])
        
        assert result.exit_code == 1
        assert 'is not a valid directory' in result.output