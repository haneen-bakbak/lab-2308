#!/usr/bin/env python3
"""
check_env.py — Lab 2308 environment probe.

Checks everything Bob needs to know before starting setup:
  - Python 3.11+ location and version
  - orchestrate binary location and ADK version
  - Lab directory (presence of mcp-proxy-shim/shim.py)
  - Shim syntax validity

Outputs a single JSON object on stdout. Always exits 0 so the
SessionStart hook (which calls this) can inject context even when
some items are missing.

Usage:
    python check_env.py              # JSON output
    python check_env.py --verbose    # JSON + human-readable summary
"""

import argparse
import json
import os
import pathlib
import shutil
import subprocess
import sys


# ─── helpers ──────────────────────────────────────────────────────────────────

def _run(*cmd, **kw) -> "tuple[int, str, str]":
    kw.setdefault("encoding", "utf-8")
    kw.setdefault("errors", "replace")
    r = subprocess.run(list(cmd), capture_output=True, text=True, **kw)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def _find_python() -> "tuple[str | None, str | None]":
    """Return (path, version_string) for the best Python ≥ 3.11, or (None, None)."""

    def _ver(exe: str) -> "tuple[int, int] | None":
        try:
            rc, out, _ = _run(exe, "-c",
                "import sys; v=sys.version_info; print(v.major, v.minor)")
            if rc == 0:
                parts = out.split()
                return int(parts[0]), int(parts[1])
        except Exception:
            pass
        return None

    def _full_ver(exe: str) -> str:
        try:
            rc, out, _ = _run(exe, "--version")
            return out.split()[-1] if rc == 0 else "?"
        except Exception:
            return "?"

    # 1. Running interpreter first
    v = _ver(sys.executable)
    if v and v >= (3, 11):
        return sys.executable, _full_ver(sys.executable)

    # 2. Windows py launcher
    if os.name == "nt":
        py = shutil.which("py")
        if py:
            for minor in (14, 13, 12, 11):
                rc, out, _ = _run(py, f"-3.{minor}", "-c",
                    "import sys; v=sys.version_info; print(v.major, v.minor)",
                    timeout=5)
                if rc == 0:
                    parts = out.split()
                    if int(parts[0]) >= 3 and int(parts[1]) >= 11:
                        # Resolve the actual path the launcher would use
                        rc2, path, _ = _run(py, f"-3.{minor}", "-c",
                            "import sys; print(sys.executable)", timeout=5)
                        exe = path if rc2 == 0 else py
                        return exe, _full_ver(exe)

    # 3. Named candidates
    for name in ("python3.14", "python3.13", "python3.12", "python3.11", "python3", "python"):
        exe = shutil.which(name)
        if exe:
            v = _ver(exe)
            if v and v >= (3, 11):
                return exe, _full_ver(exe)

    return None, None


def _find_orchestrate(python_exe: "str | None") -> "tuple[str | None, str | None]":
    """Return (path, version) for the orchestrate binary, or (None, None)."""

    candidates: list[str] = []

    if python_exe:
        bin_dir = pathlib.Path(python_exe).parent
        scripts = "Scripts" if os.name == "nt" else "bin"
        for name in ("orchestrate", "orchestrate.exe"):
            candidates.append(str(bin_dir / name))

        try:
            rc, user_base, _ = _run(python_exe, "-m", "site", "--user-base", timeout=5)
            if rc == 0 and user_base:
                for name in ("orchestrate", "orchestrate.exe"):
                    candidates.append(str(pathlib.Path(user_base) / scripts / name))
        except Exception:
            pass

        try:
            rc, scripts_path, _ = _run(
                python_exe, "-c",
                "import sysconfig; print(sysconfig.get_path('scripts'))",
                timeout=5)
            if rc == 0 and scripts_path:
                for name in ("orchestrate", "orchestrate.exe"):
                    candidates.append(str(pathlib.Path(scripts_path) / name))
        except Exception:
            pass

        # Windows only: per-user pip install lands in %APPDATA%\Python\PythonXYZ\Scripts
        if os.name == "nt":
            try:
                rc, user_scripts, _ = _run(
                    python_exe, "-c",
                    "import sysconfig; print(sysconfig.get_path('scripts', 'nt_user'))",
                    timeout=5)
                if rc == 0 and user_scripts:
                    candidates.append(str(pathlib.Path(user_scripts) / "orchestrate.exe"))
            except Exception:
                pass

    for name in ("orchestrate", "orchestrate.exe"):
        found = shutil.which(name)
        if found:
            candidates.append(found)

    for c in candidates:
        if c and pathlib.Path(c).is_file():
            # Get ADK version
            rc, ver_out, _ = _run(c, "--version", timeout=10)
            version = ver_out.strip() if rc == 0 and ver_out else None
            if not version:
                # Try 'orchestrate version'
                rc2, ver_out2, _ = _run(c, "version", timeout=10)
                version = ver_out2.strip() if rc2 == 0 and ver_out2 else "installed"
            return c, version

    return None, None


