#!/usr/bin/env bash
# =============================================================================
# LAB-2308 Setup Script
# Sets up the watsonx Orchestrate ADK environment, registers the OpenPages MCP
# toolkit, and imports the risk agent.
#
# Prerequisites:
#   - Python 3.11+ (e.g. /Users/haneenbakbak/anaconda3/bin/python3.11)
#   - pip install ibm-watsonx-orchestrate   (run once if not yet installed)
#   - Internet access to the WxO SaaS instance and TechZone OP environment
#
# Usage:
#   chmod +x setup.sh
#   ./setup.sh
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Config — edit these if your paths differ
# ---------------------------------------------------------------------------
PYTHON="/Users/haneenbakbak/anaconda3/bin/python3.11"
WXO_URL="https://api.dl.watson-orchestrate.ibm.com/instances/20250430-1824-1871-40a1-cbba522cb662"
WXO_APIKEY="azE6dXNyXzIzMzZkNDRjLTgxNjMtM2ViYS05Y2E1LTc4YTU3ZmQ5ZTUwNDpUaWJYWnVERUM4VnZWZ2FRM1BBUURMdmZRMVpsL3lGZnpBSDFYcVNXaGVjPTpacjVJ"
OP_MCP_URL="https://wxgov-govconsole-demo-n20dhevj.vsi.techzone.ibm.com/mcp"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== LAB-2308 Setup ==="
echo ""

# ---------------------------------------------------------------------------
# Step 1: Install/upgrade the ADK
# ---------------------------------------------------------------------------
echo "[1/5] Installing/upgrading ibm-watsonx-orchestrate ADK..."
"$PYTHON" -m pip install --upgrade ibm-watsonx-orchestrate --quiet
echo "      Done."

# ---------------------------------------------------------------------------
# Step 2: Configure the WxO SaaS environment
# ---------------------------------------------------------------------------
echo "[2/5] Configuring WxO SaaS environment target..."
orchestrate env add \
    --name lab2308-wxo \
    --url "$WXO_URL" \
    --api-key "$WXO_APIKEY" 2>/dev/null || echo "      (env already exists, continuing)"

orchestrate env activate lab2308-wxo
echo "      Active env: lab2308-wxo → $WXO_URL"

# ---------------------------------------------------------------------------
# Step 3: Verify the OpenPages MCP endpoint is reachable
# ---------------------------------------------------------------------------
echo "[3/5] Checking OpenPages MCP endpoint health..."
HTTP_CODE=$(curl -sk -o /dev/null -w "%{http_code}" \
    --max-time 15 \
    "${OP_MCP_URL%/mcp}/health" 2>/dev/null || echo "000")
if [[ "$HTTP_CODE" == "200" ]]; then
    echo "      ✓ OpenPages MCP endpoint is healthy (HTTP $HTTP_CODE)"
else
    echo "      ⚠ Health check returned HTTP $HTTP_CODE — the endpoint may still"
    echo "        work. Proceeding with toolkit import."
fi

# ---------------------------------------------------------------------------
# Step 4: Register the OpenPages MCP toolkit
# ---------------------------------------------------------------------------
echo "[4/5] Registering OpenPages MCP toolkit in WxO (draft + live)..."
orchestrate toolkits add \
    --kind mcp \
    --name openpages-grc-mcp \
    --description "IBM OpenPages GRC MCP server for LAB-2308 (TechXchange 2026). Provides tools to read, create, and manage GRC objects (Risks, Controls, Issues) in the shared OpenPages TechZone environment." \
    --url "$OP_MCP_URL" \
    --transport streamable_http \
    --tools "*" 2>&1 || {
        echo "      ⚠ Toolkit import failed (it may already exist). Continuing."
    }
echo "      Done."

# ---------------------------------------------------------------------------
# Step 5: Import the risk agent
# ---------------------------------------------------------------------------
echo "[5/5] Importing LAB-2308 risk agent..."
orchestrate agents import \
    --file "$SCRIPT_DIR/agents/lab2308_risk_agent.yaml" 2>&1 || {
        echo "      ⚠ Agent import failed. Check the YAML and toolkit availability."
        exit 1
    }
echo "      Done."

echo ""
echo "=== Setup complete! ==="
echo ""
echo "Next steps:"
echo "  1. Open the WxO UI: https://dl.watson-orchestrate.ibm.com"
echo "  2. Navigate to Agent Builder and open 'lab2308_risk_agent'."
echo "  3. In the chat panel, try: 'List the current operational risks in OpenPages.'"
echo "  4. Confirm the agent calls the MCP tools and returns risk records."
echo ""
echo "OpenPages UI (to verify results):"
echo "  https://wxgov-govconsole-demo-<reservation_id>.vsi.techzone.ibm.com"
echo "  Login: (Ask your lab instructors for credentials)"
echo ""
