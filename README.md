# JARVIS AI — Core

A local AI assistant with a layered architecture.

<img width="1175" height="833" alt="Screenshot_20260430_143512" src="https://github.com/user-attachments/assets/1eaeb15c-f3fa-42d5-b8fe-887f4d60d986" />

## Directory Structure

```
jarvis-core/
├── main.py                        ← entry point
├── requirements.txt
├── memory.json                    ← persistent memory (auto-generated)
│
├── core/
│   ├── llm.py                     ← Ollama streaming
│   ├── memory.py                  ← conversation persistence
│   ├── state.py                   ← thread-safe global state
│   └── commands.py                ← slash command routing
│
├── controller/
│   └── jarvis_controller.py       ← single UI ↔ core bridge
│
└── ui/
    └── cli.py                     ← rendering only, zero logic
```

## Setup

```bash
# 1. Clone the repository
git clone https://github.com/PIXELQUADRO07/Jarvis-Core

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Download Ollama
# ARCH LINUX:
sudo pacman -S ollama

# KALI LINUX or other distros:
sudo apt install ollama

# 4. Make sure Ollama is running
ollama serve

# 5. Download the model (if not already installed)
ollama pull qwen2.5:7b

# 6. Start JARVIS
python main.py
```

## Changing the Model

The model can be changed in several ways:

### 1. Modify `config.py`
Change the default value in `config.py`:
```python
model: str = "qwen2.5:7b"  # or any installed model
```

### 2. Use environment variable
```bash
dexport JARVIS_MODEL="qwen2.5:7b"
python main.py
```

### 3. Create `jarvis_config.json` file
```json
{
  "model": "qwen2.5:7b"
}
```

## Available Commands

| Command   | Action                          |
|-----------|--------------------------------|
| `/help`   | Show available commands        |
| `/clear`  | Clear the screen               |
| `/reset`  | Reset memory                   |
| `/status` | Ollama status + memory info    |
| `/config` | Show current configuration     |
| `/voice`  | Control text-to-speech         |
| `/exit`   | Exit application               |

## System Commands

JARVIS also supports natural language commands for system management:

### 📊 Monitoring (no root required)
- **"how much RAM do you have?"** → Show memory usage
- **"disk space"** → Show disk usage
- **"uptime"** → System uptime
- **"show network"** → Network interface information
- **"running processes"** → List active processes
- **"CPU temperature"** → System temperatures (if available)
- **"battery status"** → Battery level (if laptop)

### 🔧 System Management (requires root)
- **"update system"** → Update packages
- **"install firefox"** → Install package
- **"remove firefox"** → Remove package
- **"service start apache2"** → Manage systemd services
- **"hostname new-name"** → Change hostname
- **"show logs"** → Recent system logs

### 🌐 Applications
- **"open firefox"** → Launch Firefox
- **"firefox search python"** → Search on Google with Firefox
- **"open gedit"** → Open any application

### 💻 System Info
- **"what distro is this?"** → Show Linux distribution
- **"how many CPUs do you have?"** → Number of logical processors

## Text-to-Speech

JARVIS supports text-to-speech synthesis via Piper TTS to make responses audible.

### Installation
```bash
# Install Piper
pip install piper-tts

# Download Italian voice model (already included)
# Models are located in voices/
```

### Voice Commands
```
/voice on      → Enable text-to-speech
/voice off     → Disable text-to-speech  
/voice status  → Show voice status
/voice test    → Test text-to-speech
```

### Configuration
```json
{
  "enable_voice": true,
  "voice_model": "voices/it_IT-riccardo-x_low.onnx",
  "voice_volume": 0.8
}
```

### Environment Variables
```bash
export JARVIS_VOICE_ENABLED="true"
export JARVIS_VOICE_MODEL="voices/it_IT-riccardo-x_low.onnx"
export JARVIS_VOICE_VOLUME="0.8"
```

## Architecture

```
UI (cli.py)
  ↓ raw input
Controller (jarvis_controller.py)
  ↓ UIEvent generator
  ├── /command → core/commands → UIEvent(action)
  └── text    → core/llm     → UIEvent(ai_chunk) × N → UIEvent(ai_done)
UI
  ↓ renders each UIEvent
```

The UI never knows about Ollama, memory, or commands.
The core never knows about Rich or prompt_toolkit.