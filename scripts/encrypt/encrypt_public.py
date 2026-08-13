#!/usr/bin/env python3
"""
Encrypt all HTML files in public-encrypted/ using StatiCrypt,
output the protected files to public/ (the GitHub Pages release folder).

Standard: this repo follows the `encryption-setup` skill. Password strategy:
  Each file's password = HMAC-SHA256(master_secret, relative_path), base64-encoded.
  - One master secret (ENCRYPT_SECRET in .env), never committed
  - Each file gets a unique password - sharing one doesn't expose others
  - Deterministic: regenerate any password from secret + filename

Overrides: `.password-overrides.json` (gitignored, repo root) maps a relative path
to a chosen password, for the occasional client who needs something memorable:
    { "reports/example.html": "clientname2026" }
The override is honoured by every code path including the pre-commit hook, so a
custom password survives future re-encryption instead of silently reverting to the
derived one. Overrides are weaker than derived passwords by definition - keep them
for low-sensitivity documents. The file is gitignored (it holds plaintext passwords
and this is a public repo), so teammates need a copy from Michael to re-encrypt
those files without changing their password.

Branding: the Growthify gate lives in scripts/encrypt/template.html (StatiCrypt
placeholder style), so the --template-* flags below fill its copy. This is the one
intentional local customisation on top of the skill's canonical script.

Usage:
    python3 scripts/encrypt/encrypt_public.py                     # encrypt all -> public/
    python3 scripts/encrypt/encrypt_public.py --show              # show passwords only
    python3 scripts/encrypt/encrypt_public.py --skip-unchanged    # skip up-to-date output
    python3 scripts/encrypt/encrypt_public.py --file reports/x.html  # one file only
"""

import argparse
import base64
import hashlib
import hmac
import json
import os
import subprocess
import sys
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent.parent

_env_file = WORKSPACE / ".env"
if _env_file.exists():
    for _line in _env_file.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))

SOURCE_DIR = WORKSPACE / "public-encrypted"
OUTPUT_DIR = WORKSPACE / "public"
TEMPLATE = Path(__file__).parent / "template.html"
OVERRIDES_FILE = WORKSPACE / ".password-overrides.json"

# Growthify gate copy (fills the placeholders in template.html)
BRAND_FLAGS = [
    "--template-title", "Growthify - Protected",
    "--template-instructions", "Enter the password sent to you to view this document.",
    "--template-button", "Unlock",
    "--template-placeholder", "Password",
    "--template-error", "That password didn't work. Try again.",
    "--template-remember", "Keep me signed in",
    "--template-toggle-show", "Show password",
    "--template-toggle-hide", "Hide password",
]


def derive_password(master_secret: str, relative_path: str) -> str:
    key = master_secret.encode("utf-8")
    msg = relative_path.encode("utf-8")
    digest = hmac.new(key, msg, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest)[:24].decode("ascii")


def load_overrides() -> dict:
    """Read .password-overrides.json - {relative_path: password}. Absent file is fine."""
    if not OVERRIDES_FILE.exists():
        return {}
    try:
        data = json.loads(OVERRIDES_FILE.read_text())
    except json.JSONDecodeError as exc:
        print(f"ERROR: {OVERRIDES_FILE.name} is not valid JSON: {exc}", file=sys.stderr)
        sys.exit(1)
    if not isinstance(data, dict):
        print(f"ERROR: {OVERRIDES_FILE.name} must be an object of path -> password.", file=sys.stderr)
        sys.exit(1)
    bad = [k for k, v in data.items() if not isinstance(v, str) or not v]
    if bad:
        print(f"ERROR: {OVERRIDES_FILE.name} has empty/non-string password(s) for: {', '.join(bad)}",
              file=sys.stderr)
        sys.exit(1)
    return data


def password_for(master_secret: str, relative_path: str, overrides: dict) -> tuple:
    """Return (password, is_override) - an override always wins over the derived value."""
    if relative_path in overrides:
        return overrides[relative_path], True
    return derive_password(master_secret, relative_path), False


