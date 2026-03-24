#!/usr/bin/env bash
set -euo pipefail

REPO="https://github.com/drlove2002/discord-ping" 
MIN_PYTHON="3.9"

RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'; RESET='\033[0m'

info()  { echo -e "${CYAN}  →${RESET} $*"; }
ok()    { echo -e "${GREEN}  ✓${RESET} $*"; }
fail()  { echo -e "${RED}  ✗${RESET} $*"; exit 1; }

echo ""
echo -e "${CYAN}  discord-ping installer${RESET}"
echo "  ──────────────────────────────────────"

# ── Check Python ──────────────────────────────────────────────────────────────
info "Checking Python..."
if ! command -v python3 &>/dev/null; then
    fail "Python 3 is not installed. Install it with: sudo apt install python3"
fi

PYVER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if python3 -c "import sys; sys.exit(0 if sys.version_info >= (3,9) else 1)"; then
    ok "Python $PYVER found"
else
    fail "Python $MIN_PYTHON+ required, found $PYVER"
fi

# ── Check pip ─────────────────────────────────────────────────────────────────
info "Checking pip..."
if ! python3 -m pip --version &>/dev/null; then
    fail "pip not found. Install with: sudo apt install python3-pip"
fi
ok "pip found"

# ── Install ───────────────────────────────────────────────────────────────────
info "Installing discord-ping..."
python3 -m pip install --user "git+${REPO}.git" --quiet

# ── PATH check ────────────────────────────────────────────────────────────────
LOCAL_BIN="$HOME/.local/bin"
if [[ ":$PATH:" != *":$LOCAL_BIN:"* ]]; then
    echo ""
    echo -e "${RED}  ⚠  ${LOCAL_BIN} is not in your PATH.${RESET}"
    echo "     Add this to your ~/.bashrc or ~/.zshrc:"
    echo ""
    echo '     export PATH="$HOME/.local/bin:$PATH"'
    echo ""
    echo "     Then reload: source ~/.bashrc"
else
    ok "discord-ping installed → $(which discord-ping 2>/dev/null || echo $LOCAL_BIN/discord-ping)"
fi

echo ""
echo "  Run it: discord-ping"
echo ""

