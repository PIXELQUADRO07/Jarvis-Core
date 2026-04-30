# ✅ JARVIS v3.0 Implementation Checklist

Complete checklist for all 6 phases. Check off items as you complete them.

---

## 🟢 Phase 0: Quick Wins (2-3 hours)

### Token Counter
- [x] Read: PHASE_0_GUIDE.md - Feature 1
- [x] Create: `core/token_counter.py`
  - [x] `TokenCounter` class with TOKEN_RATIOS
  - [x] `estimate_tokens()` method
  - [x] `format_usage()` method
- [x] Test: `python core/token_counter.py`
- [x] Commit: "feat(phase-0): Add token counter"

### Model Switching
- [x] Read: PHASE_0_GUIDE.md - Feature 2
- [x] Modify: `core/commands.py`
  - [x] Add `get_available_models()`
  - [x] Add /model command with list|set|current
- [x] Modify: `core/llm.py`
  - [x] Import TokenCounter
  - [x] Use TokenCounter for token tracking
- [x] Test: `/model list` working
- [x] Commit: "feat(phase-0): Add /model command"

### Markdown Rendering
- [x] Read: PHASE_0_GUIDE.md - Feature 3
- [x] Modify: `ui/cli.py`
  - [x] Import `Markdown` from rich
  - [x] Add `_has_markdown()` detection
  - [x] Update `render_jarvis_panel()` for markdown
- [x] Test: Messages with markdown render correctly
- [x] Commit: "feat(phase-0): Add markdown rendering"

### Chat Export
- [x] Read: PHASE_0_GUIDE.md - Feature 4
- [x] Modify: `core/commands.py`
  - [x] Add /export command
  - [x] Export to markdown file
- [x] Create directory: `exports/`
- [x] Test: `/export` creates .md file
- [x] Commit: "feat(phase-0): Add chat export"

### Phase 0 Testing & Validation
- [x] Start JARVIS: `python main.py`
- [x] Test token counter: Tokens estimated correctly
- [x] Test /model: `/model list` shows models
- [x] Test markdown: Markdown detection working
- [x] Test export: `/export` command ready
- [x] Check logs: `tail -f logs/jarvis.log`
- [x] All Phase 0 commands working: ✅

**Phase 0 Complete:** Date: 30/04/2026 ✅

---

## 🟠 Phase 1: Robustezza Core (5 hours)

### Retry Handler & Circuit Breaker
- [ ] Read: PHASE_1_GUIDE.md - Feature 1
- [ ] Create: `core/retry_handler.py`
  - [ ] `CircuitBreaker` class (CLOSED/OPEN/HALF_OPEN)
  - [ ] `RetryHandler` class with backoff logic
  - [ ] Thread-safe implementation
  - [ ] `ollama_call()` wrapper function
- [ ] Modify: `core/llm.py`
  - [ ] Import `ollama_call()` from retry_handler
  - [ ] Wrap stream_llm() API calls
- [ ] Test: `python core/retry_handler.py`
- [ ] Commit: "feat(phase-1): Add retry handler & circuit breaker"

### Session Manager
- [ ] Read: PHASE_1_GUIDE.md - Feature 3
- [ ] Create: `core/session_manager.py`
  - [ ] `Session` class
  - [ ] `SessionManager` class
  - [ ] Persistence to memory_sessions/
  - [ ] `get_session_manager()` singleton
- [ ] Create directory: `mkdir -p memory_sessions/`
- [ ] Test: `python core/session_manager.py`
- [ ] Commit: "feat(phase-1): Add session manager"

### Session-Aware Memory
- [ ] Read: PHASE_1_GUIDE.md - Feature 4
- [ ] Modify: `core/memory.py`
  - [ ] Update `load_memory()` for session files
  - [ ] Update `save_memory()` for session files
  - [ ] Get session name from SessionManager
- [ ] Test: Separate memory per session
- [ ] Commit: "feat(phase-1): Add session-aware memory"

### Streaming UI with Live
- [ ] Read: PHASE_1_GUIDE.md - Feature 2
- [ ] Modify: `ui/cli.py`
  - [ ] Import `Live` from rich.live
  - [ ] Add `render_streaming_response()`
  - [ ] 50ms batching for updates
  - [ ] Cursor animation (▌)
- [ ] Modify: `core/commands.py`
  - [ ] Add `handle_session_command()`
  - [ ] Add "session" to COMMANDS registry
- [ ] Test: Streaming response displays smoothly
- [ ] Commit: "feat(phase-1): Add streaming live UI"

