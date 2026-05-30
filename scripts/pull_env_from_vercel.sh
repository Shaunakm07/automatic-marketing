#!/usr/bin/env bash
# Pull env vars from Vercel → .env (overwrites local file).
# Usage: ./scripts/pull_env_from_vercel.sh

set -euo pipefail

VERCEL="${VERCEL_CLI:-$(which vercel 2>/dev/null || echo "$HOME/.local/bin/vercel")}"

if ! "$VERCEL" whoami &>/dev/null; then
  echo "Not logged in to Vercel. Run: vercel login" >&2
  exit 1
fi

"$VERCEL" env pull .env --environment=production --yes
echo "Pulled production env vars into .env"
