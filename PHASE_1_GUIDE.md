# JARVIS Phase 1 — Robustezza Core Implementation Guide

**Duration:** 4-6 hours  
**Start date:** After Phase 0 complete  
**Target:** Offline resilience, streaming UI, session support

---

## Overview

Phase 1 solidifies the core by adding:
1. **Retry + Circuit Breaker** - Resilient to Ollama disconnections
2. **Streaming Live UI** - Real-time response display (no buffering)
3. **Session Manager** - Multiple concurrent conversations
4. **Session-Aware Memory** - Each session has isolated history

**Impact:** Ollama offline → auto-retry; Responses stream live; Multiple independent conversations

---

## Feature 1: Retry Handler + Circuit Breaker

### Scope
- Implement retry logic with exponential backoff
- Circuit breaker pattern for failing services
- Graceful degradation (fallback messages)
- Comprehensive logging

### Implementation

**File:** `core/retry_handler.py` (NEW)

```python
#!/usr/bin/env python3
"""
Retry handler with circuit breaker pattern.
Handles transient failures in LLM service.
"""

import time
import threading
from enum import Enum
from datetime import datetime, timedelta
from logger import debug, warning, error


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"           # Normal operation
    OPEN = "open"               # Failing, reject requests
    HALF_OPEN = "half_open"     # Testing recovery


class CircuitBreaker:
    """
    Circuit breaker for service protection.
    
    States:
    - CLOSED: Normal, requests pass through
    - OPEN: Too many failures, requests rejected immediately
    - HALF_OPEN: Testing if service recovered
    """
    
    def __init__(self, failure_threshold: int = 3, timeout: int = 60, name: str = "service"):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.name = name
        self.failures = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        self.lock = threading.Lock()
    
    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        with self.lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    debug(f"CircuitBreaker {self.name}: HALF_OPEN (testing recovery)")
                else:
                    raise CircuitBreakerOpen(
                        f"Circuit breaker {self.name} is OPEN (retry in {self.timeout}s)"
                    )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Reset on successful call"""
        with self.lock:
            self.failures = 0
            if self.state != CircuitState.CLOSED:
                debug(f"CircuitBreaker {self.name}: CLOSED (recovered)")
            self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        """Track failure"""
        with self.lock:
            self.failures += 1
            self.last_failure_time = time.time()
            
            if self.failures >= self.failure_threshold:
                self.state = CircuitState.OPEN
                warning(f"CircuitBreaker {self.name}: OPEN after {self.failures} failures")
    
    def _should_attempt_reset(self) -> bool:
        """Check if timeout expired for HALF_OPEN attempt"""
        if self.last_failure_time is None:
            return False
        elapsed = time.time() - self.last_failure_time
        return elapsed >= self.timeout
    
    def status(self) -> dict:
        """Get circuit breaker status"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failures": self.failures,
            "threshold": self.failure_threshold,
            "timeout": self.timeout,
            "last_failure": self.last_failure_time
        }


class CircuitBreakerOpen(Exception):
    """Circuit breaker is open - service unavailable"""
    pass


class RetryHandler:
    """
    Retry logic with exponential backoff.
    
    Strategy:
    - Max 3 attempts
    - Base delay: 1 second
    - Backoff multiplier: 1.5x
    - Retries on: ConnectionError, TimeoutError, URLError
    - Does NOT retry on: ValueError, JSON decode errors (application errors)
    """
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, backoff: float = 1.5):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.backoff = backoff
    
    def execute(self, func, *args, **kwargs):
        """
        Execute function with retry logic.
        
        Args:
            func: Callable to retry
            *args, **kwargs: Arguments to pass
        
        Returns:
            Result from func
        
        Raises:
            Exception: If all retries exhausted
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                debug(f"Retry attempt {attempt + 1}/{self.max_retries}")
                result = func(*args, **kwargs)
                if attempt > 0:
                    debug(f"Succeeded on attempt {attempt + 1}")
                return result
            
            except (ConnectionError, TimeoutError, OSError) as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    wait_time = self.base_delay * (self.backoff ** attempt)
                    warning(f"Attempt {attempt + 1} failed: {e}. Waiting {wait_time:.1f}s...")
                    time.sleep(wait_time)
                else:
                    error(f"All {self.max_retries} attempts failed: {e}")
                    raise
            
            except Exception as e:
                # Don't retry on application errors
                error(f"Non-retryable error: {e}")
                raise
        
        # Fallback (shouldn't reach here)
        raise last_exception or Exception("Unknown error after retries")
    
    def get_backoff_time(self, attempt: int) -> float:
        """Calculate backoff time for attempt number"""
        return self.base_delay * (self.backoff ** attempt)


# Module-level instances for singleton pattern
_circuit_breaker = CircuitBreaker(failure_threshold=3, timeout=60, name="ollama")
_retry_handler = RetryHandler(max_retries=3, base_delay=1.0, backoff=1.5)


def get_circuit_breaker() -> CircuitBreaker:
    """Get singleton circuit breaker"""
    return _circuit_breaker


def get_retry_handler() -> RetryHandler:
    """Get singleton retry handler"""
    return _retry_handler


def ollama_call(func, *args, **kwargs):
    """
    Execute Ollama API call with retry + circuit breaker.
    
    Usage:
        from core.retry_handler import ollama_call
        response = ollama_call(some_function, arg1, arg2)
    """
    cb = get_circuit_breaker()
    rh = get_retry_handler()
    
    def wrapped():
        return rh.execute(func, *args, **kwargs)
    
    return cb.call(wrapped)


# Test
if __name__ == "__main__":
    # Test circuit breaker
    cb = CircuitBreaker(failure_threshold=2, timeout=5, name="test")
    
    print("Circuit Breaker Status:")
    print(cb.status())
    
    # Test retry handler
    rh = RetryHandler(max_retries=3, base_delay=0.5)
    print("\nRetry backoff times:")
    for attempt in range(3):
        print(f"  Attempt {attempt}: wait {rh.get_backoff_time(attempt):.2f}s")
```