### Phase 1 Testing & Validation
- [ ] Create test sessions: `/session create work`, `/session create personal`
- [ ] Switch sessions: `/session switch work`
- [ ] Verify memory isolation: Each session has own conversation
- [ ] Test retry logic: Disconnect Ollama, see retries in logs
- [ ] Test circuit breaker: After 3 failures, opens gracefully
- [ ] Test streaming: Response displays in real-time with animation
- [ ] Check session file creation: `ls memory_sessions/`
- [ ] All Phase 1 features working: ✅

**Phase 1 Complete:** Date: ___________

---

## 🟡 Phase 2: UX & CLI (5-7 hours) = MVP READY

### Multiline Input (Shift+Enter)
- [ ] Read: PHASE_2_GUIDE.md - Feature 1
- [ ] Modify: `ui/cli.py`
  - [ ] Create `get_multiline_keybindings()`
  - [ ] Add `s-enter` binding for newline
  - [ ] Update `PromptSession` with multiline=True
  - [ ] Test Shift+Enter for newline, Enter to send
- [ ] Test: Multi-line messages work
- [ ] Commit: "feat(phase-2): Add multiline input"

### Command Autocomplete
- [ ] Read: PHASE_2_GUIDE.md - Feature 2
- [ ] Create: `core/completer.py`
  - [ ] `CommandCompleter` class
  - [ ] `_complete_commands()` method
  - [ ] `_complete_parameters()` method
  - [ ] Model/voice/session completers
- [ ] Modify: `ui/cli.py`
  - [ ] Import `CommandCompleter`
  - [ ] Use in `PromptSession`
- [ ] Test: `/m[TAB]` autocompletes
- [ ] Test: `/voice model [TAB]` shows models
- [ ] Commit: "feat(phase-2): Add autocomplete"

### Persistent Chat History
- [ ] Read: PHASE_2_GUIDE.md - Feature 3
- [ ] Create: `core/history.py`
  - [ ] `ChatHistory` class
  - [ ] `add_message()` method
  - [ ] `search()` method
  - [ ] `get_recent()` method
  - [ ] `export_session()` method
  - [ ] Rotation logic for file size
- [ ] Modify: `core/commands.py`
  - [ ] Add `handle_history_command()`
  - [ ] Add "history" to COMMANDS registry
  - [ ] Update message saving to track history
- [ ] Test: `/history` shows recent messages
- [ ] Test: `/history search "keyword"` finds messages
- [ ] Test: `/history export` creates .md
- [ ] Commit: "feat(phase-2): Add persistent history"

### Session Navigation
- [ ] Read: PHASE_2_GUIDE.md - Feature 4
- [ ] Modify: `ui/cli.py`
  - [ ] Create `get_navigation_keybindings()`
  - [ ] Add `escape+up` binding (previous session)
  - [ ] Add `escape+down` binding (next session)
  - [ ] Create `get_prompt_with_session()`
  - [ ] Show session name in prompt
- [ ] Test: Alt+↑ goes to previous session
- [ ] Test: Alt+↓ goes to next session
- [ ] Test: Prompt shows session name
- [ ] Commit: "feat(phase-2): Add session navigation"

### Phase 2 Testing & Validation
- [ ] Start JARVIS: `python main.py`
- [ ] Test multiline: Type, Shift+Enter for newline
- [ ] Test autocomplete: `/m[TAB]` works
- [ ] Test history: `/history` shows messages
- [ ] Test history search: `/history search` finds words
- [ ] Test session nav: Alt+↑/↓ switches sessions
- [ ] Check prompt: Shows current session name
- [ ] Verify history.json created: `ls history.json`
- [ ] All Phase 2 features working: ✅

**Phase 2 Complete - MVP READY:** Date: ___________

✅ **YOU CAN USE JARVIS DAILY NOW** ✅

---

## 🔵 Phase 3: Voice Enhancement (6-8 hours) [OPTIONAL]

### Wake Word Detection
- [ ] Read: PHASE_3_GUIDE.md - Feature 1
- [ ] Install: `pip install pocketsphinx pyaudio`
- [ ] Create: `core/wake_word.py`
  - [ ] `WakeWordDetector` class
  - [ ] `SimpleWakeWordDetector` fallback
  - [ ] Listener thread
  - [ ] `get_wake_word_detector()` singleton
- [ ] Test: `python core/wake_word.py`
- [ ] Commit: "feat(phase-3): Add wake word detection"

### Speech-to-Text
- [ ] Read: PHASE_3_GUIDE.md - Feature 2
- [ ] Install: `pip install openai-whisper`
- [ ] Create: `core/stt.py`
  - [ ] `SpeechToText` class with Whisper
  - [ ] `transcribe_file()` method
  - [ ] `record_and_transcribe()` method
  - [ ] Language detection
  - [ ] `get_stt()` singleton
- [ ] Test: `python core/stt.py` → record and transcribe
- [ ] Commit: "feat(phase-3): Add speech-to-text"

