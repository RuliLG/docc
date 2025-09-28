# Docc - AI-Powered Repository Documentation Tool 🎥

A web-based tool that generates interactive, video-like documentation explanations for code repositories using AI agents and text-to-speech technology.

## 🎯 Overview

Docc allows users to ask questions about any repository and generates a "script" that can be rendered as an interactive video-like presentation. The AI agent analyzes the codebase and provides structured explanations with code context and narration.

### Key Features

- **Web Interface**: Interactive UI for generating documentation
- **AI Analysis**: Uses Claude Code CLI or OpenCode CLI for repository analysis
- **Interactive Player**: React-based video player with VS Code-like interface
- **Text-to-Speech**: ElevenLabs and OpenAI TTS integration with caching
- **Code Highlighting**: Monaco editor with syntax highlighting for relevant code sections
- **Structured Output**: JSON-based script format for easy rendering

## 🏗️ Architecture

```
docc/
├── backend/          # FastAPI backend
│   ├── api/          # REST API endpoints
│   ├── core/         # Business logic
│   ├── integrations/ # AI and TTS providers
│   └── models/       # Pydantic models
├── frontend/         # React frontend
│   ├── components/   # UI components
│   ├── services/     # API clients
│   └── types/        # TypeScript types
└── shared/           # Shared utilities
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- Claude Code CLI (recommended) or OpenAI API key
- Optional: ElevenLabs or OpenAI API keys (for TTS)

### Automated Setup (Recommended)

```bash
# Clone and setup everything automatically
git clone <repository-url>
cd capstone-project
chmod +x scripts/dev.sh
./scripts/dev.sh
```

This script will:
- Create Python virtual environment
- Install all dependencies
- Set up the frontend
- Create necessary directories
- Set up session folder symlink
- Copy .env.example to .env

### Manual Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd capstone-project
   ```

2. **Set up Python environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Set up React frontend**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

4. **Create necessary directories and symlink**
   ```bash
   mkdir -p sessions audio_cache logs
   cd frontend/public
   ln -sf ../../sessions sessions
   cd ../..
   ```

5. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env file with your API keys
   ```

### Docker Setup

The project includes Docker configurations for both development and production:

#### Development with Docker

```bash
# Build and run with hot-reload
docker compose up

# The services will be available at:
# - Backend: http://localhost:8000
# - Frontend: http://localhost:3000
```

#### Production with Docker

```bash
# Build and run production version
docker compose -f docker-compose.prod.yml up
```

#### Accessing Local Repositories from Docker

By default, your home directory is mounted into the container at `/host/home`. When specifying repository paths in the app:

- Local path: `/Users/yourusername/projects/myrepo`
- Docker path: `/host/home/projects/myrepo`

To customize volume mounts:

1. Copy the override example:
   ```bash
   cp docker-compose.override.yml.example docker-compose.override.yml
   ```

2. Edit `docker-compose.override.yml` to mount specific directories:
   ```yaml
   services:
     backend:
       volumes:
         - /path/to/your/projects:/repositories:ro
   ```

3. Use the mounted path in the app (e.g., `/repositories/myproject`)

### AI Provider Configuration

Choose one of the following:

1. **Claude Code CLI** (Recommended)
   ```bash
   # Install Claude Code CLI
   # Follow instructions at: https://docs.anthropic.com/claude-code/
   # Make sure 'claude' command is available in your PATH
   ```

2. **OpenAI API** (Alternative)
   ```bash
   # Set in your .env file:
   OPENAI_API_KEY=your_api_key_here
   ```

3. **OpenCode CLI** (Fallback)
   ```bash
   # Install your preferred AI CLI tool
   # Ensure it's available in your PATH
   ```

### TTS Configuration (Optional)

For audio generation, configure one:

```bash
# Option 1: ElevenLabs (high quality)
ELEVENLABS_API_KEY=your_api_key_here

# Option 2: OpenAI TTS (good quality, more affordable)
OPENAI_API_KEY=your_api_key_here
```

## 🔧 Usage

### Web Interface

1. **Start the backend server**
   ```bash
   cd /path/to/capstone-project
   source venv/bin/activate
   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Start the frontend development server**
   ```bash
   cd frontend
   npm start
   ```

3. **Open your browser**
   Navigate to `http://localhost:3000`

## 📁 Session Structure

