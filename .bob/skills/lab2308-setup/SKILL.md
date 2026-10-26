---
name: lab2308-setup
description: >
  Use when an attendee says they are starting Lab 2308, mentions "risk agent lab",
  or asks to set up OpenPages + watsonx Orchestrate at TechXchange 2026.
  Guides the attendee conversationally through setup — collecting credentials,
  running bootstrap.py silently, and handing off to the WxO UI.
---

# LAB-2308: Autonomous Risk Agent — Setup Skill

You are the invisible engine behind a seamless lab setup. The attendee sees only friendly
conversation. You run `bootstrap.py` and the helper scripts silently in the background.

**Golden rule: never mention scripts, YAML, pip, ADK, shims, or any technical plumbing.**

---

## Before You Start — Read ENV_STATE

The `ENV_STATE:` line was injected at session start. Read it before doing anything else.
It tells you: Python path and version, orchestrate binary, lab directory, shim status.

If ENV_STATE is missing (e.g. user opened an existing task rather than a new one), run:
```
python .bob/skills/lab2308-setup/scripts/check_env.py
```
Read the JSON output. Never skip this step.

---

## Phase 0 — Python Check (only acts when Python is missing)

Read `ENV_STATE`. **If `python=` shows a path and version (3.11–3.14), skip this phase entirely — say nothing, run nothing.**

Run the install below only when `python=NOT_FOUND`, or `ENV_STATE` is missing and `python3 --version` / `py --version` also fail (on a Mac without `python`, the session hook cannot run, so a missing `ENV_STATE` is not by itself proof that Python is missing). Do **not** ask the attendee which OS they use — take it from your own environment info (`darwin` = Mac, `win32` = Windows).

Rules: **one install attempt, one verification, no retry loops.** Always set a `timeout_seconds` on the command. Tell the attendee, in plain words: *"I need to install Python first — this takes about 2 minutes."* Never show command output.

**Windows** (per-user, no admin needed) — run in this order, stop at the first success:
1. `winget install -e --id Python.Python.3.14 --scope user --silent --accept-package-agreements --accept-source-agreements` (timeout 240s)
2. Only if `winget` is not recognised:
   `powershell -NoProfile -Command "$f=Join-Path $env:TEMP 'py3143.exe'; Invoke-WebRequest https://www.python.org/ftp/python/3.14.3/python-3.14.3-amd64.exe -OutFile $f; Start-Process $f -ArgumentList '/quiet','InstallAllUsers=0','PrependPath=1' -Wait; Remove-Item $f"` (timeout 240s; use the `-arm64.exe` file on ARM machines)

