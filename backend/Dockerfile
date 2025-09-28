FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y \
    curl \
    git \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install Claude Code and OpenCode CLI tools
RUN npm install -g @anthropic-ai/claude-code opencode-ai

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY setup.py .
COPY pyproject.toml .
COPY backend/ backend/
COPY shared/ shared/

RUN pip install -e .

RUN mkdir -p audio_cache logs

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]