**Integration in `core/llm.py`:**

```python
from core.retry_handler import ollama_call

def stream_llm(text: str) -> Generator[str, None, None]:
    """Streaming LLM with retry + circuit breaker."""
    config = get_config()
    history = load_memory()
    history.append({"role": "user", "content": text})

    def make_request():
        payload = json.dumps({
            "model": config.model,
            "messages": [get_system_prompt()] + history,
            "stream": True,
            "options": {"temperature": config.temperature}
        }).encode("utf-8")

        req = urllib.request.Request(
            config.ollama_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        
        return urllib.request.urlopen(req, timeout=30)
    
    # Use retry + circuit breaker
    try:
        resp = ollama_call(make_request)
        # ... rest of streaming logic
    except CircuitBreakerOpen as e:
        yield f"⚠️ Servizio offline. {str(e)}"
        return
```

### Testing
```bash
python core/retry_handler.py

# In JARVIS CLI:
# 1. Stop Ollama: killall ollama
# 2. Try command: > ciao
# 3. Verify: 3 retry attempts with backoff
# 4. After timeout: graceful error message
# 5. Restart Ollama: ollama serve
# 6. Try again: Circuit breaker recovers
```

---

## Feature 2: Streaming Live UI

### Scope
- Display response text as it arrives (live typing effect)
- Buffer chunks for UI performance (50ms batching)
- Show "thinking..." indicator during streaming
- Cursor blinking animation

### Implementation

**Modify `ui/cli.py`:**

