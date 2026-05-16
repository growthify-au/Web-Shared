#!/usr/bin/env bash
# Prints the per-file password for every HTML in public-encrypted/.
# Password = HMAC-SHA256(STATICRYPT_MASTER_SECRET, relative_path), first 32 hex chars.
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
  echo "STATICRYPT_MASTER_SECRET not set (check .env)" >&2
  exit 1
fi

SRC="public-encrypted"
if [ ! -d "$SRC" ]; then
  echo "No $SRC/ folder yet."
  exit 0
fi

printf "%-50s  %s\n" "FILE" "PASSWORD"
printf "%-50s  %s\n" "----" "--------"
find "$SRC" -type f -name "*.html" | sort | while read -r f; do
  rel="${f#$SRC/}"
  pw=$(printf "%s" "$rel" \
    | openssl dgst -sha256 -hmac "$STATICRYPT_MASTER_SECRET" -hex \
    | awk '{print $NF}' | cut -c1-32)
  printf "%-50s  %s\n" "$rel" "$pw"
done
