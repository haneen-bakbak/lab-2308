"""
Stdio shim for the TechZone OpenPages MCP server.
Bridges stdio (WxO ADK) <-> streamable HTTP (TechZone self-signed endpoint)
with SSL verification disabled.

Usage (from orchestrate toolkits add --command):
  python shim.py
"""

import asyncio
import json
import ssl
import sys
import os

import httpx

# The MCP URL is read from the environment variable set at toolkit registration time.
# OPENPAGES_MCP_URL must be set — if missing, fall back to the known TechZone host.
# NOTE: WxO cloud runner does NOT propagate env vars set on the local machine;
# the variable must be injected via the toolkit's connection/env mechanism.
# We hardcode the known host as the fallback so the shim works even without the var.
MCP_URL = os.environ.get(
    "OPENPAGES_MCP_URL",
    "https://wxgov-govconsole-demo-2ho7021k.vsi.techzone.ibm.com/mcp",
)

# Disable SSL verification for TechZone self-signed cert
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE


def fix_opapp_urls(text: str) -> str:
    """
    Rewrite internal Docker URLs returned by OpenPages before they reach the LLM.
    http://opapp:10108/...  →  https://<public_host>/openpages/...
    """
    public_host = os.environ.get(
        "OPENPAGES_PUBLIC_HOST",
        MCP_URL.split("/mcp")[0],  # e.g. https://wxgov-govconsole-demo-XXXX.vsi.techzone.ibm.com
    )
    return text.replace("http://opapp:10108", public_host + "/openpages")


def _extract_inner_text(data: object) -> str | None:
    """
    Dig through the MCP JSON-RPC envelope to find the innermost text payload.
    Envelope shape:
      {"jsonrpc":"2.0","result":{"content":[{"type":"text","text":"<inner_json_string>"}]}}
    The inner text is itself a JSON string that may contain another level of result/text.
    Returns the innermost text string, or None if not found.
    """
    if not isinstance(data, dict):
        return None
    # Level 1: {"result": {"content": [{"type":"text","text":"..."}]}}
    result = data.get("result")
    if isinstance(result, dict):
        content = result.get("content")
        if isinstance(content, list) and content:
            first = content[0]
            if isinstance(first, dict) and first.get("type") == "text":
                inner = first.get("text", "")
                # Level 2: inner may be another JSON string with result/text
                try:
                    inner_data = json.loads(inner)
                    if isinstance(inner_data, dict):
                        inner_result = inner_data.get("result")
                        if isinstance(inner_result, list) and inner_result:
                            deepest = inner_result[0]
                            if isinstance(deepest, dict) and deepest.get("type") == "text":
                                return deepest.get("text", "")
                        # Sometimes it's flat: {"message":..., "resource_id":...}
                        if "resource_id" in inner_data or "message" in inner_data:
                            return inner
                except (json.JSONDecodeError, TypeError):
                    pass
                return inner
    return None


def fix_upsert_response(envelope_text: str) -> str:
    """
    Find the real OpenPages resource_id buried in the MCP envelope and rewrite
    the innermost text so the LLM sees a clean, unambiguous resource_id.
    Also rewrites opapp:10108 URLs in the inner text.
    """
    try:
        envelope = json.loads(envelope_text)
    except (json.JSONDecodeError, ValueError):
        # Not JSON — just fix URLs and return
        return fix_opapp_urls(envelope_text)

    inner_text = _extract_inner_text(envelope)
    if inner_text is None:
        return fix_opapp_urls(envelope_text)

    # Fix opapp URLs in the inner text first
    inner_text = fix_opapp_urls(inner_text)

    try:
        inner = json.loads(inner_text)
    except (json.JSONDecodeError, ValueError):
        # Can't parse inner — rewrite opapp URLs in the full envelope string and return
        return fix_opapp_urls(envelope_text)

    resource_id = inner.get("resource_id") if isinstance(inner, dict) else None
    if resource_id and str(resource_id).isdigit() and int(resource_id) < 100000:
        public_host = MCP_URL.split("/mcp")[0]
        clean_url = (
            f"{public_host}/openpages/app/jspview/react/grc/task-view/{resource_id}"
        )
        clean_inner = {
            "message": inner.get("message", "Successfully created"),
            "operation": inner.get("operation", "INSERT"),
            "name": inner.get("name", ""),
            "resource_id": str(resource_id),
            "type": inner.get("type", "SOXRisk"),
            "parent_id": str(inner.get("parent_id", "")),
            "task_view_url": clean_url,
            "description": inner.get("description", ""),
            "_note": (
                f"CONFIRMED OpenPages Resource ID is {resource_id}. "
                f"Use this ID. URL: {clean_url}"
            ),
        }
        # Rebuild the envelope with the clean inner text
        try:
            envelope["result"]["content"][0]["text"] = json.dumps(
                {"result": [{"type": "text", "text": json.dumps(clean_inner)}]}
            )
            return json.dumps(envelope)
        except (KeyError, IndexError, TypeError):
            pass

    # Fallback: just fix opapp URLs in the whole envelope
    return fix_opapp_urls(envelope_text)


