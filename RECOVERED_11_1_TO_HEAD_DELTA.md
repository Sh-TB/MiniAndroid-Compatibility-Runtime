# RECOVERED_11_1_TO_HEAD_DELTA — git-verified historical reconciliation

Campaign: UNIFIED_011.3 (this document = §3 deliverable of the master directive)
Baseline: tag `v0.11.1-unified-011-1` (commit `340a9cf`) — the UNIFIED_011.1 canonical state.
Method: **git only**. Every row below was produced from `git log/show` on the actual
repository at `/home/z/my-project/miniandroid_ws` (branch `main`). No campaign names,
no RESULT numbers, no report claims were trusted as evidence.

## 0. Answer to the mandatory question (§3)

> **What did MiniAndroid lack at 11.1, and what was actually added afterward?**

Verified ABSENT at `340a9cf` (0. occurrences in the entire 011.1 tree, `git show` grep):

| Missing at 011.1 | Symbol proof (0 hits at 340a9cf) |
|---|---|
| Runtime exception machinery (no synthetic raise, no catch lookup shared by runtime errors; aget-OOB warn-and-continue livelocked dooz for 78 s) | `find_catch_handler_for_pc` = 0, `raise_synthetic_exception` = 0 |
| Typed-catch type matching (typed handlers decoded then discarded `(void)type_idx`) | `is_exception_subtype` = 0 (added 011.3) |
| Real image resource→pixel chain (`resource_drawable_paths_` had readers but no writer since EXP-067; `src_drawable_path` written by LayoutInflater, never read by renderer) | `populate_resource_drawable_paths` = 0 |
| Touch/interaction probe (android:onClick captured, never dispatched; no click-test harness) | `stage_click_test` = 0 |
| filled-new-array semantic fixture (0x24 arg-count/G-register semantics untested — and broken) | `tests/unified0112_filled_new_array_test.cpp` absent at 340a9cf |

What was ACTUALLY added afterward = the six UNIFIED_011.2 commits plus this campaign's
commits, table below.

## 1. Per-commit delta table (§3 required format)

| Commit | Version | Files | Real change | Tests | Real-app effect | Artifact | Status |
|---|---|---|---|---|---|---|---|
| `2f05134` | 011.2 | dalvik_engine.{cpp,h} (+204/−26), tests/unified0112_filled_new_array_test.cpp (new, 180 ln) | filled-new-array 35c operand fix (A=(instr>>12), G=(instr>>8), C..F from cu2 — was constant `(instr>>4)&0xF` = 2) + SYNTH-EXC runtime exception machinery (heap exception object, catch lookup verbatim-extracted from THROW, frame unwind on uncaught) | `fna_test` 5/5 PASS; old code reproduced 4/5 FAIL | dooz aget-OOB livelock 78.0 s → 0.8 s; execution progresses past Compose setContentView; Telegram varargs (Object…) correctness underpins 3/3 `088ea640…` | fna_test binary, fixture source | INTEGRATED |
| `73e1946` | 011.2 | dalvik_engine.{cpp,h} (+79), execution_engine.cpp (+104/−5), u011_test_matrix.py (+4), experiments/exp_graphics_image_e2e/ (new: README + 4 PNGs) | IMAGE-RES-RENDER: populate_resource_drawable_paths() (density-ranked xxxhdpi→mipmap basename map) + render dispatch (image_drawable_path → resid chain → src_drawable_path fallback; PNG/JPEG/WebP magic select) | exp_graphics_image_e2e before/after frames (ssw buttons 1,278 B blank → 9,821 B real icons) | simplestopwatch ImageButtons: blank → REAL lock/settings/menu icons; ssw anchor moved WITH REASON `d495e3cb`→`2a12587a` (determinism 3/3) | E2E experiment dir + evidence | INTEGRATED |
| `8e1d633` | 011.2 | main.cpp (+6), application_runtime.h (+9/−1), execution_engine.{cpp,h} (+205/−1) | CLICK-TEST: `--click-test` probe (frame-1 save → real dispatch → re-render → pixel diff → click_frame_N.png + JSON report) + XML `android:onClick` dispatch (captured since 011-era, never consumed) | gmdice roll click report, ssw 4 XML handlers report | gmdice + ssw became interactive targets (see 011.3 correction of the pixel numbers) | click_test_report.json ×2 | INTEGRATED |
| `ae58a4d` | 011.2 | 3 campaign MDs (new), status_011_1.json (TBD placeholder → tag ref), recovery/ (3 files, new) | §5/§6 deliverables + M1 (TBD_FINAL_COMMIT placeholder) + M2 (START_HERE/recovery untracked) closure | n/a (docs/audit) | removes handoff-package inconsistencies found by audit | RECOVERED_CAMPAIGN_STATUS.md et al. | INTEGRATED |
| `43e024f` | 011.2 | START_HERE.md (new, 28 ln) | track package entry point (M2 completion) | n/a | n/a | START_HERE.md | INTEGRATED |
| `6c9a91e` | 011.2 (tag `v0.11.2-unified-011-2`, applied retroactively this campaign for monotonic versioning) | docs/evidence/u011_2/ (10 files) | curated ≤100KB evidence: click frames, matrix goldens, WhatsApp/Signal probes | evidence hashes recorded | evidence for §32 matrix rows | docs/evidence/u011_2/ | INTEGRATED |
| *(011.3, this campaign)* | 011.3 | dalvik_engine.{cpp,h}, android_shadows.h, execution_engine.cpp, tests/unified0113_typed_catch_test.cpp (new), scripts/u0113_oracle_diff.py (new) | TYPED-CATCH: is_exception_subtype (DEX chain + built-in java.* hierarchy) + typed handler matching in find_catch_handler_for_pc and THROW; caller-side try-table search at invoke sites (EXC-PROPAGATE) with post-switch pc redirect; documented uncaught-tail compatibility continue. dex_report_ + class_info_index_ now built on execute_method entry (unit path parity). FRAME-2: click-test re-render switched to stage_render_frame (identical pipeline as frame 1); activity heap id recorded and passed as handler `this`; ActivityShadow::set_activity_heap_id added | `typed_catch_test` **8/8 PASS** (old code: cases 1,2,5,7 FAIL — typed handlers never matched; case 6/8 assert the new unwind/continue contract); `fna_test` 5/5 still PASS | **frame-2 correctness**: ssw Start→"Stop"/"Lap" real second frame (12,439 px, oracle-verified, Stop/Lap = real running-state semantics); prior "181,512 px" gmdice / "918,207 px" ssw numbers RECLASSIFIED as redraw artifacts (weak ad-hoc render path), true deltas now measured; Telegram golden `088ea640…` preserved (3/3 in final matrix); IAE artifact-propagation regression found by telegram A/B and fixed by policy (uncaught tail) | typed_catch_test binary, oracle JSON+PNG evidence | INTEGRATED (this docs commit) |

