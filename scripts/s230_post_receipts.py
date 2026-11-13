#!/usr/bin/env python3
"""S230: post the wave receipts on #586, #585, #587 and push."""
import json
import os
import subprocess

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"


def token():
    cred = subprocess.run(["git", "credential", "fill"],
                          input="protocol=https\nhost=github.com\n\n",
                          capture_output=True, text=True,
                          cwd=subprocess.run(["git","rev-parse","--show-toplevel"],capture_output=True,text=True,cwd=os.path.dirname(os.path.abspath(__file__))).stdout.strip() or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))).stdout
    return [l.split("=", 1)[1] for l in cred.splitlines()
            if l.startswith("password=")][0]


def post(num, body):
    import urllib.request
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/issues/{num}/comments",
        data=json.dumps({"body": body}).encode(),
        headers={"Authorization": f"token {token()}",
                 "Accept": "application/vnd.github+json",
                 "User-Agent": "s230-receipt"},
        method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        out = json.loads(r.read().decode())
        print(f"posted #{num} comment id={out['id']}")


RECEIPT_586 = """# S230 receipt — the S226 TRANSFER patch LANDED on main (the forgotten patch per K-2), with an honest patch-integrity finding

**Reviewed HEAD:** `2246eaf9` (S230 wave). The S226 TRANSFER (issue body + comments 6830325674/6830326621/6830327432) was **never applied** — only the separate Vector Pinball fix had landed as `1a0fa259`. This wave landed the transfer.

## 1. IMPLEMENTED — the transfer on main

- 13/16 patch segments applied **verbatim** via `git apply` on the declared base `a4516511` (clean `--check` per-segment), then cherry-picked onto main with ZERO conflicts: `canonical/app_registry.json` APP-016..019 rows (Thunderbird/Tusky/Nextcloud/ConnectBot BLOCKED-at-frontier states), `canonical/root_cause_registry.json` S156 findings, `evidence/s156_4app/{BASELINE_WALL, BOOT_thunderbird, BOOT_tusky, BOOT_nextcloud, BOOT_connectbot, PIN_LEDGER, PROFILE, RERUN_AFTER_ANCHORS}.json`, `S156_T4_THUNDERBIRD.md`, `S156_T5_TUSKY.md`, `scripts/s156_tb_koin_xref.py`.
- Compliance: `evidence/s156_4app/` registered in `docs/PATH_OWNERSHIP.json` (`wave_evidence_registered_s226`), frozen `evidence/` snapshot re-baselined with a registered amendment, the two transferred historical scripts allowlisted per-entry (they are one-off campaign tools, not runtime deps), policy validator **0 violations**.

## 2. OBSERVED — patch integrity (must-know for future transfers)

- The posted parts do NOT reproduce the header's metadata: combined posted diff sha256 = `aaec3059a2bad821…` (header claims `09768a2375a08cff…`), shape **16 files / +1,397** (header claims 27 files / +2,763).
- `git apply --check` on the declared base failed on the concatenated parts: **3 hunks are truncated** (S156_T7_CONNECTBOT.md declares 67 new lines, 53 posted; `s226_post_issue.py` declares 189, 157 posted) — comment-body truncation. The 3 truncated files were reconstructed **from the posted + lines only**, with an explicit `S230 RECOVERY NOTE` marker recording declared-vs-posted counts inside the file — no tail was invented.
- Suggestion for the transfer protocol (K-2 follow-up): post large patches with per-file sha256 rows (as done elsewhere) so truncation is detectable at receipt time.

## 3. TESTED / NOT CLAIMED

- The transfer adds registry rows + wave evidence + one-off scripts only — **no engine source changes**, so the 6-pin byte-exact HOLD state is structurally unchanged (binary `06f98d2a9c21ea92`; the S230 rebuild reproduced it byte-identically, see #587 S230 closeout).
- The S156 wall states (Thunderbird/Tusky/Nextcloud/ConnectBot) are recorded exactly as transferred: BLOCKED at their measured frontiers — no new APK-execution claims are made by this receipt.
"""

