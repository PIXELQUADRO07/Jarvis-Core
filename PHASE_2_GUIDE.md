# JARVIS Phase 2 — UX & CLI Enhancement Implementation Guide

**Duration:** 5-7 hours  
**Start date:** After Phase 1 complete  
**Target:** Professional CLI with autocomplete, multiline input, history, session navigation

---

## Overview

Phase 2 transforms the CLI into a professional interface:
1. **Input Multiriga** - Shift+Enter for newlines
2. **Autocompletamento** - Tab-complete commands and parameters
3. **Cronologia Persistente** - Search chat history
4. **Navigation** - Alt+↑/↓ to switch sessions

**Impact:** MVP READY ✅ (All Priority 1-2 features complete)

---

## Feature 1: Input Multiriga (Shift+Enter)

### Scope
- Support multi-line input without sending
- Shift+Enter = newline
- Enter = send message
- Show line counter

### Implementation

**Modify `ui/cli.py`:**

```python
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.filters import ViMode, Condition

def get_multiline_keybindings() -> KeyBindings:
    """Configure key bindings for multiline input"""
    bindings = KeyBindings()
    
    @bindings.add('enter', filter=~ViMode())
    def _(event):
        """
        Enter key behavior:
        - If text is empty or contains newlines: send
        - Otherwise: newline
        Actually: always send on Enter, use Shift+Enter for newline
        """
        event.app.exit_with_value(event.app.current_buffer.text)
    
    @bindings.add('s-enter', filter=~ViMode())
    def _(event):
        """Shift+Enter: insert newline"""
        event.app.current_buffer.insert_text('\n')
    
    return bindings


def create_prompt_session():
    """Create PromptSession with multiline support"""
    from prompt_toolkit import PromptSession
    
    session = PromptSession(
        "❯ ",
        multiline=True,
        key_bindings=get_multiline_keybindings(),
        completer=CommandCompleter(),
        style=PROMPT_STYLE,
        mouse_support=True,
    )
    return session


def main_loop():
    """Updated main loop with multiline input"""
    session = create_prompt_session()
    
    while True:
        try:
            # Get input (can be multiline)
            user_input = session.prompt()
            
            # Trim empty lines
            user_input = user_input.strip()
            if not user_input:
                continue
            
            # Rest of logic...
            
        except KeyboardInterrupt:
            if console.input("[Y/n] Exit JARVIS? ").lower() != "n":
                break
```

### Testing
```bash
python main.py
# In JARVIS:
> Type something
  press Shift+Enter to add newline
  press Enter to send
# Message should preserve newlines
```

---

## Feature 2: Autocompletamento /cmd

### Scope
- Tab-complete command names: `/m` → `/memory`
- Tab-complete parameters: `/voice model ` → shows available models
- Fuzzy matching
- Help text on hover

### Implementation

**File:** `core/completer.py` (NEW)