def fix_stringified_params(msg: dict) -> dict:
    """
    The LLM sometimes serialises dict-typed tool arguments as JSON strings
    instead of objects (e.g. fields='{"key":"val"}' instead of fields={"key":"val"}).
    Also coerces primaryParentId to string (OpenPages server requires a string,
    not an integer, or it throws 'int object has no attribute isdigit').
    """
    params = msg.get("params", {})
    args = params.get("arguments") or params.get("input") or {}
    if not isinstance(args, dict):
        return msg

    changed = False

    # Coerce primaryParentId to string — OpenPages MCP server requires it
    if "primaryParentId" in args and isinstance(args["primaryParentId"], int):
        args["primaryParentId"] = str(args["primaryParentId"])
        changed = True

    # Deserialise any dict/list arguments that were accidentally JSON-stringified.
    # Also handle double-brace escaping ({{ → {, }} → }) that the LLM sometimes
    # produces when it treats the JSON string as a Python format template.
    for key, value in args.items():
        if isinstance(value, str) and (
            (value.startswith("{") and value.endswith("}"))
            or (value.startswith("[") and value.endswith("]"))
            or (value.startswith("[{{") or value.startswith("{{"))
        ):
            candidate = value
            # First try as-is
            try:
                args[key] = json.loads(candidate)
                changed = True
                continue
            except json.JSONDecodeError:
                pass
            # Try unescaping double-braces ({{ → {, }} → })
            unescaped = candidate.replace("{{", "{").replace("}}", "}")
            if unescaped != candidate:
                try:
                    args[key] = json.loads(unescaped)
                    changed = True
                except json.JSONDecodeError:
                    pass

    if changed:
        new_params = dict(params)
        if "arguments" in params:
            new_params["arguments"] = args
        elif "input" in params:
            new_params["input"] = args
        msg = dict(msg, params=new_params)

    return msg


async def forward(client: httpx.AsyncClient, line: bytes) -> None:
    try:
        msg = json.loads(line)
    except json.JSONDecodeError:
        return

    msg = fix_stringified_params(msg)
    line = json.dumps(msg).encode()

    resp = await client.post(
        MCP_URL,
        content=line,
        headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"},
    )

    is_upsert = b"upsert" in line or b"openpages_upsert" in line

    content_type = resp.headers.get("content-type", "")
    if "text/event-stream" in content_type:
        async for raw in resp.aiter_lines():
            raw = raw.strip()
            if raw.startswith("data:"):
                data = raw[5:].strip()
                if data:
                    if is_upsert:
                        data = fix_upsert_response(data)
                    else:
                        data = fix_opapp_urls(data)
                    sys.stdout.buffer.write((data + "\n").encode())
                    sys.stdout.buffer.flush()
    else:
        body = resp.content.strip().decode(errors="replace")
        if body:
            if is_upsert:
                body = fix_upsert_response(body)
            else:
                body = fix_opapp_urls(body)
            sys.stdout.buffer.write((body + "\n").encode())
            sys.stdout.buffer.flush()


async def main() -> None:
    async with httpx.AsyncClient(verify=False, timeout=60) as client:
        loop = asyncio.get_event_loop()
        reader = asyncio.StreamReader()
        proto = asyncio.StreamReaderProtocol(reader)
        await loop.connect_read_pipe(lambda: proto, sys.stdin)

        while True:
            try:
                line = await reader.readline()
            except Exception:
                break
            if not line:
                break
            line = line.strip()
            if not line:
                continue
            await forward(client, line)


if __name__ == "__main__":
    asyncio.run(main())