### Voice Interruption
- [ ] Read: PHASE_3_GUIDE.md - Feature 3
- [ ] Modify: `core/voice_engine.py`
  - [ ] Add `interrupt_requested` flag
  - [ ] Add `request_interrupt()` method
  - [ ] Check interrupt in `_play_chunk()`
- [ ] Test: Can interrupt TTS mid-sentence
- [ ] Commit: "feat(phase-3): Add voice interruption"

### Voice Model Selection
- [ ] Read: PHASE_3_GUIDE.md - Feature 4
- [ ] Modify: `core/commands.py`
  - [ ] Add `handle_voice_command()`
  - [ ] Add "voice" to COMMANDS registry
- [ ] Test: `/voice list` shows models
- [ ] Test: `/voice set [name]` works
- [ ] Commit: "feat(phase-3): Add voice model command"

### Phase 3 Testing & Validation
- [ ] Say "Ehi JARVIS" → triggers STT
- [ ] STT transcribes correctly
- [ ] Can interrupt TTS
- [ ] `/voice list` shows models
- [ ] `/voice current` shows settings
- [ ] All Phase 3 features working: ✅

**Phase 3 Complete:** Date: ___________

---

## 🟣 Phase 4: Tool System (5-6 hours) [OPTIONAL]

### Tool Base Interface
- [ ] Read: PHASE_4_GUIDE.md - Feature 1
- [ ] Create: `core/tools/base.py`
  - [ ] `ToolParameter` dataclass
  - [ ] `Tool` abstract base class
  - [ ] Schema generation
  - [ ] Parameter validation
- [ ] Test: `python core/tools/base.py`
- [ ] Commit: "feat(phase-4): Add tool base interface"

### Plugin Loader
- [ ] Read: PHASE_4_GUIDE.md - Feature 2
- [ ] Create: `core/tools/plugin_loader.py`
  - [ ] `PluginLoader` class
  - [ ] Auto-discovery from plugins/ folder
  - [ ] `get_plugin_loader()` singleton
- [ ] Create: `mkdir -p core/tools/plugins/`
- [ ] Test: `python core/tools/plugin_loader.py`
- [ ] Commit: "feat(phase-4): Add plugin loader"

### Web Search Tool
- [ ] Read: PHASE_4_GUIDE.md - Feature 3
- [ ] Install: `pip install duckduckgo-search`
- [ ] Create: `core/tools/plugins/web_search.py`
  - [ ] `WebSearchTool` class
  - [ ] DuckDuckGo integration
- [ ] Test: Web search returns results
- [ ] Commit: "feat(phase-4): Add web search tool"

### Filesystem Tool
- [ ] Read: PHASE_4_GUIDE.md - Feature 4
- [ ] Create: `core/tools/plugins/filesystem.py`
  - [ ] `FilesystemTool` class
  - [ ] Read/write/list/delete operations
  - [ ] Security (path traversal prevention)
- [ ] Create: `mkdir -p jarvis_files/`
- [ ] Test: Read/write files in jarvis_files/
- [ ] Commit: "feat(phase-4): Add filesystem tool"

### Tool Router Integration
- [ ] Modify: `core/tools/router.py`
  - [ ] Wire plugin loader
  - [ ] Route queries to tools
- [ ] Test: Tools are discovered and called
- [ ] Commit: "feat(phase-4): Integrate tool routing"

### Phase 4 Testing & Validation
- [ ] Plugin loader discovers tools
- [ ] Web search returns results
- [ ] Filesystem operations work
- [ ] Tools routed correctly from queries
- [ ] All Phase 4 features working: ✅

**Phase 4 Complete:** Date: ___________

---

## 🟢 Phase 5: Advanced Memory (4-5 hours) [OPTIONAL]

### Vector Database
- [ ] Read: PHASE_5_GUIDE.md - Feature 1
- [ ] Install: `pip install chromadb sentence-transformers`
- [ ] Create: `core/vector_db.py`
  - [ ] `VectorDatabase` class with ChromaDB
  - [ ] `add_message()` method
  - [ ] `search_similar()` method
  - [ ] `get_user_context()` method
- [ ] Test: Messages stored and searched by similarity
- [ ] Commit: "feat(phase-5): Add vector database"

### Auto-Compression
- [ ] Read: PHASE_5_GUIDE.md - Feature 2
- [ ] Create: `core/summarizer.py`
  - [ ] `ConversationSummarizer` class
  - [ ] Age-based compression logic
  - [ ] `compress_memory()` method
- [ ] Test: Old messages compressed
- [ ] Commit: "feat(phase-5): Add auto-compression"

### User Profile
- [ ] Read: PHASE_5_GUIDE.md - Feature 3
- [ ] Create: `core/user_profile.py`
  - [ ] `UserProfile` class
  - [ ] Preference learning
  - [ ] `record_interaction()` method
  - [ ] `get_user_profile()` singleton