```python
#!/usr/bin/env python3
"""
Command and parameter autocompletion.
"""

from prompt_toolkit.completion import Completer, Completion, CompleteEvent
from prompt_toolkit.document import Document
from core.commands import COMMANDS
from core.session_manager import get_session_manager
from typing import List, Generator
import re


class CommandCompleter(Completer):
    """Autocomplete JARVIS commands and parameters"""
    
    def get_completions(
        self, 
        document: Document, 
        complete_event: CompleteEvent
    ) -> Generator[Completion, None, None]:
        """Generate completions"""
        text = document.text_before_cursor
        
        # Only complete if starts with /
        if not text.strip().startswith('/'):
            return
        
        # Extract command and parameters
        parts = text.split()
        if not parts:
            return
        
        command_part = parts[0]
        
        # If only command typed, complete command names
        if len(parts) == 1:
            yield from self._complete_commands(command_part)
        else:
            # Complete parameters based on command
            command = command_part.lstrip('/')
            yield from self._complete_parameters(command, parts[1:], text)
    
    def _complete_commands(self, prefix: str) -> Generator[Completion, None, None]:
        """Complete command names"""
        prefix_lower = prefix.lower()
        
        for cmd_name, (help_text, _) in COMMANDS.items():
            if cmd_name.startswith(prefix_lower.lstrip('/')):
                yield Completion(
                    f"/{cmd_name}",
                    start_position=-len(prefix),
                    display=f"/{cmd_name}",
                    display_meta=help_text[:40]  # First 40 chars of help
                )
    
    def _complete_parameters(
        self, 
        command: str, 
        params: List[str], 
        full_text: str
    ) -> Generator[Completion, None, None]:
        """Complete command parameters"""
        
        if command == "model" and params[0] == "set":
            # Complete model names
            yield from self._complete_models()
        
        elif command == "voice" and params[0] == "model":
            # Complete voice model names
            yield from self._complete_voice_models()
        
        elif command == "session" and params[0] == "switch":
            # Complete session names
            yield from self._complete_sessions()
        
        elif command == "export":
            # Optional filename suggestions
            yield Completion(
                "",
                display="[filename]",
                display_meta="optional: custom filename"
            )
    
    def _complete_models(self) -> Generator[Completion, None, None]:
        """Get available models from Ollama"""
        try:
            from core.commands import get_available_models
            models = get_available_models()
            for model in models:
                yield Completion(model, display=model, display_meta="Ollama model")
        except:
            pass
    
    def _complete_voice_models(self) -> Generator[Completion, None, None]:
        """Get available voice models"""
        from pathlib import Path
        voices_dir = Path("voices")
        
        if voices_dir.exists():
            for voice_file in voices_dir.glob("*.onnx"):
                model_name = voice_file.stem
                yield Completion(
                    model_name,
                    display=model_name,
                    display_meta="Voice model"
                )
    
    def _complete_sessions(self) -> Generator[Completion, None, None]:
        """Get session names"""
        sm = get_session_manager()
        for session in sm.list_sessions():
            yield Completion(
                session.name,
                display=session.name,
                display_meta=f"{session.message_count} messages"
            )


# Export for use in ui/cli.py
__all__ = ["CommandCompleter"]
```

**Update `ui/cli.py`:**

```python
from core.completer import CommandCompleter

def main_loop():
    """Main loop with completer"""
    session = PromptSession(
        "❯ ",
        multiline=True,
        completer=CommandCompleter(),  # ← Use our custom completer
        style=PROMPT_STYLE,
    )
    # ...
```

### Testing
```bash
python main.py
# In JARVIS:
/m[TAB] → /memory
/voice model [TAB] → shows available models
/session switch [TAB] → shows session names
```

---

## Feature 3: Cronologia Persistente

### Scope
- Save all messages to `history.json`
- Search history: `/history search [query]`
- View recent: `/history [n]` - last n messages
- Rotate file when too large (>10MB)

### Implementation

**File:** `core/history.py` (NEW)