```python
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text
import time

def render_streaming_response(generator: Generator[str, None, None]):
    """
    Render streaming response with live updating.
    
    Shows:
    - Thinking indicator while waiting for chunks
    - Live text as it arrives
    - Smooth animation (no jumpy updates)
    """
    
    buffer = ""
    start_time = time.time()
    last_render = start_time
    render_interval = 0.05  # 50ms batching
    
    with Live(
        Panel(
            Text("", style=BRIGHT_RED),
            border_style=RED,
            expand=False,
            padding=(1, 2)
        ),
        console=console,
        refresh_per_second=20,
    ) as live:
        
        for chunk in generator:
            buffer += chunk
            current_time = time.time()
            
            # Update UI every 50ms to avoid flicker
            if current_time - last_render >= render_interval:
                # Add cursor for typing effect
                display_text = buffer + "▌"
                live.update(Panel(
                    Markdown(display_text) if _has_markdown(display_text) else Text(display_text),
                    border_style=RED,
                    expand=False,
                    padding=(1, 2)
                ))
                last_render = current_time
        
        # Final render without cursor
        live.update(Panel(
            Markdown(buffer) if _has_markdown(buffer) else Text(buffer, style=BRIGHT_RED),
            border_style=RED,
            expand=False,
            padding=(1, 2)
        ))
    
    return buffer

def main_loop():
    """Main CLI loop with streaming support."""
    session = PromptSession(
        "❯ ",
        style=PROMPT_STYLE,
        completer=CommandCompleter(),
    )
    
    while True:
        try:
            user_input = session.prompt()
            
            if user_input.startswith("/"):
                # Handle command
                result = handle_input(user_input)
                console.print(Text(result, style=GREEN))
            else:
                # Stream LLM response
                console.print(Text("🧠 Thinking...", style=GREY, italic=True))
                
                try:
                    generator = handle_input(user_input)
                    response = render_streaming_response(generator)
                    
                    # Save to memory
                    save_message("user", user_input)
                    save_message("assistant", response)
                    
                except Exception as e:
                    console.print(Text(f"❌ Error: {e}", style=RED))
        
        except KeyboardInterrupt:
            if console.input("[Y/n] Exit JARVIS? ").lower() != "n":
                break
```

### Testing
```bash
python main.py
# In JARVIS:
> Dammi una poesia su AI
# Should see text arriving live, not all at once
# Cursor blinking animation during typing
```

---

## Feature 3: Session Manager

### Scope
- Create isolated conversation sessions
- Switch between sessions
- List active sessions
- Auto-save session state
- Each session has independent memory

### Implementation

**File:** `core/session_manager.py` (NEW)

```python
#!/usr/bin/env python3
"""
Session manager for multiple conversations.
Each session is independent with isolated memory.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from logger import debug, info, warning

class Session:
    """Represents a single conversation session"""
    
    def __init__(self, name: str, created_at: datetime = None):
        self.name = name
        self.created_at = created_at or datetime.now()
        self.last_updated = self.created_at
        self.message_count = 0
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "message_count": self.message_count
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'Session':
        s = Session(data["name"])
        s.created_at = datetime.fromisoformat(data["created_at"])
        s.last_updated = datetime.fromisoformat(data["last_updated"])
        s.message_count = data["message_count"]
        return s


class SessionManager:
    """Manages multiple conversation sessions"""
    
    def __init__(self, sessions_dir: str = "memory_sessions"):
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(exist_ok=True)
        
        self.current_session: Optional[Session] = None
        self.sessions: Dict[str, Session] = {}
        self.sessions_metadata_file = self.sessions_dir / "sessions.json"
        
        self._load_sessions()
    
    def create_session(self, name: str) -> Session:
        """Create new session"""
        if name in self.sessions:
            warning(f"Session '{name}' already exists")
            return self.sessions[name]
        
        session = Session(name)
        self.sessions[name] = session
        self._save_sessions_metadata()
        
        info(f"Session created: {name}")
        return session
    
    def switch_session(self, name: str) -> bool:
        """Switch to session"""
        if name not in self.sessions:
            warning(f"Session '{name}' not found")
            return False
        
        self.current_session = self.sessions[name]
        info(f"Switched to session: {name}")
        return True
    
    def get_current_session(self) -> Optional[Session]:
        """Get current session"""
        if self.current_session is None and self.sessions:
            # Default to first session
            self.current_session = list(self.sessions.values())[0]
        return self.current_session
    
    def list_sessions(self) -> List[Session]:
        """List all sessions"""
        return list(self.sessions.values())
    
    def get_session_memory_file(self, session_name: str) -> Path:
        """Get memory file path for session"""
        return self.sessions_dir / f"memory_{session_name}.json"
    
    def delete_session(self, name: str) -> bool:
        """Delete session and its memory"""
        if name not in self.sessions:
            return False
        
        # Delete memory file
        memory_file = self.get_session_memory_file(name)
        if memory_file.exists():
            memory_file.unlink()
        
        # Remove from sessions
        del self.sessions[name]
        
        # If deleted current session, switch to another
        if self.current_session and self.current_session.name == name:
            if self.sessions:
                self.current_session = list(self.sessions.values())[0]
            else:
                self.current_session = None
        
        self._save_sessions_metadata()
        info(f"Session deleted: {name}")
        return True
    
    def _load_sessions(self):
        """Load sessions from disk"""
        if self.sessions_metadata_file.exists():
            with open(self.sessions_metadata_file) as f:
                data = json.load(f)
                for session_data in data.get("sessions", []):
                    session = Session.from_dict(session_data)
                    self.sessions[session.name] = session
        
        # If no sessions, create default
        if not self.sessions:
            self.create_session("main")
            self.current_session = self.sessions["main"]
    
    def _save_sessions_metadata(self):
        """Save sessions to disk"""
        data = {
            "sessions": [s.to_dict() for s in self.sessions.values()]
        }
        with open(self.sessions_metadata_file, "w") as f:
            json.dump(data, f, indent=2)
    
    def status(self) -> str:
        """Get status string"""
        if not self.current_session:
            return "No session"
        
        current = self.current_session
        return (
            f"📍 Session: {current.name}\n"
            f"   Created: {current.created_at.strftime('%d/%m %H:%M')}\n"
            f"   Messages: {current.message_count}\n"
            f"   Total sessions: {len(self.sessions)}"
        )


# Module-level singleton
_session_manager: Optional[SessionManager] = None

def get_session_manager() -> SessionManager:
    """Get singleton session manager"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager

# Test
if __name__ == "__main__":
    sm = get_session_manager()
    
    sm.create_session("work")
    sm.create_session("personal")
    
    print(f"Sessions: {[s.name for s in sm.list_sessions()]}")
    
    sm.switch_session("work")
    print(sm.status())
```

