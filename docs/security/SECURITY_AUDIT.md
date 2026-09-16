# Security Audit — S49

| Field | Value |
|---|---|
| Audit date | 2026-09-16 |
| Commit audited | `7967c037` (main, = origin/main at audit time) |
| Auditor | S49 security campaign (automated + manual forensic passes) |
| Overall result | **NO CREDENTIAL COMPROMISE FOUND** — 0 real secrets in tree, history, metadata, or release assets |
| Report hygiene | This report never reproduces secret values. Findings identify type + location only. |

---

## 1. Scope and method

### 1.1 Surfaces scanned

| Surface | Tool | Coverage |
|---|---|---|
| Working tree (all files incl. untracked) | `scripts/security/deep_secret_scan.py`, `scripts/security/check_secrets.sh --tree` | every file under the repo root except `.git/`, `node_modules/` |
| `.git` metadata + reflogs | deep scanner (`--surfaces=meta`) | `config`, `packed-refs`, `COMMIT_EDITMSG`, `FETCH_HEAD`, `info/exclude`, every file under `.git/logs/` |
| Entire git object store | deep scanner (`--surfaces=objects`) | EVERY blob/commit/tag object reachable or unreachable (via `git cat-file --batch-all-objects`), i.e. **all history including deleted content** |
| Remote refs | `git ls-remote origin` + non-destructive fetch of divergent tags into `refs/s49-temp/*`, then a second full object-store scan | remote-only objects verified to add zero new findings |
| GitHub release assets | all 15 assets of the 7 published releases downloaded, extracted (tar.gz + zip), raw bytes AND extracted contents scanned | v0.0.1, v0.0.2, v0.0.2-alpha, v0.0.3-Chantecler, v0.0.4-Chantecler, v0.0.5-Silkie (0 assets), v0.0.6-Leghorn |
| Environment | `env` inspection (masked), `~/.gitconfig`, `~/.git-credentials`, `~/.netrc`, shell history files | no credential env vars, no credential files, no shell history exists in the build container |

### 1.2 Detection patterns

GitHub fine-grained PAT (`github_pat_…`), GitHub classic tokens (`ghp_/gho_/ghu_/ghs_/ghr_…`),
AWS access/temp keys (`AKIA…`/`ASIA…`), PEM private key blocks, URL-embedded credentials
(`scheme://user:pass@host`), Authorization headers, OpenAI-style keys (`sk-…`), Google API keys
(`AIza…`), GitLab PATs (`glpat-…`), npm tokens, and generic token assignment forms
(`GITHUB_TOKEN=…` and friends). Placeholder filtering suppresses documentation values
(`changeme`, `user:password@…example`, `${VAR}` forms, …).

---

## 2. Results

### 2.1 NOT FOUND (the decisive negatives)

- **GitHub PAT / classic token / OAuth token**: NOT FOUND in the working tree, in any
  commit message or diff across all history, in any reflog, in `.git/config`
  (remote URL is credential-free), in any release asset, or in any commit/tag object.
- **Private keys, cloud credentials, password dumps, `.env`-style credential files**: NOT FOUND.
  The single `.env` file present is untracked, ignored by `.gitignore:39`, and contains only a
  local SQLite path — no credential.
- **`docs/evidence/PUSH_BLOCKED.json`** (tracked, audited explicitly per S49 §0.6): contains
  push-failure forensics only. Zero secret-shaped strings. Its historical record also supplied
  the provenance that explains the early-tag lineage divergence (§2.4).
- **Credential infrastructure**: no `credential.helper` configured, no `~/.git-credentials`,
  no `~/.netrc`, no `gh` CLI state, no GitHub Actions workflows exist (`.github/` absent).

### 2.2 Findings classified as NOT-a-credential (public-by-design / documentation)

| # | Location (tree path or git blob) | Pattern | Classification | Published? |
|---|---|---|---|---|
| F1 | `docs/runtime/research/raw/android_bytecode_doc.json` (blob `3944b6a3`) | Google API key ×9 | The captured devsite configuration of Google's own public developer sites (source.android.com / developers.google.com). These browser keys are printed inside Google's public HTML. **Public-by-design.** | Yes (on origin/main) |
| F2 | `download/exp038_telegram/resource_values.json` (blob `3bc64b59`), `download/exp038_telegram/Telegram.apk` (blob `b2d52d57`), `run/exp067/manifest.json` (blob `53435a15`) | Google API key | Same public devsite key family captured during research; APK-resident keys are public inside the distributed APK artifact by definition. **Public-by-design.** | No (local-only blobs; paths retired from tree) |
| F3 | `download/exp037_real_apks/fdroid_index_v2.json` (blob `76819507`) | URL-embedded credential | The F-Droid app changelog text "Allows basic auth using urls" followed by a literal placeholder with an RFC-2606 `.example` host. **Documentation placeholder.** | No (local-only blob) |
| F4 | legacy v0.0.1-Brahma Windows release asset | Google API key ×5 | The v0.0.1 release shipped a full source/docs snapshot containing the same `android_bytecode_doc.json` research file as F1. **Public-by-design** (same constants as F1). | Yes (GitHub release asset) |
| F5 | various HTML/image design assets | AWS/sk-/AIza shapes | Matches **inside base64 asset blobs** (random 4-byte alignment inside embedded images/videos). Eliminated from the permanent guard by two-sided boundary rules; verify with the deep scanner when in doubt. **Not credentials.** | mixed |

### 2.3 Tooling defect found and fixed during the audit (process security)