RECEIPT_585 = """# S230 status receipt — EXECUTION MANDATE §-map on current main + what remains honestly OPEN

**Reviewed HEAD:** `2246eaf9` (S230 wave). This maps the §0–§9 mandate (comment 6818394994) onto the landed state; nothing is re-labelled without evidence.

## Section map

- **§0 provenance gate — DONE** (S225-M receipt, comment 6821914883): repo/branch/HEAD/dirty-diff provenance recorded, the uncommitted 434+/-158 diff recovered and landed.
- **§1 test foundation — DELIVERED in the engine's own harness**: `make test-all` **28/28** at the release commit (recorded in the S212 closeout) + the new 22-row law battery (`tests/s225m_wave_law_test.cpp`) added by the S225-M receipt; the archive's CTest wiring finding remains applicable to the upstream source-archive route and is tracked in `docs/compatibility/legacy_100_audit.*` rather than re-audited here.
- **§2 diagnostics races — DONE** (S225-M §2, synchronized runtime_event ingestion).
- **§3 JNI ownership/semantics — DONE** (S225-M §3 registration-precedence + marshal honesty).
- **§4 native loading boundaries — DONE** (S225-M §4 DT_STRTAB VA law).
- **§6 pthread/Looper/lifecycle — DONE** (S225-M §6 locked-section law + POSIX error semantics).
- **§5 view/resource contract tests — PENDING** (not executed by any wave since the mandate; honest OPEN).
- **§7 real-app cohort 10–20 — PARTIAL**: the standing cohort evidence grew this wave (S230): the four README gallery apps re-verified ON the release-candidate binary `06f98d2a9c21ea92` with per-frame board-evolution proof (`evidence/s230/gallery_rc_rerun.json` — g2048/minicraft full real-interaction passes; tetris/snake-deluxe real gameplay rendered, tick chains live), alongside the 5 byte-exact pinned demos. The formal 3-cold-baseline/3-post-fix cohort protocol for 10–20 titles remains OPEN.
- **§8/§9 deliverables — PARTIAL**: this receipt + the #587 S230 closeout carry the current evidence; the §8 discipline is enforced by the S213/S214 law battery (validator 0 violations, 17/17 retention tests).

No section is marked complete that lacks a landed artifact. §5 and the §7 cohort are the next shared-runtime levers.
"""