**Modify `core/memory.py` to be session-aware:**

```python
from core.session_manager import get_session_manager

def load_memory() -> list:
    """Load memory for current session"""
    sm = get_session_manager()
    session = sm.get_current_session()
    
    if session is None:
        return []
    
    memory_file = sm.get_session_memory_file(session.name)
    
    if not memory_file.exists():
        return []
    
    try:
        with open(memory_file) as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def save_memory(messages: list):
    """Save memory for current session"""
    sm = get_session_manager()
    session = sm.get_current_session()
    
    if session is None:
        return
    
    memory_file = sm.get_session_memory_file(session.name)
    
    with open(memory_file, "w") as f:
        json.dump(messages, f, indent=2)
    
    # Update message count
    session.message_count = len(messages)
    session.last_updated = datetime.now()
    sm._save_sessions_metadata()
```

**Add commands in `core/commands.py`:**

```python
def handle_session_command(args: list) -> str:
    """
    Handle /session commands:
    - /session list       → show all sessions
    - /session create [name] → create new session
    - /session switch [name] → switch to session
    - /session delete [name] → delete session
    - /session status    → show current session info
    """
    sm = get_session_manager()
    
    if not args:
        return "Usage: /session list|create|switch|delete|status [name]"
    
    command = args[0].lower()
    
    if command == "list":
        sessions = sm.list_sessions()
        current = sm.get_current_session()
        lines = ["📍 Sessions:"]
        for s in sessions:
            marker = "►" if current and s.name == current.name else " "
            lines.append(f"  {marker} {s.name} ({s.message_count} messages)")
        return "\n".join(lines)
    
    elif command == "create" and len(args) > 1:
        name = args[1]
        sm.create_session(name)
        return f"✅ Session created: {name}"
    
    elif command == "switch" and len(args) > 1:
        name = args[1]
        if sm.switch_session(name):
            return f"✅ Switched to session: {name}"
        else:
            return f"❌ Session not found: {name}"
    
    elif command == "delete" and len(args) > 1:
        name = args[1]
        if sm.delete_session(name):
            return f"✅ Session deleted: {name}"
        else:
            return f"❌ Session not found: {name}"
    
    elif command == "status":
        return sm.status()
    
    else:
        return "Unknown subcommand"
```

### Testing
```bash
python main.py
# In JARVIS:
/session create work
/session create personal
/session list
# Verify: ► main, work, personal shown
/session switch work
> Ciao, sono nella sessione work
/session switch personal
> Ciao, sono nella sessione personal
/session switch work
# Memory should show "Ciao, sono nella sessione work"
```

---

## Feature 4: Session-Aware Memory (Enhancement)