def _find_lab_dir() -> "pathlib.Path | None":
    """Return the lab root (directory containing mcp-proxy-shim/shim.py)."""
    # This script lives at .bob/skills/lab2308-setup/scripts/check_env.py
    # → go up 4 levels to reach the lab root
    here = pathlib.Path(__file__).resolve()
    for candidate in [
        here.parents[3],                        # .bob/skills/lab2308-setup/scripts → up 4
        here.parents[2],                        # up 3 (in case script is run from elsewhere)
        pathlib.Path.cwd(),                     # current working directory
        pathlib.Path.home() / "lab-2308",
    ]:
        if (candidate / "mcp-proxy-shim" / "shim.py").is_file():
            return candidate
    return None


def _check_shim(lab_dir: "pathlib.Path | None") -> bool:
    """Return True if shim.py exists and compiles cleanly."""
    if lab_dir is None:
        return False
    shim = lab_dir / "mcp-proxy-shim" / "shim.py"
    if not shim.is_file():
        return False
    rc, _, _ = _run(sys.executable, "-m", "py_compile", str(shim), timeout=10)
    return rc == 0


# ─── main ─────────────────────────────────────────────────────────────────────

def probe() -> dict:
    python_exe, python_version = _find_python()
    orchestrate_path, adk_version = _find_orchestrate(python_exe)
    lab_dir = _find_lab_dir()
    shim_ok = _check_shim(lab_dir)

    return {
        "python": python_exe,
        "python_version": python_version,
        "orchestrate": orchestrate_path or "NOT_FOUND",
        "adk_version": adk_version,
        "lab_dir": str(lab_dir) if lab_dir else None,
        "shim_ok": shim_ok,
        "platform": os.name,          # 'nt' on Windows, 'posix' elsewhere
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Lab 2308 environment probe")
    ap.add_argument("--verbose", "-v", action="store_true",
                    help="Print a human-readable summary after the JSON")
    args = ap.parse_args()

    state = probe()
    print(json.dumps(state, indent=2))

    if args.verbose:
        print()
        ok   = lambda s: f"  ✓ {s}"
        warn = lambda s: f"  ✗ {s}"
        print("Summary:")
        print(ok(f"Python {state['python_version']} → {state['python']}") if state["python"]
              else warn("Python 3.11+ not found"))
        print(ok(f"orchestrate → {state['orchestrate']} (ADK {state['adk_version']})") if state["orchestrate"] != "NOT_FOUND"
              else warn("orchestrate not installed (ADK not installed yet)"))
        print(ok(f"Lab dir → {state['lab_dir']}") if state["lab_dir"]
              else warn("Lab directory not found"))
        print(ok("shim.py compiles cleanly") if state["shim_ok"]
              else warn("shim.py missing or has syntax errors"))
        print()


if __name__ == "__main__":
    main()
