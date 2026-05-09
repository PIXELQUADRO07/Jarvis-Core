FROM python:3.11-slim

# Metadati
LABEL maintainer="JARVIS PRO"
LABEL description="JARVIS AI Local Assistant"

# Dipendenze sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    aplay \
    alsa-utils \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Directory di lavoro
WORKDIR /app

# Requirements prima (cache Docker layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia sorgenti
COPY . .

# Crea directory necessarie
RUN mkdir -p logs exports db memory_sessions voices plugins

# Variabili d'ambiente di default
ENV OLLAMA_URL=http://host.docker.internal:11434/api/chat
ENV JARVIS_MODEL=qwen2.5:7b
ENV JARVIS_LANGUAGE=it
ENV JARVIS_VOICE_ENABLED=false

# Porta API REST
EXPOSE 8000

# Entrypoint
CMD ["python", "main.py", "--no-voice"]
