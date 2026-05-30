#!/usr/bin/env bash
# Push all non-empty vars from .env → Vercel (production + preview + development).
# Usage: ./scripts/push_env_to_vercel.sh [--production-only]
#
# Skips lines that are comments, blank, or have an empty value.
# Safe to re-run — Vercel overwrites existing vars with the same name.

set -euo pipefail

VERCEL="${VERCEL_CLI:-$(which vercel 2>/dev/null || echo "$HOME/.local/bin/vercel")}"
ENV_FILE="${ENV_FILE:-.env}"
ENVS="production preview development"

if [[ "${1:-}" == "--production-only" ]]; then
  ENVS="production"
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Error: $ENV_FILE not found. Run from the project root." >&2
  exit 1
fi

if ! "$VERCEL" whoami &>/dev/null; then
  echo "Not logged in to Vercel. Run: vercel login" >&2
  exit 1
fi

pushed=0
skipped=0

while IFS= read -r line || [[ -n "$line" ]]; do
  # Skip comments and blank lines
  [[ "$line" =~ ^[[:space:]]*# ]] && continue
  [[ -z "${line//[[:space:]]/}" ]]  && continue

  # Split on first = only (handles values that contain =)
  key="${line%%=*}"
  value="${line#*=}"

  # Skip if key is empty or value is empty
  [[ -z "$key" || -z "$value" ]] && { skipped=$((skipped+1)); continue; }

  echo "→ $key"
  # shellcheck disable=SC2086
  printf '%s' "$value" | "$VERCEL" env add "$key" $ENVS --force 2>/dev/null || \
  printf '%s' "$value" | "$VERCEL" env add "$key" $ENVS
  pushed=$((pushed+1))
done < "$ENV_FILE"

echo ""
echo "Done: pushed $pushed vars, skipped $skipped (blank values)."
echo "Redeploy to apply: vercel --prod"
