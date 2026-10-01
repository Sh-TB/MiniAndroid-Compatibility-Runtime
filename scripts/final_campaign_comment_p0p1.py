#!/usr/bin/env python3
"""Post FINAL CAMPAIGN Phase 0+1 comment to issue #354 (idempotent)."""
import json
import subprocess
import sys
import urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
API = f"https://api.github.com/repos/{REPO}/issues/354/comments"

HEADER = "## FINAL GENERIC RUNTIME COMPATIBILITY CAMPAIGN — Phase 0 + Phase 1 DONE (repo hygiene: 591.89 → 160.04 MiB, −73%)"

BODY = HEADER + """

Mission received (21 phases). Final proof chain accepted: SOURCE → SEMANTIC LAW → RUNTIME IMPLEMENTATION → REAL APK EXECUTION → VIEWTREE/OBJECT STATE → MEASURE → LAYOUT → DRAW → AUTHORITATIVE FRAME → PIXEL METRICS → 3-RUN REPRODUCIBILITY. Hard constraints accepted: EVERY fix GENERIC, ZERO package-name checks, ZERO app-specific branches, diagnostic pixels never in authoritative frames.

### PHASE 0 — LAW + REAL HEAD (established, not assumed)
- LAWS/RULES READ: `CONSTITUTION_V2.md` (all 56 sections — §2 source-first, §16 first divergence, §18 null semantics, §27 blank-screen-is-a-symptom, §30 window/content, §31-35 visual proof chain, §34 no fake visual success, §37 instrumentation behavior-neutral, §51 no app-specific hacks, §52 generic fix fan-out); `docs/ROADMAP_STATUS.md` (full); `docs/ARTIFACT_LIFECYCLE.md` (full — the repository hygiene law); `docs/REPO_HYGIENE_FORENSICS.md`; `canonical/root_cause_registry.json` (454 roots projection) + `canonical/capability_registry.json` (197 capabilities) + `docs/ARTIFACT_REGISTRY.json`; latest S134/S135 worklog entries (S130..S134-wave-6 + S135 logger full record).
- HEAD: `7bf17710` (main, clean tree). **S135 logger commit `a60db4b5` PROVEN ancestor of current main via `git merge-base --is-ancestor`** — the visual logger is in current HEAD implementation, not just history. Remote synced before this phase.
- Build state: laws130 target + battery baseline to be re-verified at first engine-touch phase.

### PHASE 1 — REPOSITORY HYGIENE (measured, dispositioned, gated)
- **AUDIT** (`scripts/final_campaign_phase1_audit.py`): tracked tree **591.89 MiB / 9,673 files** — exactly the mission numbers. evidence/ 264.57 MiB + tmp/ 189.82 MiB = **76.8%**. Waste decomposition: **1,129 raw trace files = 241.47 MiB inside evidence/** (canonical screenshots ≈ 12 MiB only); tmp/ offenders: `archidx.json` 88.44, `index-v1.json` 60.20, `mykanji_extract/` 14.38 (extracted APK + 12.89 MiB external font), `idx.jar` 13.98, `blid/classes.dex` 7.15 (APK-derived), flappy_build/ac_x/aa_check scratch.
- **REFERENCE CHECK before any deletion** (no blind dedup): archidx/index-v1/idx.jar/mykanji_extract/notoserifjp = ZERO canonical refs (measured by grep over worklog+docs+canonical+scripts+tools); `tmp/blid` referenced by exactly ONE one-off script; z.ai production JS bundle (3.09 MiB — mission-forbidden class) referenced by REPORT_S133.md table.
- **EXECUTION** (`scripts/final_campaign_phase1_cleanup.py --apply`):
  - 1,129 raw traces **distilled** into 545 `evidence/*/TRACE_SUMMARIES.json` — each trace keeps SHA256 + size + generated_at + session_id + total_calls + top-20 API census + distinct-API count (provenance + analytic value preserved, payload gone).
  - `DISPOSITION_LEDGER.json`: **1,283 entries**, every one with SHA256 + size + reason + law citation (`docs/history/final_campaign_phase1/`). Never deleted silently.
  - `git rm` 1,283 tracked files; `blid` dex restored to `external_backup/s112/blid/` (SHA `c4ca8802…e88e` verified byte-exact) and the s112 script re-pointed; REPORT_S133.md bundle row updated to SHA provenance.
  - `.gitignore` extended: tmp scratch classes, evidence raw-trace classes, `*_bundle*.js`, `*.apk`, `*.aab`.
  - Hygiene gate oversize allowlist documented for two canonical pinned artifacts (NOT APK payloads): `framework_res/resources.arsc` (AOSP framework-res base data, S127 R-NEW-423 law — required by every APK resource resolve) and `tools/r8/r8.jar` (pinned R8/D8 fixture-build tool, Apache-2.0).
- **GATES**: `tools/check_repo_hygiene.py` **PASS** (8,390 files — zero APK/so, zero build dirs, zero raw logs, zero archive blobs, zero oversize, zero secrets). Artifact registry REGENERATED from the actual tree (stale registry retired).
- **RESULT: tracked tree 591.89 → 160.04 MiB (−431.85 MiB, −73%). evidence/ 264.57 → 20.01. tmp/ 189.82 → 2.50. Large files removed/moved: 1,283.** Commit `d6237036` pushed.

### NEXT (in progress)
Phase 2 — complete field-identity audit (F-NEW-160: DEX-defined qualified identity vs the bare-name mirror; reflection/Unsafe/initializer defaults; field identity table; goldens must stay byte-identical), then Phase 3 — F-NEW-169 attack via bounded first-REC-MISS trace."""


def gh_token():
    out = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        capture_output=True, text=True, cwd="/home/z/my-project",
    ).stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line[len("password="):]
    raise RuntimeError("no token")


def req(url, token, data=None, method=None):
    r = urllib.request.Request(url, method=method)
    r.add_header("Authorization", f"token {token}")
    r.add_header("Accept", "application/vnd.github+json")
    r.add_header("User-Agent", "miniandroid-campaign")
    body = json.dumps(data).encode() if data is not None else None
    if body:
        r.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(r, body) as resp:
        return json.loads(resp.read().decode())


def main():
    token = gh_token()
    existing = req(f"{API}?per_page=100", token)
    if any(c["body"].split("\n")[0] == HEADER for c in existing):
        print("SKIP (exists)")
        return
    c = req(API, token, data={"body": BODY}, method="POST")
    print(f"POSTED: {c['html_url']}")


if __name__ == "__main__":
    main()
