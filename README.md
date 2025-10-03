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
- Claude Code CLI (recommended) or OpenCode CLI
- ElevenLabs or OpenAI TTS

### Docker Setup

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

**Open your browser**
Navigate to `http://localhost:3000`

## 📋 API Endpoints

API documentation is available at `http://localhost:8000/docs`

## 🧪 Testing

### Backend Tests
```bash
source venv/bin/activate
cd backend
pytest tests/ -v
```

## 🔍 Troubleshooting

### Common Issues

1. **"No AI providers are available"**
   - Install Claude CLI or Opencode CLI
   - Ensure they're in your PATH
   - Test with `claude --version` or `opencode --version`

2. **TTS not working**
   - Set `ELEVENLABS_API_KEY` or `OPENAI_API_KEY` environment variables
   - Check API key validity
   - Audio will fallback to text-only mode if TTS fails

## 📝 License

MIT
