import pytest
import os
from unittest.mock import patch
import tempfile

# Clean environment before tests
for key in list(os.environ.keys()):
    if key.startswith(('CORS_', 'DOCC_', 'LOG_', 'DEBUG', 'DEVELOPMENT', 'API_', 'AUDIO_', 'ELEVENLABS_', 'OPENAI_', 'CLAUDE_')):
        os.environ.pop(key, None)

# Set test environment variables before importing any modules
os.environ['DOCC_CORS_ORIGINS'] = 'http://localhost:3000,http://127.0.0.1:3000'
os.environ['LOG_LEVEL'] = 'INFO'
os.environ['DEBUG'] = 'false'
os.environ['DEVELOPMENT'] = 'false'
os.environ['API_HOST'] = '0.0.0.0'
os.environ['API_PORT'] = '8000'
os.environ['AUDIO_CACHE_DIR'] = 'test_audio_cache'
os.environ['LOG_FILE'] = 'test.log'


@pytest.fixture(autouse=True)
def mock_settings_env():
    """Automatically mock environment for all tests."""
    test_env = {
        'DOCC_CORS_ORIGINS': 'http://localhost:3000,http://127.0.0.1:3000',
        'LOG_LEVEL': 'INFO',
        'DEBUG': 'false',
        'DEVELOPMENT': 'false',
        'API_HOST': '0.0.0.0',
        'API_PORT': '8000',
        'AUDIO_CACHE_DIR': 'test_audio_cache',
        'LOG_FILE': 'test.log'
    }
    
    with patch.dict(os.environ, test_env, clear=False):
        yield


@pytest.fixture(autouse=True)
def reset_settings():
    """Reset the global settings instance between tests."""
    import backend.core.config
    backend.core.config._settings = None
    yield
    backend.core.config._settings = None