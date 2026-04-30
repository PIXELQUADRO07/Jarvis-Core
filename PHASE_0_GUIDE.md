# JARVIS Phase 0 — Quick Wins Implementation Guide

**Duration:** 2-3 hours  
**Start date:** 30 Apr 2026  
**Target:** Deploy quick-win features with immediate UX impact

---

## Overview

Four quick-win features requiring **zero dependencies** and **zero integration complexity**:

1. **Token Counter** - Show LLM token usage
2. **Model Switch** - `/model switch` command for live model changes
3. **Markdown Rendering** - Rich markdown panels in responses
4. **Chat Export** - `/export` command to save chat as .md file

---

## Feature 1: Token Counter

### Scope
- Implement simple token counter using approximation formula
- Display tokens used in LLM response
- Store stats in response metadata

### Implementation

**File:** `core/token_counter.py` (NEW)

```python
#!/usr/bin/env python3
"""
Token counter for Ollama LLM requests/responses.
Estimation formula: average 1.3 characters = 1 token (varies by model).
For precise counting, would need Ollama token count endpoint.
"""

class TokenCounter:
    """Simple token estimation for Italian/English text."""
    
    # Empirical ratios for common models
    TOKEN_RATIOS = {
        "mistral": 1.33,      # ~1 token per 1.33 chars
        "neural-chat": 1.30,
        "dolphin": 1.35,
        "openhermes": 1.32,
    }
    DEFAULT_RATIO = 1.33
    
    @staticmethod
    def estimate_tokens(text: str, model: str = "mistral") -> int:
        """Estimate token count from text."""
        ratio = TokenCounter.TOKEN_RATIOS.get(model, TokenCounter.DEFAULT_RATIO)
        return max(1, int(len(text) / ratio))
    
    @staticmethod
    def format_usage(prompt_tokens: int, completion_tokens: int) -> str:
        """Format token usage for display."""
        total = prompt_tokens + completion_tokens
        return f"📊 Tokens: {prompt_tokens} prompt + {completion_tokens} completion = {total} total"


# Unit tests
if __name__ == "__main__":
    tc = TokenCounter()
    
    text = "Ciao, come stai? Come posso aiutarti oggi con l'assistente JARVIS?"
    tokens = tc.estimate_tokens(text)
    print(f"Text: {text}")
    print(f"Estimated tokens: {tokens}")
    print(f"Ratio: {len(text)} / {tokens} ≈ {len(text)/tokens:.2f} chars per token")
    
    usage = tc.format_usage(15, 42)
    print(f"Usage: {usage}")
```

**Integration Points:**

1. **In `core/llm.py`** - Track tokens after streaming:
```python
from core.token_counter import TokenCounter

def stream_llm(text: str) -> Generator[str, None, None]:
    config = get_config()
    history = load_memory()
    
    prompt_tokens = TokenCounter.estimate_tokens(
        text, config.model
    )
    
    response_text = ""
    for chunk in # ... streaming ...
        response_text += chunk
        yield chunk
    
    completion_tokens = TokenCounter.estimate_tokens(
        response_text, config.model
    )
    
    # Return metadata (can be used in CLI)
    return {
        "text": response_text,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens
    }
```

2. **In `ui/cli.py`** - Display after response:
```python
# After jarvis response rendered:
token_info = TokenCounter.format_usage(
    response_metadata["prompt_tokens"],
    response_metadata["completion_tokens"]
)
console.print(Text(token_info, style="dim white"))
```

### Testing
```bash
python -c "
from core.token_counter import TokenCounter
tc = TokenCounter()
print(tc.format_usage(15, 42))
print(f'Tokens for \"hello\": {tc.estimate_tokens(\"hello\")}')
"
```

---

## Feature 2: Model Switch (/model switch)

### Scope
- Add `/model list` - list available models from Ollama
- Add `/model set [name]` - switch active model live
- Update config in-memory (NOT persistent between sessions unless added to jarvis_config.json)

### Implementation

**Modify `core/commands.py`:**

