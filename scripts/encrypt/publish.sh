#!/usr/bin/env bash
# One-step publish: copy a report into public-encrypted/reports/, encrypt it,
# and print the shareable URL + password.
#
# Usage:
#   make publish FILE="/path/to/report.html"
#   make publish FILE="/path/to/report.html" NAME="billiard-shop-google-ads-audit.html"
#
# FILE  - the generated HTML report to publish (any location)
# NAME  - optional output filename (defaults to the source basename)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

SRC="${FILE:-}"
if [ -z "$SRC" ]; then
  echo "ERROR: pass the report path, e.g. make publish FILE=\"/path/to/report.html\"" >&2
  exit 1
fi
if [ ! -f "$SRC" ]; then
  echo "ERROR: file not found: $SRC" >&2
  exit 1
fi

NAME="${NAME:-$(basename "$SRC")}"
REL="reports/$NAME"
DEST="public-encrypted/$REL"

mkdir -p "public-encrypted/reports"
cp "$SRC" "$DEST"
echo "Copied -> $DEST"

python3 scripts/encrypt/encrypt_public.py --file "$REL"

echo "Done. Commit + push to deploy (or it happens automatically on your next commit)."
