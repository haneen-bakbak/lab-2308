#!/usr/bin/env python3
"""
patch_agent.py — Lab 2308 agent YAML patcher.

Replaces the placeholder OpenPages host in lab2308_risk_agent.yaml
with the attendee's real host, writes the result to a temp file,
and prints the temp file path on stdout.

Usage:
    python patch_agent.py --lab-dir <path> --op-hostname <host>

Example:
    python patch_agent.py \
        --lab-dir C:\\Users\\attendee\\lab-2308 \
        --op-hostname wxgov-govconsole-demo-abc123.vsi.techzone.ibm.com

Exits 0 and prints the patched file path on success.
Exits 1 and prints an error to stderr on failure.
"""

import argparse
import os
import pathlib
import sys
import tempfile

PLACEHOLDER = "wxgov-govconsole-demo-<reservation_id>.vsi.techzone.ibm.com"


def main() -> None:
    ap = argparse.ArgumentParser(description="Patch lab2308_risk_agent.yaml")
    ap.add_argument("--lab-dir", required=True,
                    help="Root directory of the lab-2308 repo")
    ap.add_argument("--op-hostname", required=True,
                    help="OpenPages host (no https://, no trailing /mcp)")
    args = ap.parse_args()

    lab_dir   = pathlib.Path(args.lab_dir).resolve()
    agent_src = lab_dir / "agents" / "lab2308_risk_agent.yaml"
    hostname  = args.op_hostname.strip().rstrip("/")

    # Remove any scheme the user accidentally included
    for prefix in ("https://", "http://"):
        if hostname.startswith(prefix):
            hostname = hostname[len(prefix):]

    if not agent_src.is_file():
        sys.stderr.write(f"ERROR: agent source not found: {agent_src}\n")
        sys.exit(1)

    if not hostname:
        sys.stderr.write("ERROR: --op-hostname must not be empty\n")
        sys.exit(1)

    src_text = agent_src.read_text(encoding="utf-8")

    if PLACEHOLDER not in src_text:
        sys.stderr.write(
            f"ERROR: placeholder '{PLACEHOLDER}' not found in {agent_src}\n"
            "The agent YAML may have already been patched or is from a different version.\n"
        )
        sys.exit(1)

    patched = src_text.replace(PLACEHOLDER, hostname)

    # Sanity check: placeholder must be gone and real host must be present
    if PLACEHOLDER in patched or hostname not in patched:
        sys.stderr.write("ERROR: patch did not apply correctly\n")
        sys.exit(1)

    tmp_dir  = pathlib.Path(tempfile.gettempdir())
    tmp_path = tmp_dir / "lab2308_risk_agent_patched.yaml"
    tmp_path.write_text(patched, encoding="utf-8")

    # Print the path so the caller can pass it to `orchestrate agents import`
    print(str(tmp_path))


if __name__ == "__main__":
    main()
