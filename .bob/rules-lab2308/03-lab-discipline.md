# Lab Discipline Rules — Lab 2308

## What the Attendee Sees

- **Never** show raw subprocess output, stdout dumps, stack traces, file paths, or ADK command syntax.
- **Never** mention scripts, YAML files, virtual environments, pip, shim proxies, or internal plumbing.
- Progress messages must be friendly and non-technical:
  - ✅ "Installing the AI agent toolkit... ⚙️"
  - ✅ "Connecting to your watsonx Orchestrate instance... 🔗"
  - ❌ "Running: python -m pip install --upgrade ibm-watsonx-orchestrate"
- When something fails: say "Hit a small snag — let me try a different approach. One moment..."
  Then diagnose silently. Only surface one clear user action if human intervention is truly needed.

## Always Confirm State Before Reporting Done

Before telling an attendee setup is complete, run:
```
python .bob/skills/lab2308-setup/scripts/check_env.py
```
Verify the JSON output shows:
- `python_version` ≥ 3.11
- `orchestrate` path is not `"NOT_FOUND"`
- `adk_version` is not `null`
- `shim_ok` is `true`
- `lab_dir` is not `null`

If any field is missing, fix it before declaring success.

## Re-Runnable Phases

Every phase of setup is independently re-runnable:
- Re-install ADK: `python bootstrap.py --wxo-apikey <key> --op-mcp-url <url>` (full re-run)
- Re-register toolkit only: Step E in bootstrap.py logic via `orchestrate toolkits add ...`
- Re-import and re-deploy agent only: Step F in bootstrap.py logic via `orchestrate agents import/deploy`
- Re-activate WxO environment: `orchestrate env activate lab2308-wxo --api-key <key>`

Always identify the earliest failing step and re-run from there — never start from scratch
unless the attendee explicitly asks to reset everything.

## Session Start Protocol

At the start of every new conversation, read the `ENV_STATE:` line injected by the SessionStart hook.
This tells you exactly what is and isn't installed before the attendee says a word.
Never ask "what version of Python do you have?" — you already know from ENV_STATE.

## Troubleshooting Reference

| Symptom | Fix |
|---|---|
| Agent says it can't find the tool | Re-run Steps E + F (toolkit re-register + agent re-import + deploy) |
| Traces are empty / Draft agent | Run `agents deploy --name lab2308_risk_agent`, open Live agent |
| Timeout / connection refused | Check `python .bob/skills/lab2308-setup/scripts/check_env.py --verbose` |
| Auth error / 401 / token expired | Re-run `orchestrate env activate lab2308-wxo --api-key <key>` then Steps E + F |
| Agent asks for op_username etc. | Re-import agent (Step F) |
| URLs show opapp:10108 | "Ask the agent to reformat those links" |
| No risks returned | Confirm OpenPages URL ends in `/openpages`, re-run Step F |
| pip / orchestrate not on PATH (Windows) | Run `python -m pip install ibm-watsonx-orchestrate` in a new PowerShell window |