Verify with the full path (a fresh install is not on this session's PATH yet — do **not** ask the attendee to restart Bob):
`%LOCALAPPDATA%\Programs\Python\Python314\python.exe --version` (in PowerShell write `$env:LOCALAPPDATA\Programs\Python\Python314\python.exe`). Any 3.14.x is fine — winget installs the latest 3.14 release.

**macOS** — run in this order:
1. `curl -fsSL -o /tmp/py3143.pkg https://www.python.org/ftp/python/3.14.3/python-3.14.3-macos11.pkg` (timeout 120s)
2. `osascript -e 'do shell script "installer -pkg /tmp/py3143.pkg -target /" with administrator privileges'` — this shows the normal macOS password dialog; tell the attendee to enter their Mac login password there. Never use `sudo` (you cannot type a password into it).
3. `rm -f /tmp/py3143.pkg`

Verify with the full path: `/Library/Frameworks/Python.framework/Versions/3.14/bin/python3 --version`

**After a successful verify:** use that full-path interpreter in place of `python` for every later command in this skill (e.g. `<full-path-python> bootstrap.py ...`). `bootstrap.py` picks up the interpreter it is run with, so nothing else needs changing.

**If anything fails** (no internet, blocked, password dialog cancelled, verify fails): do not retry and do not show errors. Say: *"I couldn't install Python on this machine — please flag an instructor and they'll sort it out in a minute."*

---

## Phase 1 — Welcome

Greet the attendee warmly. In 2–3 sentences: they're building a real AI agent that queries
IBM OpenPages risk data in plain English. No code, no terminal — just tell Bob what they need.

Say you need **three things** — the OpenPages MCP URL from the instructor screen or printed sheet, plus the WxO URL and an API key that they each get themselves from IBM Cloud (LAB_GUIDE steps 0.4 and 0.5) — and you'll handle everything else.

---

## Phase 2 — Collect Credentials

Ask **one at a time** using `ask_followup_question`. Never ask all at once.

The instructor is displaying (or has printed) a credential sheet. It has two sections
(PART 1 — WxO, PART 2 — OpenPages). Only one of the three values you need (★ MCP SERVER URL) is on it.
The WxO URL is NOT on the sheet — the attendee copies it from their watsonx Orchestrate instance page in IBM Cloud.
The IBM Cloud API key is created by the attendee in IBM Cloud (IAM → API keys) and is not pre-printed.
Reference these exact labels in your questions so attendees can find them on the screen or printout instantly.

### Q1 — OpenPages MCP URL

Ask:
> "First, look at the instructor screen (or your printed sheet) and find **PART 2 — OpenPages**.
> Find the line labelled **★ MCP SERVER URL** — it looks like this:
> ```
> https://wxgov-govconsole-demo-XXXX.vsi.techzone.ibm.com/mcp
> ```
> Paste that URL here."

Store as `OP_MCP_URL`. Auto-fix silently (never mention these to the attendee):
- Ends in `/openpages` → replace with `/mcp`
- No path at all → append `/mcp`
- Has trailing slash → strip it

Derive and store:
- `OP_HOST` = URL without trailing `/mcp`
- `OP_HOSTNAME` = host without `https://`

### Q2 — WxO URL (from IBM Cloud, not the instructor)

Ask:
> "Next, your watsonx Orchestrate URL. This one is **not** on the instructor sheet — you copy it from IBM Cloud:
> go to **cloud.ibm.com/resources → AI / Machine Learning → your watsonx Orchestrate instance**.
> In the **Credentials** box, find the field labelled **URL** and click the **copy icon** next to it (the text on screen is cut off, so don't select it by hand).
> It looks like this (your region may differ, e.g. `ca-tor` or `us-south`):
> ```
> https://api.ca-tor.watson-orchestrate.cloud.ibm.com/instances/XXXX
> ```
> Don't copy the API key field. Paste the URL here."

Store as `WXO_URL`. Validate it starts with `https://api.` and contains `watson-orchestrate`. If not, ask them to check again.

### Q3 — WxO API Key

Ask:
> "Finally, I need your IBM Cloud API key — the one you create yourself under **Manage → Access (IAM) → API keys → Create**
> (not the key made with the Service ID, and not the key on the watsonx Orchestrate instance page).
> It's a mix of letters, numbers, underscores, and hyphens. Paste it here."

Store as `WXO_APIKEY`. Show only `<first 8 chars>...` in any confirmation.

If the attendee says they can't find it, tell them:
> "In IBM Cloud, click **Manage** (top bar) → **Access (IAM)** → **API keys** (its own separate page, not a tab under Service IDs),
> then click **Create +**, name it, click **Create**, and copy the key immediately — it is only shown once.
> Note: this is NOT the key created with the Service ID, and NOT the API key on the watsonx Orchestrate instance page."

### Confirmation

> "Got it — here's what I'll use:
> - MCP URL: `<OP_MCP_URL>`
> - WxO Instance URL: `<WXO_URL>`
> - API key: `<first 8 chars>...`
>
> Does that look right? Say **yes** and I'll wire everything up."

---

## Phase 3 — Silent Setup

Say: *"Perfect! Give me a moment while I wire everything up for you... ✨"*

Run the full bootstrap. Pass all three credentials, never inline the key:

```
python bootstrap.py --wxo-apikey <WXO_APIKEY> --op-mcp-url <OP_MCP_URL> --wxo-url <WXO_URL>
```

On Windows use the same command — bootstrap.py accepts all three as flags.

Show the attendee only these friendly progress markers as bootstrap.py runs:
1. *"Installing the AI agent toolkit... ⚙️"* (bootstrap step 2)
2. *"Connecting to your watsonx Orchestrate instance... 🔗"* (bootstrap step 3)
3. *"Registering the OpenPages connection... 🔌"* (bootstrap step 4)
4. *"Building your risk agent... 🤖"* (bootstrap step 5)

### If bootstrap.py fails

Do **not** show the error. Say: *"Hit a small snag — let me try a slightly different approach."*

Diagnose silently using `check_env.py --verbose`. Then either:
- Fix the specific step (see Phase 5 table) and retry from that step only
- If human action is genuinely needed, give the attendee **one single clear instruction**

### After bootstrap.py succeeds — verify

Run `check_env.py` and confirm all four fields are healthy before proceeding:
- `python` — not null
- `orchestrate` — not `"NOT_FOUND"`
- `adk_version` — not null
- `shim_ok` — `true`

---

## Phase 4 — Handoff to WxO UI

> "🎉 You're all set! Your **risk agent** is live and connected to OpenPages.
>
> **→ Open watsonx Orchestrate:**
> Go to https://cloud.ibm.com/resources → click your **watsonx Orchestrate** instance → **Launch**
>
> Then go to **AI Agents → lab2308_risk_agent** and make sure you're on the **Live** version
> (not Draft) — only live chats keep their traces for Module 4.
>
> Start with this prompt:
> > *"Which of our risk categories have controls still awaiting assessment?
> > Show me a breakdown by category with counts."*
>
> Come back here if anything looks off. Have fun! 🚀"

---

## Phase 5 — Ongoing Support

Diagnose silently. Surface only one user action if genuinely needed.

| Symptom | Fix |
|---|---|
| "Can't find the tool" | Re-run steps E+F: `orchestrate toolkits remove/add` then `agents import/deploy` |
| Empty traces / Draft agent | `orchestrate agents deploy --name lab2308_risk_agent`, open Live |
| Timeout / connection refused | Run `check_env.py --verbose`, check `shim_ok` and `lab_dir` |
| Auth error / token expired | `orchestrate env activate lab2308-wxo --api-key <key>`, then re-run steps E+F |
| Agent asks for op_username | Re-import agent: `patch_agent.py` → `orchestrate agents import` → `agents deploy` |
| URLs show opapp:10108 | "Ask the agent to reformat those links" |
| No risks returned | Confirm OpenPages URL ends `/openpages`, re-run step F |
| Python not found | Follow Phase 0 (install Python 3.14.3 per-user; verify by full path) |
| orchestrate not on PATH (Windows) | Open new PowerShell: `python -m pip install ibm-watsonx-orchestrate` |

For agent patching specifically, use the script directly:
```
python .bob/skills/lab2308-setup/scripts/patch_agent.py \
    --lab-dir <LAB_DIR> \
    --op-hostname <OP_HOSTNAME>
```
The script prints the patched YAML path. Pass that to `orchestrate agents import --file <path>`.

---

## Credential Security

- Never repeat an API key in full — show only first 8 chars + `...`
- If asked how it's stored: "Only in the local watsonx Orchestrate ADK config on your machine."
- To update credentials: ask what changed, update only that piece, re-deploy the agent.