When you generate documentation, it creates a session folder with the following structure:

```
sessions/
└── repository_name_20240315_143022/
    ├── script.json          # Generated documentation script
    └── audio/               # Audio files for narration
        ├── block_0.mp3
        ├── block_1.mp3
        └── ...
```

The frontend automatically loads sessions using the `?session=` URL parameter.

## 📋 API Endpoints

### Script Generation
- `POST /api/v1/generate-script` - Generate documentation script
- `GET /api/v1/health` - Health check

### Text-to-Speech
- `POST /api/v1/generate-audio` - Generate TTS audio
- `GET /api/v1/audio/{audio_id}` - Retrieve audio file
- `GET /api/v1/voices` - Get available voices
- `GET /api/v1/cache/stats` - Get cache statistics
- `DELETE /api/v1/cache` - Clear audio cache

## 🎨 Script Format

The generated scripts follow this JSON structure:

```json
[
  {
    "type": "text",
    "markdown": "## TL;DR\nBrief explanation of the answer"
  },
  {
    "type": "code",
    "file": "/path/to/relevant/file.py",
    "relevant_lines": [
      {"from": 10, "to": 15},
      {"line": 20}
    ],
    "markdown": "Explanation of this code block"
  }
]
```

## 🧪 Testing

### Backend Tests
```bash
source venv/bin/activate
pytest backend/tests/ -v
```

### Frontend Tests
```bash
cd frontend
npm test
```

### API Testing
```bash
python test_api.py
```

## 🎛️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ELEVENLABS_API_KEY` | ElevenLabs API key for TTS | None |
| `OPENAI_API_KEY` | OpenAI API key for TTS | None |
| `CLAUDE_API_KEY` | Claude API key (if using API instead of CLI) | None |

### AI Providers

The system supports multiple AI providers with automatic fallback:

1. **Claude CLI** (Primary) - Uses local `claude` command
2. **OpenCode CLI** (Fallback) - Uses local `opencode` command

### TTS Providers

Text-to-Speech providers with automatic fallback:

1. **ElevenLabs** (Primary) - High-quality voices
2. **OpenAI TTS** (Fallback) - Good quality, more affordable

## 🛠️ Development

### Code Style

- **Backend**: Black formatter, flake8 linting
- **Frontend**: Prettier, ESLint

Format code:
```bash
# Backend
source venv/bin/activate
black backend/ shared/
flake8 backend/ shared/

# Frontend
cd frontend
npm run format
npm run lint
```

### Project Structure

- **Modular Design**: Separate concerns between AI providers, TTS services, and business logic
- **Dependency Injection**: Easy to swap providers and test components
- **Type Safety**: Full TypeScript coverage in frontend, Pydantic models in backend
- **Error Handling**: Comprehensive error handling with user-friendly messages

## 🔍 Troubleshooting

### Common Issues

1. **"No AI providers are available"**
   - Install Claude CLI or OpenCode CLI
   - Ensure they're in your PATH
   - Test with `claude --version` or `opencode --version`

2. **TTS not working**
   - Set `ELEVENLABS_API_KEY` or `OPENAI_API_KEY` environment variables
   - Check API key validity
   - Audio will fallback to text-only mode if TTS fails

3. **Frontend not connecting to backend**
   - Ensure backend is running on port 8000
   - Check CORS settings in `backend/main.py`
   - Verify API base URL in `frontend/src/services/api.ts`

### Debug Mode

Enable verbose logging:
```bash
# Backend
uvicorn backend.main:app --log-level debug
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make changes and add tests
4. Run tests: `pytest` and `npm test`
5. Format code: `black .` and `npm run format`
6. Commit changes: `git commit -m 'Add amazing feature'`
7. Push to branch: `git push origin feature/amazing-feature`
8. Open a Pull Request

## 📝 License

This project is part of a university capstone project and is for educational purposes.

## 🎓 Academic Context

This is a capstone project demonstrating:

- **Full-stack development** (Python/FastAPI + React/TypeScript)
- **AI integration** (Claude Code, OpenAI)
- **Modern tooling** (Docker-ready, CI/CD-ready)
- **Clean architecture** (SOLID principles, dependency injection)
- **User experience** (Interactive UI, error handling)
- **Testing** (Unit tests, integration tests)

---

**Built with ❤️ using Claude Code**