Add new command handler:
```python
def handle_model_command(args: list) -> str:
    """
    Handle /model subcommands:
    - /model list           → list available models
    - /model set [name]     → switch to model
    - /model current        → show current model
    """
    config = get_config()
    
    if not args:
        return "Usage: /model list | /model set [name] | /model current"
    
    subcommand = args[0].lower()
    
    if subcommand == "list":
        # Query Ollama for available models
        try:
            models = get_available_models()  # see below
            return "📦 Available Models:\n" + "\n".join(f"  • {m}" for m in models)
        except Exception as e:
            return f"❌ Error listing models: {e}"
    
    elif subcommand == "set" and len(args) > 1:
        model_name = args[1]
        # Verify model exists (optional)
        try:
            models = get_available_models()
            if model_name not in models:
                return f"❌ Model '{model_name}' not found. Available: {', '.join(models)}"
        except:
            pass  # If can't verify, try anyway
        
        config.model = model_name
        info(f"Model switched to {model_name}")
        return f"✅ Model switched to: {model_name}"
    
    elif subcommand == "current":
        return f"📌 Current model: {config.model}"
    
    else:
        return "Unknown subcommand. Use: list | set | current"


def get_available_models() -> list:
    """Query Ollama API for available models."""
    import urllib.request
    import json
    from config import get_config
    
    config = get_config()
    url = config.ollama_url.replace("/api/chat", "/api/tags")
    
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            models = [m["name"].split(":")[0] for m in data.get("models", [])]
            return sorted(set(models))
    except Exception as e:
        error(f"Failed to list models: {e}")
        raise
```

**Update `core/commands.py` command registry:**
```python
COMMANDS = {
    "help":    ("Mostra questa lista di comandi", handle_help),
    "tools":   ("Lista tool disponibili", lambda _: router.list_tools()),
    "memory":  ("Statistiche memoria", handle_memory),
    "clear":   ("Cancella memoria", handle_clear),
    "history": ("Ultimi messaggi", handle_history),
    "status":  ("Status sistema", handle_status),
    "config":  ("Mostra configurazione", handle_config),
    "model":   ("Switch modello: /model list|set|current", handle_model_command),
    "exit":    ("Esci da JARVIS", lambda _: "EXITCODE"),
}
```

### Testing
```bash
# Terminal 1: Start Ollama with models
ollama serve

# Terminal 2:
python main.py
# In CLI:
/model list
/model set neural-chat
/model current
```

---

## Feature 3: Markdown Rendering

### Scope
- Parse markdown in LLM responses
- Render with rich.Markdown (bold, italic, code blocks, lists, etc.)
- Fallback to plain text if no markdown detected

### Implementation

**Modify `ui/cli.py`:**

Replace simple `render_jarvis_panel()` with markdown-aware version:

```python
from rich.markdown import Markdown

def render_jarvis_panel(text: str):
    """Risposta di JARVIS con markdown support."""
    console.print(Panel(
        Markdown(text, style=BRIGHT_RED) 
        if _has_markdown(text) 
        else Text(text, style=BRIGHT_RED),
        border_style=RED,
        expand=False,
        padding=(1, 2)
    ))

def _has_markdown(text: str) -> bool:
    """Quick check if text contains markdown patterns."""
    markdown_patterns = [
        '**', '__',           # bold
        '*', '_',             # italic
        '`', '```',           # code
        '#', '##', '###',     # headers
        '- ', '* ',           # lists
        '> ',                 # blockquote
        '[', ']()',           # links
    ]
    return any(pattern in text for pattern in markdown_patterns)
```

**Test:**
```python
# In JARVIS CLI:
/help   # Should render # Help as header

# Ask something that generates formatted response:
> Dammi 3 motivi per usare AI, in lista
# Should show:
# - Motivo 1: ...
# - Motivo 2: ...
# - Motivo 3: ...
```

---

## Feature 4: Chat Export (/export)

### Scope
- `/export` - export current session to timestamped .md file
- Save to `exports/` directory
- Include metadata (date, model, token usage)
- Format: readable markdown with clear conversation flow

### Implementation

**File:** `core/export.py` (NEW)

```python
#!/usr/bin/env python3
"""
Chat export to markdown format.
"""

import json
from pathlib import Path
from datetime import datetime

class ChatExporter:
    """Export memory to markdown file."""
    
    def __init__(self, export_dir: str = "exports"):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(exist_ok=True)
    
    def export_memory(self, memory_data: list, filename: str = None) -> str:
        """
        Export memory list to .md file.
        
        Args:
            memory_data: list of {"role": "user"|"assistant", "content": "..."}
            filename: custom filename (no extension), default: jarvis_chat_TIMESTAMP
        
        Returns:
            Path to exported file
        """
        if not memory_data:
            return "❌ Memory is empty, nothing to export"
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"jarvis_chat_{timestamp}"
        
        filepath = self.export_dir / f"{filename}.md"
        
        # Build markdown content
        lines = [
            "# JARVIS Chat Export",
            f"**Exported:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
            "---",
            ""
        ]
        
        for message in memory_data:
            role = message["role"]
            content = message["content"]
            
            if role == "user":
                lines.append("## 👤 User")
                lines.append(content)
            else:
                lines.append("## 🤖 JARVIS")
                lines.append(content)
            
            lines.append("")
        
        # Add footer
        lines.extend([
            "---",
            f"*Total messages: {len(memory_data)}*",
            f"*Generated by JARVIS v3.0*"
        ])
        
        content = "\n".join(lines)
        filepath.write_text(content, encoding="utf-8")
        
        return f"✅ Chat exported to: {filepath}"


# Test
if __name__ == "__main__":
    exporter = ChatExporter()
    test_memory = [
        {"role": "user", "content": "Ciao!"},
        {"role": "assistant", "content": "Ciao! Come stai?"},
        {"role": "user", "content": "Bene, grazie!"},
    ]
    print(exporter.export_memory(test_memory, "test_export"))
```

