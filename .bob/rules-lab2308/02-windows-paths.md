# Windows & Cross-Platform Path Rules — Lab 2308

These rules ensure setup works correctly on Windows (Python 3.14), macOS, and Linux.

## Never Use These

- **No Bash syntax**: no `#!/bin/bash`, `set -euo pipefail`, `$()`, `&&`, `||`, here-docs (`<<EOF`),
  `$HOME`, `~/`, `which`, `find ... | xargs`, `sed`, `awk`, `curl`
- **No POSIX-only paths**: no `/tmp/`, `/opt/homebrew/`, `/usr/local/bin/`
- **No shell scripts**: `.sh` files cannot be run on Windows without WSL

## Single Exception: Installing Python (SKILL.md Phase 0)

Python cannot be used to install itself. **Only** when Python is missing, Phase 0 of the
`lab2308-setup` skill may run native commands (`winget`, PowerShell, `curl`, `osascript`, `installer`).
Run them exactly as written in Phase 0, once, with a timeout. Everything else still goes through Python.

## Always Use These Instead

- **Python for everything**: all subprocess calls go through `bootstrap.py` or scripts in
  `.bob/skills/lab2308-setup/scripts/`
- **`pathlib.Path`** for all path construction — never string concatenation with `/` or `\`
- **`tempfile.gettempdir()`** for temp files — never `/tmp/`
- **`shutil.which()`** for binary discovery — never `which` or `Get-Command`
- **`os.name == "nt"`** to detect Windows — never `sys.platform.startswith("win")`

## Python Discovery Order (Windows-first)

Always try candidates in this order:
1. `sys.executable` (the interpreter running this script) — check if ≥ 3.11
2. `py` launcher (Windows only — tries `py -3.14`, `py -3.13`, etc.)
3. `python3.14`, `python3.13`, `python3.12`, `python3.11`
4. `python3`, `python`

## Windows-Specific Path Conventions

- The `orchestrate` binary lives in `Scripts\` on Windows (not `bin/`)
- User-base scripts: `%USERPROFILE%\AppData\Roaming\Python\PythonXXX\Scripts\`
- Bob config: `%USERPROFILE%\.bob\` on Windows, `~/.bob/` on macOS/Linux
- When building error messages that reference Python installation:
  - **Windows**: `https://www.python.org/downloads/` (check "Add to PATH")
  - **macOS**: `brew install python@3.11`
  - **Linux**: `sudo apt install python3.11`

## orchestrate.exe

Always include `orchestrate.exe` as a candidate alongside `orchestrate` when searching PATH.
The WxO ADK installs `orchestrate.exe` on Windows.
