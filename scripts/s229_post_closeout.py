#!/usr/bin/env python3
"""S229 — post the S213/S214 closeout comment on #587 (the forgotten-items wave)."""
import json
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]  # repo-root discovery (WP4/R11 law)

BODY = """# S229 closeout — S213 + S214 governance packages implemented (the items that arrived after the S212 closeout)

**Audited state:** the S212 closeout (comment 6847022917) delivered WP0–WP11/R01–R35, but the two packages posted afterwards — **S213** (comment 6853869494 + addendum §S213) and **S214** (comment 6853939129 + addendum §S214) — were not yet executed. This wave implements both, in code + tests + enforcement, not documentation alone. Base `ba178ed4` → HEAD `501391cf` (7 reviewable commits, pushed).

## S213 — evidence image formats and storage budgets

- **A. JPEG-by-default policy — IMPLEMENTED.** Photographic/noisy → optimized JPEG (ladder 85→80→75→70, sRGB, optimize+progressive, metadata stripped); target ≤100 KiB; >200 KiB fails promotion without a reviewed per-file exception; PNG >100 KiB disallowed by default for photographic content; PNG mandatory for alpha/diagram/pixel-art; animations never flattened; `fixtures/`/`upstream/`/runtime resources never converted; idempotent (no recompression, no derivative chains); documented resize fallback only when the quality ladder cannot meet the budget.
- **B. Tooling + enforcement — IMPLEMENTED/TESTED.** `tools/evidence_image_optimizer.py` (inventory / convert-to-staging / validate / baseline modes; staging-only non-destructive; SHA-256 source→output mapping + settings + size delta; RMS-Δ visual metric — documented SSIM-equivalent; lossy conversion never supports pixel-exact claims). 9 unit tests covering **all 8 required cases** (JPEG idempotence, large noisy PNG, transparent PNG, pixel-art/diagram PNG, GIF animation preservation, corrupt input, duplicate-output determinism, already-small) — **9/9 OK**. Validator integration: `IMAGE_POLICY_NEW`/`IMAGE_POLICY_MUTATED` reject new over-threshold evidence; registries `docs/IMAGE_POLICY_BASELINE.json` (**72 per-path legacy entries, 38,179,812 B** — adoption inventory with owner/reason/review-trigger, not a blanket exception) + `docs/IMAGE_EXCEPTIONS.json` (exact-path exceptions; today exactly ONE entry). Full tracked-image inventory committed (`evidence/s229_s213_s214/image_inventory.csv`, 1,349 images: 1,184 OK / 90 MIGRATE_TO_JPEG / 22 REJECT_PROMOTION / 20 animations / 17 unreadable 0–33 B residue recorded UNREADABLE_CORRUPT→DELETE_CANDIDATE at the migration wave).
- **C. cont69_mosaic — IMPLEMENTED (measured, claim not repeated).** Claimed 12x is wrong: **measured 17.78x total** (PNG 896,399 B @2160x5000 vs tracked JPG 50,423 B @553x1280), of which **only 1.75x is the format effect at identical native resolution** (512,223 B @q85) — the rest is the 15.3x downsampling. JPG proven derived (RMS-Δ 0.814, max Δ 9/255). Disposition: JPG = presentation asset; PNG = provenance source under the single narrow exception; consumers audited (registry references the PNG as provenance; no presentation embed exists — future presenters link the JPG). Full audit: `evidence/s229_s213_s214/cont69_mosaic_audit.md`.
- **D. s195/s202 paths — IMPLEMENTED.** `evidence/s202_625_forced/` = **NOT_PRESENT** (no commit history on main — honest finding, nothing tracked to classify). `evidence/s195_audit/` = 252 files classified (144 JSON/33 JSONL/36 MD compact reproducibility metadata KEEP; 11 reconstruction patches KEEP; 6 canonical JPG faces KEEP; 3 oversized PNG screenshots MIGRATE_CANDIDATE; store trees incl. db/-wal/-lck KEEP as recorded run state). `tictactoe_s195fix_r1/` = 4 compact metadata files KEEP + the 3,360,833 B PNG **demonstrated through the optimizer**: 99,178 B JPEG (q75, RMS-Δ 0.634, 33.89x smaller) committed under the wave dir with the full SHA-256 mapping — frozen-area original untouched, migration goes through this ledger. Per-run folders: one compact machine-readable summary + minimal promoted visual; raw frames default to ignored `.cache/`.
- **E. Canonical demo gallery — IMPLEMENTED.** All four named GIFs verified genuine animations (g2048 65 frames/22.5 s/979,913 B; tetris 75/13.66 s/770,771 B; snakedeluxe 49/14.4 s/493,247 B; minicraft 15/5.6 s/172,914 B) with canonical-registry provenance (records 50/51/52/147, per-record in-house APK SHA-256). README now shows the four-demo gallery **immediately after the scope statement and before architecture/build details**, with captions + evidence links. Honest boundary, stated in the gallery note: RC-binary re-runs of these four are **PARTIAL** (the five demos re-verified on `06f98d2a9c21ea92` remain the RC-proven set). No GIF flattened.
- **F. Deliverables — IMPLEMENTED.** Before/after inventory + conversion manifest + policy/tests/validator/CI integration + cont69 comparison + three-path disposition + README gallery diff + clean-clone validation, all under `evidence/s229_s213_s214/`.

## S214 — hard release gate + zero-drift repository law

- **WP1 — IMPLEMENTED (gate) / BLOCKED (artifact — measured, not assumed).**
  - `docs/releases/RELEASE_MANIFEST.json` v2: `required_platforms` (linux-x64=PASS w/ sha256+bytes+evidence; windows-x64=**BLOCKED** w/ exact blocker + diagnosis + unblock path) and `release_class=linux-only-preview` naming the Windows gap prominently.
  - `scripts/release/validate_release_manifest.py`: **no-silent-downgrade** — a normal/stable release class with any non-PASS mandated platform FAILS; PASS without artifact/sha/bytes FAILS; BLOCKED without blocker+diagnosis FAILS. Negative tests demonstrated: stable+missing-Windows rejected; fake PASS rejected; missing enumeration rejected.
  - Windows attempt (real, pinned route `pip install ziglang==0.17.1`): cross-probe of 4 representative TUs fails with exact errors (`dlfcn.h`, `zlib.h`, `execinfo.h`, `sqlite3.h` not found); 15 sources use POSIX-only APIs; 11 C-dependency families have no Windows builds. Recipe + matrix + unblock path: `docs/ci/WINDOWS_TOOLCHAIN.md`; probe script `scripts/release/build_windows_zig.sh`; log `evidence/s229_s213_s214/windows_probe.log`. No wine/Windows host here, so the artifact stays honestly BLOCKED — **R19 remains OPEN**; the gate now makes a mislabelled "stable" release impossible.
  - CI: `docs/ci/windows-build.yml` + `docs/ci/windows-release-gate.yml` (shipped in docs/ci/ under the recorded PAT workflow-scope constraint, same as policy.yml; the manifest gate runs locally today and is part of the preflight battery).
  - v0.0.6.2 Silver reclassified **Linux-only preview** on the GitHub release page (body edited in place; no re-tag, no history rewrite, no stale binary reuse).
- **WP2 — IMPLEMENTED/TESTED.** `docs/PATH_OWNERSHIP.json` (per-area owner/purpose/classes/lifecycle; **500 approved dir prefixes** as the adoption inventory; **9 frozen-area snapshots** by count+path-list SHA-256; run-output routing to ignored `.cache/<tool-or-suite>/<run-id>/`; scratch rules). `tools/policy_validator.py` now enforces: `FROZEN_SNAPSHOT_DRIFT` (any added/removed child in frozen audit/campaigns/reports/research/hc_provenance/probe_store/plugins/evidence/docs-history), `UNREGISTERED_DIRECTORY` (new dirs forbidden by default), `SCRATCH_RESIDUE` (.rej/.bak/.orig universal + stdout/stderr/scratch/api-dump/cache/build-system names), `SYMLINK_ESCAPE` (absolute/out-of-repo targets), `SIZE_BUDGET_EXCEEDED`; registry is authoritative for root/top-level law; identical rules local + CI; violations exit 1 (warnings never pass). Required tests: **13/13 PASS** (`tests/path_ownership_gate_test.py`, log `gate_tests.log`): positives (runtime source/test/fixture/approved image/pinned manifest/baseline/exception) + negatives each asserting the exact code (unregistered dir, frozen-area new file, oversized PNG, oversized JPEG, duplicate screenshot, raw log, machine path, consumer-less scratch, symlink escape, budget breach, .rej). **Clean-clone no-residue proof PASS** (`clean_clone_residue.md`): fresh clone builds `make -C miniandroid -j1`, zero tracked changes, zero untracked residue outside ignored paths, validator 0 violations on the clone. Demonstrated on itself: this wave's evidence dir was **registered in the registry BEFORE creation** (`wave_evidence_registered`), then created — the approval process executed end-to-end. Enforcement also caught on current main: 3 tracked `.rej` patch-residue files deleted; 3 s228 scripts' `/home/z` literals converted to repo-root discovery.
- **WP3 — IMPLEMENTED.** `docs/SIZE_BUDGET.json` per-area tracked-byte budgets (adoption +10% headroom) enforced by the validator; canonical/ stays index+curated-proof; demo GIFs preserved animated with provenance; promotion requirements (APK/run/runtime-commit provenance, hashes, claim, status) recorded in the registry.
- **WP4 — IMPLEMENTED.** Proof package in `evidence/s229_s213_s214/` (inventories, manifests, dispositions, probe + gate + clean-clone logs, closeout). Reviewable commit series: `c710511c` s228 registration → `5d58276a` S213-A/B → `482a4f1f` S214-WP2/3 → `a3f18118` S214-WP1 → `12b3e608` S213-C/D/E/F proof → 2 fixups (`501391cf`).

## Status register (S213/S214 completion proof)

| item | status | evidence |
|---|---|---|
| S213-A JPEG-by-default policy | IMPLEMENTED | `tools/evidence_image_optimizer.py` |
| S213-B tooling + 8-case tests + validator | IMPLEMENTED/TESTED | 9/9 OK; `IMAGE_POLICY_*` codes |
| S213-C cont69 measured comparison | IMPLEMENTED | 17.78x/1.75x + RMS-Δ 0.814 audit |
| S213-D three-path disposition | IMPLEMENTED | s202 NOT_PRESENT; 252 files classified; demo conversion 33.89x |
| S213-E README gallery (4 GIFs) | IMPLEMENTED / RC re-runs PARTIAL | gallery after scope; records 50/51/52/147 |
| S213-F deliverables | IMPLEMENTED | `evidence/s229_s213_s214/` |
| S214-WP1 Windows gate | IMPLEMENTED (gate) / BLOCKED (artifact) | manifest v2 + validator + zig probe log; R19 OPEN |
| S214-WP2 default-deny law + tests | IMPLEMENTED/TESTED | 13/13; clean-clone PASS |
| S214-WP3 structure + budget | IMPLEMENTED | `docs/SIZE_BUDGET.json` + validator |
| S214-WP4 proof | IMPLEMENTED | proof package + commit series |

**Verification commands (all green 2026-11-13):** `python3 tests/test_evidence_image_optimizer.py` · `python3 tests/path_ownership_gate_test.py` · `python3 tools/policy_validator.py` (0 violations) · `python3 scripts/release/validate_release_manifest.py` · `bash scripts/release/build_windows_zig.sh` (exit 1 = measured BLOCKED) · `bash scripts/s229_clean_clone_residue_test.sh` · `python3 tools/check_readme_metrics.py`.

## Honest boundaries

- No Windows binary exists; the release stays Linux-only-preview labelled until a tested PE artifact passes the full battery (wine/Windows-host unavailable here — the gate enforces the label rather than trusting prose).
- No legacy image migration and no legacy deletions: the 90 MIGRATE_TO_JPEG / 22 REJECT_PROMOTION assets and the 17 unreadable files are recorded per-path in the baseline for the #386 migration wave; the conversion was demonstrated on the owner-named example instead.
- The four gallery GIFs are proven at their record time (canonical registry); re-running them on the current RC binary is recorded PARTIAL, not claimed.
"""

def cred():
    out = subprocess.run(["git", "credential", "fill"], input="protocol=https\nhost=github.com\n",
                         capture_output=True, text=True, cwd=str(BASE)).stdout
    user = passw = ""
    for line in out.splitlines():
        if line.startswith("username="):
            user = line.split("=", 1)[1]
        elif line.startswith("password="):
            passw = line.split("=", 1)[1]
    return user, passw


def main():
    user, passw = cred()
    payload = json.dumps({"body": BODY}).encode()
    r = subprocess.run([
        "curl", "-s", "-u", f"{user}:{passw}", "-X", "POST",
        "-H", "Content-Type: application/json",
        "-d", "@-", "-w", "%{http_code}", "-o", "/tmp/s229_comment_result.json",
        "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/587/comments",
    ], input=payload, capture_output=True)
    code = r.stdout.decode()[-3:] if r.stdout else "???"
    result = json.load(open("/tmp/s229_comment_result.json"))
    print("HTTP", code, "| comment id:", result.get("id"), "| url:", result.get("html_url", result.get("message", "?")))
    return 0 if code == "201" else 1


if __name__ == "__main__":
    sys.exit(main())
