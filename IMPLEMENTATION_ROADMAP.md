# JARVIS v3.0 — Piano di Implementazione

**Data creazione:** 30 Aprile 2026  
**Status:** In pianificazione  
**Target:** Phase-based implementation con quick wins prima

---

## 📊 Mappa Dipendenze

```
QUICK WINS (no dependencies)
├─ Token counter
├─ /model switch
├─ Render Markdown
└─ Esporta chat

PRIORITÀ 1 - CORE ROBUSTEZZA (no dependencies)
├─ Retry + circuit breaker (indipendente)
├─ Streaming live UI (dipende da: CLI refactor)
└─ Sessioni multiple (dipende da: Memory upgrade)

PRIORITÀ 2 - UX CLI (dipende da: Prompt-toolkit upgrade)
├─ Autocompletamento /cmd
├─ Input multiriga (Shift+Enter)
├─ Cronologia persistente (dipende da: Session storage)
└─ Navigation ↑↓ tra sessioni

PRIORITÀ 3 - VOCE (parzialmente implementata)
├─ Wake word detection (indipendente, nuovo modulo)
├─ Interruzione voce (modifica voice_engine.py)
└─ /voice model [nome] (indipendente)

PRIORITÀ 4 - TOOL SYSTEM (modulo plugin)
├─ Tool system modulare (base architecture)
├─ Plugin loader da cartella
├─ Web search tool (DuckDuckGo/SearXNG)
└─ File system tool

PRIORITÀ 5 - MEMORIA AVANZATA (database upgrade)
├─ ChromaDB setup + embeddings
├─ Riassunto automatico compressione
└─ Profilo utente persistente

PRIORITÀ 6 - ARCHITETTURA (testing + config)
├─ Pydantic models per config
├─ JSON structured logging
├─ pytest test suite
└─ Log rotation + search

```

---

## 🚀 FASE 0 — QUICK WINS (2-3 ore)
Impatto immediato, zero dipendenze. **Start here!**

| # | Feature | File | Effort | Est. Time | Blockers |
|---|---------|------|--------|-----------|----------|
| 1 | Token counter | core/token_counter.py | 🟢 Low | 20m | 0 |
| 2 | /model switch | core/commands.py | 🟢 Low | 15m | 0 |
| 3 | Render Markdown | ui/cli.py | 🟢 Low | 20m | 0 |
| 4 | Esporta chat /export | core/commands.py | 🟡 Medium | 30m | Memory loading |

### Checklist FASE 0
- [ ] Token counter implementato
- [ ] /model switch funzionante (switch Ollama model live)
- [ ] Markdown rendering in rich panels
- [ ] /export crea file .md con timestamp

---

## 🛡️ FASE 1 — ROBUSTEZZA CORE (4-6 ore)
Rendi il core robusto alle disconnessioni e migliora streaming UI.

| # | Feature | File | Effort | Est. Time | Dipendenze |
|---|---------|------|--------|-----------|------------|
| 1 | Retry + circuit breaker | core/retry_handler.py | 🟡 Medium | 1.5h | 0 |
| 2 | Streaming live in pannello | ui/cli.py | 🟡 Medium | 1h | Retry handler |
| 3 | Sessioni multiple | core/session_manager.py | 🟡 Medium | 1.5h | Memory upgrade |
| 4 | Memoria per conversazione | core/memory.py | 🟡 Medium | 1h | 0 |

### Dettagli Implementazione

**1.1 Retry + Circuit Breaker** (`core/retry_handler.py`)
```python
class CircuitBreaker:
    def __init__(self, failure_threshold=3, timeout=60):
        self.failures = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED | OPEN | HALF_OPEN
    
    def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
            else:
                raise CircuitBreakerOpen()
        
        try:
            result = func(*args, **kwargs)
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise

class RetryHandler:
    def __init__(self, max_retries=3, backoff=1.5):
        self.max_retries = max_retries
        self.backoff = backoff
    
    def execute(self, func, *args, **kwargs):
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except ConnectionError:
                if attempt == self.max_retries - 1:
                    raise
                wait_time = self.backoff ** attempt
                time.sleep(wait_time)
```

