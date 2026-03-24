#!/usr/bin/env bash
set -euo pipefail

REPO="https://github.com/drlove2002/discord-ping"

RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'; RESET='\033[0m'
info()  { echo -e "${CYAN}  →${RESET} $*"; }
ok()    { echo -e "${GREEN}  ✓${RESET} $*"; }
fail()  { echo -e "${RED}  ✗${RESET} $*"; exit 1; }

echo ""
echo -e "${CYAN}  discord-ping installer${RESET}"
echo "  ──────────────────────────────────────"

# ── Check Python ──────────────────────────────────────────────────────────────
info "Checking Python..."
if ! command -v python3 >/dev/null 2>&1; then
  fail "Python 3 is not installed. Install it with: sudo apt install python3 python3-venv"
fi

PYVER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3,9) else 1)"; then
  fail "Python 3.9+ required, found $PYVER"
fi
ok "Python $PYVER found"

# ── Check pip ─────────────────────────────────────────────────────────────────
info "Checking pip..."
if ! python3 -m pip --version >/dev/null 2>&1; then
  fail "pip not found. Install with: sudo apt install python3-pip"
fi
ok "pip found"

# ── Nix fast path (optional) ─────────────────────────────────────────────────
if command -v nix >/dev/null 2>&1 && nix --version 2>&1 | grep -q "flake"; then
  info "Nix with flakes detected — installing via nix profile..."
  nix profile install "github:drlove2002/discord-ping"
  ok "Installed via Nix. Run: discord-ping"
  exit 0
fi

# ── Install into a per‑user virtualenv (PEP 668‑safe) ────────────────────────
VENV_DIR="$HOME/.venvs/discord-ping"
WRAPPER="$HOME/.local/bin/discord-ping"

info "Creating isolated virtual env at $VENV_DIR..."
mkdir -p "$(dirname "$VENV_DIR")"
python3 -m venv "$VENV_DIR"

info "Installing discord-ping into the virtual env..."
"$VENV_DIR/bin/pip" install --upgrade pip >/dev/null 2>&1 || true
"$VENV_DIR/bin/pip" install "git+${REPO}.git"

info "Creating launcher at $WRAPPER..."
mkdir -p "$(dirname "$WRAPPER")"
cat > "$WRAPPER" <<EOF
#!/usr/bin/env bash
exec "$VENV_DIR/bin/discord-ping" "\$@"
EOF
chmod +x "$WRAPPER"

ok "Installed discord-ping."

# ── PATH hint ────────────────────────────────────────────────────────────────
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
  echo ""
  echo -e "${RED}  ⚠  $HOME/.local/bin is not in your PATH.${RESET}"
  echo "     Add this to your shell rc (e.g. ~/.bashrc or ~/.zshrc):"
  echo ""
  echo '     export PATH="$HOME/.local/bin:$PATH"'
  echo ""
  echo "     Then run: source ~/.bashrc"
else
  echo ""
  echo "  Run: discord-ping"
fi

echo ""
