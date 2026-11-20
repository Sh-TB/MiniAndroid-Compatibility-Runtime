# MASTER CROSS-CODER ACHIEVEMENT AUDIT — complete item-by-item verification

Source mission: the pasted MASTER TASK (1040 lines, §0-§12). Execution date: **2026-11-20**. Auditor: independent (repo owner account), working from HEAD `d8b8fbb9` before audit edits, audit commit `9b953ce1`.

**Method (per mission §0):** every mandatory section read line by line; every claim tested where the environment allowed; no coder status accepted as proof; one disposition per claim; unavailable verification marked BLOCKED with the exact missing dependency — never turned into a PASS.

**Baseline manifest:** repo `Sh-TB/MiniAndroid-Compatibility-Runtime`, branch `main`, HEAD `d8b8fbb9`, tree clean at start. Toolchain g++ 14.2.0 + GNU Make; **cmake ABSENT** (CMake graph measurements BLOCKED, not skipped). Host 2 vCPU / 4 GB, hypervisor steal measured 24-25 % of every build window today. Tracker: 300 issues+PRs fetched via API — every mission-referenced issue exists (#586-#634, incl. #625/#626 as PRs). No destructive cleanup performed.

---

## §1 — Mission checklist (registered in full, nothing omitted)

### A. Issue #632 registry (194 items, 11 comments)
- [x] Fetched full body + all 11 comments via API (43 KB body + 132 KB comments)
- [x] Section structure mapped (§A hygiene → §R testing/CI)
- [x] Architectural corrections rechecked: layout path = `layout_inflater.cpp` ✔ (file + gravity handling verified); FriBidi/HarfBuzz/FreeType text pipeline ✔ (text_shaper.h + FONTS_LIBS); GridLayout absent ✔ CONFIRMED-live; nine-patch npTc absent ✔ CONFIRMED-live; ScrollView wiring PARTIAL (aged claim — wiring now exists, offset laws open); 174-attribute claim → item-level PENDING
- [x] B1/B2: CMake battery loop without EXCLUDE_FROM_ALL ✔ CONFIRMED (CMakeLists:493); QuickJS compiled twice (two OBJECT libs :298+:459) ✔ CONFIRMED-source (Make compiles once ✔); `all: $(EXECUTABLE) anchors` ✔; TEST_CORE/HOSTILE/LAW counts ✔; NEW-9 guard at :433 ✔ CONFIRMED (retraction justified); 52-links+OOM BLOCKED (no cmake; OOM NOT observed on Make path — peak RSS 1221 MB / 4 GB across ~40 full builds)
- [x] B1 historical figures (94k lines = 94,305 ✔ CONFIRMED; 5,436-line function → SUPERSEDED by W4 split default; PCH 36.4 s ✔ preserved rejection ×3; inline-params placebo ✔ preserved BUG-5)
- [x] B3 ccache ✔ CONFIRMED (cold 553.42 s / 0 hits; warm 20.94 s / 88-88; warm rebuild 25.40 s — committed logs)
- [x] B4 mold/lld ✘ REJECTED (link 1.5 s of 350 s)
- [x] B5 -gsplit-dwarf ✘ REJECTED-MEASURED TODAY (+4 % slower on heaviest TU, ABBA probe)
- [x] B6 ggc-min tuning ✘ REJECTED-MEASURED TODAY (3× slower — GC thrash)
- [x] B7 -fno-var-tracking-assignments ✘ REJECTED-MEASURED TODAY (no win; GCC14 fixed VTA; -g1 already covers)
- [x] B8 .DELETE_ON_ERROR ✔ CONFIRMED-missing → **FIXED: added to Makefile this audit**, behavior demo on failed target + full link rc0
- [x] B9 job pools ✔ CONFIRMED non-issue at -j2 (zero OOM in ~40 full builds)

### B. RC-12 ScaleType pixel-exact verification
- [x] Verifier + probe searched: `verifier/scaletype_oracle.py` ABSENT, `apps/probe_scaletype` ABSENT, commits `46ca6258/73dcadb6/1439627a/d77edba6` ABSENT (git cat-file ×4) → **BLOCKED / NOT-INTEGRATED** — the 0/579,784-pixel + 8/8-mutation results are NOT reproducible in mainline and are not counted as runtime capabilities
- [ ] Negative-mutation re-run → BLOCKED on obtaining the 4 commits

### C. #633 vector PathData / #634 animated drawable
- [x] MG-011 fix `out->ok = err.empty() && !paths.empty();` searched in src/ → **ABSENT → CONFIRMED-NOT-INTEGRATED** (top recovery candidate)
- [x] MG-010 clip-path: handling exists in vector_inflater.cpp + s132_svg_reader.cpp → PARTIALLY CONFIRMED (completeness tests open)
- [ ] #634 full source audit → PENDING (tracker state fetched: open, 5 comments)

### D. #630/#631 layout test apps
- [x] `apps/` directory EMPTY in mainline → **CONFIRMED-NOT-INTEGRATED** (diagnostic/local-only work); canonical tracking recommendation + links preserved in ledger

### E. #629 R8 dispatch knowledge → tracker-confirmed open; knowledge-vs-implementation separation recorded in ledger (PENDING deeper pass)
### F. #628 CoroutineScheduler --frames 12
- [x] Exact APK (emmanuelmess TicTacToe) ABSENT → BLOCKED; substitute run (itsfrz ttt_5, today) rc=1 with 0 setGraph occurrences — claim NOT confirmable on a different app (recorded honestly)
### G. #627 Dalvik/build audit
- [x] move/from16, move-wide/from16, const-string/jumbo → focused tests EXIST (tests/w15_dalvik_lit_from16_law_test.cpp) + battery rc0 today ✔; lit8/lit16 → semantic tests ✔; UBSan E-05 → PENDING (no sanitizer profile in Makefile); Make/CMake opt differences ✔ (WEBP gap CONFIRMED)
### H. #625 (merged PR, dev-so) ✔ CONFIRMED (PR closed per tracker + dev-so target in Makefile:771 + gate exercises dev path today) · #626 (open PR) ✔ CONFIRMED-open, numbers partially superseded by today's candidate dev-so measurement (268.98 s)
### I. #612 build perf + six-pin regression → targets honestly MEASURED-MISS (<280 s by 10 s; <250 s) with floor arithmetic; six-app gate: 5-APK gate 11/11 IDENTICAL today on candidate codegen; bouncy piece BLOCKED (APK absent); bisect commits unverifiable here (BLOCKED)
### J. #618 Counter (CLOSED per tracker ✔; re-verify BLOCKED-at-APK) · #619 TicTacToe (CLOSED ✔; render parity RE-PROVEN today: ttt screenshot hash d55056a8928a26ff identical in the 11/11 gate)
### K. #597 OpenCalc → BLOCKED-at-APK (7×3=21 untestable here; tracker open, 8 comments)
### L. #586 four apps → FORTIFY claim **CONFIRMED** (nm: exactly 3 defined `__*_chk` in the binary); route/coroutine states BLOCKED-at-APK
### M. #614/#610/#621/#622/#624/#623 → tracker states fetched (#623 CLOSED ✔ justified-closure recorded; others open); APK-level re-verification BLOCKED (corpus absent); no source-built substitutes used anywhere
### N. #295/#296/#297 vector stroke/trimPath → beyond fetched page range (pages 1-3 = #335-#634); flagged PENDING fetch in next batch (not silently omitted)

---

## §2 — Final ledger (50 rows, full detail in `evidence/audit/ACHIEVEMENT_LEDGER.csv` at commit 9b953ce1)

| Verdict | Count | Examples with the deciding reason |
|---|---:|---|
| CONFIRMED | 30 | W24 tiering −17.3 % wall/−17.7 % CPU (ABBA ×4, byte-identical reps, battery 49/49 + gate 11/11 today); ccache warm 20.94 s; monolith 94,305 lines; NEW-9 guard :433; FORTIFY 3; opcode law tests + battery rc0; Make QuickJS-1× |
| REJECTED | 4 (+2 re-cited) | B4 mold/lld (link 1.5 s of 350 s); B5 split-dwarf (+4 % ABBA); B6 ggc-min (3× slower); B7 var-tracking (no win) — plus Ninja & PCH rejections re-cited |
| PARTIALLY CONFIRMED | 5 | §D gravity depth; §I ScrollView offsets; §L reference chain; MG-010; #606 closure scope |
| BLOCKED | 4 | CMake graph (no cmake); RC-12 (4 commits absent); #628/#597/#618 APK corpus absent |
| PENDING | 3 | #634 audit; UBSAN profile; BUG-7 dedupe |
| NOT-INTEGRATED (confirmed to exist elsewhere) | 3 | RC-12 oracle; #633 MG-011 fix; #630/#631 apps |

**Levels used for CONFIRMED rows:** Source-confirmed / Build-graph-confirmed / Unit-test-confirmed / Integration-test-confirmed / Runtime-observed / Original-APK-verified — each row in the CSV carries its exact level.

## §3 — Integrated into the main program during this audit (commit 9b953ce1)
1. **`.DELETE_ON_ERROR:` added to the Makefile** (AUD-09) — behavior demonstrated on a failed target BEFORE enabling; full link rc0 after.
2. **`evidence/audit/` committed** — all 8 mission deliverables: MASTER_AUDIT.md, ACHIEVEMENT_LEDGER.csv, INTEGRATION_MAP.md, REJECTED_AND_CORRECTED.md, BLOCKED_AND_PENDING.md, REGRESSION_RESULTS.md, PRESERVED_WORK_MANIFEST.md, NEXT_INTEGRATION_PLAN.md + raw probe logs + tracker index snapshot.
3. Previously-integrated confirmed work re-verified on today's HEAD: W24 tiering (ABBA), BUG-4/5/8 fixes, BUG-1/1b object libraries, ccache opt-in path.

## §4 — False-green / test-quality findings (mission §8)
- BUG-5 placebo law preserved (page-cache order bias) — every future timing claim must alternate run order (ABBA).
- The 5-APK gate compares SHA-256 screenshot hashes against a recorded canonical set — no static placeholders; battery asserts laws, not exit codes.
- RC-12's V-1/V-2 false-green history could NOT be re-audited — the oracle is absent from mainline (BLOCKED, not assumed clean).

## §5 — Counts reconcile with the ledger
30 confirmed · 4 rejected · 5 partial · 4 blocked · 3 pending · 3 confirmed-not-integrated · regressions reproduced: 0 (gates all hold on today's candidate) · fixes integrated this audit: 1 (DELETE_ON_ERROR) + audit registration itself · tests independently reproduced today: battery 49/49, gate 11/11, 8 ABBA probe compiles, 4 substitute-run source checks.

## §6 — Dependency-ordered next steps
BUG-7 dedupe → #633 MG-011 apply + parity test → CMake WEBP define (when cmake restored) → #626 rebase → RC-12 commit recovery → layout apps recovery → GridLayout/nine-patch laws → UBSAN profile → -Werror/CI. Full rationale: `evidence/audit/NEXT_INTEGRATION_PLAN.md`.

*Per mission rule 10/§7: no existing issue was closed by this audit; this single issue is the cumulative ledger the mission requires, and the row-level CSV is the source of truth for the counts above.*
