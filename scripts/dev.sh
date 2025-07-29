#!/bin/bash
# Development setup script

set -e

echo "🚀 Setting up Docc development environment..."

# Check if Python 3.8+ is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python $REQUIRED_VERSION or higher is required. Found: $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION found"

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed"
    exit 1
fi

NODE_VERSION=$(node --version | cut -c 2-)
echo "✅ Node.js $NODE_VERSION found"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

# Install development dependencies
echo "🧪 Installing development dependencies..."
pip install pytest-cov isort mypy

# Set up frontend
echo "🎨 Setting up frontend..."
cd frontend

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
npm install

# Install additional dev dependencies
npm install --save-dev @typescript-eslint/eslint-plugin @typescript-eslint/parser eslint prettier

cd ..

# Copy environment file
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file from template..."
    cp .env.example .env
    echo "✏️  Please edit .env file with your API keys"
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p audio_cache logs sessions

# Create symlink for sessions in frontend public folder
echo "🔗 Creating symlink for sessions folder..."
cd frontend/public
if [ -L "sessions" ]; then
    echo "  Symlink already exists"
else
    ln -sf ../../sessions sessions
    echo "  Created symlink: frontend/public/sessions -> sessions"
fi
cd ../..

echo "✅ Development environment setup complete!"
echo ""
echo "🏃 To start developing:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Start backend: uvicorn backend.main:app --reload"
echo "  3. Start frontend: cd frontend && npm start"
echo "  4. Edit .env file with your API keys"
echo ""
echo "🧪 To run tests:"
echo "  Backend: pytest backend/tests/"
echo "  Frontend: cd frontend && npm test"
echo ""
echo "🎨 To format code:"
echo "  Backend: black backend/ cli/ shared/"
echo "  Frontend: cd frontend && npm run format"