**1.2 Streaming Live UI**
- Modifica `stream_llm()` per yield tokens più granulari
- Crea modalità rendering "live typing" con cursor blinking
- Usa rich.Live() con aggiornamento real-time
- Buffer di 50ms tra chunks per batching (UX + performante)

**1.3 Sessioni Multiple**
```
core/session_manager.py:
  - SessionManager singleton
  - Switch tra sessioni: /session [name]
  - Auto-load memoria per sessione
  - Persistent storage in memory_sessions/
```

**1.4 Memoria per Conversazione**
- Separata da user message history (memory.py già ha user/assistant split)
- Aggiungi `session_context: str` a ogni messaggio
- Filtra memoria per sessione attuale

### Checklist FASE 1
- [ ] CircuitBreaker + RetryHandler implementati
- [ ] Ollama offline → 3 tentativi con backoff
- [ ] Streaming live in CLI (vedi testo che arriva in tempo reale)
- [ ] /session list | /session new [name] | /session switch [name]
- [ ] Memoria sessione-specifica funzionante

---

## 💬 FASE 2 — UX & CLI ENHANCEMENT (5-7 ore)
Migliora l'esperienza di input/output della CLI.

| # | Feature | File | Effort | Est. Time | Dipendenze |
|---|---------|------|--------|-----------|------------|
| 1 | Input multiriga (Shift+Enter) | ui/cli.py | 🟡 Medium | 1h | Prompt-toolkit upgrade |
| 2 | Autocompletamento /cmd | ui/cli.py | 🟡 Medium | 1.5h | 0 |
| 3 | Cronologia persistente | core/history.py | 🟡 Medium | 1h | 0 |
| 4 | Navigation ↑↓ tra sessioni | ui/cli.py | 🟢 Low | 30m | Sessioni multiple |

### Dettagli Implementazione

**2.1 Input Multiriga**
```python
# ui/cli.py - Upgrade prompt_toolkit usage
session = PromptSession(
    multiline=True,
    completer=CommandCompleter(),
    style=PROMPT_STYLE,
    key_bindings=custom_keybindings()
)
# Shift+Enter → newline, Enter → send
```

**2.2 Autocompletamento**
```python
from prompt_toolkit.completion import Completer, Completion

class CommandCompleter(Completer):
    def get_completions(self, document, complete_event):
        # /m → /memory, /mo → /model, /ex → /export
        # Tools: /weather → auto-complete città
        # /voice → auto-complete modelli vocali
```

**2.3 Cronologia Persistente**
```
core/history.py:
  - File: history.json (rotate ogni 10K righe)
  - Format: [{"timestamp": ISO8601, "input": "", "output": "", "session": ""}]
  - Commands: /history [n] - ultime n righe
  - /history search [query] - grep history
```

**2.4 Navigation Sessioni**
```
ui/cli.py:
  - Alt+↑ / Alt+↓ → switch tra ultime 5 sessioni
  - /session status → mostra sessione corrente + ultime 3
  - Status bar: "Sessione: [main] (5 msg)" 
```

### Checklist FASE 2
- [ ] Shift+Enter funziona per newline
- [ ] Tab-completion per /cmd
- [ ] history.json generato + searchable
- [ ] Alt+↑/↓ naviga sessioni precedenti

---

## 🎤 FASE 3 — VOICE ENHANCEMENT (6-8 ore)
Migliora il sistema vocale con wake words e controllo.

| # | Feature | File | Effort | Est. Time | Dipendenze |
|---|---------|------|--------|-----------|------------|
| 1 | Wake word detection | core/wake_word.py | 🔴 High | 2h | pyannote-audio o simile |
| 2 | STT (Speech-to-Text) | core/stt.py | 🔴 High | 2h | openai-whisper o simile |
| 3 | Interruzione voce | core/voice_engine.py | 🟡 Medium | 1h | 0 |
| 4 | /voice model [nome] | core/commands.py | 🟢 Low | 30m | 0 |