- `mawk` 1.3.4 mishandles ERE interval expressions (`{20,}`): it produced both false
  positives and missed detections versus GNU grep on identical input. The permanent guard
  uses GNU `grep -E` as its only regex engine; the defect is documented in the guard header
  so no future revision reintroduces awk matching.
- A value-disclosure hazard was found and closed in the guard's own reporting path: with a
  single-file scan target, `grep` omits the filename prefix, which historically would have
  allowed a matched line to be misreported. The guard now (a) forces `-H`, (b) reformats
  matches to `path:line` inside the pipe, and (c) reports **only** lines that parse as
  `path:digits` — any other shape is dropped. A secret value therefore has no path to
  stdout even under tool failure. The `--selftest` battery (7 synthetic detections +
  5 false-positive sources) catches any regression of this property.

### 2.4 Early-tag lineage divergence (audited, explained, no action)

`v0.0.1`, `v0.0.2`, `v0.0.2-alpha` tag objects differ between local and remote
(remote = annotated `4deef95d` → commit `ed2dae0e`; local = re-created lightweight/annotated
variants pointing at twin commits `d5af5ec0`/`0abed01b`/`dc7be2d0` with identical subjects and
dates, all OFF the main lineage). Root cause has provenance: `PUSH_BLOCKED.json` records these
tags as "tags_on_remote_only" before the 2026-09-05 credential-free period ended; the local
re-tagging happened during the resolution. All six commits predate the main lineage's current
root; the deep scan covered the fetched remote-only objects and found **zero** new findings.
No history rewrite is required or performed.

---

## 3. GitHub release audit (S49 §0.4)

- All 7 releases enumerated via the public releases page; 15 assets downloaded and scanned
  (see §1.1). **No credential found in any asset.**
- `v0.0.6-Leghorn` (current): both artifacts independently downloaded and their SHA256
  **match** `docs/releases/RELEASE_MANIFEST.json`:
  - `MiniAndroid-v0.0.6-Leghorn-linux-x64.tar.gz` = `20ece925…f8780`
  - `MiniAndroid-v0.0.6-Leghorn-windows-x64.zip` = `934d6edc…f3267`
  (full digests recorded in the manifest; deliberately abbreviated here).
- **DEFECT (release hygiene, not a secret)**: the `SHA256SUMS.txt` asset attached to the
  v0.0.6-Leghorn GitHub release contains the **v0.0.4-Chantecler** checksum list (copy-paste
  error at publish time) and omits the v0.0.6 digests entirely. Correct content is fully
  recoverable from `docs/releases/RELEASE_MANIFEST.json`. **Status: BLOCKED** — replacing a
  release asset requires an authenticated GitHub API call, and no credential is available to
  the audit session (by policy none is stored). Fix when a credential is next available:
  delete/replace the `SHA256SUMS.txt` asset with the manifest-derived digest list, then
  re-verify by re-downloading.
- `v0.0.5-Silkie` ships **0 assets** (documentation-only release) — noted, no action.
- `v0.0.1`/`v0.0.2-alpha` shipped full source/docs snapshots (including the F4 research file);
  releases since v0.0.3 follow the lean packaging law. Legacy assets remain public-by-design;
  no remediation required.

---

## 4. Prevention (S49 §0.5) — permanent, fail-closed

1. **`scripts/security/check_secrets.sh`** — fast guard, three modes:
   `--tree` (whole working tree), `--staged` (git index), `PATH…` (release staging).
   Fail-closed exit codes (0 clean / 1 SECRET FOUND / 2 usage error). Never prints values
   (see §2.3). `--selftest` proves detection + filtering on demand.
2. **`scripts/security/deep_secret_scan.py`** — forensic tool of record: scans the ENTIRE git
   object store (all history incl. unreachable objects), `.git` metadata/reflogs, and the
   working tree. Same no-value-output contract. Runs per audit campaign and before any
   history-sensitive operation.
3. **Release pipeline integration** — `scripts/release/check_release_artifacts.sh` step 5 now
   runs the secret guard on every extracted staging tree; a finding fails the release guard.
4. **Git hooks** — `scripts/security/hooks/pre-commit` (scans staged content) and
   `scripts/security/hooks/pre-push` (scans the tree) via idempotent
   `scripts/security/install_hooks.sh`. Both installed in this clone.
5. **Allowlist discipline** — `scripts/security/secret_scan_allowlist` contains only the two
   documented, independently verified public-constant locations (F1, F3). Every entry must
   cite this audit. Never silence a real credential here.

---

## 5. Remediation record

| Item | Action | Status |
|---|---|---|
| Repo/history secrets | none found — no removal, no history rewrite needed | N/A (clean) |
| Chat-exposed PAT (never committed) | token never entered tree/history/assets (verified §2.1). It was shared in plaintext chat, so **rotation at expiry is still recommended** as standard hygiene | RECOMMENDED (owner action) |
| v0.0.6 `SHA256SUMS.txt` asset | replace with manifest-derived digests (authenticated API) | **BLOCKED** — no credential in session; content prepared in `docs/releases/RELEASE_MANIFEST.json` |
| Guard tooling | implemented + self-tested + integrated + hooks installed | DONE (VERIFIED) |
| Allowlist entries | documented with citations to this report | DONE |

## 6. Re-audit protocol

Run before every release and any credential-adjacent change:

```bash
bash scripts/security/check_secrets.sh --selftest   # guard operational?
bash scripts/security/check_secrets.sh --tree       # working tree clean?
python3 scripts/security/deep_secret_scan.py --surfaces=objects,meta   # full history clean?
```

All three must pass (selftest exit 0; tree/meta/objects "NOT FOUND") before
commit/push/publish proceeds.
