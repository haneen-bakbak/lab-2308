# Credential Safety Rules — Lab 2308

These rules apply in every conversation while in `lab2308` mode.

## API Key Handling

- **Never** display a WxO API key in full. Always show only the first 8 characters followed by `...`
  Example: `p9xK3mQr...`
- **Never** include an API key in any visible output, log message, or confirmation message.
- **Never** write an API key to any file other than the ADK environment config
  (managed by `orchestrate env activate`).
- When the attendee asks how their key is stored: "Your API key is saved only in the local
  watsonx Orchestrate ADK config on your machine — it's never stored anywhere else."
- If the attendee pastes a key that looks wrong (fewer than 20 characters, contains spaces,
  starts with `sk-`), ask them to re-check before proceeding.

## MCP URL Handling

- Silently normalise the MCP URL before using it:
  - Strip trailing slashes
  - If it ends in `/openpages`, replace with `/mcp`
  - If it has no path, append `/mcp`
- Never display the full URL in a way that could be copy-pasted to another attendee's setup.

## After Setup

- If setup succeeds, confirm with `check_env.py` output before saying the attendee is done.
- Never hard-code or reuse any credential found in any file in this repo.
  Every attendee has their own TechZone reservation with their own key and URL.
