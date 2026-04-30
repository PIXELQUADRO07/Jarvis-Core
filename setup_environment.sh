#!/bin/bash
# JARVIS v3.0 Environment Setup Script
# Prepares workspace directories and validates prerequisites

set -e

echo "🚀 JARVIS v3.0 Environment Setup"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Python version
echo "📋 Checking Python..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Python version: $PYTHON_VERSION"
if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' 2>/dev/null; then
    echo -e "${RED}✗ Python 3.8+ required${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python 3.8+ available${NC}"
echo ""

# Create directories
echo "📁 Creating directories..."
DIRS=(
    "memory_sessions"
    "jarvis_files"
    "exports"
    "logs"
    "core/tools/plugins"
    "tests"
    ".chromadb"
)

for dir in "${DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        echo "   Created: $dir"
    else
        echo "   Exists: $dir"
    fi
done
echo -e "${GREEN}✓ Directories ready${NC}"
echo ""

# Check Python packages
echo "📦 Checking Python packages..."
REQUIRED_PACKAGES=(
    "rich"
    "prompt_toolkit"
    "requests"
)

MISSING=()
for package in "${REQUIRED_PACKAGES[@]}"; do
    if python3 -c "import $package" 2>/dev/null; then
        echo "   ✓ $package"
    else
        echo "   ✗ $package (missing)"
        MISSING+=("$package")
    fi
done

if [ ${#MISSING[@]} -gt 0 ]; then
    echo ""
    echo "⚠️  Installing missing packages..."
    pip install "${MISSING[@]}" || {
        echo -e "${RED}✗ Failed to install packages${NC}"
        exit 1
    }
fi
echo -e "${GREEN}✓ All required packages available${NC}"
echo ""

# Check Ollama
echo "🤖 Checking Ollama..."
if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✓ Ollama installed${NC}"
else
    echo -e "${YELLOW}⚠ Ollama not found (required for Phase 0)${NC}"
    echo "   Install from: https://ollama.ai"
fi
echo ""

# Setup git
echo "📝 Setting up git..."
if [ ! -d ".git" ]; then
    git init
    echo "   Initialized git repository"
else
    echo "   Git repository exists"
fi

# Create .gitignore entries if not present
if ! grep -q "venv" .gitignore 2>/dev/null; then
    cat >> .gitignore << 'EOF'

# Python
venv/
__pycache__/
*.pyc
*.pyo
*.egg-info/
dist/
build/

# Project
.chromadb/
logs/
jarvis_files/
memory_sessions/
history.json
user_profile.json
jarvis_chat_*.md
.env
*.log

# IDE
.vscode/
.idea/
*.swp
*.swo

EOF
    echo "   Updated .gitignore"
fi
echo -e "${GREEN}✓ Git configured${NC}"
echo ""

# Create config
echo "⚙️  Checking configuration..."
if [ ! -f "jarvis_config.json" ]; then
    cat > jarvis_config.json << 'EOF'
{
  "name": "JARVIS",
  "version": "3.0.0",
  "ollama": {
    "host": "localhost",
    "port": 11434,
    "model": "mistral",
    "timeout": 60
  },
  "voice": {
    "enabled": true,
    "model": "it_IT-riccardo-x_low",
    "speed": 1.0,
    "volume": 1.0
  },
  "memory": {
    "max_history": 100,
    "memory_dir": "memory_sessions",
    "vector_db_dir": ".chromadb",
    "compression_days": 7
  },
  "logging": {
    "level": "INFO",
    "format": "text",
    "output": "logs/jarvis.log",
    "max_bytes": 10000000,
    "backup_count": 5
  }
}
EOF
    echo "   Created jarvis_config.json"
else
    echo "   Configuration exists"
fi
echo -e "${GREEN}✓ Configuration ready${NC}"
echo ""

# Check Ollama is running
echo "🔌 Checking Ollama service..."
if timeout 2 curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Ollama service running${NC}"
else
    echo -e "${YELLOW}⚠ Ollama service not responding${NC}"
    echo "   Start Ollama with: ollama serve"
fi
echo ""

# Display next steps
echo "✅ Setup complete!"
echo ""
echo "📚 Next steps:"
echo "   1. Read:   cat START_HERE.md"
echo "   2. Read:   cat PHASE_0_GUIDE.md"
echo "   3. Start:  python main.py"
echo ""
echo "📖 Phase breakdown:"
echo "   Phase 0 (2-3h):  Quick Wins - token counter, /model, exports"
echo "   Phase 1 (5h):    Robustezza - retry logic, sessions, streaming"
echo "   Phase 2 (5-7h):  UX - autocomplete, history, navigation = MVP"
echo "   Phase 3 (6-8h):  Voice (optional)"
echo "   Phase 4 (5-6h):  Tools (optional)"
echo "   Phase 5 (4-5h):  Memory/RAG (optional)"
echo "   Phase 6 (5-6h):  Testing (optional)"
echo ""
echo "⏱️  Total: 16-19 hours for MVP (Phases 0-2)"
echo "📊 Checklist: IMPLEMENTATION_CHECKLIST.md"
echo ""