### Dettagli Implementazione

**3.1 Wake Word** (optional: Porcupine o PocketSphinx)
```python
# core/wake_word.py
class WakeWordDetector:
    def __init__(self, keyword="jarvis", sensitivity=0.5):
        # Usa PocketSphinx or PyAudio + microphone listener
        pass
    
    def listen_for_wake_word(self, timeout=30):
        # Blocking: ascolta fino a "Ehi JARVIS"
        pass

# Opzione semplice: riconoscimento tramite Ollama + STT
# "Ehi JARVIS" detected → abilita STT
```

**3.2 STT** (openai-whisper)
```python
# core/stt.py
import whisper

class SpeechToText:
    def __init__(self, model="base", language="it"):
        self.model = whisper.load_model(model)
    
    def transcribe_audio(self, audio_file):
        result = self.model.transcribe(audio_file, language=self.language)
        return result["text"]
```

**3.3 Interruzione Voce**
- Flag in VoiceEngine: `interrupt_requested`
- Quando STT detect "stop" o "basta" → set flag
- TTS check flag a ogni chunk, interrompi se true

**3.4 /voice model**
```
/voice model list        → mostra modelli disponibili
/voice model set [name]  → cambia modello Piper
/voice status            → mostra modello corrente + velocità
```

### Checklist FASE 3
- [ ] Microfono init (pyaudio + capture stream)
- [ ] Wake word detector funzionante
- [ ] STT transcription (Whisper)
- [ ] /voice model [nome] funziona
- [ ] Interruzione TTS con flag

---

## 🔧 FASE 4 — TOOL SYSTEM MODULARE (5-6 ore)
Crea sistema plugin per strumenti.

| # | Feature | File | Effort | Est. Time | Dipendenze |
|---|---------|------|--------|-----------|------------|
| 1 | Tool system base | core/tools/base.py | 🟡 Medium | 1h | 0 |
| 2 | Plugin loader | core/tools/plugin_loader.py | 🟡 Medium | 1h | 0 |
| 3 | Web search tool | core/tools/web_search.py | 🟡 Medium | 1.5h | 0 |
| 4 | File system tool | core/tools/filesystem.py | 🟡 Medium | 1h | 0 |

### Dettagli Implementazione

**4.1 Tool Base Interface**
```python
# core/tools/base.py
from abc import ABC, abstractmethod

class Tool(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Univoco identificatore tool"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Descrizione breve per LLM"""
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> str:
        """Esegui tool con parametri"""
        pass
    
    @property
    def schema(self) -> dict:
        """JSON schema dei parametri"""
        pass
```

**4.2 Plugin Loader**
```python
# core/tools/plugin_loader.py
import importlib.util
from pathlib import Path

class PluginLoader:
    def __init__(self, plugin_dir="core/tools/plugins"):
        self.plugin_dir = Path(plugin_dir)
        self.tools = {}
    
    def load_plugins(self):
        for plugin_file in self.plugin_dir.glob("*.py"):
            if plugin_file.name.startswith("_"):
                continue
            spec = importlib.util.spec_from_file_location(
                plugin_file.stem, plugin_file
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Assume: module.TOOL è istanza di Tool
            if hasattr(module, "TOOL"):
                self.tools[module.TOOL.name] = module.TOOL
```

**4.3 Web Search Tool** (DuckDuckGo)
```python
# core/tools/web_search.py
from duckduckgo_search import DDGS

class WebSearchTool(Tool):
    @property
    def name(self) -> str:
        return "web_search"
    
    def execute(self, query: str, max_results: int = 3) -> str:
        results = DDGS().text(query, max_results=max_results)
        return "\n".join([
            f"- {r['title']}: {r['body'][:200]}"
            for r in results
        ])
```

