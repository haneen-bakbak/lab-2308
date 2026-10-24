#!/usr/bin/env python3
"""
bootstrap.py — LAB-2308 Bootstrap  (IBM TechXchange 2026)
Build an Autonomous Risk & Compliance Agent

Works on macOS, Linux, and Windows (Python 3.11+).
Bob calls this automatically — attendees never run it directly.

Usage:
    python bootstrap.py --wxo-apikey <key> --op-mcp-url <url>

Environment variables (alternative to flags):
    WXO_APIKEY   your IBM Cloud API key (created in IBM Cloud → Manage → Access (IAM) → API keys)
    OP_MCP_URL   your OpenPages MCP Server URL (…/mcp)
    WXO_URL      your watsonx Orchestrate instance URL (auto-discovered if omitted)
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

# ─── Windows-only compatibility ───────────────────────────────────────────────
# Everything below is gated on IS_WINDOWS. macOS / Linux behaviour is unchanged.
IS_WINDOWS = os.name == "nt"

# Explicit tool list. On Windows the CLI shell expands a bare "*" into filenames
# from the current folder, so "--tools *" breaks there. macOS / Linux keep "*".
OPENPAGES_TOOLS = (
    "echo,list_resources,get_resource,execute_openpages_query,"
    "openpages_delete_object,openpages_associate_objects,"
    "openpages_dissociate_objects,openpages_upsert_object"
)


def tools_arg() -> str:
    return OPENPAGES_TOOLS if IS_WINDOWS else "*"


def confirm_kwargs() -> dict:
    """Windows: auto-answer the CLI's interactive 'are you sure?' prompt. Others: no stdin."""
    return {"input": "y\n"} if IS_WINDOWS else {}


def setup_windows_utf8() -> None:
    """Windows consoles default to a legacy codepage; force UTF-8 so ✓ → ✅ don't crash."""
    os.environ["PYTHONUTF8"] = "1"
    os.environ["PYTHONIOENCODING"] = "utf-8"
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


if IS_WINDOWS:
    setup_windows_utf8()

# ─── Colour helpers (disabled on Windows unless ANSICON/WT is present) ────────
_USE_COLOUR = sys.stdout.isatty() and (os.name != "nt" or os.environ.get("WT_SESSION"))

def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _USE_COLOUR else text

def ok(msg: str)   -> None: print(f"  {_c('0;32', '✓')} {msg}")
def warn(msg: str) -> None: print(f"  {_c('1;33', '⚠')} {msg}", file=sys.stderr)
def fail(msg: str) -> None:
    print(f"  {_c('0;31', '✗ ERROR:')} {msg}", file=sys.stderr)
    sys.exit(1)
def step(n: int, total: int, msg: str) -> None:
    print(f"\n{_c('1', f'[{n}/{total}]')} {msg}")


TOTAL_STEPS = 5

# ─── Argument parsing ─────────────────────────────────────────────────────────
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="LAB-2308 bootstrap")
    p.add_argument("--wxo-apikey", default=os.environ.get("WXO_APIKEY", ""))
    p.add_argument("--op-mcp-url", default=os.environ.get("OP_MCP_URL", ""))
    p.add_argument("--wxo-url",    default=os.environ.get("WXO_URL", ""),
                   help="Your watsonx Orchestrate instance URL "
                        "(cloud.ibm.com/resources → WxO instance → Instance URL)")
    return p.parse_args()


# ─── Step 1: Find Python 3.11+ ───────────────────────────────────────────────
def find_python() -> str:
    """Return the path to the current interpreter if it is 3.11+, else search."""
    def _meets_min(exe: str) -> bool:
        try:
            out = subprocess.check_output(
                [exe, "-c", "import sys; print(sys.version_info.major, sys.version_info.minor)"],
                stderr=subprocess.DEVNULL, text=True, encoding="utf-8", errors="replace",
            ).strip().split()
            return int(out[0]) >= 3 and int(out[1]) >= 11
        except Exception:
            return False

    # Prefer the interpreter running this script
    if _meets_min(sys.executable):
        return sys.executable

    # Common candidate names, in priority order
    names = [
        "python3.14", "python3.13", "python3.12", "python3.11",
        "python3", "python",
    ]
    # On Windows also look for the py launcher
    if os.name == "nt":
        names = ["py"] + names

    for name in names:
        exe = shutil.which(name)
        if exe and _meets_min(exe):
            return exe

    fail(
        "Python 3.11+ not found.\n"
        "  macOS:   brew install python@3.11\n"
        "  Linux:   sudo apt install python3.11  (or equivalent)\n"
        "  Windows: https://www.python.org/downloads/  (check 'Add to PATH')"
    )


