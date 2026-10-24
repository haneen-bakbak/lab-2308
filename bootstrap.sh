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

# ─── Credentials — YOUR OWN values, from YOUR TechZone reservation ───────────
# Required environment variables (there are NO defaults on purpose):
#   WXO_APIKEY  your IBM Cloud API key (IBM Cloud → Manage → Access (IAM) → API keys → Create)
#   OP_MCP_URL  your OpenPages MCP Server URL (…/mcp)
# Optional:
#   WXO_URL     your watsonx Orchestrate instance URL (auto-discovered if omitted)
: "${WXO_APIKEY:?Set WXO_APIKEY to the IBM Cloud API key you created under IAM > API keys}"
: "${OP_MCP_URL:?Set OP_MCP_URL to the MCP Server URL from your own reservation (…/mcp)}"
WXO_URL="${WXO_URL:-}"

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
        if [[ "$major" -ge 3 && "$minor" -ge 11 ]]; then
            PYTHON="$candidate"
            break
        fi
    fi
done

if [[ -z "$PYTHON" ]]; then
    fail "Python 3.11+ not found.\n  macOS:  brew install python@3.11\n  Linux:  sudo apt install python3.11  (or equivalent)"
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

# ─── Step 3: Connect to YOUR watsonx Orchestrate instance ────────────────────
step 3 "Configuring WxO environment ($ENV_NAME)..."

if [[ -z "$WXO_URL" ]]; then
    WXO_URL=$(WXO_APIKEY="$WXO_APIKEY" "$PYTHON" - <<'PYEOF'
import os, re, sys, requests
key = os.environ["WXO_APIKEY"]
r = requests.post("https://iam.cloud.ibm.com/identity/token",
    data={"grant_type": "urn:ibm:params:oauth:grant-type:apikey", "apikey": key}, timeout=30)
r.raise_for_status()
tok = r.json()["access_token"]
res = requests.get("https://resource-controller.cloud.ibm.com/v2/resource_instances",
    params={"type": "service_instance"}, headers={"Authorization": f"Bearer {tok}"}, timeout=30).json()
found = []
for i in res.get("resources", []):
    m = re.match(r"crn:v1:bluemix:public:watsonx-orchestrate:([^:]+):[^:]*:([^:]+)::", i.get("crn", ""))
    if m:
        found.append(f"https://api.{m.group(1)}.watson-orchestrate.cloud.ibm.com/instances/{m.group(2)}")
print(found[0] if len(found) == 1 else "")
PYEOF
)
fi
[[ -n "$WXO_URL" ]] || fail "Could not find your watsonx Orchestrate instance. Re-run with WXO_URL=<your instance URL>."
echo "  WxO URL:      $WXO_URL"

"$ORCHESTRATE" env remove --name "$ENV_NAME" >/dev/null 2>&1 || true
"$ORCHESTRATE" env add --name "$ENV_NAME" --url "$WXO_URL" --type ibm_iam 2>&1 | grep -v "^$" || true
"$ORCHESTRATE" env activate "$ENV_NAME" --api-key "$WXO_APIKEY" 2>&1 | grep -v "^$" || true
"$ORCHESTRATE" agents list >/dev/null 2>&1 || fail "Could not authenticate to watsonx Orchestrate with your API key."
ok "Environment '$ENV_NAME' activated"

# ─── Step 4: Register the OpenPages MCP toolkit ──────────────────────────────
step 4 "Registering OpenPages MCP toolkit..."

# Your MCP URL is passed to the shim as an argument (the WxO cloud runner does not
# forward local env vars, and the shim refuses to start without a URL).
"$ORCHESTRATE" toolkits remove --name "$TOOLKIT_NAME" >/dev/null 2>&1 || true
"$ORCHESTRATE" toolkits add \
    --kind mcp \
    --name "$TOOLKIT_NAME" \
    --description "IBM OpenPages GRC MCP server for LAB-2308 (TechXchange 2026). Reads and writes Risks, Controls, and Issues." \
    --package-root "$SHIM_DIR" \
    --command "python shim.py $OP_MCP_URL" \
    --tools "*" 2>&1 | grep -v "^$" || fail "Toolkit registration failed."

ok "Toolkit '$TOOLKIT_NAME' registered → $OP_MCP_URL"

# ─── Step 5: Patch + import agent ────────────────────────────────────────────
step 5 "Importing risk agent..."

TMP_AGENT="/tmp/lab2308_risk_agent_patched.yaml"

# Replace the placeholder host in the agent YAML with YOUR OpenPages host
OP_HOSTNAME="${OP_HOST#https://}"
sed "s|wxgov-govconsole-demo-<reservation_id>.vsi.techzone.ibm.com|${OP_HOSTNAME}|g" "$AGENT_FILE" > "$TMP_AGENT"
if grep -q "<reservation_id>" "$TMP_AGENT" || ! grep -q "$OP_HOSTNAME" "$TMP_AGENT"; then
    fail "Could not patch the agent with your OpenPages host."
fi

"$ORCHESTRATE" agents import --file "$TMP_AGENT" 2>&1 | grep -v "^$" \
    || fail "Agent import failed."

# Import only updates the DRAFT. Deploy to LIVE so attendees chat with the live agent
# (live conversations keep their execution traces for Module 4).
"$ORCHESTRATE" agents deploy --name lab2308_risk_agent 2>&1 | grep -v "^$" \
    || fail "Agent deploy to live failed."

ok "Agent 'lab2308_risk_agent' imported and deployed (live)"

# ─── Done ─────────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}════════════════════════════════════════════════════════════${RESET}"
echo -e "${BOLD}  ✅  Setup complete!${RESET}"
echo -e "${BOLD}════════════════════════════════════════════════════════════${RESET}"
echo ""
echo "  → Open WxO:  Launch watsonx Orchestrate from https://cloud.ibm.com/resources"
echo "  → Agent:     lab2308_risk_agent"
echo "  → OpenPages: $OP_BASE_URL"
echo "  → Login:     (Ask your lab instructors for credentials)"
echo ""
