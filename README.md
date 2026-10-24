# LAB-2308 — Build an Autonomous Risk & Compliance Agent

**IBM TechXchange 2026**  
**Stack:** IBM OpenPages · watsonx Orchestrate · MCP · IBM Bob

---

## Prerequisites

- **IBM Bob** installed ([bob.ibm.com](https://bob.ibm.com))
- **Python 3.11 or newer** on your machine  
  - Windows: [python.org/downloads](https://www.python.org/downloads/) — check **Add to PATH**
  - macOS: `brew install python@3.11`
  - Linux: `sudo apt install python3.11`
- Your **instructor sheet / TechZone reservation** open and ready, plus an **IBM Cloud API key** you create yourself (IBM Cloud → Manage → Access (IAM) → API keys → Create). See the **Prerequisites** section of [`LAB_GUIDE.md`](./LAB_GUIDE.md) for the exact steps.

---

## Getting Started — 3 steps

### Step 1 — Get the files

Clone this repo or download and unzip it:

```
git clone https://github.ibm.com/Haneen-Bakbak/lab-2308.git
```

### Step 2 — Open the folder in Bob

In IBM Bob, open the `lab-2308/` folder as your workspace.

### Step 3 — Switch to Lab 2308 mode and say hi

In the Bob mode selector, choose **🔬 Lab 2308 — Risk Agent Setup**.

Then type:

```
Hi Bob! I'm in Lab 2308 at TechXchange. Can you set me up?
```

Bob will ask for your OpenPages MCP URL, your watsonx Orchestrate instance URL and your IBM Cloud API key (one at a time),
then handle everything else — no terminal, no YAML editing, no scripts.

When Bob says **"🎉 You're all set!"**, go to:

```
https://cloud.ibm.com/resources → your watsonx Orchestrate instance → Launch
```

Open **AI Agents → lab2308_risk_agent** and start chatting.

---

## What You'll Build

An AI agent that reads live risk data from IBM OpenPages in plain English:

```
You → "List the current open risks"
Agent → queries OpenPages via MCP → returns a formatted risk table
```

Full lab instructions are in [`LAB_GUIDE.md`](./LAB_GUIDE.md).

---

## Repo Contents

| Path | What it is |
|---|---|
| `LAB_GUIDE.md` | Full attendee lab guide |
| `AGENTS.md` | Project context Bob reads in every conversation |
| `bootstrap.py` | Cross-platform setup script (macOS / Linux / Windows) |
| `agents/lab2308_risk_agent.yaml` | WxO risk agent definition |
| `mcp-proxy-shim/shim.py` | SSL-bypass bridge to TechZone MCP endpoint |
| `.bob/custom_modes.yaml` | **Lab 2308** Bob mode — loads automatically when you open this folder |
| `.bob/skills/lab2308-setup/` | Bob skill + helper scripts — auto-discovered, no copying needed |
| `.bob/rules-lab2308/` | Mode-scoped rules (credential safety, Windows paths, lab discipline) |
| `.bob/hooks/session_start.py` | Probes your environment at session start so Bob already knows your state |

---

## Troubleshooting

If anything goes wrong, stay in **Lab 2308** mode and tell Bob what you're seeing.
Bob already knows your environment state (Python version, ADK install status, etc.)
and will diagnose and fix silently.

Common issues and their causes:

| Issue | Likely cause |
|---|---|
| Bob can't find the tool | Toolkit registration incomplete — tell Bob to re-register the connection |
| Empty traces in Module 4 | Chatting with Draft agent — tell Bob to deploy to Live |
| 401 / auth error | ADK token expired — tell Bob to re-authenticate |
| Python not found | Python not installed or not on PATH — see Prerequisites above |