```python
#!/usr/bin/env python3
"""
Persistent chat history with search and rotation.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from logger import debug, info, warning


class ChatHistory:
    """Persistent chat history with search"""
    
    def __init__(self, history_file: str = "history.json", max_file_size: int = 10_000_000):
        self.history_file = Path(history_file)
        self.max_file_size = max_file_size
        self.max_file_size = max_file_size
        
        # Create file if not exists
        if not self.history_file.exists():
            self.history_file.write_text(json.dumps({"messages": []}))
    
    def add_message(self, role: str, content: str, session: str = "main"):
        """Add message to history"""
        message = {
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "content": content[:500],  # Truncate long messages
            "session": session,
        }
        
        data = self._load_history()
        data["messages"].append(message)
        self._save_history(data)
        
        debug(f"History: added {role} message")
    
    def search(self, query: str, limit: int = 10) -> List[dict]:
        """Search history by text"""
        data = self._load_history()
        query_lower = query.lower()
        
        results = []
        for msg in reversed(data["messages"]):
            if query_lower in msg["content"].lower():
                results.append(msg)
                if len(results) >= limit:
                    break
        
        return results
    
    def get_recent(self, n: int = 10, session: Optional[str] = None) -> List[dict]:
        """Get last n messages, optionally filtered by session"""
        data = self._load_history()
        messages = data["messages"]
        
        # Filter by session if provided
        if session:
            messages = [m for m in messages if m.get("session") == session]
        
        return messages[-n:]
    
    def clear_history(self):
        """Clear all history"""
        self._save_history({"messages": []})
        info("History cleared")
    
    def export_session(self, session: str, output_file: str = None) -> str:
        """Export session history to markdown"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"exports/history_{session}_{timestamp}.md"
        
        data = self._load_history()
        messages = [m for m in data["messages"] if m.get("session") == session]
        
        lines = [
            f"# History: {session}",
            f"Exported: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
            "",
        ]
        
        for msg in messages:
            role_emoji = "👤" if msg["role"] == "user" else "🤖"
            timestamp = msg["timestamp"][:16]  # YYYY-MM-DD HH:MM
            lines.append(f"**{role_emoji} {msg['role']} [{timestamp}]**")
            lines.append(msg["content"])
            lines.append("")
        
        output_path = Path(output_file)
        output_path.parent.mkdir(exist_ok=True)
        output_path.write_text("\n".join(lines))
        
        return f"✅ Exported to: {output_file}"
    
    def _load_history(self) -> dict:
        """Load history from disk"""
        try:
            with open(self.history_file) as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"messages": []}
    
    def _save_history(self, data: dict):
        """Save history to disk with rotation"""
        with open(self.history_file, "w") as f:
            json.dump(data, f, indent=2)
        
        # Check if file exceeds max size and rotate
        if self.history_file.stat().st_size > self.max_file_size:
            self._rotate_history()
    
    def _rotate_history(self):
        """Rotate history file when too large"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.history_file.with_stem(
            f"{self.history_file.stem}_backup_{timestamp}"
        )
        self.history_file.rename(backup_file)
        info(f"History rotated: {backup_file}")
        
        # Create new empty history
        self.history_file.write_text(json.dumps({"messages": []}))


# Module-level singleton
_chat_history: Optional[ChatHistory] = None

def get_chat_history() -> ChatHistory:
    """Get singleton chat history"""
    global _chat_history
    if _chat_history is None:
        _chat_history = ChatHistory()
    return _chat_history


# Commands
def handle_history_command(args: list) -> str:
    """
    Handle /history commands:
    - /history [n]          → show last n messages
    - /history search [query] → search messages
    - /history export       → export to markdown
    - /history clear        → clear history (DANGEROUS!)
    """
    history = get_chat_history()
    
    if not args:
        # Show last 10
        messages = history.get_recent(10)
        lines = ["📜 Recent messages (last 10):"]
        for msg in messages:
            role = "You" if msg["role"] == "user" else "JARVIS"
            content = msg["content"][:60] + ("..." if len(msg["content"]) > 60 else "")
            lines.append(f"  [{msg['timestamp'][:16]}] {role}: {content}")
        return "\n".join(lines)
    
    elif args[0] == "search" and len(args) > 1:
        query = " ".join(args[1:])
        results = history.search(query, limit=5)
        if not results:
            return f"❌ No results for: {query}"
        
        lines = [f"🔍 Search results for '{query}' (found {len(results)}):"]
        for msg in results:
            role = "👤" if msg["role"] == "user" else "🤖"
            lines.append(f"\n  {role} [{msg['timestamp'][:16]}]")
            lines.append(f"  {msg['content'][:100]}")
        return "\n".join(lines)
    
    elif args[0].isdigit():
        n = int(args[0])
        messages = history.get_recent(n)
        lines = [f"📜 Recent messages (last {n}):"]
        for msg in messages:
            role = "👤" if msg["role"] == "user" else "🤖"
            lines.append(f"  {role} {msg['content'][:60]}")
        return "\n".join(lines)
    
    elif args[0] == "export":
        from core.session_manager import get_session_manager
        sm = get_session_manager()
        session = sm.get_current_session()
        if session:
            return history.export_session(session.name)
        return "❌ No active session"
    
    elif args[0] == "clear":
        history.clear_history()
        return "✅ History cleared"
    
    else:
        return "Usage: /history [n]|search|export|clear [query]"


# Test
if __name__ == "__main__":
    h = ChatHistory()
    h.add_message("user", "Ciao JARVIS")
    h.add_message("assistant", "Ciao! Come stai?")
    
    print("Recent:")
    for msg in h.get_recent(2):
        print(f"  {msg['role']}: {msg['content']}")
    
    print("\nSearch 'Ciao':")
    for msg in h.search("Ciao"):
        print(f"  {msg['role']}: {msg['content']}")
```