# ─── Step 2: Install ADK ─────────────────────────────────────────────────────
def install_adk(python: str) -> str:
    """Install ibm-watsonx-orchestrate and return the path to the orchestrate binary."""
    result = subprocess.run(
        [python, "-m", "pip", "install", "--upgrade", "ibm-watsonx-orchestrate", "--quiet"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if result.returncode != 0:
        fail(
            "Failed to install the watsonx Orchestrate ADK.\n"
            f"{result.stderr.strip()}\n"
            "  Tip: make sure pip is available and you have write access to the Python environment."
        )

    # Locate the orchestrate binary
    candidates = []

    # Same dir as the python executable (venv, conda, or global install)
    bin_dir = Path(python).parent
    for name in ("orchestrate", "orchestrate.exe"):
        candidates.append(str(bin_dir / name))

    # User-base scripts dir
    try:
        user_base = subprocess.check_output(
            [python, "-m", "site", "--user-base"], text=True,
            stderr=subprocess.DEVNULL, encoding="utf-8", errors="replace",
        ).strip()
        scripts = "Scripts" if os.name == "nt" else "bin"
        for name in ("orchestrate", "orchestrate.exe"):
            candidates.append(str(Path(user_base) / scripts / name))
    except Exception:
        pass

    # sysconfig scripts path
    try:
        scripts_path = subprocess.check_output(
            [python, "-c", "import sysconfig; print(sysconfig.get_path('scripts'))"],
            text=True, stderr=subprocess.DEVNULL, encoding="utf-8", errors="replace",
        ).strip()
        for name in ("orchestrate", "orchestrate.exe"):
            candidates.append(str(Path(scripts_path) / name))
    except Exception:
        pass

    # Windows only: when pip can't write to the main Python folder it installs to the
    # per-user scheme, e.g. %APPDATA%\Python\Python314\Scripts (not <user-base>\Scripts).
    if IS_WINDOWS:
        try:
            user_scripts = subprocess.check_output(
                [python, "-c", "import sysconfig; print(sysconfig.get_path('scripts', 'nt_user'))"],
                text=True, stderr=subprocess.DEVNULL, encoding="utf-8", errors="replace",
            ).strip()
            candidates.append(str(Path(user_scripts) / "orchestrate.exe"))
        except Exception:
            pass

    # PATH fallback
    for name in ("orchestrate", "orchestrate.exe"):
        found = shutil.which(name)
        if found:
            candidates.append(found)

    for c in candidates:
        if c and Path(c).is_file():
            return c

    fail(
        "'orchestrate' binary not found after install.\n"
        f"  Try adding Python's Scripts folder to PATH and re-running.\n"
        f"  Python is at: {python}"
    )


# ─── Step 3: Discover WxO instance URL ───────────────────────────────────────
def discover_wxo_url(python: str, apikey: str) -> str:
    script = textwrap.dedent("""\
        import os, re, sys
        try:
            import requests
        except ImportError:
            import subprocess, sys
            subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])
            import requests
        key = os.environ["WXO_APIKEY"]
        r = requests.post("https://iam.cloud.ibm.com/identity/token",
            data={"grant_type": "urn:ibm:params:oauth:grant-type:apikey", "apikey": key},
            timeout=30)
        r.raise_for_status()
        tok = r.json()["access_token"]
        res = requests.get("https://resource-controller.cloud.ibm.com/v2/resource_instances",
            params={"type": "service_instance"},
            headers={"Authorization": f"Bearer {tok}"}, timeout=30).json()
        found = []
        for i in res.get("resources", []):
            m = re.match(
                r"crn:v1:bluemix:public:watsonx-orchestrate:([^:]+):[^:]*:([^:]+)::",
                i.get("crn", ""))
            if m:
                found.append(
                    f"https://api.{m.group(1)}.watson-orchestrate.cloud.ibm.com/instances/{m.group(2)}")
        if len(found) == 1:
            print(found[0])
        else:
            sys.stderr.write(f"found {len(found)} watsonx Orchestrate instances\\n")
            sys.exit(1)
    """)
    env = {**os.environ, "WXO_APIKEY": apikey}
    result = subprocess.run(
        [python, "-c", script],
        capture_output=True, text=True, encoding="utf-8", errors="replace", env=env,
    )
    url = result.stdout.strip()
    if not url:
        fail(
            "Could not auto-discover your watsonx Orchestrate instance.\n"
            "  Re-run with --wxo-url <your instance URL>."
        )
    return url


# ─── Step 4: Find the lab directory ──────────────────────────────────────────
def find_lab_dir() -> Path:
    """Return the root of the lab repo (the directory containing this script)."""
    # bootstrap.py lives at the repo root
    here = Path(__file__).resolve().parent
    if (here / "mcp-proxy-shim" / "shim.py").is_file():
        return here
    fail(
        "Cannot locate lab files relative to bootstrap.py.\n"
        "  Make sure bootstrap.py is in the root of the lab-2308 repo."
    )


# ─── Helpers ──────────────────────────────────────────────────────────────────
def run(cmd: list[str], check: bool = True, **kwargs) -> subprocess.CompletedProcess:
    kwargs.setdefault("encoding", "utf-8")
    kwargs.setdefault("errors", "replace")
    return subprocess.run(cmd, check=check, capture_output=True, text=True, **kwargs)


def orchestrate(binary: str, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return run([binary, *args], check=check)


# ─── Main ─────────────────────────────────────────────────────────────────────
def main() -> None:
    args = parse_args()

    if not args.wxo_apikey:
        fail("WXO_APIKEY is required. Pass --wxo-apikey or set the WXO_APIKEY environment variable.")
    if not args.op_mcp_url:
        fail("OP_MCP_URL is required. Pass --op-mcp-url or set the OP_MCP_URL environment variable.")
    if not args.wxo_url.strip():
        fail(
            "WXO_URL is required. Pass --wxo-url or set the WXO_URL environment variable.\n"
            "  Find it in IBM Cloud: cloud.ibm.com/resources → AI / Machine Learning\n"
            "  → your watsonx Orchestrate instance → Instance URL"
        )

    wxo_apikey  = args.wxo_apikey
    op_mcp_url  = args.op_mcp_url.rstrip("/")
    if not op_mcp_url.endswith("/mcp"):
        fail(f"OP_MCP_URL must end in /mcp, got: {op_mcp_url}")

    op_host     = op_mcp_url[: -len("/mcp")]
    op_hostname = re.sub(r"^https?://", "", op_host)
    op_base_url = op_host + "/openpages"
    wxo_url     = args.wxo_url.strip()

    env_name     = "lab2308-wxo"
    toolkit_name = "openpages-grc-mcp"

    print()
    print(_c("1", "=" * 60))
    print(_c("1", "  IBM TechXchange 2026 — LAB-2308 Bootstrap"))
    print(_c("1", "  Build an Autonomous Risk & Compliance Agent"))
    print(_c("1", "=" * 60))
    print()
    print(f"  OP MCP URL:   {op_mcp_url}")
    print(f"  OP Base URL:  {op_base_url}")
    print()

    # ── Step 1 ────────────────────────────────────────────────────────────────
    step(1, TOTAL_STEPS, "Checking Python...")
    python = find_python()
    ver = subprocess.check_output(
        [python, "--version"], text=True, stderr=subprocess.STDOUT,
        encoding="utf-8", errors="replace",
    ).strip()
    ok(f"{ver} → {python}")

    # ── Step 2 ────────────────────────────────────────────────────────────────
    step(2, TOTAL_STEPS, "Installing watsonx Orchestrate ADK...")
    orchestrate_bin = install_adk(python)
    ok(f"ADK installed → {orchestrate_bin}")

    # ── Step 3 ────────────────────────────────────────────────────────────────
    step(3, TOTAL_STEPS, f"Configuring WxO environment ({env_name})...")

    print(f"  WxO URL:      {wxo_url}")

    env = {**os.environ, "WXO_APIKEY": wxo_apikey}

    run([orchestrate_bin, "env", "remove", "--name", env_name], check=False, env=env, **confirm_kwargs())
    run([orchestrate_bin, "env", "add", "--name", env_name, "--url", wxo_url, "--type", "ibm_iam"], env=env)
    run([orchestrate_bin, "env", "activate", env_name, "--api-key", wxo_apikey], env=env)

    probe = run([orchestrate_bin, "agents", "list"], check=False, env=env)
    if probe.returncode != 0:
        fail("Could not authenticate to watsonx Orchestrate with your API key.")
    ok(f"Environment '{env_name}' activated")

    # ── Step 4 ────────────────────────────────────────────────────────────────
    step(4, TOTAL_STEPS, "Registering OpenPages MCP toolkit...")

    lab_dir  = find_lab_dir()
    shim_dir = str(lab_dir / "mcp-proxy-shim")

    run([orchestrate_bin, "toolkits", "remove", "--name", toolkit_name], check=False, env=env, **confirm_kwargs())
    result = run([
        orchestrate_bin, "toolkits", "add",
        "--kind", "mcp",
        "--name", toolkit_name,
        "--description", "IBM OpenPages GRC MCP server for LAB-2308 (TechXchange 2026). Reads and writes Risks, Controls, and Issues.",
        "--package-root", shim_dir,
        "--command", f"python shim.py {op_mcp_url}",
        "--tools", tools_arg(),
    ], check=False, env=env)

    if result.returncode != 0:
        fail(f"Toolkit registration failed:\n{result.stderr.strip()}")
    ok(f"Toolkit '{toolkit_name}' registered → {op_mcp_url}")

    # ── Step 5 ────────────────────────────────────────────────────────────────
    step(5, TOTAL_STEPS, "Importing risk agent...")

    agent_src = lab_dir / "agents" / "lab2308_risk_agent.yaml"
    tmp_agent  = Path(tempfile.gettempdir()) / "lab2308_risk_agent_patched.yaml"

    src_text = agent_src.read_text(encoding="utf-8")
    patched  = src_text.replace(
        "wxgov-govconsole-demo-<reservation_id>.vsi.techzone.ibm.com",
        op_hostname,
    )
    if "<reservation_id>" in patched or op_hostname not in patched:
        fail("Could not patch the agent with your OpenPages host.")
    tmp_agent.write_text(patched, encoding="utf-8")

    result = run([orchestrate_bin, "agents", "import", "--file", str(tmp_agent)], check=False, env=env)
    if result.returncode != 0:
        fail(f"Agent import failed:\n{result.stderr.strip()}")

    result = run([orchestrate_bin, "agents", "deploy", "--name", "lab2308_risk_agent"], check=False, env=env)
    if result.returncode != 0:
        fail(f"Agent deploy failed:\n{result.stderr.strip()}")

    ok("Agent 'lab2308_risk_agent' imported and deployed (live)")

    # ── Done ──────────────────────────────────────────────────────────────────
    print()
    print(_c("1", "=" * 60))
    print(_c("1", "  ✅  Setup complete!"))
    print(_c("1", "=" * 60))
    print()
    print(f"  → Open WxO:  Launch watsonx Orchestrate from https://cloud.ibm.com/resources")
    print(f"  → Agent:     lab2308_risk_agent")
    print(f"  → OpenPages: {op_base_url}")
    print(f"  → Login:     (Ask your lab instructors for credentials)")
    print()


if __name__ == "__main__":
    main()