**4.4 Filesystem Tool**
```python
# core/tools/filesystem.py
import os
from pathlib import Path

class FilesystemTool(Tool):
    def __init__(self, base_dir="~/jarvis_files"):
        self.base_dir = Path(base_dir).expanduser()
        self.base_dir.mkdir(exist_ok=True)
    
    def execute(self, action: str, path: str, content: str = "") -> str:
        # action: "read", "write", "list", "delete"
        # Validazione: path must be within base_dir
        full_path = (self.base_dir / path).resolve()
        if not str(full_path).startswith(str(self.base_dir)):
            raise PermissionError("Path outside base_dir")
        
        if action == "read":
            return full_path.read_text()
        elif action == "write":
            full_path.write_text(content)
            return f"Scritto: {path}"
        elif action == "list":
            return "\n".join([f.name for f in full_path.iterdir()])
```

### Checklist FASE 4
- [ ] Tool base class + interface definiti
- [ ] PluginLoader funzionante
- [ ] Web search tool integrato
- [ ] Filesystem tool con validazione
- [ ] tools/router.py aggiornato per nuovo sistema

---

## 🧠 FASE 5 — MEMORIA AVANZATA (4-5 ore)
Upgrade a memoria vettoriale e RAG locale.

| # | Feature | File | Effort | Est. Time | Dipendenze |
|---|---------|------|--------|-----------|------------|
| 1 | ChromaDB setup | core/vector_db.py | 🟡 Medium | 1.5h | 0 |
| 2 | Embedding generator | core/embeddings.py | 🟡 Medium | 1h | 0 |
| 3 | Riassunto automatico | core/summarizer.py | 🟡 Medium | 1h | 0 |
| 4 | Profilo utente | core/user_profile.py | 🟢 Low | 30m | 0 |

### Dettagli Implementazione

**5.1 ChromaDB Integration**
```python
# core/vector_db.py
import chromadb

class VectorMemory:
    def __init__(self, persist_dir="./chroma_db"):
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(
            name="jarvis_memory",
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_message(self, text: str, session: str, role: str):
        # Genera embedding automaticamente
        self.collection.add(
            ids=[str(uuid.uuid4())],
            documents=[text],
            metadatas=[{"session": session, "role": role, "timestamp": time.time()}]
        )
    
    def search(self, query: str, n_results: int = 5) -> list:
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results["documents"][0]
```

**5.2 Embedding Generator**
```python
# core/embeddings.py
from sentence_transformers import SentenceTransformer

class EmbeddingGenerator:
    def __init__(self, model="distiluse-base-multilingual-cased-v2"):
        self.model = SentenceTransformer(model)
    
    def encode(self, text: str) -> list:
        return self.model.encode(text).tolist()
```

**5.3 Riassunto Automatico**
```python
# core/summarizer.py
class ConversationSummarizer:
    def __init__(self, max_messages=100, compress_above=200):
        self.max_messages = max_messages
        self.compress_above = compress_above
    
    def should_compress(self, memory: list) -> bool:
        return len(memory) > self.compress_above
    
    def compress(self, messages: list) -> str:
        # Usa LLM per riassumere ultimi 50 messaggi
        text_to_summarize = "\n".join([
            f"{m['role']}: {m['content']}"
            for m in messages[-50:]
        ])
        # Call LLM con "Riassumi brevemente questi messaggi in 1 paragrafo:"
        # Salva riassunto e rimuovi messaggi vecchi
```

**5.4 Profilo Utente**
```python
# core/user_profile.py
class UserProfile:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.preferences = {}  # tema, lingua, voice speed, etc.
        self.settings_file = Path(f"./profiles/{user_id}.json")
    
    def update_preference(self, key: str, value):
        self.preferences[key] = value
        self.save()
    
    def get_system_prompt_addition(self) -> str:
        # Personalizza system prompt con preferenze utente
        return f"Preferenze utente: {json.dumps(self.preferences)}"
```