**Update `core/commands.py`:**

```python
from core.history import handle_history_command, get_chat_history

COMMANDS = {
    # ... existing ...
    "history": ("Visualizza cronologia messaggi", handle_history_command),
    # ... existing ...
}

# Update message saving to also save to history
def save_and_track(role: str, content: str):
    """Save to memory AND history"""
    from core.history import get_chat_history
    from core.session_manager import get_session_manager
    
    # Save to memory (session-specific)
    memory = load_memory()
    memory.append({"role": role, "content": content})
    save_memory(memory)
    
    # Save to history (global)
    sm = get_session_manager()
    session = sm.get_current_session()
    session_name = session.name if session else "unknown"
    get_chat_history().add_message(role, content, session_name)
```

### Testing
```bash
python main.py
# In JARVIS:
> Ciao
> Come stai?
> Mi piace fare domande
/history
# Shows: last 10 messages
/history search piace
# Shows: "Mi piace fare domande"
/history export
# Creates exports/history_*.md
/history 5
# Shows last 5 messages
```

---

## Feature 4: Navigation ↑↓ (Session Switching)

### Scope
- Alt+↑ = switch to previous session
- Alt+↓ = switch to next session
- Show session name in status line
- Update memory when switching

### Implementation

**Modify `ui/cli.py`:**

```python
from prompt_toolkit.filters import EmacsInsertMode, ViInsertMode

def get_navigation_keybindings() -> KeyBindings:
    """Key bindings for session navigation"""
    bindings = KeyBindings()
    
    @bindings.add('escape', 'up')  # Alt+↑
    def _(event):
        """Switch to previous session"""
        from core.session_manager import get_session_manager
        
        sm = get_session_manager()
        sessions = [s.name for s in sm.list_sessions()]
        current = sm.get_current_session()
        
        if current and current.name in sessions:
            idx = sessions.index(current.name)
            prev_session = sessions[(idx - 1) % len(sessions)]
            sm.switch_session(prev_session)
            console.print(Text(f"→ Session: {prev_session}", style=YELLOW))
        
        # Prevent default behavior
        event.app.invalidate()
    
    @bindings.add('escape', 'down')  # Alt+↓
    def _(event):
        """Switch to next session"""
        from core.session_manager import get_session_manager
        
        sm = get_session_manager()
        sessions = [s.name for s in sm.list_sessions()]
        current = sm.get_current_session()
        
        if current and current.name in sessions:
            idx = sessions.index(current.name)
            next_session = sessions[(idx + 1) % len(sessions)]
            sm.switch_session(next_session)
            console.print(Text(f"→ Session: {next_session}", style=YELLOW))
        
        event.app.invalidate()
    
    return bindings


def get_prompt_with_session():
    """Prompt with current session name"""
    from core.session_manager import get_session_manager
    
    sm = get_session_manager()
    session = sm.get_current_session()
    session_name = session.name if session else "unknown"
    
    return f"[{session_name}] ❯ "


def main_loop():
    """Main loop with session navigation"""
    session = create_prompt_session()
    
    while True:
        try:
            # Dynamic prompt with session name
            prompt_text = get_prompt_with_session()
            
            user_input = session.prompt(prompt_text)
            # ...
```