def encrypt_file(src: Path, output_dir: Path, password: str) -> bool:
    output_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        "npx", "--no-install", "staticrypt",
        str(src),
        "--password", password,
        "-d", str(output_dir),
        "--short",
    ]
    if TEMPLATE.exists():
        cmd += ["--template", str(TEMPLATE), *BRAND_FLAGS]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"    staticrypt error: {result.stderr.strip()}", file=sys.stderr)
        return False
    return True


BASE_URL = "https://go.growthify.com.au/public/"


def print_password_table(passwords: dict, results: dict = None, overrides: dict = None):
    # Copy-paste friendly: URL + password per file (what you send the client).
    overrides = overrides or {}
    print()
    for name, pwd in passwords.items():
        status = f"  [{results[name]}]" if results else ""
        print(f"  {name}{status}")
        print(f"    URL:      {BASE_URL}{name}")
        tag = "  (override)" if name in overrides else ""
        print(f"    Password: {pwd}{tag}")
        print()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--show", action="store_true")
    parser.add_argument("--skip-unchanged", action="store_true")
    parser.add_argument("--file", metavar="FILENAME")
    args = parser.parse_args()

    master_secret = os.environ.get("ENCRYPT_SECRET", "")
    if not master_secret:
        print("ERROR: ENCRYPT_SECRET environment variable is not set.", file=sys.stderr)
        print("  Add ENCRYPT_SECRET='...' to .env (openssl rand -base64 32)", file=sys.stderr)
        sys.exit(1)

    if not SOURCE_DIR.exists():
        print(f"ERROR: Source directory '{SOURCE_DIR}' does not exist.", file=sys.stderr)
        sys.exit(1)

    html_files = sorted(SOURCE_DIR.rglob("*.html"))
    rel_paths = {f: str(f.relative_to(SOURCE_DIR)) for f in html_files}

    if args.file:
        html_files = [f for f in html_files if rel_paths[f] == args.file or f.name == args.file]
        if not html_files:
            print(f"ERROR: '{args.file}' not found in {SOURCE_DIR}", file=sys.stderr)
            sys.exit(1)

    if args.skip_unchanged:
        def _is_up_to_date(src: Path, rel: str) -> bool:
            out = OUTPUT_DIR / rel
            return out.exists() and out.stat().st_mtime >= src.stat().st_mtime

        skipped = [f for f in html_files if _is_up_to_date(f, rel_paths[f])]
        html_files = [f for f in html_files if not _is_up_to_date(f, rel_paths[f])]
        if skipped:
            print(f"Skipping {len(skipped)} up-to-date file(s): {', '.join(rel_paths[f] for f in skipped)}")

    if not html_files:
        print(f"No HTML files to process in {SOURCE_DIR}")
        sys.exit(0)

    overrides = load_overrides()
    passwords = {}
    used_overrides = {}
    for f in html_files:
        rel = rel_paths[f]
        pwd, is_override = password_for(master_secret, rel, overrides)
        passwords[rel] = pwd
        if is_override:
            used_overrides[rel] = pwd

    if args.show:
        print(f"\nPasswords for files in {SOURCE_DIR.relative_to(WORKSPACE)}/")
        print("(Master secret not shown - store it in your password manager)")
        if used_overrides:
            print(f"({len(used_overrides)} from {OVERRIDES_FILE.name}, marked override)")
        print_password_table(passwords, overrides=used_overrides)
        return

    template_note = f" (template: {TEMPLATE.name})" if TEMPLATE.exists() else " (default template)"
    print(f"\nEncrypting {len(html_files)} file(s){template_note}")
    print(f"  {SOURCE_DIR.relative_to(WORKSPACE)}/ -> {OUTPUT_DIR.relative_to(WORKSPACE)}/\n")

    results = {}
    for src in html_files:
        rel = rel_paths[src]
        out_dir = OUTPUT_DIR / Path(rel).parent
        print(f"  {rel} ...", end=" ", flush=True)
        ok = encrypt_file(src, out_dir, passwords[rel])
        results[rel] = "OK" if ok else "FAILED"
        print(results[rel])

    print("\nPasswords (share individually per recipient):")
    print_password_table(passwords, results, overrides=used_overrides)

    failed = [rel for rel, status in results.items() if status != "OK"]
    if failed:
        print(f"WARNING: {len(failed)} file(s) failed: {', '.join(failed)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