### Checklist FASE 5
- [ ] ChromaDB setup + persistenza
- [ ] Embedding generator funzionante
- [ ] Compressione memoria automatica
- [ ] Profilo utente persistente

---

## 🏗️ FASE 6 — ARCHITETTURA & TESTING (5-6 ore)
Solidifica config, logging strutturato, tests.

| # | Feature | File | Effort | Est. Time | Dipendenze |
|---|---------|------|--------|-----------|------------|
| 1 | Pydantic config models | config.py | 🟡 Medium | 1h | 0 |
| 2 | JSON structured logging | logger.py | 🟡 Medium | 1h | 0 |
| 3 | pytest test suite | tests/ | 🔴 High | 2h | 0 |
| 4 | Log rotation + search | logger.py | 🟡 Medium | 1h | 0 |

### Dettagli Implementazione

**6.1 Pydantic Config**
```python
# config.py (refactor)
from pydantic import BaseModel, Field, validator

class OllamaConfig(BaseModel):
    url: str = Field(default="http://localhost:11434/api/chat")
    model: str = Field(default="mistral")
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)

class VoiceConfig(BaseModel):
    enabled: bool = True
    model: str = "it_IT-riccardo-x_low"
    speed: float = 1.0

class JarvisConfig(BaseModel):
    ollama: OllamaConfig
    voice: VoiceConfig
    memory_max_messages: int = 100
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Singleton
_config = None
def get_config() -> JarvisConfig:
    global _config
    if _config is None:
        _config = JarvisConfig()
    return _config
```

**6.2 Structured Logging**
```python
# logger.py (upgrade)
import logging
import json
from pythonjsonlogger import jsonlogger

class StructuredFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record["timestamp"] = datetime.now().isoformat()
        log_record["level"] = record.levelname
        log_record["module"] = record.module

# File handlers con JSON
json_handler = logging.FileHandler("logs/jarvis.json")
json_handler.setFormatter(StructuredFormatter())
```

**6.3 Test Suite** (`tests/`)
```python
# tests/test_retry_handler.py
def test_circuit_breaker_open_after_failures():
    cb = CircuitBreaker(failure_threshold=2)
    
    def failing_func():
        raise ConnectionError()
    
    with pytest.raises(ConnectionError):
        cb.call(failing_func)
    with pytest.raises(ConnectionError):
        cb.call(failing_func)
    
    with pytest.raises(CircuitBreakerOpen):
        cb.call(failing_func)

# tests/test_llm.py
def test_stream_llm_with_retry():
    # Mock Ollama connection
    # Verify retry logic
    pass

# tests/test_tools.py
def test_plugin_loader():
    loader = PluginLoader("tests/mock_plugins")
    loader.load_plugins()
    assert "web_search" in loader.tools
```

**6.4 Log Rotation**
```python
# logger.py
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    "logs/jarvis.log",
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
```

### Checklist FASE 6
- [ ] Pydantic config models funzionanti
- [ ] JSON structured logging configurato
- [ ] pytest suite con 15+ test
- [ ] Log rotation setup (10MB file, 5 backup)
- [ ] Log search utility in CLI

---

## 📈 Timeline Totale

| Fase | Componenti | Effort | Tempo Stimato | Dipendenze |
|------|-----------|--------|---------------|-----------|
| 0 | Quick wins | 🟢 Low | **2-3h** | None |
| 1 | Core robustezza | 🟡 Medium | **4-6h** | Phase 0 |
| 2 | UX CLI | 🟡 Medium | **5-7h** | Phase 1 |
| 3 | Voice | 🔴 High | **6-8h** | External deps |
| 4 | Tool system | 🟡 Medium | **5-6h** | Phase 2 |
| 5 | Memoria avanzata | 🟡 Medium | **4-5h** | Phase 3 |
| 6 | Architettura | 🟡 Medium | **5-6h** | All |
| **TOTALE** | | | **32-45h** | Phases 0→6 |

