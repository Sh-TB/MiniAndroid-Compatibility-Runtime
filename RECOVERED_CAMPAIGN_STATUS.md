# RECOVERED_CAMPAIGN_STATUS — evidence-based historical reconciliation

Campaign: UNIFIED_011.2 (this document = §5 deliverable)
Baseline: tag `v0.11.1-unified-011-1` (340a9cf) + commits 2f05134, 73e1946, 8e1d633
Method: git history + recovery/ forensics + docs/ + fresh execution on HEAD.
**Not a recommendation document.** Every row was verified against artifacts.

## 1. Campaign timeline (reconstructed)

| Campaign | Tag/Commit | Requested/Reported | Actually committed | Actually tested | Integrated | Evidence status |
|----------|-----------|--------------------|--------------------|-----------------|------------|-----------------|
| UNIFIED_000–010 | archived ZIPs (12, SHA-recorded in recovery/FORENSICS_SUMMARY.json) | per-campaign reports | imported via 3b862e5 (152 files, +38,349 lines) | matrix byte-identical to verified 010 snapshot (`status_011_1.json .regression`) | default build + preserved-not-wired split (§4 of CROSS_CAMPAIGN_RECOVERY_011_1) | OK — SHA mismatches in forensics noted below |
| UNIFIED_011 | v0.11-unified-011 (388fb45) | 60 commits, docs set, START_HERE | 388fb45 + 937f043 + c061770 + f45505d | clean-clone verification claimed in docs | YES | OK |
| UNIFIED_011.1 | v0.11.1-unified-011-1 (340a9cf) | recovery import §1–20, reconciliation §12–14, matrix anchor | 3b862e5, 78bad82, 340a9cf | PNG fixtures 12/12 on clean clone; telegram 3/3 `088ea640…` | YES | OK — **but**: `status_011_1.json.local_head_after_docs` shipped as `TBD_FINAL_COMMIT` (fixed in this campaign); START_HERE.md + recovery/ shipped UNTRACKED (not committed) — handoff-package inconsistency, fixed by commit in this campaign |
| UNIFIED_011.2 (this) | 2f05134, 73e1946, 8e1d633 | §1–36 execution directive | 3 code commits (see MASTER_CURRENT_GAP_MATRIX) | full matrix + FNA fixtures + E2E + click tests | YES | fresh evidence in experiments/ + run/ |
| 011.5 / 012 / NEXT | **do not exist** | referenced only in the directive text | nothing in repo/history | n/a | n/a | no artifacts found — documented as non-existent |
| "later graphics/image discoveries" | EXP-096/097/098 lineage | image codecs, RLottie | present at HEAD (linked libwebp/libjpeg/rlottie) | EXP-097/098 docs + code at HEAD | YES (default build) | OK |

## 2. §6 missing-delivery audit (every found case)

| # | Case | Category (A–E) | Disposition |
|---|------|----------------|-------------|
| M1 | `status_011_1.json.local_head_after_docs = "TBD_FINAL_COMMIT"` (placeholder never filled) | C (only documented) | **FIXED** this campaign — replaced with tag reference, committed |
| M2 | Root `START_HERE.md` + `recovery/` untracked in the canonical repo | D (missing) | **FIXED** — committed in UNIFIED_011.2 housekeeping |
| M3 | filled-new-array 35c operand bug (claimed by prior agent; EXP-071 audit marked 0x24 "✓ verified" — presence-only, not semantics) | E (contradicted by source: `(pc>>4)&0xF` still at HEAD) | **FIXED** 2f05134 + semantic fixture (old code 4/5 FAIL proof) |
| M4 | `resource_drawable_paths_` read in 2 places, populated nowhere (EXP-067 declared the map, delivery incomplete) | D | **FIXED** 73e1946 (populate_resource_drawable_paths) |
| M5 | `src_drawable_path` written by LayoutInflater, never read by renderer (§14 mismatch) | D | **FIXED** 73e1946 (render fallback) |
| M6 | `android:onClick` captured in `onClick_handler`, never dispatched | D | **FIXED** 8e1d633 (stage_click_test XML dispatch) |
| M7 | Registry download URLs stale: `telegram.org/dl/android` now redirects to Play Store (both Telegram entries); tinymusicplayer + openlauncher SHA mismatches vs F-Droid current | C | Documented; Telegram obtained via `telegram.org/dl/android/apk` (SHA-verified f5e11927… = registry v12) |
| M8 | u011_test_matrix expects `corpus/dooz.apk`, `corpus/tictactoe.apk`, `corpus/stopwatch.apk` but downloader writes `dooztictactoegvariant.apk` etc. — two official scripts disagree | D | Worked around via verified symlinks in cache; scripts left unmodified (behavior-preserving) — flagged for owner |
| M9 | 3 "superseded tag iterations" + dangling stash objects | A (integrated via anchored docs) | no action (documented in status_011_1.json .recoveries) |

## 3. Prior fixes verified at HEAD (sample, evidence-based)

| Prior claim | Verification at HEAD | Result |
|-------------|---------------------|--------|
| Telegram v12 deterministic render | re-run 3×: SHA `088ea640587ec0d2…` identical | CONFIRMED |
| libpng decoder 12/12 | PNGDecoder in default build; ssw icons decode on real APK | CONFIRMED |
| EXP-052 exception machinery (throw/catch) | THROW handler + tries decode present; now shared via find_catch_handler_for_pc | CONFIRMED |
| gmdice 158,040 px | reproduced exactly | CONFIRMED |
| EXP-098 RLottie on SMS screen | wiring code present at HEAD (EXP098-RLOTTIE path) | CONFIRMED (not re-run — telegram screen unchanged 3/3) |
| "stopwatch exit 1 = pre-existing truncated APK" | reproduced exit=1 | CONFIRMED |
| "dooz blank pre-existing" | RECLASSIFIED this campaign: blank due to aget OOB warn-and-continue livelock (78 s) — engine progressed post-2f05134 | CORRECTED |
| EXP071_OPCODE_AUDIT "filled-new-array ✓ verified" | FALSE at semantic level (see M3) | REJECTED |

## 4. Artifacts delivered by this campaign

- Commits: 2f05134 (FNA + SYNTH-EXC), 73e1946 (IMAGE-RES-RENDER), 8e1d633 (CLICK-TEST + XML onClick), plus docs/housekeeping.
- `miniandroid/tests/unified0112_filled_new_array_test.cpp` — 5/5 PASS semantic fixture with old-code discrimination proof.
- `miniandroid/experiments/exp_graphics_image_e2e/` — §13/§15 E2E with before/after frames.
- `scripts/u011_test_matrix.py` — simplestopwatch anchor moved WITH REASON (§28 policy).
- MASTER_CURRENT_GAP_MATRIX.md, CAMPAIGN_REAL_GRAPHICS_COMPATIBILITY_FINAL.md, this file.
- Final handoff ZIP + SHA256 (see CAMPAIGN_REAL_GRAPHICS_COMPATIBILITY_FINAL.md).
