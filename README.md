# LAB-2308 — Build an Autonomous Risk & Compliance Agent

**IBM TechXchange 2026**  
**Stack:** IBM OpenPages · watsonx Orchestrate · MCP · IBM Bob

---

## Getting Started

### Step 1 — Get the files

**Option A — Clone this repo**
```bash
git clone https://github.ibm.com/Haneen-Bakbak/lab-2308.git
```

**Option B — Open in Bob as a workspace**  
Open IBM Bob, then open the `lab-2308/` folder as your workspace.

---

### Step 2 — Copy the Bob skill into place

The Bob skill is in `bob-skill/SKILL.md`. Copy it to your Bob skills folder so Bob can pick it up:

```bash
mkdir -p ~/.bob/skills/lab2308-setup
cp bob-skill/SKILL.md ~/.bob/skills/lab2308-setup/SKILL.md
```

> If you opened this folder directly as a Bob workspace, Bob already sees the skill — skip this step.

---

### Step 3 — Start a new Bob conversation and say this

```
Hi Bob! I'm in Lab 2308 at TechXchange. Can you set me up?
```

Bob will ask for your TechZone OpenPages URL and WxO API key (one at a time), then silently handle everything else — no terminal, no YAML editing, no scripts.

When Bob says **"🎉 You're all set!"**, go to:

```
https://dl.watson-orchestrate.ibm.com
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

| File/Folder | What it is |
|---|---|
| `LAB_GUIDE.md` | Full attendee lab guide |
| `bob-skill/SKILL.md` | Bob setup skill — does all wiring conversationally |
| `agents/lab2308_risk_agent.yaml` | WxO risk agent definition |
| `mcp-proxy-shim/shim.py` | SSL-bypass bridge to TechZone MCP endpoint |
| `toolkits/openpages_mcp_toolkit.yaml` | MCP toolkit reference spec |
| `bootstrap.sh` | Instructor fallback script (attendees don't need this) |