**Raccomandazione:** Start con Phase 0 (quick wins) → Phase 1 (core) → scegli feature per
 priorità business.

---

## 🎯 Quick Start per Implementazione

### Step 1: Setup Environment
```bash
cd /home/gaetal/Desktop/jarvis-core-fixed

# Upgrade requirements.txt con nuove dipendenze
pip install pydantic duckduckgo-search chromadb sentence-transformers pytest
```

### Step 2: Create Feature Branch
```bash
git checkout -b feature/phase-0-quick-wins
```

### Step 3: Implement Phase 0
Vedi checklist sotto.

---

## 📝 Checklist Complessiva

### FASE 0 - QUICK WINS
- [ ] Token counter (core/token_counter.py)
- [ ] /model switch (core/commands.py)
- [ ] Markdown rendering (ui/cli.py)
- [ ] /export chat (core/commands.py)

### FASE 1 - CORE ROBUSTEZZA
- [ ] Retry + CircuitBreaker (core/retry_handler.py)
- [ ] Streaming live UI (ui/cli.py)
- [ ] Session manager (core/session_manager.py)
- [ ] Session-aware memory (core/memory.py)

### FASE 2 - UX CLI
- [ ] Multiline input (ui/cli.py)
- [ ] Command autocomplete (ui/cli.py)
- [ ] Persistent history (core/history.py)
- [ ] Session navigation (ui/cli.py)

### FASE 3 - VOICE
- [ ] Wake word detector (core/wake_word.py)
- [ ] STT integration (core/stt.py)
- [ ] Voice interruption (core/voice_engine.py)
- [ ] /voice model command (core/commands.py)

### FASE 4 - TOOL SYSTEM
- [ ] Tool base class (core/tools/base.py)
- [ ] Plugin loader (core/tools/plugin_loader.py)
- [ ] Web search tool (core/tools/web_search.py)
- [ ] Filesystem tool (core/tools/filesystem.py)

### FASE 5 - MEMORIA AVANZATA
- [ ] ChromaDB setup (core/vector_db.py)
- [ ] Embeddings (core/embeddings.py)
- [ ] Auto summarizer (core/summarizer.py)
- [ ] User profile (core/user_profile.py)

### FASE 6 - ARCHITETTURA
- [ ] Pydantic config (config.py refactor)
- [ ] JSON logging (logger.py upgrade)
- [ ] pytest suite (tests/)
- [ ] Log rotation (logger.py)

---

## 🔗 Dipendenze Esterne Richieste

```
# requirements.txt additions

# FASE 0
# (nessuna nuova dipendenza)

# FASE 1
# (nessuna nuova dipendenza)

# FASE 2
# (upgrade prompt_toolkit già presente)

# FASE 3
openai-whisper==20231117
pyaudio==0.2.13
# (optional: pyannote-audio per wake word)

# FASE 4
duckduckgo-search==3.9.2

# FASE 5
chromadb==0.4.3
sentence-transformers==2.2.2

# FASE 6
pydantic==2.5.0
pytest==7.4.3
python-json-logger==2.0.7
```

---

## 💡 Note Implementazione

1. **Testing iterativo:** After every phase, manual testing + logs review
2. **Git commits:** Atomic commits per feature (non mega-commit)
3. **Backward compatibility:** Nuove feature non rompono CLI/voice
4. **Documentation:** Update QUICKSTART.md dopo ogni phase
5. **Performance:** Profile LLM streaming + tool router
6. **Error recovery:** Sempre fallback graceful

---

## 📞 Support

- Consulta `IMPROVEMENTS.md` per context v2.0
- Vedi `QUICKSTART.md` per user guide current
- Logs in `logs/` directory - check prima di debug
- Memory in `memory.json` + `memory_sessions/` after FASE 1

**Created:** 30 Apr 2026  
**Next review:** After FASE 0 completion
