[Screencast_20260515_144732.webm](https://github.com/user-attachments/assets/8855cad6-1b1e-4ebd-93f1-ef6904674e11)
# 🤖 JARVIS PRO — Local AI Assistant

> A powerful, feature-rich local AI assistant powered by Ollama with advanced CLI, voice support, REST API, plugin system, and more.

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Supported-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen)]()

---

## ⭐ Features

- **🗣️ Voice Support** — Natural text-to-speech and voice input capabilities
- **⚡ Fast & Local** — Runs entirely on your machine using Ollama
- **🔌 Plugin System** — Extensible architecture for custom plugins
- **🌐 REST API** — Full-featured HTTP API with interactive docs
- **💾 Memory Management** — SQLite + JSON-based persistent storage
- **🔐 Encryption** — Optional AES encryption for sensitive data
- **🌍 Multi-Language** — Support for EN, IT, ES, FR, DE
- **📊 Session Management** — Create and manage multiple conversations
- **🎯 Advanced CLI** — Powerful command interface with 20+ commands
- **🐳 Docker Ready** — Pre-configured Docker & Docker Compose setup

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- [Ollama](https://ollama.ai) installed and running

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/PIXELQUADRO07/Jarvis-Core.git
cd Jarvis-Core

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate          # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start Ollama (in a separate terminal)
ollama serve
ollama pull qwen2.5:7b            # or your preferred model

# 5. Launch JARVIS
python main.py --lang en
```

---

## 🎮 Launch Options

```bash
python main.py --lang en           # Start in English
python main.py --silent            # Enable short/quiet responses
python main.py --api               # Start REST API server (port 8000)
python main.py --no-voice          # Disable voice synthesis
python main.py --no-plugins        # Disable plugins
python main.py --cleanup           # Clean old DB messages and exit
```

---

## 🐳 Docker Setup

### Option 1: Complete Setup (JARVIS + Ollama)
```bash
docker-compose up -d
```

### Option 2: JARVIS Only (Ollama running separately)
```bash
docker build -t jarvis-pro .
docker run -it --rm \
  -e OLLAMA_URL=http://host.docker.internal:11434/api/chat \
  jarvis-pro
```

---

## 💬 CLI Commands Reference

| Command | Description |
|---------|-------------|
| `/help` | Display all available commands |
| `/status` | Show system and Ollama status |
| `/config` | Display current configuration |
| `/lang [it\|en\|es\|fr\|de]` | Change interface language |
| `/silent on\|off` | Toggle silent/quiet mode |
| `/model list` | List available Ollama models |
| `/model set [name]` | Switch to different model |
| `/session create [name]` | Create a new conversation session |
| `/session switch [name]` | Switch to existing session |
| `/session list` | Display all sessions |
| `/export` | Export chat history to Markdown |
| `/search [text]` | Search conversation history |
| `/cleanup` | Remove old/archived messages |
| `/voice on\|off\|status\|test` | Voice control & testing |
| `/encrypt on\|off` | Toggle memory encryption |
| `/api on\|off` | Start/stop REST API server |
| `/plugins` | List loaded plugins |
| `/clear` | Reset current session |
| `/history` | Show recent messages |
| `/exit` | Quit JARVIS |

---

## 🌐 REST API

Start the API with `python main.py --api` (or `/api on` in CLI).

### Interactive Documentation
Visit: **http://localhost:8000/docs**

### API Endpoints

#### Chat
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "hello", "session": "default"}'
```

#### System Status
```bash
curl http://localhost:8000/status
```

#### Session Management
```bash
curl http://localhost:8000/sessions
```

#### Chat History
```bash
curl http://localhost:8000/history/default
```

#### Search History
```bash
curl "http://localhost:8000/search?q=weather"
```

#### With API Key (if configured)
```bash
curl -H "X-API-Key: your-api-key" http://localhost:8000/status
```

---

## 🔌 Plugin System

Create custom plugins to extend JARVIS capabilities!

### Creating a Plugin

Create a new file in `plugins/my_plugin.py`:

```python
from core.plugin_manager import PluginBase

class MyPlugin(PluginBase):
    name        = "my_plugin"
    description = "What your plugin does"
    version     = "1.0.0"

    def can_handle(self, query: str) -> bool:
        """Return True if this plugin should handle the query"""
        return "my_keyword" in query.lower()

    def handle(self, query: str) -> str:
        """Process the query and return response"""
        return "My plugin response!"
```

Plugins load automatically on next startup. No additional configuration needed!

---

## 🔐 Memory Encryption

Enable AES encryption to protect sensitive conversation data.

```bash
# Install cryptography (if not already installed)
pip install cryptography

# Enable encryption in CLI
/encrypt on
```

Your encryption key is stored in `.jarvis_key` — **Never commit this file to version control!**

---

## 🧪 Testing

Run the test suite to ensure everything works correctly:

```bash
# Run all tests with verbose output
pytest tests/ -v

# Run tests with coverage report
pytest tests/ --cov=core --cov-report=term-missing
```

---

## 📁 Project Structure

```
Jarvis-Core/
├── main.py                        # Application entry point
├── config.py                      # Configuration manager
├── logger.py                      # Structured logging with rotation
├── jarvis_config.json             # Default configuration
├── requirements.txt               # Python dependencies
├── Dockerfile
├── docker-compose.yml
│
├── core/                          # Core functionality
│   ├── llm.py                     # LLM streaming (Ollama)
│   ├── memory.py                  # Memory management
│   ├── db.py                      # SQLite persistence
│   ├── state.py                   # Thread-safe state
│   ├── commands.py                # CLI command dispatcher
│   ├── security.py                # Security & encryption
│   ├── i18n.py                    # Multi-language support
│   ├── notifications.py           # Desktop notifications
│   ├── plugin_manager.py          # Plugin system
│   ├── retry_handler.py           # Retry logic & circuit breaker
│   ├── session_manager.py         # Session management
│   ├── token_counter.py           # Token counting
│   ├── voice.py                   # Voice interface
│   ├── voice_engine.py            # TTS worker
│   ├── voice_queue.py             # Audio queue
│   ├── audio_fx.py                # Audio effects
│   ├── tts_piper.py               # Piper TTS integration
│   └── tools/                     # Utility tools
│       ├── router.py              # Tool routing
│       ├── api_weather.py         # Weather API
│       ├── api_wiki.py            # Wikipedia integration
│       ├── web_search.py          # Web search
│       ├── math.py                # Math utilities
│       ├── scraper.py             # Web scraping
│       ├── system.py              # System info
│       └── cache.py               # Response caching
│
├── controller/
│   └── jarvis_controller.py       # UI-Core bridge
│
├── ui/
│   └── cli.py                     # Advanced CLI interface
│
├── api/
│   └── rest_api.py                # FastAPI REST server
│
├── plugins/                       # User-created plugins
│   └── example_hello.py
│
├── tests/                         # Unit tests
│   └── test_core.py
│
├── logs/                          # Application logs
├── exports/                       # Exported conversations
├── db/                            # SQLite databases
├── memory_sessions/               # Session data
└── voices/                        # Piper voice models
```

---

## ⚙️ Configuration

### Environment Variables

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

All settings can be configured via:
- Environment variables
- `.jarvis_config.json` (JSON format)
- Command-line arguments
- Interactive CLI commands

---

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs via Issues
- Suggest features
- Submit Pull Requests
- Create plugins

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 📞 Support

- 📖 Check the [Documentation](docs/)
- 🐛 Report issues on [GitHub Issues](https://github.com/PIXELQUADRO07/Jarvis-Core/issues)
- 💬 Start a discussion

---

## 🙏 Acknowledgments

- Built with [Ollama](https://ollama.ai)
- API powered by [FastAPI](https://fastapi.tiangolo.com/)
- Voice synthesis using [Piper TTS](https://github.com/rhasspy/piper)

---

<div align="center">

**⭐ If you find this project helpful, please consider starring it! ⭐**

Made with ❤️ by [PIXELQUADRO07](https://github.com/PIXELQUADRO07)

</div>