### Testing
```bash
python main.py
# In JARVIS:
/session create work
/session create personal
# Prompt should show: [main] ❯
# Press Alt+↓
# Prompt should change: [work] ❯
# Press Alt+↓
# Prompt should change: [personal] ❯
# Press Alt+↑
# Prompt should change: [work] ❯
```

---

## 📋 Phase 2 Implementation Checklist

### Step 1: Multiline Input (1 hour)
- [ ] Create `get_multiline_keybindings()` in `ui/cli.py`
- [ ] Add `s-enter` binding for newline
- [ ] Update `PromptSession` with multiline=True
- [ ] Test: Shift+Enter adds newline, Enter sends

### Step 2: Autocompletamento (1.5 hours)
- [ ] Create `core/completer.py`
- [ ] Implement `CommandCompleter` class
- [ ] Add `_complete_commands()` method
- [ ] Add `_complete_parameters()` method
- [ ] Add model, voice, session completers
- [ ] Update `ui/cli.py` to use completer
- [ ] Test: /m[TAB], /voice model [TAB], etc.

### Step 3: History (2 hours)
- [ ] Create `core/history.py`
- [ ] Implement `ChatHistory` class
- [ ] Add methods: add_message, search, get_recent, export_session
- [ ] Add rotation logic
- [ ] Create `handle_history_command()` in `core/commands.py`
- [ ] Add "history" to COMMANDS registry
- [ ] Update message saving to track in history
- [ ] Test: /history, /history search, /history export

### Step 4: Navigation (30-45 min)
- [ ] Create `get_navigation_keybindings()` in `ui/cli.py`
- [ ] Add Alt+↑ binding for previous session
- [ ] Add Alt+↓ binding for next session
- [ ] Update prompt to show session name
- [ ] Test: Alt+↑/↓ switches sessions

### Step 5: Integration Testing (1 hour)
- [ ] Start JARVIS: `python main.py`
- [ ] Test multiline: Shift+Enter in input
- [ ] Test autocomplete: /m[TAB], /voice[TAB]
- [ ] Test history: /history search, /history export
- [ ] Test navigation: Alt+↑/↓ switches sessions
- [ ] Verify prompt shows session name
- [ ] Verify history.json created
- [ ] Check no errors in logs

### Step 6: Documentation
- [ ] Update `QUICKSTART.md`
- [ ] Add keyboard shortcuts section
- [ ] Document /history commands
- [ ] Update help text

### Step 7: Git Commits
```bash
git add core/completer.py ui/cli.py
git commit -m "feat: add command autocomplete and multiline input"

git add core/history.py core/commands.py
git commit -m "feat: add persistent chat history with search"

git add ui/cli.py core/session_manager.py
git commit -m "feat: add session navigation with Alt+↑/↓"

git add QUICKSTART.md
git commit -m "docs: update Phase 2 features"
```

---

## ✅ Success Criteria = MVP READY ✅

Phase 2 = SUCCESS when:

✅ Shift+Enter creates newline in input  
✅ Tab autocompletes /commands  
✅ /history shows recent messages  
✅ /history search works  
✅ Alt+↑/↓ navigates sessions  
✅ Prompt shows current session name  
✅ history.json created and updated  
✅ No errors in logs  
✅ All Priority 1-2 features working  

**Estimated time:** 5-7 hours  
**Complexity:** Medium  
**Risk:** Low  

**= MVP READY MILESTONE = 16-19 hours total (Phases 0-2)**

---

Created: 30 Apr 2026  
Last updated: 30 Apr 2026  
Next: PHASE_3_GUIDE.md (Voice - Optional)

