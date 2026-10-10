#!/usr/bin/env python3
import json, urllib.request, os, yaml

creds_path = os.path.expanduser('~/.cache/orchestrate/credentials.yaml')
creds = yaml.safe_load(open(creds_path))
token = creds.get('wxo_mcsp_token', '')
if not token:
    print("ERROR: no wxo_mcsp_token in credentials.yaml")
    exit(1)

agent_yaml = os.path.join(os.path.dirname(__file__), 'agents/lab2308_risk_agent.yaml')
with open(agent_yaml) as f:
    agent = yaml.safe_load(f)

instructions = agent['instructions']
agent_id = '071222e2-9b7c-4c4f-8b37-258bc3587ad9'
wxo_url = 'https://api.ca-tor.watson-orchestrate.cloud.ibm.com/instances/616b18d0-1d1b-414d-9064-10f973502afb'

print(f"Patching agent {agent_id}...")
print(f"Instructions length: {len(instructions)} chars")

payload = json.dumps({'instructions': instructions}).encode()
req = urllib.request.Request(
    f'{wxo_url}/v1/orchestrate/agents/{agent_id}',
    data=payload,
    headers={
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    },
    method='PATCH'
)
try:
    resp = urllib.request.urlopen(req, timeout=30)
    print(f'✅ PATCH status: {resp.status} — agent updated')
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f'❌ PATCH error {e.code}: {body[:300]}')
