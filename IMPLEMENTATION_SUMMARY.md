# JARVIS v3.0 - Implementation Plan Summary

📅 **30 April 2026** | **32-45 hours** | **6 Phases** | **40+ features**

---

## 🎯 Quick Overview

Your requirements organized into **6 implementation phases** with dependencies mapped:

```
QUICK WINS (2-3h)
  ├─ 📊 Token counter
  ├─ 🔄 /model switch
  ├─ 📝 Markdown render
  └─ 📤 /export chat
         ↓
PHASE 1: ROBUSTEZZA CORE (4-6h) ← START HERE
  ├─ 🛡️ Retry + circuit breaker
  ├─ 💬 Streaming live in UI
  ├─ 📦 Sessioni multiple
  └─ 🧠 Memoria per sessione
         ↓
PHASE 2: UX & CLI (5-7h)
  ├─ 📝 Input multiriga (Shift+Enter)
  ├─ 🔍 Autocompletamento /cmd
  ├─ 📜 Cronologia persistente
  └─ ↑↓ Navigation tra sessioni
         ↓
PHASE 3: VOICE (6-8h) ← OPTIONAL (external deps)
  ├─ 🎤 Wake word ("Ehi JARVIS")
  ├─ 🔊 STT (transcription)
  ├─ 🤐 Interruzione voce
  └─ 🎵 /voice model [nome]
         ↓
PHASE 4: TOOL SYSTEM (5-6h)
  ├─ 🔧 Tool base interface
  ├─ 🔌 Plugin loader
  ├─ 🌐 Web search (DuckDuckGo)
  └─ 📁 File system tool
         ↓
PHASE 5: MEMORIA AVANZATA (4-5h)
  ├─ 🧬 ChromaDB + vector search
  ├─ 📊 Embeddings
  ├─ 🗜️ Auto-compressione memoria
  └─ 👤 Profilo utente persistente
         ↓
PHASE 6: ARCHITETTURA (5-6h)
  ├─ 📐 Pydantic config validation
  ├─ 📋 JSON structured logging
  ├─ ✅ pytest test suite
  └─ 🔄 Log rotation + search
```

---

## 📊 Phase Dependency Matrix

| Phase | Effort | Time | Requires | Blocks |
|-------|--------|------|----------|--------|
| **Quick Wins** | 🟢 Low | 2-3h | None | - |
| **Phase 1** | 🟡 Medium | 4-6h | Quick Wins | Phase 2 |
| **Phase 2** | 🟡 Medium | 5-7h | Phase 1 | Streaming UX |
| **Phase 3** | 🔴 High | 6-8h | External APIs | Voice commands |
| **Phase 4** | 🟡 Medium | 5-6h | Phase 2 | Plugin ecosystem |
| **Phase 5** | 🟡 Medium | 4-5h | Phase 4 | RAG search |
| **Phase 6** | 🟡 Medium | 5-6h | All phases | Production ready |

---

## 🚀 Recommended Implementation Order

### Path A: Fast MVP (16-19 hours)
```
Quick Wins (2-3h)
  ↓
Phase 1 (4-6h)        ← Core stability
  ↓
Phase 2 (5-7h)        ← Better CLI/UX
  ↓
DONE: Deployable AI assistant with retry, sessions, CLI UX
```

### Path B: Full Feature Set (32-45 hours)
```
Quick Wins → Phase 1 → Phase 2 → Phase 3 (skip if no audio) 
  → Phase 4 → Phase 5 → Phase 6
```

### Path C: Voice-Focused (25-30 hours)
```
Quick Wins → Phase 1 → Phase 2 → Phase 3 (audio) → Phase 6 (tests)
```

---

## 📂 Files to Create/Modify

### NEW FILES (14 files)
```
core/
  ├─ token_counter.py              [Phase 0]
  ├─ retry_handler.py              [Phase 1] 🔴
  ├─ session_manager.py            [Phase 1] 🔴
  ├─ history.py                    [Phase 2]
  ├─ wake_word.py                  [Phase 3] (optional)
  ├─ stt.py                        [Phase 3] (optional)
  ├─ vector_db.py                  [Phase 5]
  ├─ embeddings.py                 [Phase 5]
  ├─ summarizer.py                 [Phase 5]
  ├─ user_profile.py               [Phase 5]
  ├─ export.py                     [Phase 0]
  └─ tools/
      ├─ base.py                   [Phase 4]
      ├─ plugin_loader.py          [Phase 4]
      ├─ web_search.py             [Phase 4]
      └─ filesystem.py             [Phase 4]

tests/
  ├─ test_retry.py                 [Phase 6]
  ├─ test_llm.py                   [Phase 6]
  ├─ test_tools.py                 [Phase 6]
  └─ test_sessions.py              [Phase 6]

docs/
  ├─ IMPLEMENTATION_ROADMAP.md     [New]
  ├─ PHASE_0_GUIDE.md              [New]
  └─ PHASE_1_GUIDE.md              [To create]
```

### MODIFIED FILES (5 files)
```
core/
  ├─ commands.py                   [Phase 0, 2]
  ├─ memory.py                     [Phase 1, 5]
  ├─ voice_engine.py               [Phase 3]
  └─ llm.py                        [Phase 0, 1]

ui/
  └─ cli.py                        [Phase 0, 1, 2]

config.py                          [Phase 6]
logger.py                          [Phase 6]
requirements.txt                   [All phases]
```

---

## 📦 New Dependencies by Phase