## 2. Historical claim audit (§4) — verified contradictions

| Claim | Git/forensic verdict |
|---|---|
| `4a39f1b` commit with "176-176" result | **REJECTED** — `git cat-file -t 4a39f1b` → "Not a valid object name"; 0 of 75 commits on any ref match; string absent from repo + recovery archives. Preserved as historical evidence of a claim without a handoff. Never fabricated. |
| EXP071_OPCODE_AUDIT "filled-new-array ✓ verified" | **REJECTED** (was presence-only; semantics provably broken until 2f05134 — old-code fixture reproduced 4/5 FAIL) |
| "dooz blank is pre-existing, engine cannot progress" | **CORRECTED** in 011.2 (livelock was an engine aget-OOB warn-and-continue, fixed by SYNTH-EXC) |
| "011.5 / 012 / NEXT campaigns" | **DO NOT EXIST** — no commits, no tags, no artifacts anywhere in history (verified again this campaign via `git log --all`) |
| UNIFIED_011.2 "gmdice 181,512 px / ssw 918,207 px state change" | **RECLASSIFIED this campaign**: the click DID dispatch and app code DID run, but the pixel counts came from an ad-hoc re-render path that bypassed the real renderer (near-blank second frame — see §23 evidence). True deltas after the pipeline fix: gmdice roll = 0 px (app's roll-flow views are runtime-constructed, not yet shadow-connected), ssw Start/Reset = 12,439 px real. |
| "121/122 semantic fixture suite (smali 2.5.2 + OpenJDK 21 oracle)" | **NOT IN REPOSITORY** — absent from tree, history, and all 12 recovery archives: work existed without a handoff (the exact §0 failure mode). Partially REVIVED this campaign as in-repo C++ semantic fixtures (`unified0112_filled_new_array_test` 5/5, `unified0113_typed_catch_test` 8/8) including the typed-exception case class that the historical 121/122 reportedly failed. |

## 3. Version chain

```text
v0.11-unified-011        388fb45
v0.11.1-unified-011-1    340a9cf   ← BASE for this delta
v0.11.2-unified-011-2    6c9a91e   (tag applied retroactively, monotonic bookkeeping)
v0.11.3-unified-011-3    <this campaign's final commit>
```