**Integrate in `core/commands.py`:**

```python
from core.export import ChatExporter

exporter = ChatExporter()  # Singleton

def handle_export_command(args: list) -> str:
    """
    Handle /export command.
    Usage: 
      /export                    → export with auto filename
      /export my_conversation    → export with custom name
    """
    filename = args[0] if args else None
    
    try:
        memory = load_memory()
        if not memory:
            return "❌ Niente da esportare (memoria vuota)"
        
        result = exporter.export_memory(memory, filename)
        return result
    except Exception as e:
        return f"❌ Export failed: {e}"
```

**Add to command registry:**
```python
COMMANDS = {
    # ... existing commands ...
    "export": ("Esporta chat in .md", handle_export_command),
}
```

### Testing
```bash
python main.py
# In JARVIS:
> Ciao!
> Come stai?
/export
# Check: ls exports/ → should see jarvis_chat_YYYYMMDD_HHMMSS.md
```

---

## 📋 Phase 0 Implementation Checklist

### Step 1: Create Token Counter
- [ ] Create `core/token_counter.py`
- [ ] Implement TokenCounter class
- [ ] Test with sample text
- [ ] Update requirements.txt (if needed - none required)

### Step 2: Add Model Switch
- [ ] Create `get_available_models()` in `core/commands.py`
- [ ] Create `handle_model_command()` in `core/commands.py`
- [ ] Add "model" to COMMANDS registry
- [ ] Test `/model list` | `/model set` | `/model current`

### Step 3: Add Markdown Rendering
- [ ] Create `_has_markdown()` in `ui/cli.py`
- [ ] Import `Markdown` from rich
- [ ] Update `render_jarvis_panel()` to use Markdown
- [ ] Test with formatted response

### Step 4: Add Chat Export
- [ ] Create `core/export.py` with ChatExporter class
- [ ] Create `handle_export_command()` in `core/commands.py`
- [ ] Add "export" to COMMANDS registry
- [ ] Create `exports/` directory (auto-created by exporter)
- [ ] Test `/export` creates .md file

### Step 5: Testing
- [ ] Manual CLI testing all 4 features
- [ ] Check logs for errors
- [ ] Verify files created (exports/*.md)
- [ ] Test edge cases (empty memory, invalid model, etc.)

### Step 6: Documentation
- [ ] Update `QUICKSTART.md` with new commands
- [ ] Add `/token` display to status info (optional)

---

## 🎬 Quick Start Script

```bash
#!/bin/bash
# Run this to prepare Phase 0 implementation

cd /home/gaetal/Desktop/jarvis-core-fixed

# Create Phase 0 branch
git checkout -b feature/phase-0-quick-wins

# Create new files
touch core/token_counter.py
touch core/export.py
mkdir -p exports

# Activate venv and test
source venv/bin/activate
python core/token_counter.py
python core/export.py

# Check imports work
python -c "from core.token_counter import TokenCounter; print('✅ Token counter OK')"
python -c "from core.export import ChatExporter; print('✅ Export OK')"

echo "✅ Phase 0 setup ready!"
```

---

## ⚠️ Common Issues & Fixes

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: no module named 'rich'` | Already installed (used in cli.py) |
| `/model list` returns error | Check Ollama is running (`ollama serve`) |
| Export file not created | Check `exports/` dir exists + permissions |
| Markdown not rendering | Check `_has_markdown()` detects patterns |

---

## ✅ Success Criteria

After Phase 0, you should be able to:

1. ✅ See token counts after each response
2. ✅ Switch models with `/model set [name]` without restart
3. ✅ See formatted responses with **bold**, *italic*, code blocks
4. ✅ Export chat with `/export` to timestamped .md file

**Estimated time:** 2-3 hours  
**Complexity:** Low  
**Risk:** Minimal (no breaking changes)

---

## 📝 Notes

- **Token counting** uses estimation (not exact counts from Ollama API)
- **Model switch** doesn't save config to disk (transient, uses in-memory config)
- **Markdown rendering** gracefully falls back to plain text
- **Export** saves to `exports/` directory in project root

---

Created: 30 Apr 2026  
Last updated: 30 Apr 2026