```bash
# Phase 0: None (already have rich)

# Phase 1-2: None (already have prompt-toolkit)

# Phase 3: Voice (optional)
pip install openai-whisper pyaudio

# Phase 4: Web search
pip install duckduckgo-search

# Phase 5: Memory + Embeddings
pip install chromadb sentence-transformers

# Phase 6: Config + Testing
pip install pydantic pytest python-json-logger

# TOTAL: pip install pydantic duckduckgo-search chromadb sentence-transformers pytest openai-whisper pyaudio python-json-logger
```

---

## 🎬 Getting Started - Next Steps

### Immediate (Now)
1. ✅ Read [IMPLEMENTATION_ROADMAP.md](./IMPLEMENTATION_ROADMAP.md) - detailed specs
2. ✅ Read [PHASE_0_GUIDE.md](./PHASE_0_GUIDE.md) - step-by-step
3. Review the 4 quick-win features

### Quick Wins (Today - 2-3 hours)
1. Implement token counter (`core/token_counter.py`)
2. Add `/model` command (`core/commands.py`)
3. Enable markdown rendering (`ui/cli.py`)
4. Add `/export` command (`core/export.py`)

### Phase 1 (This Week - 4-6 hours)
1. Build retry + circuit breaker
2. Implement streaming live UI
3. Create session manager
4. Add session-aware memory

---

## 💡 Key Design Principles for v3.0

1. **Modularity** - Each phase is independent, can deploy incrementally
2. **Backward compatibility** - New features don't break existing CLI
3. **Error resilience** - Graceful degradation (markdown fallback, retry backoff)
4. **Logging everywhere** - Debug with structured JSON logs
5. **Config-driven** - Behavior via `jarvis_config.json` not hardcoding
6. **Testing first** - Phase 6 adds comprehensive pytest suite

---

## 📈 Estimated Timeline

| Milestone | Date | Features |
|-----------|------|----------|
| Quick Wins | 30 Apr | Token counter, model switch, markdown, export |
| Phase 1 Complete | 2 May | Retry, sessions, streaming UI |
| Phase 2 Complete | 5 May | CLI UX (multiline, autocomplete, history) |
| Phase 3 Complete | 9 May | Voice (if priority) |
| Phase 4 Complete | 12 May | Plugin system, web search, file ops |
| **MVP Ready** | **5 May** | Phases 0-2 (recommended stopping point) |
| Full v3.0 | 20 May | All phases + testing |

---

## 🎯 Quick Wins: What You Get

After 2-3 hours (Phase 0):

```
✅ Token counter:
   > 2 + 2
   JARVIS: Il risultato è 4
   📊 Tokens: 12 prompt + 8 completion = 20 total

✅ Model switch:
   > /model list
   📦 Available Models: mistral, neural-chat, dolphin, ...
   > /model set neural-chat
   ✅ Model switched to: neural-chat

✅ Markdown rendering:
   > Dammi 3 motivi per usare AI
   JARVIS: 
   ## Motivi per usare AI
   - **Automazione** - riduce tempo manuale
   - **Precisione** - meno errori umani
   - **Scalabilità** - gestisce volumi grandi

✅ Export chat:
   > /export my_chat
   ✅ Chat exported to: exports/my_chat.md
   # (file created with formatted conversation)
```

---

## ⚡ Why This Order?

**Quick Wins first** because:
- No dependencies (0 new `pip install`)
- High UX impact (visible immediately)
- Foundation for Phase 1 (token counter + export used later)
- Confidence builder (4 features in 2-3 hours 💪)

**Phase 1 (Robustezza) second** because:
- Core infrastructure for future phases
- Fixes "Ollama offline" pain point
- Enables sessions (Phase 2 dependency)
- Prerequisite for streaming UI (Phase 2)

**Phase 2 (UX/CLI)** because:
- Builds on Phase 1 infrastructure
- Major QoL improvements
- Reaches MVP status (all priorities 1-2 satisfied)

---

## 🔗 Documentation Structure

```
root/
├─ IMPLEMENTATION_ROADMAP.md     ← Master plan (this file)
├─ PHASE_0_GUIDE.md              ← Step-by-step Phase 0
├─ PHASE_1_GUIDE.md              ← Coming (Phase 1 details)
├─ QUICKSTART.md                 ← User guide (update after each phase)
├─ IMPROVEMENTS.md               ← Changelog v2.0
└─ README.md                     ← Project overview
```

---

## 🆘 Support & Questions

- **Architecture questions?** → See `IMPLEMENTATION_ROADMAP.md` design sections
- **Implementation details?** → See `PHASE_0_GUIDE.md` for Phase 0, etc.
- **Testing approach?** → See Phase 6 section
- **Timeline concerns?** → Adjust phases based on priority

---

## ✨ Success Metrics

After each phase, verify:

| Phase | Success = |
|-------|-----------|
| **0** | 4/4 quick wins working, no errors in logs |
| **1** | Ollama offline → retry works, streaming shows live, 2 sessions created |
| **2** | Multiline input works, /cmd autocomplete, ↑↓ navigation, history.json created |
| **3** | Microphone detects wake word, STT transcribes, /voice model works |
| **4** | Plugin loads from folder, web search returns results, file tool reads/writes |
| **5** | ChromaDB stores messages, query returns context, summarizer compresses memory |
| **6** | pytest shows 15+ passing tests, JSON logs structured, config validates |

---

**Created:** 30 Apr 2026  
**Author:** JARVIS Development Team  
**Status:** Ready for implementation  
**Next:** Start Phase 0 with [PHASE_0_GUIDE.md](./PHASE_0_GUIDE.md)

