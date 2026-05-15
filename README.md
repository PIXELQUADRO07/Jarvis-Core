# JARVIS PRO — Local AI Assistant

Local AI assistant powered by Ollama with an advanced CLI, voice support, REST API, plugins, and more.

---

## Quick Start

```bash
# 1. Clone or extract the project
cd jarvis-pro

# 2. Create a virtual environment and install dependencies
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Start Ollama in a separate terminal
ollama serve
ollama pull qwen2.5:7b         # or your preferred model

# 4. Start JARVIS
python main.py --lang en
```

---

## Launch options

```bash
python main.py --lang en           # Start in English
python main.py --silent            # Enable short/quiet responses
python main.py --api               # Start REST API server (port 8000)
python main.py --no-voice          # Disable voice synthesis
python main.py --no-plugins        # Disable plugins
python main.py --cleanup           # Clean old DB messages and exit
```

---

## Docker

```bash
# Build and run
docker-compose up -d

# Run JARVIS only (if Ollama is already running)
docker build -t jarvis-pro .
docker run -it --rm -e OLLAMA_URL=http://host.docker.internal:11434/api/chat jarvis-pro
```

---

## CLI Commands

| Command | Description |
|---------|-------------|
| `/help` | Show commands |
| `/status` | Show system and Ollama status |
| `/config` | Show current configuration |
| `/lang [it\|en\|es\|fr\|de]` | Change language |
| `/silent on\|off` | Enable/disable silent mode |
| `/model list` | List available Ollama models |
| `/model set [name]` | Change model |
| `/session create [name]` | Create session |
| `/session switch [name]` | Switch session |
| `/session list` | List sessions |
| `/export` | Export chat to Markdown |
| `/search [text]` | Search conversation history |
| `/cleanup` | Remove old messages |
| `/voice on\|off\|status\|test` | Voice control |
| `/encrypt on\|off` | Memory encryption |
| `/api on\|off` | REST API server |
| `/plugins` | List plugins |
| `/clear` | Reset session memory |
| `/history` | Show last messages |
| `/exit` | Quit |

---

## REST API

Run with `python main.py --api` (or `/api on`):

```bash
# Chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "hello", "session": "default"}'

# Status
curl http://localhost:8000/status

# Sessions
curl http://localhost:8000/sessions

# History
curl http://localhost:8000/history/default

# Search
curl "http://localhost:8000/search?q=weather"

# With API key (if configured)
curl -H "X-API-Key: your-api-key" http://localhost:8000/status
```

Interactive docs: **http://localhost:8000/docs**

---

## Plugins

Create a file in `plugins/my_plugin.py`:

```python
from core.plugin_manager import PluginBase

class MyPlugin(PluginBase):
    name        = "my_plugin"
    description = "What the plugin does"
    version     = "1.0.0"

    def can_handle(self, query: str) -> bool:
        return "my_keyword" in query.lower()

    def handle(self, query: str) -> str:
        return "My plugin response!"
```

The plugin will load automatically on the next start.

---

## Memory Encryption

```bash
pip install cryptography

# In CLI
/encrypt on
```

An AES key is generated in `.jarvis_key` (do not commit this file).

---

## Testing

```bash
pytest tests/ -v
pytest tests/ --cov=core --cov-report=term-missing
```

---

## Project Structure

```
jarvis-pro/
├── main.py                    # Entry point
├── config.py                  # Configuration (JSON + YAML + env)
├── logger.py                  # Structured JSON logging with rotation
├── jarvis_config.json         # Default configuration
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
│
├── core/
│   ├── llm.py                 # LLM streaming (Ollama)
│   ├── memory.py              # Memory (SQLite + JSON file)
│   ├── db.py                  # Persistent SQLite database
│   ├── state.py               # Thread-safe internal state
│   ├── commands.py            # Slash command dispatcher
│   ├── security.py            # AES, rate limiting, sanitization
│   ├── i18n.py                # Multi-language support (it/en/es/fr/de)
│   ├── notifications.py       # Desktop notifications
│   ├── plugin_manager.py      # Auto-loading plugin system
│   ├── retry_handler.py       # Retry + circuit breaker
│   ├── session_manager.py     # Multiple sessions
│   ├── token_counter.py       # Token counter
│   ├── voice.py               # Voice facade
│   ├── voice_engine.py        # TTS worker daemon
│   ├── voice_queue.py         # Priority TTS queue
│   ├── audio_fx.py            # Iron Man audio effects
│   ├── tts_piper.py           # Piper synthesis
│   └── tools/
│       ├── router.py          # Tool + plugin router
│       ├── api_weather.py     # Weather
│       ├── api_wiki.py        # Wikipedia
│       ├── web_search.py      # DuckDuckGo search
│       ├── math.py            # Calculations
│       ├── scraper.py         # URL scraping
│       ├── system.py          # System info
│       └── cache.py           # Response cache
│
├── controller/
│   └── jarvis_controller.py   # UI↔core controller
│
├── ui/
│   └── cli.py                 # Advanced CLI
│
├── api/
│   └── rest_api.py            # FastAPI REST API
│
├── plugins/                   # User plugins
│   └── example_hello.py
│
├── tests/
│   └── test_core.py           # Pytest unit tests
│
├── logs/                      # Rotating JSON logs
├── exports/                   # Exported chat Markdown
├── db/                        # SQLite database
├── memory_sessions/           # Session JSON files
└── voices/                    # Piper voice models (.onnx)
```

---

## Environment Variables

```bash
OLLAMA_URL=http://localhost:11434/api/chat
JARVIS_MODEL=qwen2.5:7b
JARVIS_TEMPERATURE=0.2
JARVIS_LANGUAGE=en
JARVIS_VOICE_ENABLED=false
JARVIS_VOICE_MODEL=en_US-ryan-high.onnx
JARVIS_ENABLE_API=false
JARVIS_API_PORT=8000
JARVIS_API_KEY=your-secret-key
JARVIS_ENCRYPT_MEMORY=false
JARVIS_SILENT_MODE=false
```
