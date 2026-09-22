# S82 — PER-TITLE COMPATIBILITY TRACKER

Status: **RECORDS_COMPLETE · EXECUTION_PARTIAL (41/202 executed, evidence-gated)** ·
Date: 2026-09-22 · HEAD at execution: `981e656e`

## 0. What S82 is (§1/§55)

The move from "one umbrella issue" to a real compatibility database: every
APK/app/game = one independent, permanent Compatibility Record + one
independent GitHub issue, following the emulator-tracker pattern (Play!
title status, Cxbx-Reloaded title issues, psOff per-game reports) adapted to
the Android Compatibility Runtime. Issue #24 remains the umbrella/index only.

## 1. Registry freeze (§3/§4)

- `docs/corpus/s82/title_registry.json` — frozen from S81
  `docs/corpus/s81/corpus_index.json` (CORPUS_SEED pinned), 202 records:
  GAME-001..100 · APP-001..100 · MAND-001 (P9) · MAND-002 (TimeLimit).
- Zero duplicate packages in the 200. Stopwatch (16) / platformer (10)
  inventories marked: members cross-referenced, 15 inventory-only packages
  recorded honestly (never dropped, §56).
- TITLE_ID = identity, independent of issue numbers (§4).

## 2. Issue architecture (§2/§5/§9/§21-§25/§45-§47)

- **202 title issues created** (CREATED 202, UPDATED 0, FAILED 0) via
  `scripts/s82_create_title_issues.py`: idempotent (REST identity-index by
  `TITLE_ID` marker + title prefix, immune to search-index sync lag),
  registry backfills `ISSUE_NUMBER`/`ISSUE_URL`, labels synced.
- **Root-cause issues separate from title issues (§18)**: #227 F-NEW-156
  (onCreate APP-BOUNDARY-UNWIND), #228 F-NEW-157 (libGDX EGL frontier),
  #229 VF-NEW-003 (IMAGE_DECODED_VS_RENDERED_GAP) — each with the full
  fanout list = the regression blast radius (§19/§34/§41).
- **Issue template**: `.github/ISSUE_TEMPLATE/title-compatibility.yml` —
  automation-populated for coder-tested titles (§6).
- **46 labels created** (§21): status ladder family, failure family,
  workflow family — statuses and failures kept separate.
- **Query-based verification (§46)**: label counts match registry 1:1
  (compatibility 202, game 100, app 100, mandatory 2, executed 41,
  not-tested 161, state-nonblank 39, state-rendered 1,
  state-graphically-nontrivial 1, fail-oncreate 35, open-source 202).

## 3. Hard gates actually executed (§27/§49/§50/§51 — not just records)

