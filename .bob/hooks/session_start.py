#!/usr/bin/env python3
"""
session_start.py — Lab 2308 Bob SessionStart hook.

Runs check_env.py and returns a structured JSON response that Bob
injects as additional context at the start of every new task in the
lab2308 mode.

Bob receives this on stdout as a SessionStart additionalContext payload.
The attendee never sees this output — Bob reads it silently.

Registered in .bob/settings.json:
  "SessionStart" → matcher "^startup$" → command "python .bob/hooks/session_start.py"
"""

import json
import os
import pathlib
import subprocess
import sys


def main() -> None:
    # Locate check_env.py relative to this file
    # session_start.py lives at .bob/hooks/session_start.py
    # check_env.py lives at .bob/skills/lab2308-setup/scripts/check_env.py
    here     = pathlib.Path(__file__).resolve().parent          # .bob/hooks/
    bob_dir  = here.parent                                      # .bob/
    check_py = bob_dir / "skills" / "lab2308-setup" / "scripts" / "check_env.py"

    state: dict = {}

    if check_py.is_file():
        try:
            result = subprocess.run(
                [sys.executable, str(check_py)],
                capture_output=True, text=True, timeout=20,
                cwd=str(bob_dir.parent),   # run from lab root (cwd)
            )
            if result.returncode == 0 and result.stdout.strip():
                state = json.loads(result.stdout)
        except Exception as e:
            state = {"probe_error": str(e)}
    else:
        state = {"probe_error": f"check_env.py not found at {check_py}"}

    # Build a concise one-line ENV_STATE summary for Bob's context
    def _fmt_python() -> str:
        if state.get("python"):
            return f"python={state['python']} ({state.get('python_version', '?')})"
        return "python=NOT_FOUND"

    def _fmt_orch() -> str:
        orch = state.get("orchestrate", "NOT_FOUND")
        if orch != "NOT_FOUND":
            ver = state.get("adk_version") or "installed"
            return f"orchestrate={orch} (ADK {ver})"
        return "orchestrate=NOT_FOUND"

    def _fmt_lab() -> str:
        d = state.get("lab_dir")
        return f"lab_dir={d}" if d else "lab_dir=NOT_FOUND"

    def _fmt_shim() -> str:
        return f"shim_ok={str(state.get('shim_ok', False)).lower()}"

    platform = "windows" if state.get("platform") == "nt" else state.get("platform", "unknown")

    summary = (
        f"ENV_STATE: {_fmt_python()} | {_fmt_orch()} | "
        f"{_fmt_lab()} | {_fmt_shim()} | platform={platform}"
    )

    # Emit the structured SessionStart hook response
    response = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": summary,
        }
    }
    print(json.dumps(response))


if __name__ == "__main__":
    main()