RECEIPT_587 = """# S230 closeout — the remaining forgotten items of this issue executed (evidence-heavy; nothing re-labelled without an artifact)

**Audited state:** the S212 closeout delivered WP0–WP11/R01–R35 and the S229 closeout delivered S213+S214; the owner's instruction was that items were still forgotten. Re-pull of the full issue + all comments against the actual tree found four concrete gaps. All four are now executed. Base `501391cf` → HEAD `2246eaf9` (pushed, reviewable commits).

## A. The four gallery demos' RC re-runs (S229 honest PARTIAL → EXECUTED)

- The release binary was **rebuilt from a clean tree: `sha16 06f98d2a9c21ea92` — byte-identical to the release RC** (a reproducible-build proof in itself).
- Record: `evidence/s230/gallery_rc_rerun.json`. Per app:
  - **g2048 — PASS**: 38 closed-loop cycles of REAL merges (score 224, board_max 32, vision-verified against the driver's simulated overlay), compact probe REAL_APP_CONTENT, deterministic ×2.
  - **minicraft — PASS**: terrain + cursor walk + brick placements (state change 20,108 px), REAL_APP_CONTENT, deterministic ×2, 0 uncaught.
  - **tetris — REAL GAMEPLAY RUNNING**: START tap dispatches (`F117-TAP … target=89` → `UI-EVENT CLICK DISPATCHED listener=MainActivity$5`), `toggleStart` executes (board allocated, seed, spawn), the `TetrisView$1` ticker chain is LIVE (dequeued at ready_at=420 ms, gravity steps, re-enqueued), and the board **evolves every ~2 frames** (per-frame board-SHA series in the record). The closed-loop driver's cycle-4 sim divergence is recorded honestly as a driver-sim timing frontier, not claimed as an engine regression.
  - **snake-deluxe — REAL GAMEPLAY RUNNING**: menu→board transition (2,073,600 px), snake advances per tick (board SHA changes EVERY frame, frames 6–15); the naive fixed schedule then kills the snake (expected; the closed-loop driver owns turns).
- README gallery note updated; metrics check OK. The canonical GIFs remain the display assets with registry provenance (records 50/51/52/147).

## B. Forensic-addendum §5 required tests + §7 runner defaults (the missing enforcement)

- `tests/evidence_retention_test.py` — **17/17 PASS**: canonical golden pixel-exactness under lossless optimization, JPEG derivatives are noncanonical/lossy-marked, duplicate SHA detection, per-run IDs+SHAs survive compaction (incl. the live retention manifest), and a deliberately contradictory `NO_APP_OPS + REAL_APP_CONTENT + SUCCESS` report is **rejected** with the exact codes.
- `tools/report_sanity.py` — the W14/W18 defect classes as a mechanical gate: STALE_SCREENSHOT_SIZE, DUPLICATE_SCREENSHOT_EMBED, MISSING_RUN_ID, APK_PATH_MISMATCH (the r4→r1 store bug shape), MISSING_SCREENSHOT_SHA, CONTRADICTORY_VERDICT, PIXEL_PROVENANCE_MISMATCH. The corrected W18 halma reports PASS clean.
- `tools/duplicate_scan.py` — byte-identical duplicate detection with an exemption registry.
- §7 runner defaults: `scripts/autoplay/common.py` gains `compact_preview` (≤640 px JPEG, DERIVATIVE / NOT PIXEL-EXACT manifest) + `retain_full_screenshot` opt-in + an inline report-sanity gate; `run_all.py` writes the batch-level `runs.jsonl` (per-run metrics + SHAs, no per-run PNG) and fails on report-sanity violations.

## C. W18 p9_* reports corrected (same wave the addendum named; halma was already corrected at S212)

- 18 p9_* reports carried the exact defect class the addendum banned (the same screenshot embedded twice / "Output Frame" ×2, 7.91 MB stale size claims, missing run IDs, SUCCESS headlines over APIs=0/0 ms runs). All corrected with honest statuses; the removed screenshots point at their S214 noise-retro-clean manifest rows (recoverable by hash). Ledger: `evidence/s230/report_corrections_ledger.tsv`.
- The rest of the historical tree was **censused, not mass-edited** (frozen-area law): 964 historical reports with 2,216 violations → `evidence/s230/report_sanity_census.tsv` as the #386 migration queue.

## D. The legacy image migration wave (S213's "incremental migration" trigger, executed with measured gates)

- Ledger: `evidence/s230/legacy_migration_ledger.tsv`. Of the 90 MIGRATE_TO_JPEG candidates: **15 MIGRATED** (zero-real-consumer winners, 248 KB checkout bytes saved, source→output SHA + RMS rows), **27 KEPT_PNG_MEASURED** (the JPEG came out LARGER — the measured outcome supersedes the blanket verdict, recorded per file), **45 DEFERRED** (real consumers or frozen consumers — the #386 queue now carries per-file byte measurements), 2 optimizer-policy refusals (miniandroid runtime resources), 1 upstream untouched.
- 17 unreadable 0–33 B campaign014 residue files **DELETED** per the S229 DELETE_CANDIDATE disposition (docs/evidence/, no real consumers).
- `docs/IMAGE_POLICY_BASELINE.json` updated by its own expiry rule (72→55 entries; expired removed, KEPT_PNG entries carry the measured reason); frozen-snapshot amendment registered; policy validator **0 violations**.

## E. Also landed this wave (cross-issue, posted as receipts there)

- The **S226 TRANSFER** (#586) — the never-applied 27-file patch — landed on main (13/16 verbatim + 3 reconstructed with truncation markers; APP-016..019 registered). Receipt on #586.
- #585 mandate §-map receipt posted (§0/§2/§3/§4/§6 DONE, §1 delivered via make test-all + law battery, §5 and the §7 cohort honestly OPEN/PARTIAL).

## Gate state at HEAD

`make test-all` 28/28 (S212 release baseline; no engine source changed in S230), policy validator **0 violations**, retention tests 17/17, optimizer tests OK, README metrics OK, 6-pin byte-exact HOLD structurally unchanged (no engine source touched). R12/R32 CI-trigger activation still requires a workflow-scope token (owner action, unchanged). R19 Windows stays BLOCKED (measured; unchanged).
"""

post(586, RECEIPT_586)
post(585, RECEIPT_585)
post(587, RECEIPT_587)
