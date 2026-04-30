# JARVIS v3.0 — Quick Reference Card

**Print this or keep it open while coding**

---

## 🎯 What Are We Building?

6-phase implementation plan: **32-45 hours** total  
**MVP (Phase 0-2):** 16-19 hours  
**Quick Wins only:** 2-3 hours  

---

## 📋 Phase Quick Reference

| Phase | Name | Duration | Key Feature | Effort | Start When |
|-------|------|----------|-------------|--------|-----------|
| 0 | Quick Wins | 2-3h | Token counter, /model, markdown, /export | 🟢 Low | NOW |
| 1 | Robustezza | 4-6h | Retry, streaming, sessions | 🟡 Med | After Phase 0 |
| 2 | UX & CLI | 5-7h | Multiline, autocomplete, history | 🟡 Med | After Phase 1 |
| 3 | Voice | 6-8h | Wake word, STT, interruption | 🔴 High | Optional |
| 4 | Tools | 5-6h | Plugin system, web search | 🟡 Med | After Phase 2 |
| 5 | Memory | 4-5h | ChromaDB, embeddings, summarizer | 🟡 Med | After Phase 4 |
| 6 | Architecture | 5-6h | Pydantic, JSON logs, tests | 🟡 Med | Last |

---

## 🚀 Phase 0 — 4 Quick Wins (2-3 hours)

### Feature 1: Token Counter (25-30 min)
```
File: core/token_counter.py
What: Show tokens used per request
Test: python core/token_counter.py
Output format: 📊 Tokens: X prompt + Y completion = Z total
```

### Feature 2: /model switch (20-25 min)
```
File: core/commands.py (modify)
What: Switch LLM model live
Commands:
  /model list       → show available models
  /model set [name] → switch to model
  /model current    → show active model
Test: /model list → /model set neural-chat → /model current
```

### Feature 3: Markdown Rendering (15-20 min)
```
File: ui/cli.py (modify)
What: Render markdown in responses
Support: **bold**, *italic*, `code`, # headers, - lists
Test: Ask for formatted list, verify bullets render
```

### Feature 4: Chat Export (30-40 min)
```
File: core/export.py (new)
What: Save chat to .md file
Command: /export [optional_filename]
Output: exports/jarvis_chat_TIMESTAMP.md
Test: /export → check exports/ directory
```

---

## 🛠️ New Files Checklist

### Phase 0 (Create These)
```
✓ core/token_counter.py        ~150 lines
✓ core/export.py               ~100 lines
✓ exports/                      (directory)
```

### Phase 0 (Modify These)
```
✓ core/commands.py             (add 2 functions)
✓ ui/cli.py                    (add markdown rendering)
✓ core/llm.py                  (optional: token tracking)
```

---

## 🔄 Implementation Order

### Day 1 (2-3 hours)
1. Token Counter (30 min)
   - Create core/token_counter.py
   - Test locally
   - Integrate into LLM response

2. /model switch (25 min)
   - Add get_available_models() function
   - Add handle_model_command() function
   - Add to COMMANDS registry

3. Markdown Rendering (20 min)
   - Import Markdown from rich
   - Add _has_markdown() check
   - Update render_jarvis_panel()

4. Chat Export (40 min)
   - Create ChatExporter class
   - Add handle_export_command()
   - Test file creation

### Full Integration Test (30 min)
```bash
python main.py

# Test each feature:
2 + 2                    # Check token counter
/model list              # Check models available
/model set neural-chat   # Switch model
Dammi 5 colori          # Check markdown
/export test            # Check exports/ directory
```

---

## 💾 Git Workflow for Phase 0

```bash
# Start
git checkout -b feature/phase-0-quick-wins

# Commit 1: Token counter
git add core/token_counter.py
git commit -m "feat: add token counter for LLM usage tracking"

# Commit 2: Model switch
git add core/commands.py
git commit -m "feat: add /model command for live model switching"

# Commit 3: Markdown
git add ui/cli.py
git commit -m "feat: add markdown rendering in responses"

# Commit 4: Export
git add core/export.py core/commands.py
git commit -m "feat: add chat export to markdown"

# Commit 5: Docs
git add QUICKSTART.md IMPROVEMENTS.md
git commit -m "docs: update guides for Phase 0"

# Final
git push -u origin feature/phase-0-quick-wins
```

---

## ⚠️ Common Issues

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: rich` | Already installed (used in cli.py) |
| `/model list` fails | Verify Ollama running: `ollama serve` |
| Export file not created | Check `exports/` directory exists |
| Markdown not rendering | Verify `_has_markdown()` detects patterns |
| Token counter import fails | Check `core/token_counter.py` created |

---

## 🧪 Testing Checklist

### Token Counter
- [x] `python core/token_counter.py` runs without error
- [x] Estimate tokens for sample text
- [x] Format output with 📊 emoji
- [x] Integrated in LLM response display

### /model switch
- [x] `/model list` shows 2+ models
- [x] `/model set [valid_model]` succeeds
- [x] `/model set invalid_model` shows error
- [x] `/model current` shows active model

### Markdown Rendering
- [x] Response with **bold** renders bold
- [x] Response with - bullets renders as list
- [x] Response with # headers renders as header
- [x] Plain text still works (no markdown detected)

### Chat Export
- [x] `/export` creates file in exports/
- [x] Filename format: jarvis_chat_YYYYMMDD_HHMMSS.md
- [x] File contains conversation formatted as markdown
- [x] File has header + footer metadata

---

## 🔗 Reference Links

- **Details:** PHASE_0_GUIDE.md (full implementation guide)
- **Checklist:** PHASE_0_CHECKLIST.sh (task-by-task)
- **All Features:** IMPLEMENTATION_ROADMAP.md (all phases)
- **Timeline:** IMPLEMENTATION_SUMMARY.md (phases overview)

---

## 📊 Success Criteria

Phase 0 = SUCCESS when:

✅ All 4 features working  
✅ No import errors  
✅ No crashes in CLI  
✅ Logs show no ERROR  
✅ Git commits created  
✅ Ready to move to Phase 1  

**Estimated time:** 2-3 hours  
**Blocking Phase 1?** No (can start Phase 1 anytime)  

---

## 🚀 After Phase 0

### Immediate Next Steps
1. Review Phase 1 guide
2. Implement retry + circuit breaker
3. Add streaming response display
4. Create session manager

### Phase 1 Timeline
- Duration: 4-6 hours
- Focus: Core robustezza
- Impact: Offline resilience + better UX

### By End of Phase 2 (16-19h total)
✅ MVP complete with all Priority 1-2 features

---

## 📞 Quick Help

**Need implementation details?**  
→ PHASE_0_GUIDE.md

**Need task checklist?**  
→ PHASE_0_CHECKLIST.sh

**Need architecture overview?**  
→ IMPLEMENTATION_ROADMAP.md

**Need timeline?**  
→ IMPLEMENTATION_SUMMARY.md

**Need code examples?**  
→ PHASE_0_GUIDE.md (each feature has code)

---

## ⏱️ Time Budget

```
Token Counter:     25-30 min
/model switch:     20-25 min
Markdown render:   15-20 min
Chat export:       30-40 min
Integration test:  20-25 min
Documentation:     10-15 min
─────────────────────────────
TOTAL:             2-3 hours
```

---

**Keep this card handy while implementing Phase 0!**

30 Apr 2026 | JARVIS v3.0 Ready

