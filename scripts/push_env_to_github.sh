#!/usr/bin/env bash
# Sync secrets from local .env → GitHub Actions repo secrets.
# Requires: Python 3 + PyNaCl (pip install PyNaCl) + httpx (pip install httpx).
#
# Usage:
#   ./scripts/push_env_to_github.sh
#   REPO=org/repo ./scripts/push_env_to_github.sh       # override repo
#   ENV_FILE=.env.local ./scripts/push_env_to_github.sh # override env file

set -euo pipefail

REPO="${REPO:-Shaunakm07/automatic-marketing}"
ENV_FILE="${ENV_FILE:-.env}"

# Secrets the workflows actually need (GITHUB_TOKEN is auto-provided by Actions)
REQUIRED_SECRETS=(
  ANTHROPIC_API_KEY
  SUPABASE_URL
  SUPABASE_SERVICE_ROLE_KEY
  X_BEARER_TOKEN
)

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Error: $ENV_FILE not found. Run from the project root." >&2
  exit 1
fi

# Extract GitHub token from .env for API auth
GITHUB_TOKEN=$(grep -m1 "^GITHUB_TOKEN=" "$ENV_FILE" 2>/dev/null | cut -d= -f2- | tr -d '"' || true)
if [[ -z "$GITHUB_TOKEN" ]]; then
  echo "GITHUB_TOKEN not found in $ENV_FILE." >&2
  exit 1
fi

# Build KEY=VALUE pairs for secrets we want to push
PAIRS=""
for key in "${REQUIRED_SECRETS[@]}"; do
  value=$(grep -m1 "^${key}=" "$ENV_FILE" 2>/dev/null | cut -d= -f2- | tr -d '"' || true)
  if [[ -n "$value" ]]; then
    PAIRS+="${key}=${value}"$'\n'
  else
    echo "  skip  $key (not set in $ENV_FILE)"
  fi
done

echo "Pushing secrets to $REPO ..."

python3 - "$REPO" "$GITHUB_TOKEN" <<PYEOF
import sys, base64, json
import httpx

repo      = sys.argv[1]
token     = sys.argv[2]
pairs_raw = """${PAIRS}"""

pairs = {}
for line in pairs_raw.strip().splitlines():
    if "=" in line:
        k, _, v = line.partition("=")
        pairs[k.strip()] = v.strip()

headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

client = httpx.Client(headers=headers, timeout=15)

# Get repo public key for secret encryption
pk_data = client.get(f"https://api.github.com/repos/{repo}/actions/secrets/public-key").json()
key_id  = pk_data["key_id"]
pub_key = pk_data["key"]

try:
    from nacl import encoding, public as nacl_public
    def encrypt(secret_value: str) -> str:
        pk  = nacl_public.PublicKey(pub_key, encoding.Base64Encoder)
        box = nacl_public.SealedBox(pk)
        return base64.b64encode(box.encrypt(secret_value.encode())).decode()
except ImportError:
    print("PyNaCl not installed. Run: pip install PyNaCl", file=sys.stderr)
    sys.exit(1)

pushed = 0
for name, value in pairs.items():
    encrypted = encrypt(value)
    resp = client.put(
        f"https://api.github.com/repos/{repo}/actions/secrets/{name}",
        json={"encrypted_value": encrypted, "key_id": key_id},
    )
    ok = resp.status_code in (201, 204)
    print(f"  {'→' if ok else '✗'}  {name}: {'ok' if ok else f'ERROR {resp.status_code}'}")
    if ok:
        pushed += 1

print(f"\nDone: {pushed}/{len(pairs)} secrets pushed to {repo}")
PYEOF