| Gate | Result |
|---|---|
| **A: P9** | EXECUTED (2 runs). APK v0.1.1 vc11 sha256 e69e4083…, screenshot, official F-Droid reference (sha256 9c338cae…), comparison **VISUAL_FAIL**. Root cause found: libGDX `AndroidGraphics.createGLSurfaceView` NPE → registered **F-NEW-157** (#228). Honest status: STATE-NONBLANK (§16 blank face), never "passing on launch". |
| **B: TimeLimit** | EXECUTED (2 runs). v7.7.1 vc231 sha256 93dc5e3c…, reference, comparison PARTIAL. Multiple NPE escapes at `MainActivity.onCreate`. Multi-subsystem app NOT passed — recorded as F-NEW-156 family member. |
| **C: BATCH-01** | 21/25 executed at HEAD; 3 BLOCKED (delisted from F-Droid API: com.droidquest, fr.neamar.androidtimesbugger, com.alaskalinuxuser.hourlyreminder), 1 BLOCKED (persistent download fail: com.dash1971.maia_chess). |
| **D: families** | Stopwatch 3/3 (APP-046/079/089). Platformer 6 ≥ 3 (GAME-034/046/047/048/050/052). 19/20 category families executed; file-manager APK 404s → BLOCKED honest. |
| **E: failure families** | onCreate ×3 reproduced with crash.log traces (solitaire/chessclock/simplestopwatch). IMAGE_GAP ×3 re-run + traced (unote/gmdice/chessclock). DIALOG: GAME-014 solitaire DEX-proven framework `AlertDialog$Builder.setItems` ×3 dialog classes + GAME-021 mykanji (Material chain) retested — dialog path gated upstream by #227 (no fake pass). PLACEHOLDER: unote + muellerma stopwatch re-run — **zero class-descriptor garble** (VF-NEW-002 AFTER-state holds). |

## 4. Execution results (honest counts, §52/§54)

```text
TITLE RECORDS 202 · GITHUB ISSUES 205 (202 title + 3 root-cause)
EXECUTED 41 (25 games, 14 apps, 2 mandatory) · BLOCKED 4 · NOT_TESTED 157
STATE-NONBLANK 39 · STATE-RENDERED 1 (GAME-052 boxcars) ·
STATE-GRAPHICALLY-NONTRIVIAL 1 (GAME-004 balancetheball, comparison lvl 2)
INTERACTIVE 0 · STATE_CHANGED 0 · VISUAL_CORRELATED 0 · HUMAN_VERIFIED 0
VISUAL_FAIL_VS_REFERENCE 31 · PARTIAL_PALETTE 4
ONCREATE_FAILURES 35 · IMAGE_RENDER_GAPS 40/41 executed · REFERENCES 177 OK/25 NA
```

**§54 law respected**: 202 records ≠ 202 tested; 202 issues ≠ 202 verified;
GAME-004's menu render ≠ "game works"; no fix this wave, so no regression
claimed. Every status above L0 carries session + APK SHA + screenshot SHA +
trace excerpt; the §44 validator enforces it (PASS).

## 5. Corpus-wide findings

1. **F-NEW-156 dominates**: 35/41 executed titles die at the onCreate
   APP-BOUNDARY family — one common runtime fix (#227) unblocks 35 title
   issues at once (the bulk-fix workflow §17 was built for this).
2. **F-NEW-157 (new)**: libGDX GL-surface creation is its own frontier —
   P9 + every future libGDX game lands here.
3. **IMAGE_DECODED_VS_RENDERED_GAP is corpus-wide**: 40/41 executed titles
   ship rasters yet paint zero image pixels (#229).
4. **References change the verdict**: 31/35 comparisons are VISUAL_FAIL
   against official F-Droid screenshots even where a screen renders —
   exactly the S81 §19 law at corpus scale.

## 6. Evidence & artifacts

- `docs/evidence/s82/` — 53 JPGs ≤100KB + SHA256SUMS (per-title screenshots,
  gate faces, dialog/placeholder retests).
- `run/s82/` (untracked, §38 retention): per-title sessions, crash logs,
  cached-gates report, label verification, hygiene audit.
- `docs/corpus/s82/`: title_registry.json (canonical), REGISTRY_FREEZE.md,
  COMPATIBILITY_INDEX.md + compatibility_index.json (§32/§33 dashboard),
  root_cause_graph.md + .json (§41 fanout).
- Scripts: s82_freeze_registry.py, s82_lib.py, s82_execute.py,
  s82_cached_gates.py, s82_dialog_gate.py/2.py, s82_references.py,
  s82_refs_bulk.py, s82_enrich.py, s82_issue_body.py,
  s82_create_title_issues.py, s82_labels.py, s82_dashboard.py,
  s82_validator.py, s82_register_f157.py.

## 7. Hygiene (§38/§39/§40/§44/§53)

- Validator PASS (202/202 linked issues; no status without evidence; no
  auto-L5; BLOCKED never state-inflated).
- Disk 7.2G avail; APK cache deduped by SHA (23 duplicates removed);
  zero new APKs inside the repo.
- Hidden-state audit: stash 0, worktrees pruned (1 stale removed),
  20 unreachable objects recorded (no evidence references them; not
  force-deleted), backup dirs none.
- False-completion scan: only pre-existing documentation flags; zero S82
  false completions.

## 8. Queued next (S83)

1. Attack F-NEW-156 via the per-face disasm queue → one law → 35-title
   regression wave (title-level, §34).
2. F-NEW-157 GL surface law (unblocks P9 + libGDX corpus slice).
3. BATCH-02..04 execution (155 not-tested titles keep their honest records).
4. L4/L5 reference comparisons need non-blank renders first; L5 additionally
   requires the human-review record (§31).