- [ ] Modify: `core/commands.py`
  - [ ] Add `/profile` command
- [ ] Test: Profile learns from interactions
- [ ] Commit: "feat(phase-5): Add user profile"

### Memory Commands
- [ ] Modify: `core/commands.py`
  - [ ] Add `/memory search [query]` command
- [ ] Test: `/memory search` finds by semantic similarity
- [ ] Commit: "feat(phase-5): Add memory search command"

### Phase 5 Testing & Validation
- [ ] Vector DB stores and searches messages
- [ ] Compression summarizes old messages
- [ ] Profile learns preferences
- [ ] `/memory search` works
- [ ] `/profile` shows learned info
- [ ] All Phase 5 features working: ✅

**Phase 5 Complete:** Date: ___________

---

## 🔴 Phase 6: Architecture & Testing (5-6 hours) [OPTIONAL]

### Pydantic Configuration
- [ ] Read: PHASE_6_GUIDE.md - Feature 1
- [ ] Refactor: `config.py`
  - [ ] Import Pydantic models
  - [ ] Create `OllamaConfig`, `VoiceConfig`, etc.
  - [ ] Add validation
  - [ ] Add environment variable support
- [ ] Test: Config loads and validates correctly
- [ ] Commit: "refactor(phase-6): Use Pydantic for config"

### JSON Logging
- [ ] Read: PHASE_6_GUIDE.md - Feature 2
- [ ] Refactor: `logger.py`
  - [ ] Add `JSONFormatter` class
  - [ ] Implement log rotation
  - [ ] Add structured fields
- [ ] Test: logs/jarvis.log has JSON format
- [ ] Commit: "refactor(phase-6): Add JSON structured logging"

### pytest Test Suite
- [ ] Read: PHASE_6_GUIDE.md - Feature 3
- [ ] Install: `pip install pytest pytest-cov`
- [ ] Create: `tests/` directory
  - [ ] `__init__.py`
  - [ ] `conftest.py` (fixtures)
  - [ ] `test_config.py`
  - [ ] `test_memory.py`
  - [ ] `test_commands.py`
  - [ ] `test_voice_engine.py`
  - [ ] `test_tools.py`
  - [ ] `test_integration.py`
- [ ] Test: `pytest tests/ -v`
- [ ] Target: 80%+ coverage
- [ ] Commit: "test(phase-6): Add comprehensive test suite"

### Error Recovery
- [ ] Read: PHASE_6_GUIDE.md - Feature 5
- [ ] Add fallbacks to major modules:
  - [ ] Ollama fallback in llm.py
  - [ ] TTS fallback in voice_engine.py
  - [ ] STT fallback in stt.py
- [ ] Test: All fallbacks work gracefully
- [ ] Commit: "feat(phase-6): Add error recovery fallbacks"

### Phase 6 Testing & Validation
- [ ] Config validation works
- [ ] JSON logs parseable
- [ ] pytest coverage 80%+
- [ ] All tests passing
- [ ] Error recovery functional
- [ ] All Phase 6 features working: ✅

**Phase 6 Complete - PRODUCTION READY:** Date: ___________

---

## 🎯 Final Validation

### Complete System Test
- [ ] Start: `python main.py`
- [ ] Test all commands: `/help`, `/memory`, `/session`, etc.
- [ ] Test voice (if Phase 3): Wake word, STT, TTS
- [ ] Test tools (if Phase 4): `/web_search`, filesystem ops
- [ ] Check logs: `tail -f logs/jarvis.log`
- [ ] Run tests: `pytest tests/ --cov=core`
- [ ] Everything working: ✅

### Documentation
- [ ] Update `QUICKSTART.md` with your setup
- [ ] Create `DEPLOYMENT.md` for production
- [ ] Document custom tools/extensions added
- [ ] Create troubleshooting guide

### Git
- [ ] All phases committed
- [ ] Clean git history: `git log --oneline`
- [ ] Tag final version: `git tag v3.0.0`
- [ ] Push to repository

**JARVIS v3.0 COMPLETE:** Date: ___________

---

## 📊 Summary

| Phase | Status | Date | Hours |
|-------|--------|------|-------|
| 0 | ⬜ | ___ | 2-3h |
| 1 | ⬜ | ___ | 5h |
| 2 | ⬜ | ___ | 5-7h |
| 3 | ⬜ | ___ | 6-8h |
| 4 | ⬜ | ___ | 5-6h |
| 5 | ⬜ | ___ | 4-5h |
| 6 | ⬜ | ___ | 5-6h |

**Total Time: 32-45 hours**

---

Created: 30 Apr 2026  
Type: Implementation Checklist  
Status: Ready to use

