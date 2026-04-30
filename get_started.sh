#!/bin/bash
# JARVIS v3.0 — Getting Started Script
# Run this to navigate the documentation

cd "$(dirname "$0")" 2>/dev/null || cd /home/gaetal/Desktop/jarvis-core-fixed

echo "╔════════════════════════════════════════════════════╗"
echo "║  JARVIS v3.0 — Getting Started                     ║"
echo "║  30 April 2026                                     ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""
echo "Welcome! 👋"
echo ""
echo "This is a complete implementation plan for JARVIS v3.0"
echo "with 40+ features organized into 6 phases."
echo ""
echo "Total effort: 32-45 hours"
echo "MVP ready: 16-19 hours (Phases 0-2)"
echo ""
echo "═════════════════════════════════════════════════════"
echo ""
echo "Choose what to do:"
echo ""
echo "  1) 📖 Read START_HERE.md (5 min overview)"
echo "  2) 📖 Read QUICK_REFERENCE.md (print-friendly card)"
echo "  3) 📖 Read PHASE_0_GUIDE.md (ready to code)"
echo "  4) 📖 Read IMPLEMENTATION_SUMMARY.md (big picture)"
echo "  5) 📖 List all documentation files"
echo "  6) 🚀 Start Phase 0 implementation"
echo "  7) 🛠️ Show project structure"
echo "  8) 📋 Show timeline summary"
echo "  0) ❌ Exit"
echo ""
echo "═════════════════════════════════════════════════════"
echo ""
read -p "Enter your choice (0-8): " choice

case $choice in
  1)
    echo ""
    echo "Opening START_HERE.md..."
    echo ""
    less START_HERE.md
    ;;
  2)
    echo ""
    echo "Opening QUICK_REFERENCE.md..."
    echo ""
    less QUICK_REFERENCE.md
    ;;
  3)
    echo ""
    echo "Opening PHASE_0_GUIDE.md..."
    echo ""
    less PHASE_0_GUIDE.md
    ;;
  4)
    echo ""
    echo "Opening IMPLEMENTATION_SUMMARY.md..."
    echo ""
    less IMPLEMENTATION_SUMMARY.md
    ;;
  5)
    echo ""
    echo "Documentation files:"
    echo ""
    ls -lh *.md | grep -E "(START|QUICK|IMPLEMENTATION|PHASE|DOCUMENTATION|DELIVERY|FINAL)" | awk '{printf "  %-40s %8s\n", $9, $5}'
    echo ""
    ;;
  6)
    echo ""
    echo "Phase 0 Implementation Plan:"
    echo ""
    echo "  Features (2-3 hours total):"
    echo "    1. Token Counter        (25-30 min)  → core/token_counter.py"
    echo "    2. /model switch        (20-25 min)  → core/commands.py"
    echo "    3. Markdown Rendering   (15-20 min)  → ui/cli.py"
    echo "    4. Chat Export          (30-40 min)  → core/export.py"
    echo ""
    echo "  Ready to start? Open PHASE_0_GUIDE.md and follow:"
    echo "    1. Read implementation details"
    echo "    2. Create files one by one"
    echo "    3. Reference PHASE_0_GUIDE.md while coding"
    echo "    4. Check off items in PHASE_0_CHECKLIST.sh"
    echo ""
    echo "  First step:"
    echo "    mkdir exports/"
    echo "    touch core/token_counter.py"
    echo "    # Then follow PHASE_0_GUIDE.md"
    echo ""
    ;;
  7)
    echo ""
    echo "Project Structure:"
    echo ""
    echo "jarvis-core-fixed/"
    echo "├── 📄 Documentation (NEW!):"
    echo "│   ├── START_HERE.md                 ← Read first"
    echo "│   ├── QUICK_REFERENCE.md           ← Keep handy"
    echo "│   ├── IMPLEMENTATION_SUMMARY.md    ← Overview"
    echo "│   ├── PHASE_0_GUIDE.md             ← How to code Phase 0"
    echo "│   ├── PHASE_0_CHECKLIST.sh         ← Checklist"
    echo "│   ├── IMPLEMENTATION_ROADMAP.md    ← Full spec"
    echo "│   ├── DOCUMENTATION_INDEX.md       ← Index"
    echo "│   └── DELIVERY_MANIFEST.md         ← This delivery"
    echo "│"
    echo "├── 💻 Source Code:"
    echo "│   ├── main.py"
    echo "│   ├── config.py"
    echo "│   ├── logger.py"
    echo "│   ├── core/"
    echo "│   ├── controller/"
    echo "│   ├── ui/"
    echo "│   └── voices/"
    echo "│"
    echo "└── 📦 Support Files:"
    echo "    ├── jarvis_config.json"
    echo "    ├── requirements.txt"
    echo "    ├── memory.json"
    echo "    └── logs/"
    echo ""
    ;;
  8)
    echo ""
    echo "Implementation Timeline:"
    echo ""
    echo "Phase 0: Quick Wins            2-3 hours"
    echo "├─ Token Counter              25-30 min"
    echo "├─ /model switch              20-25 min"
    echo "├─ Markdown Rendering         15-20 min"
    echo "└─ Chat Export                30-40 min"
    echo ""
    echo "Phase 1: Robustezza Core       4-6 hours"
    echo "├─ Retry + Circuit Breaker"
    echo "├─ Streaming Live UI"
    echo "├─ Sessions Multiple"
    echo "└─ Memory per Conversation"
    echo ""
    echo "Phase 2: UX & CLI              5-7 hours"
    echo "├─ Input Multiriga (Shift+Enter)"
    echo "├─ Autocompletamento"
    echo "├─ Cronologia Persistente"
    echo "└─ Navigation ↑↓"
    echo ""
    echo "═══════════════════════════════════════════════════"
    echo "= MVP READY                   16-19 hours total ==="
    echo "═══════════════════════════════════════════════════"
    echo ""
    echo "Phase 3: Voice (optional)      6-8 hours"
    echo "Phase 4: Tool System           5-6 hours"
    echo "Phase 5: Memory Advanced       4-5 hours"
    echo "Phase 6: Architecture          5-6 hours"
    echo ""
    echo "FULL SYSTEM:                   32-45 hours total"
    echo ""
    ;;
  0)
    echo ""
    echo "Goodbye! 👋"
    echo ""
    echo "Next step: Read START_HERE.md"
    echo "  cat START_HERE.md"
    echo ""
    ;;
  *)
    echo ""
    echo "❌ Invalid choice. Exiting."
    echo ""
    ;;
esac

echo ""
echo "═════════════════════════════════════════════════════"
echo "Remember: Everything you need is documented!"
echo "═════════════════════════════════════════════════════"
echo ""
