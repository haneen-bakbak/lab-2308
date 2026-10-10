#!/usr/bin/env bash
# =============================================================================
# LAB-2308 Bootstrap — IBM TechXchange 2026
# Build an Autonomous Risk & Compliance Agent
#
# macOS / Linux. Run once at the start of the lab.
# Bob calls this automatically — attendees never run it directly.
#
# What this script does:
#   1. Find Python 3.9+ on this machine
#   2. Install the watsonx Orchestrate ADK
#   3. Register the WxO environment
#   4. Register the OpenPages MCP toolkit (via SSL-bypass shim)
#   5. Patch and import the lab2308_risk_agent
# =============================================================================

set -euo pipefail

# ─── Colour helpers ──────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BOLD='\033[1m'; RESET='\033[0m'
ok()   { echo -e "  ${GREEN}✓${RESET} $*"; }
warn() { echo -e "  ${YELLOW}⚠${RESET} $*"; }
fail() { echo -e "  ${RED}✗ ERROR:${RESET} $*"; exit 1; }
step() { echo -e "\n${BOLD}[$1/5]${RESET} $2"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ─── Credentials — passed in by Bob as environment variables ─────────────────
# Bob sets: WXO_URL, WXO_APIKEY, OP_MCP_URL
# Fallback defaults (test/instructor environment) used when run directly.
DEFAULT_WXO_URL="https://api.ca-tor.watson-orchestrate.cloud.ibm.com/instances/616b18d0-1d1b-414d-9064-10f973502afb"
DEFAULT_WXO_APIKEY="oC99Z6EaFazlzAFh6siLM222TL9WZZkW2Zwux2bd67VE"
DEFAULT_OP_MCP_URL="https://wxgov-govconsole-demo-2ho7021k.vsi.techzone.ibm.com/mcp"

WXO_URL="${WXO_URL:-$DEFAULT_WXO_URL}"
WXO_APIKEY="${WXO_APIKEY:-$DEFAULT_WXO_APIKEY}"
OP_MCP_URL="${OP_MCP_URL:-$DEFAULT_OP_MCP_URL}"

# Derive URLs from MCP URL
OP_HOST="${OP_MCP_URL%/mcp}"
OP_BASE_URL="${OP_HOST}/openpages"

ENV_NAME="lab2308-wxo"
TOOLKIT_NAME="openpages-grc-mcp"
AGENT_FILE="$SCRIPT_DIR/agents/lab2308_risk_agent.yaml"
SHIM_DIR="$SCRIPT_DIR/mcp-proxy-shim"

# ─── Banner ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}════════════════════════════════════════════════════════════${RESET}"
echo -e "${BOLD}  IBM TechXchange 2026 — LAB-2308 Bootstrap${RESET}"
echo -e "${BOLD}  Build an Autonomous Risk & Compliance Agent${RESET}"
echo -e "${BOLD}════════════════════════════════════════════════════════════${RESET}"
echo ""
echo "  WxO URL:      $WXO_URL"
echo "  OP MCP URL:   $OP_MCP_URL"
echo "  OP Base URL:  $OP_BASE_URL"
echo ""

# ─── Step 1: Find Python ─────────────────────────────────────────────────────
step 1 "Checking Python..."

PYTHON=""
for candidate in \
    "$(which python3.13 2>/dev/null)" \
    "$(which python3.12 2>/dev/null)" \
    "$(which python3.11 2>/dev/null)" \
    "$(which python3.10 2>/dev/null)" \
    "$(which python3.9 2>/dev/null)" \
    "$(which python3 2>/dev/null)" \
    "/opt/homebrew/bin/python3" \
    "/usr/local/bin/python3" \
    "$HOME/anaconda3/bin/python3.11" \
    "$HOME/anaconda3/bin/python3" \
    "$HOME/miniconda3/bin/python3" \
    "$HOME/.pyenv/shims/python3"
do
    if [[ -n "$candidate" && -x "$candidate" ]]; then
        ver=$("$candidate" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || true)
        major=$(echo "$ver" | cut -d. -f1)
        minor=$(echo "$ver" | cut -d. -f2)
        if [[ "$major" -ge 3 && "$minor" -ge 9 ]]; then
            PYTHON="$candidate"
            break
        fi
    fi
done

if [[ -z "$PYTHON" ]]; then
    fail "Python 3.9+ not found.\n  macOS:  brew install python@3.11\n  Linux:  sudo apt install python3.11  (or equivalent)"
fi
ok "Python $("$PYTHON" --version 2>&1 | awk '{print $2}') → $PYTHON"

# ─── Step 2: Install ADK ─────────────────────────────────────────────────────
step 2 "Installing watsonx Orchestrate ADK..."

"$PYTHON" -m pip install --upgrade ibm-watsonx-orchestrate --quiet 2>&1 \
    | grep -E "(Successfully|already|error|ERROR)" || true

# Locate the orchestrate binary (handles venv, user-install, and global paths)
ORCHESTRATE=""
for p in \
    "$(dirname "$PYTHON")/orchestrate" \
    "$("$PYTHON" -m site --user-base 2>/dev/null)/bin/orchestrate" \
    "$("$PYTHON" -c "import sysconfig; print(sysconfig.get_path('scripts'))" 2>/dev/null)/orchestrate" \
    "$(which orchestrate 2>/dev/null)"
do
    if [[ -n "$p" && -x "$p" ]]; then
        ORCHESTRATE="$p"
        break
    fi
done

if [[ -z "$ORCHESTRATE" ]]; then
    fail "'orchestrate' binary not found after install.\n  Try: export PATH=\"\$($PYTHON -m site --user-base)/bin:\$PATH\"\n  Then re-run."
fi
ok "ADK installed → $ORCHESTRATE"

# ─── Step 3: Configure WxO environment ───────────────────────────────────────
step 3 "Configuring WxO environment ($ENV_NAME)..."

"$ORCHESTRATE" env remove --name "$ENV_NAME" 2>/dev/null || true
"$ORCHESTRATE" env add \
    --name "$ENV_NAME" \
    --url "$WXO_URL" \
    --api-key "$WXO_APIKEY" 2>&1 | grep -v "^$" || true
"$ORCHESTRATE" env activate "$ENV_NAME" 2>&1 | grep -v "^$" || true
ok "Environment '$ENV_NAME' activated"

# ─── Step 4: Set up shim + register MCP toolkit ──────────────────────────────
step 4 "Registering OpenPages MCP toolkit..."

SHIM_VENV="$SHIM_DIR/venv"
SHIM_PY="$SHIM_VENV/bin/python"

if [[ ! -x "$SHIM_PY" ]]; then
    echo "  Setting up SSL-bypass shim virtual environment..."
    "$PYTHON" -m venv "$SHIM_VENV" --clear
    "$SHIM_PY" -m pip install --upgrade pip --quiet
    "$SHIM_PY" -m pip install -r "$SHIM_DIR/requirements.txt" --quiet
fi

# Patch the shim with this attendee's MCP URL (env var takes precedence at runtime)
export OPENPAGES_MCP_URL="$OP_MCP_URL"

# Remove any stale toolkit registration
"$ORCHESTRATE" toolkits remove --name "$TOOLKIT_NAME" 2>/dev/null || true

# Register via package-root (stdio shim) — WxO calls the shim, which forwards
# over HTTPS to the TechZone endpoint with SSL verification disabled.
"$ORCHESTRATE" toolkits add \
    --kind mcp \
    --name "$TOOLKIT_NAME" \
    --description "IBM OpenPages GRC MCP server for LAB-2308 (TechXchange 2026). Reads and writes Risks, Controls, and Issues." \
    --package-root "$SHIM_DIR" \
    --command "$SHIM_VENV/bin/python shim.py" \
    --tools "*" 2>&1 | grep -v "^$" || warn "Toolkit add returned non-zero — may already be registered."

ok "Toolkit '$TOOLKIT_NAME' registered"

# ─── Step 5: Patch + import agent ────────────────────────────────────────────
step 5 "Importing risk agent..."

TMP_AGENT="/tmp/lab2308_risk_agent_patched.yaml"

# Replace the default test hostname with this attendee's OP host in the agent YAML
DEFAULT_OP_HOST="https://wxgov-govconsole-demo-2ho7021k.vsi.techzone.ibm.com"

sed "s|${DEFAULT_OP_HOST}/openpages|${OP_BASE_URL}|g" "$AGENT_FILE" > "$TMP_AGENT"
sed -i.bak "s|${DEFAULT_OP_HOST}|${OP_HOST}|g" "$TMP_AGENT" 2>/dev/null || true

"$ORCHESTRATE" agents import --file "$TMP_AGENT" 2>&1 | grep -v "^$" \
    || warn "Agent import returned non-zero — may already exist."

ok "Agent 'lab2308_risk_agent' imported"

# ─── Done ─────────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}════════════════════════════════════════════════════════════${RESET}"
echo -e "${BOLD}  ✅  Setup complete!${RESET}"
echo -e "${BOLD}════════════════════════════════════════════════════════════${RESET}"
echo ""
echo "  → Open WxO:  https://dl.watson-orchestrate.ibm.com"
echo "  → Agent:     lab2308_risk_agent"
echo "  → OpenPages: $OP_BASE_URL"
echo "  → Login:     (Ask your lab instructors for credentials)"
echo ""
