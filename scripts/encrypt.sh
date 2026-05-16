#!/usr/bin/env bash
# Encrypts every HTML file under public-encrypted/ into public/ using StatiCrypt.
# Per-file password = HMAC-SHA256(master_secret, relative_path).
# Deterministic per-repo salt → no commit noise when source is unchanged.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

if [ -z "${STATICRYPT_MASTER_SECRET:-}" ]; then
  echo "encrypt.sh: STATICRYPT_MASTER_SECRET not set — skipping" >&2
  exit 0
fi

SRC="public-encrypted"
OUT="public"

if [ ! -d "$SRC" ]; then
  exit 0
fi

# Per-repo salt (32 hex chars, deterministic)
REPO_SALT=$(printf "%s" "staticrypt-salt" \
  | openssl dgst -sha256 -hmac "$STATICRYPT_MASTER_SECRET" -hex \
  | awk '{print $NF}' | cut -c1-32)

mkdir -p "$OUT"

while IFS= read -r -d '' src_file; do
  rel_path="${src_file#$SRC/}"
  password=$(printf "%s" "$rel_path" \
    | openssl dgst -sha256 -hmac "$STATICRYPT_MASTER_SECRET" -hex \
    | awk '{print $NF}' | cut -c1-32)
  out_dir="$OUT/$(dirname "$rel_path")"
  mkdir -p "$out_dir"
  npx --no-install staticrypt "$src_file" \
    --password "$password" \
    --salt "$REPO_SALT" \
    --short \
    -d "$out_dir" >/dev/null
done < <(find "$SRC" -type f -name "*.html" -print0)

# Stage regenerated output
git add "$OUT/" 2>/dev/null || true