### Scope
- Already mostly covered by SessionManager
- Add session context to memory metadata
- Update memory.py functions

### Implementation

**Already handled above in `core/memory.py`** - each session has separate `memory_*.json` file.

No additional implementation needed - just verify:
- `load_memory()` loads session-specific file
- `save_memory()` saves to session-specific file
- Session switching reloads appropriate memory

---

## 📋 Phase 1 Implementation Checklist

### Step 1: Retry Handler + Circuit Breaker (1 hour)
- [ ] Create `core/retry_handler.py`
- [ ] Implement `CircuitBreaker` class
- [ ] Implement `RetryHandler` class
- [ ] Test locally: `python core/retry_handler.py`
- [ ] Import in `core/llm.py`
- [ ] Update streaming to use `ollama_call()`
- [ ] Test with Ollama offline

### Step 2: Streaming Live UI (1-1.5 hours)
- [ ] Create `_has_markdown()` if not already done
- [ ] Add `render_streaming_response()` to `ui/cli.py`
- [ ] Import `Live` from `rich.live`
- [ ] Update `main_loop()` to use streaming renderer
- [ ] Test: responses should display live
- [ ] Verify: cursor blinking animation

### Step 3: Session Manager (1.5-2 hours)
- [ ] Create `core/session_manager.py`
- [ ] Implement `Session` class
- [ ] Implement `SessionManager` class
- [ ] Create `memory_sessions/` directory
- [ ] Test locally: `python core/session_manager.py`
- [ ] Modify `core/memory.py` for session awareness
- [ ] Add `handle_session_command()` to `core/commands.py`
- [ ] Add "session" to COMMANDS registry
- [ ] Test: /session list|create|switch

### Step 4: Integration Testing (30-45 min)
- [ ] Start JARVIS: `python main.py`
- [ ] Test retry logic:
  - [ ] Stop Ollama
  - [ ] Type a message
  - [ ] Verify 3 retry attempts
  - [ ] Verify circuit breaker error
  - [ ] Restart Ollama
  - [ ] Verify recovery

- [ ] Test streaming:
  - [ ] Ask for long response
  - [ ] Verify live typing effect
  - [ ] No buffering (appears immediately)

- [ ] Test sessions:
  - [ ] /session list (shows main)
  - [ ] /session create work
  - [ ] /session create personal
  - [ ] /session switch work
  - [ ] Type message in work
  - [ ] /session switch personal
  - [ ] Type different message
  - [ ] /session switch work
  - [ ] Verify original message in memory

### Step 5: Documentation
- [ ] Update `QUICKSTART.md` with new commands
- [ ] Add `/session` to help text
- [ ] Document circuit breaker behavior

### Step 6: Git Commits
```bash
git add core/retry_handler.py
git commit -m "feat: add retry handler and circuit breaker"

git add core/session_manager.py core/memory.py core/commands.py
git commit -m "feat: add multi-session support with isolated memory"

git add ui/cli.py
git commit -m "feat: implement streaming response rendering"

git add QUICKSTART.md IMPROVEMENTS.md
git commit -m "docs: update guides for Phase 1"
```

---

## ⚠️ Common Issues & Fixes

| Issue | Solution |
|-------|----------|
| Circuit breaker stays OPEN | Check timeout value, manually reset if needed |
| Streaming shows garbled text | Ensure markdown detection working, check terminal encoding |
| Session memory not persisting | Check `memory_sessions/` directory writable |
| /session not recognized | Verify added to COMMANDS registry + help text |
| Multiple streaming calls crash | Use `Live` context manager correctly (see example) |

---

## ✅ Success Criteria

Phase 1 = SUCCESS when:

✅ Ollama offline → retries 3 times with backoff  
✅ After threshold → circuit breaker opens gracefully  
✅ Ollama recovers → circuit breaker closes  
✅ Responses stream live (not buffered)  
✅ /session list shows sessions  
✅ /session switch changes context  
✅ Memory is session-isolated  
✅ No errors in logs  

**Estimated time:** 4-6 hours  
**Complexity:** Medium  
**Risk:** Low (isolated features, well-tested patterns)  

---

Created: 30 Apr 2026  
Last updated: 30 Apr 2026  
Next: PHASE_2_GUIDE.md

