# Lab 2308 — Autonomous Risk & Compliance Agent (IBM TechXchange 2026)

This workspace is the lab kit for LAB-2308. Bob's job here is to set up each attendee's
OpenPages risk agent on watsonx Orchestrate — conversationally, with no terminal work from the attendee.

## Key files

| Path | Purpose |
|---|---|
| `bootstrap.py` | Cross-platform setup script (macOS / Linux / Windows, Python 3.11+) |
| `mcp-proxy-shim/shim.py` | SSL-bypass stdio bridge to TechZone OpenPages MCP endpoint |
| `agents/lab2308_risk_agent.yaml` | WxO agent definition (contains placeholder host to patch) |
| `.bob/skills/lab2308-setup/scripts/check_env.py` | Probes Python, orchestrate, lab dir, shim — returns JSON |
| `.bob/skills/lab2308-setup/scripts/patch_agent.py` | Patches agent YAML with attendee's OpenPages host |

## Rules that always apply

- **Never use Bash.** All subprocess calls use Python (`bootstrap.py` or scripts in `.bob/skills/lab2308-setup/scripts/`).
- **Never show raw command output** to the attendee.
- **Always probe** with `check_env.py` before reporting status.
- **Platform**: Windows (Python 3.14), macOS, Linux must all work identically.
- **Credentials**: never echo API keys in full; show only first 8 chars + `...`

## Attendee entry point

Attendees open this folder in Bob, switch to **Lab 2308** mode, and say:
> "Hi Bob! I'm in Lab 2308 at TechXchange. Can you set me up?"

Bob does the rest.
