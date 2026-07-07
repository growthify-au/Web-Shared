# Web-Shared

Public GitHub Pages repo. Serves at `go.growthify.com.au` (custom domain).

Sibling of the client services repo (lives at `~/Documents/gAIme plan/Business/web shared/`) - the public layer for client-facing HTML deliverables.

## What lives here vs in the workspace
- **Workspace** (`Business/client services/`, private): drafts, data, working files
- **This repo** (public): only files ready to publish

## Layout
- `index.html` - root landing (blank for now)
- `public-encrypted/` - **source** HTML for sensitive content (you edit here)
- `public/` - encrypted output, auto-generated on commit (deploys to `go.growthify.com.au/public/...`)
- `scripts/encrypt/` - `encrypt_public.py` (encrypt) + `template.html` (Growthify gate). Follows the `encryption-setup` skill (gAIme plan level).
- `Makefile` - `make encrypt` / `make encrypt-show` / `make encrypt-changed`
- `.githooks/pre-commit` - runs `encrypt_public.py --skip-unchanged` on every commit

## Encrypt vs leave public
**Encrypt** (drop into `public-encrypted/`):
- Client reports, dashboards, audits
- Internal performance data (revenue, ROAS, CPA)
- Proposals with pricing
- Campaign briefs with competitive intel
- Strategy docs

**Leave public** (drop at repo root or in plain subfolders):
- Personal portfolio / about pages
- Marketing for Growthify's own services
- Public case studies (with sensitive numbers redacted)
- Training materials

## Workflow

### Add an encrypted deliverable
1. Save the HTML to `public-encrypted/<path>/<file>.html`
2. `git add` + `git commit` - pre-commit hook encrypts it into `public/<path>/<file>.html`
3. `git push`
4. Live at `go.growthify.com.au/public/<path>/<file>.html`

### Look up the password to share with a client
```
make encrypt-show
```
Shows file → password mapping (derives without re-encrypting). Send the URL and password in **separate channels** (e.g. URL via email, password via DM).

### Re-encrypt without committing (e.g. after editing locally)
```
make encrypt
```

## Teammate onboarding (one-time per machine)
1. `git clone https://github.com/growthify-au/Web-Shared.git`
2. `npm install` (installs StatiCrypt)
3. `cp .env.example .env` and paste in the master secret as `ENCRYPT_SECRET` (get it from Michael)
4. `git config core.hooksPath .githooks` (enables auto-encrypt on commit)

## Master secret
Stored in `.env` (gitignored). Back up in password manager. If lost, all passwords change on the next encryption - see the encryption docs for recovery.
