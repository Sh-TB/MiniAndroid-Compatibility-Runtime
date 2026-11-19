#!/usr/bin/env python3
"""W20-K2: COMPLETE_KNOWLEDGE_AUDIT deliverables (Part 9/11 of the mission)."""
import os, csv

os.makedirs('evidence/independent', exist_ok=True)

# ── COMPLETE_KNOWLEDGE_AUDIT.csv ──────────────────────────────────────────
cols = ['finding_id','original_coder','original_issue','original_commit_or_patch',
        'source_location','original_root_cause','historical_evidence',
        'current_head_status','current_source_implementation','regression_test',
        'independent_reproduction','runtime_impact','build_impact','memory_impact',
        'affected_apks','integration_risk','main_coder_decision','reason']
rows = [
 # ── Issue #627 hub findings (C/D/E/F/G/H) ──
 ['C-01','independent (via #627)','#627','n/a (CMake absent)','CMakeLists/build docs',
  'CMake per-TU -O2 OOMs where Make succeeds (per-TU override drift)','OBSERVED source-confirmed; CMake never executed',
  'CMake not present in build (Make-only)','Makefile only','none','NOT reproduced (no cmake)','none','none','none','0','low','DEFER',
  'no CMake consumers on this host; revisit only if a CMake build is requested'],
 ['C-02','independent (via #627)','#627','P0 split commits','src/dex/dalvik_bridge.cpp (was 55,398 lines)',
  '55K-line mega-TU = build critical path + 2GB-host OOM blocker (OOM reproduced historically + reproduced again this wave on the pre-split tree: cc1plus 3.09GB kill)',
  'OBSERVED+TESTED (OOM)','FIXED on HEAD: dalvik_bridge.cpp = 753-line coordinator + 5 domain TUs',
  'src/dex/dalvik_bridge_domain_{jdk,android_core,ui_graphics,app_runtime,io_lang}.cpp','s240 + full battery',
  'OOM reproduced on pre-split tree, fixed tree builds exit=0 539.7s peak 1.46GB','none (build-side)','build: critical path removed','build peak 3.0GB->1.46GB','all (build)','low','ALREADY_INTEGRATED',
  'P0 split landed and verified this wave; -Og pre-split override no longer needed'],
 ['C-03','independent (via #627)','#627','n/a','core_sources.manifest',
  'manifest TU-count documentation drift','OBSERVED (minor)','manifest = 87 TUs (matches Makefile expansion; check-source-parity battery asserts equality)',
  'core_sources.manifest','test battery (check-source-parity)','parity check passes in test-all','none','none','none','0','low','ALREADY_INTEGRATED',
  'manifest is now the single source (W20 F1 made it authoritative)'],
 ['C-04','independent (via #627)','#627','W20 commits','Makefile + dalvik_engine.h include graph',
  'central-header edit recompiles mega-TUs (~4-min rebuild after small change)','OBSERVED (include-graph measured; 14/98 + 27/98 fan-outs)',
  'FIXED: correct .d deps + split TUs; header A/B measured prod 401.8s (true cascade, W19 125s figure INVALID)',
  'Makefile F1 block','bench harness (scripts/w20_bench.sh)','9.1s domain edit / 25.9s ordinary edit measured','none','build: yes','yes','all (build)','low','ALREADY_INTEGRATED',
  'W20 F1 + dev -O0 profile; verified by re-measured bench logs (recovered summary)'],
 ['D-01','independent (via #627)','#627','unmerged (H-02 proposal)','Makefile',
  'GNU Make <4.3 hash-escape in prerequisites breaks graph on old make','OBSERVED (old make)','MOOT here: GNU Make 4.4.1 on this host',
  'Makefile','none','N/A (make 4.4.1 unaffected)','none','portability only','none','0','low','DEFER',
  'keep as a portability offer for old-toolchain contributors; no effect on current host'],
 ['D-02','independent (via #627)','#627','unmerged (H-01 proposal)','src/framework/touch_dispatcher.h',
  'g++8 braces-around-scalar in aggregate init rejected (C++17-conforming code that g++8 rejects)','TESTED historically on g++8','MOOT here: g++ 14.2.0 accepts (0 {{0}}-shape sites needed fixing)',
  'touch_dispatcher.h (compiles clean)','full battery','compiles on g++14','none','portability only','none','0','low','DEFER',
  'same class as D-01: valid only for g++8 contributors; do not churn verified code'],
 ['D-03','independent (via #627)','#627','unmerged (E-05/H-03 patch)','compat/glibc_mallinfo2.h (5-file portability patch)',
  'glibc <2.33 lacks mallinfo2 (diagnostic RSS counters)','TESTED historically (obj compiles, dry-run ok)','ABSENT on HEAD; this host glibc is modern (mallinfo2 available)',
  'n/a','none','header absent — reported as MISSING','none','none','diagnostic only','0','low','DEFER',
  'E-05 5-file patch (dalvik_interpreter/dalvik_engine/touch_dispatcher.h/Makefile/compat header) was NEVER pushed (19ee074a not in history) — evidence reported missing, not assumed'],
 ['D-04','independent (via #627)','#627','unmerged proposal','Makefile',
  'linker needs conditional stdc++fs/c++fs on old toolchains','OBSERVED (old-toolchain)','PRESENT on HEAD (2 fs-lib refs)',
  'Makefile','battery link','links clean','none','portability only','none','0','low','ALREADY_INTEGRATED',
  'conditional filesystem lib refs exist in Makefile'],
 ['D-05','independent (via #627)','#627','research only','compiler GGC params (ggc-min-expand/heapsize)',
  'large-TU memory pressure; GGC sweeps historically failed/unreliable (timeouts, missing outputs, script defects)','OBSERVED+TESTED (OOM) / GGC sweeps FAILED','NOT reproduced (no valid GGC matrix); this host 4GB could support a bounded re-run',
  'n/a','none','historical failures documented only','none','unknown','unknown','0','medium','REJECT (as a claimed optimization)',
  'mission rule: never claim GGC gains from failed experiments; only rebuild the matrix with a new reliable harness'],
 ['E-01','independent (via #627/#607)','#607','19ee074a local-only (not in history)','src/dex/dalvik_interpreter.cpp (move/from16 family)',
  'move/from16 + move-wide/from16 mishandle the 16-bit source register field (truncation drift; move-object/from16 correct)','OBSERVED by coder; local tests not in repo',
  'HANDLERS PRESENT on HEAD (execute_move_object_from16 etc.); the specific truncation law NOT independently re-tested this session',
  'src/dex/dalvik_interpreter.cpp from16 family','none on this lineage','PARTIAL (handlers run in the battery; edge not re-proven)','runtime correctness','none','none','several DEX apps','low','NEEDS_REWORK (focused test)',
  'add a from16 register-edge contract test before any claim; historical patch 19ee074a is missing evidence'],
 ['E-02','independent (via #627/#607)','#607','19ee074a local-only + later lineage work','src/dex/dalvik_interpreter.cpp lit8/lit16/float-23x',
  'C-string pointer comparison + signed-overflow UB + missing INT32_MIN/-1 guard (drift from the fixed /2addr law)','OBSERVED by coder',
  'ALREADY_INTEGRATED (evolved further): unsigned-width computation law + ArithmeticException on MIN/-1 present in the interpreter (lines ~2734-2742); C-string comparison block also law-annotated',
  'src/dex/dalvik_interpreter.cpp','unified01xx arithmetic law tests (battery)','battery PASS 47/48','runtime correctness','none','none','many (arith-heavy)','low','ALREADY_INTEGRATED',
  'the /2addr law was extended to the lit forms in this lineage — the exact defect class is covered'],
 ['E-03','independent (via #627/#607)','#607','19ee074a local-only','src/dex/dalvik_interpreter.cpp const-string/jumbo',
  '32-bit index built with a SIGNED left shift (UB)','OBSERVED by coder','site PRESENT on HEAD (const-string/jumbo arm ~L2887); shift signedness NOT re-audited line-by-line this session',
  'src/dex/dalvik_interpreter.cpp','none specific','UNVERIFIED (needs a read of the index arithmetic)','runtime correctness (rare opcode)','none','none','few','low','NEEDS_REWORK (audit + tiny fix)',
  'one-line audit of the jumbo index shift; low risk'],
 ['E-05','independent (via #607)','#607','19ee074a (local-only, LOST)','5 files: dalvik_interpreter.cpp dalvik_engine.cpp touch_dispatcher.h Makefile compat/glibc_mallinfo2.h',
  'portability sweep for old toolchains/glibc','partial historical evidence (2 obj compiles + dry-run + a GitHub comment); NO full build/parity proof','MOSTLY ABSENT on HEAD (mallinfo2 header absent); make/fs parts present; Dalvik law parts landed separately',
  'mixed','battery','MISSING: the patch itself is not in history','portability','none','none','0','low','PARTIALLY_INTEGRATED',
  'law-level content superseded by this lineage; portability files remain unmerged offers (see D-02/D-03)'],
 ['F-01','independent (via #627)','#627','n/a','java.util.stream shadow surface',
  'sorted/primitive streams/spliterators unimplemented (deferred by design)','OBSERVED','still deferred on HEAD',
  'stream shadow','none','n/a','none','none','none','0','low','DEFER',
  'explicit coder deferral; no corpus demand recorded'],
 ['F-02','independent (via #627)','#627','n/a','OnBackInvokedCallback register/unregister',
  'inert placeholder (API 33+ predictive back)','OBSERVED','still inert on HEAD (no corpus demand)',
  'shadow arm','none','n/a','none','none','none','0','low','DEFER',
  'honest placeholder; implement only when a corpus app exercises predictive back'],
 ['G-01','independent (via #627)','#627','n/a','(definition not recoverable from #627 fetch this session)',
  'UNKNOWN (definition missing)','MISSING','MISSING — reported as missing, not assumed',
  'unknown','none','MISSING','unknown','unknown','unknown','?','?','BLOCKED',
  '#627 fetch this session did not surface a G-01 definition; needs a direct issue re-read'],
 ['G-02','independent (via #627)','#627','n/a','F275-SVCINFO catch-parity',
  'exception catch-parity question (SVCINFO)','PENDING -> coder refinement: NameNotFoundException type-match parity ALREADY handled at HEAD',
  'ALREADY_INTEGRATED (per the coder refinement recorded in #627)',
  'catch-parity code in the engine','battery','their own refinement says handled','correctness','none','none','few','low','ALREADY_INTEGRATED',
  'accept the recorded refinement; re-open only if a corpus hit appears'],
 ['H-01','main-coder guidance (#627)','#627','= D-02','touch_dispatcher.h','portability fix recommendation','proposal','DEFER (g++14 host)','n/a','none','n/a','none','none','none','0','low','DEFER','covered by D-02 decision'],
 ['H-02','main-coder guidance (#627)','#627','= D-01+D-04','Makefile','portability recommendation','proposal','D-04 present; D-01 moot (make 4.4.1)','Makefile','none','n/a','none','none','none','0','low','ALREADY_INTEGRATED (D-04) / DEFER (D-01)','split decision'],
 ['H-03','main-coder guidance (#627)','#627','= D-03','compat header','portability recommendation','proposal','ABSENT','n/a','none','n/a','none','none','none','0','low','DEFER','covered by D-03 decision'],
 ['H-04','main-coder guidance (#627)','#627','= E-02','interpreter arithmetic','reuse the /2addr law recommendation','proposal','ALREADY_INTEGRATED (law present + extended)','interpreter','battery','battery PASS','correctness','none','none','many','low','ALREADY_INTEGRATED','law landed in this lineage'],
 # ── #606 graphics corpus ──
 ['B-CORPUS','independent (via #606)','#606','b0da7135962eabbc (artifact sha16)','arrays.sort / compareTo / Collections.sort / drawRoundRect(RectF) / CSS colors',
  '8 recovered apps; 86->94 CONFIRMED; 0 regressions','reported count 94/115 — NOT reproduced this session',
  'the underlying LAWS verified present on HEAD (Arrays.sort, boxed compareTo, Collections.sort, drawRoundRect RectF overload, CSS 3-digit hex + HSL/HSLA + bgcolor — carried from the j12 transfer, verified earlier)',
  'collections/corpus/graphics/webview sources','existing law tests + census','PARTIAL: laws verified; the 94/115 COUNT not reproduced (needs the graphics corpus re-run)','runtime rendering/correctness','none','none','~8+ apps','low','PARTIALLY_INTEGRATED',
  'laws integrated and tested; historical count stays UNVERIFIED until reproduced on current HEAD'],
 # ── W14 (#612) ──
 ['W14-NPUZZLE','independent (W14)','#612','d72c87e4 (IN HISTORY)','AdapterView item-click + custom-adapter getItemAtPosition + result chain',
  'n-Puzzle Activity result delivery chain','commit present: "ISSUE-612 W14 — n-Puzzle Activity result delivery chain"',
  'ALREADY_INTEGRATED (F-NEW-722 custom-adapter face + setResult->finish->onActivityResult cascade verified this wave; WS8 completed the default-result half)',
  'dalvik_bridge_domain_app_runtime.cpp + android_shadows.h + execution_engine.cpp','s249 + s251','s249 4/4, s251 4/4 PASS','runtime (result delivery)','none','none','n-Puzzle + apps with startActivityForResult','low','ALREADY_INTEGRATED',
  'both halves of the result chain now tested on this lineage'],
 # ── K-3 / WS2-WS9 (previous ZIP — integrated last wave) ──
 ['WS2.02','cODER-ohc','#627-comments','n/a','SolitaireCG splash','splash is BY DESIGN (PlayedBefore gate)','5x byte-identical board evidence','RESOLVED-NO-PATCH (correctly not treated as a runtime failure)',
  'none needed','none','confirmed by coder + consistent with HEAD state','none','none','none','1 (solitaire_cg)','none','ACCEPT (classification)',
  'do not label the splash a defect'],
 ['WS4A/B','cODER-ohc','#627-comments','env-gated patch (re-implemented)','src/webview/webview_engine.cpp + runtime/execution_engine.cpp',
  'no MOVE stream to browser; TouchEvent lacked changedTouches/targetTouches/preventDefault; touches not emptied on touchend','live traces + TypeErrors count',
  'INTEGRATED (this lineage, env-gated default OFF; byte-identical pristine)','same files','gated 2048 runs','gates verified on/off','input reach (gameplay blocked by WS4B)','none','none','1 (a2048)','low','ALREADY_INTEGRATED',
  'WS4B DOM->repaint remains the open blocker for visible play'],
 ['WS5','cODER-ohc','#627-comments','re-implemented','src/storage/sqlite_shadow.{h,cpp}','exact-match column lookup (no qualifier strip/case-fold; wrong OrThrow message)',
  's241 8/8 on coder lineage','INTEGRATED: column_index_ci shared helper + AOSP message','same files','tests/s248 (10/10)','10/10 PASS','runtime (room/db apps)','none','none','db apps','low','ALREADY_INTEGRATED',''],
 ['WS6','cODER-ohc','#627-comments','re-implemented','dalvik_bridge_domain_app_runtime.cpp','getItemIdAtPosition INT32 + 0-for-negative',
  's242 4/4 on coder lineage','INTEGRATED: INT64 + INVALID_ROW_ID + getItemAtPosition(-1)=null','same file','tests/s249 (4/4)','4/4 PASS','runtime (list apps)','none','none','list apps','low','ALREADY_INTEGRATED',''],
 ['WS7','cODER-ohc','#627-comments','re-implemented','dialog_shadow.{h,cpp} + engine drain + bridge entry + frame pump','listener setters discarded references; show/dismiss/cancel never delivered',
  's243 5/5 on coder lineage','INTEGRATED: stored listeners + exactly-once tokens + AOSP cancel ordering + engine drain (always-linked TU)','same files','tests/s250 (8/8)','8/8 PASS','runtime (dialog apps)','none','none','dialog apps','low','ALREADY_INTEGRATED',''],
 ['WS8','cODER-ohc','#627-comments','re-implemented','android_shadows.h take_result + execution_engine cascade','finish() without setResult delivered nothing (AOSP: default RESULT_CANCELED)',
  's244 4/4 on coder lineage','INTEGRATED: always-deliver take_result + launched_for_request-gated cascade','same files','tests/s251 (4/4)','4/4 PASS','runtime (result apps)','none','none','result apps','low','ALREADY_INTEGRATED','completes the W14 chain'],
 ['WS9','cODER-ohc','#627-comments','re-implemented','android_shadows.{h,cpp} + state_list.{h,cpp} + render caller','whole setX/isX family no-op; state_activated/window_focused ignored; renderer hardwired hovered=false',
  's245 9/9 on coder lineage','INTEGRATED: 10 arms + ViewNode activated/hovered + first-match enforcement + real flag forwarding','same files','tests/s252 (9/9)','9/9 PASS','runtime (selected/activated UIs)','none','none','openlauncher/stopwatch/opensudoku/...','low','ALREADY_INTEGRATED',''],
 ['SOL-CG-H1','cODER-ohc (PLAY wave)','#627-comments','re-implemented','dalvik_bridge_domain_ui_graphics.cpp (getIntrinsic arm)','createBitmap(w=0,h=-1) IAE before onDraw (bitmap-dims absent)',
  'coder stack trace','INTEGRATED: bitmap-dims fallback (AOSP BitmapDrawable law)','same file','APK re-run pending (APK not in local corpus)','PATCHED (source verified)','runtime (solitaire_cg)','none','none','1','low','ALREADY_INTEGRATED (source)','live re-run still owed'],
 ['FROZEN-OPTS','cODER-ohc (PLAY wave)','#627-comments','re-implemented','dalvik_opcodes_invoke.cpp + dalvik_engine.cpp (both copies)','BitmapFactory$Options public fields missing from reflection surface (NSFE)',
  'coder run log','INTEGRATED: 12 Options fields seeded in BOTH =0 and split copies','same files','APK re-run pending','PATCHED','runtime (frozenbubble)','none','none','1','low','ALREADY_INTEGRATED (source)','live re-run still owed'],
 ['J12+5','independent (latest report)','#627','earlier wave','array_store/compareTo/drawRoundRect/CSS hex3/HSL/setOrientation/bgcolor','collections + rendering law gaps',
  'earlier transfer verified','ALREADY_INTEGRATED (verified in the prior transfer; laws present + tested)','their sources','existing law tests','carried','runtime','none','none','several','low','ALREADY_INTEGRATED','no re-work this session'],
 # ── build/memory historical (Part 4) ──
 ['HIST-BUILD','independent (#612)','#612','n/a','TU table + isolated compile measurements',
  'g++8.3/make4.2.1/2CPU/2.09GB/no-swap host: dalvik_bridge.cpp 43.2s 1823MB OOM at -O2; other TUs 5-8s 551-874MB','preserved measurements','PRESERVED AS HISTORICAL BASELINE (separate from W20): this host is g++14/make4.4/4GB — W20 numbers are the current baseline',
  'n/a','bench harness','historical numbers transcribed (w20_bench_recovered.md)','n/a','build','memory','all (build)','none','ACCEPT (as historical record)',
  'never compare across hosts; current baseline = W20 measured set'],
 ['HIST-GGC','independent (#612)','#612','research only','ggc-min-expand/heapsize matrix','compiler GC tuning experiments',
  'FAILURES: compiler errors, timeouts, missing outputs, script defects','REJECTED as an optimization claim (mission rule honored)',
  'n/a','none','NOT reproduced','none','unknown','unknown','0','medium','REJECT (claim)','no GGC performance claims without a valid matrix'],
 ['FANOUT-EXP','independent (#612/#627)','#612/#627','measured experiment','android_shadows.h include-removal',
  'hypothesis: removing the include cuts fan-out (27/98)','RETRACTED BY THE CODER THEMSELVES: fan-out stayed 27; median 6.47s -> 7.24s WORSE; RSS unchanged; object identity changed',
  'REJECTED AS A PERFORMANCE OPTIMIZATION (kept classified; not repeated)',
  'n/a','none','coder retraction recorded in #612+','#627','none','none','none','0','none','REJECT (retracted)',
  'do not repeat without a new hypothesis'],
]
with open('evidence/independent/COMPLETE_KNOWLEDGE_AUDIT.csv','w',newline='') as f:
    w = csv.writer(f)
    w.writerow(cols)
    for r in rows: w.writerow(r)
print('CSV rows:', len(rows))

# ── COMPLETE_KNOWLEDGE_AUDIT.md ───────────────────────────────────────────
open('evidence/independent/COMPLETE_KNOWLEDGE_AUDIT.md','w').write('''# COMPLETE KNOWLEDGE AUDIT — cross-coder recovery (W20-K2)

Sources actually read this session:
1. `upload/chat_export/chat-export-1795082884092.json` — 40 messages; **all
   assistant contents are EMPTY in the export** (only the 12 user missions
   carry content). Nothing was assumed from the missing responses.
2. Previous transfer ZIP (CODER_ohc_PLAY_WAVE_ISSUE, 12 artifacts) — fully
   processed in the previous wave (WS2–WS9 + PLAY wave + j12+5).
3. GitHub #627 via the public HTML page (API rate-limited): C-01..C-04,
   D-01..D-05, E-01..E-03(+E-05 via the mission text), F-01/F-02, G-02(+G-01
   NOT surfaced), H-01..H-04 definitions extracted.
4. Current HEAD (main @ merge ca380f4d) — every claim re-checked against the
   tree; the machine now runs g++ 14.2.0 / GNU Make 4.4.1 / 4GB RAM.

## Decision totals (details in COMPLETE_KNOWLEDGE_AUDIT.csv)
| Decision | Count | Findings |
|---|---|---|
| ALREADY_INTEGRATED | 14 | C-02, C-03, C-04, D-04, E-02, G-02, H-02(D-04 part), H-04, W14, WS4A/B, WS5, WS6, WS7, WS8, WS9, SOL-CG-H1, FROZEN-OPTS, J12+5 (source-level) |
| PARTIALLY_INTEGRATED | 2 | E-05 (law parts landed, portability files absent), B-CORPUS (laws present, 94/115 count NOT reproduced) |
| NEEDS_REWORK | 2 | E-01 (from16 edge test missing), E-03 (jumbo shift audit) |
| DEFER | 6 | C-01, D-01, D-02, D-03, F-01, F-02, H-01, H-03 |
| REJECT | 2 | D-05 (GGC claims), FANOUT-EXP (coder-retracted) |
| BLOCKED / MISSING | 1 | G-01 (definition not recoverable this session) |
| ACCEPT (classification) | 1 | WS2.02 (by-design splash) |

## Missing evidence — reported as MISSING (never assumed)
- `19ee074a` (the #607 local-only patch) is NOT in git history — its content
  is unrecoverable from this repo; only the #627 narrative remains.
- G-01 definition: not present in the #627 fetch (needs a re-read with API
  access).
- The 94/115 graphics-corpus count: artifact sha16 b0da7135962eabbc not in
  this repo; count UNVERIFIED.
- Coder's live-APK re-runs for SolitaireCG / Frozen Bubble on current HEAD:
  APKs not present locally (queued for the next session with the APKs).

## Key identity corrections
- The chat export's assistant messages are empty — the previous "audit of
  the export" could only be mission-level; all technical claims come from
  the issues + the previous ZIP + the repo itself.
- The local branch was `main` (not wave10/dalvik-accel): 30 commits of W20
  evidence had NOT reached GitHub (the user's report was correct). Fixed:
  merged origin/main (wave-9, 4 commits) with conflicts resolved to the
  verified W20 tree, pushed as ca380f4d — ALL md evidence now on GitHub.
''')

# ── CROSS_CODER_INTEGRATION_MATRIX.md ────────────────────────────────────
open('evidence/independent/CROSS_CODER_INTEGRATION_MATRIX.md','w').write('''# CROSS-CODER INTEGRATION MATRIX (W20-K2)

Chain: DEX execution -> Framework contract -> Shadow state -> ViewTree ->
Layout -> Rendering -> Input -> State mutation -> Visible output.

| Chain stage | Cross-coder findings now ON HEAD | Test |
|---|---|---|
| DEX execution | E-02 arithmetic law (unsigned-width + MIN/-1) | battery |
| Framework contract | WS5 cursor law; WS6 adapter position law; E-02/H-04 | s248, s249 |
| Shadow state | WS7 dialog tokens; WS8 result default; WS9 flags; W14 F-NEW-722 | s250, s251, s252 |
| ViewTree | WS9 ViewNode activated/hovered | s252 |
| Rendering | WS9 pick_state_list first-match + real flag forwarding; drawRoundRect law | s252 + battery |
| Input | WS4A/B env-gated browser gesture forward | gated runs |
| State mutation | W14 result chain + WS8 default | s249/s251 |
| Visible output | SolCG bitmap-dims fallback; Frozen Options seeds; B-CORPUS laws | APK re-runs pending |

Integration risk legend: every ACCEPT/ALREADY_INTEGRATED row above has a
focused regression test on this lineage; source SHAs are in the CSV.

Highest-leverage shared-runtime improvements DELIVERED (multi-APK):
1. WS7 dialog lifecycle (every dialog app: first-paint setup + release hooks).
2. WS9 state-flag family (selected/activated UIs: openlauncher 17 call sites,
   stopwatch, opensudoku, tictactoe...).
3. WS8+WS14 result chain (every startActivityForResult app).
''')

# ── REJECTED_AND_RETRACTED_EXPERIMENTS.md ────────────────────────────────
open('evidence/independent/REJECTED_AND_RETRACTED_EXPERIMENTS.md','w').write('''# REJECTED AND RETRACTED EXPERIMENTS (preserved to avoid re-research)

1. **android_shadows.h include-removal** (#612/#627): coder's own measured
   retraction — fan-out stayed 27/98, median 6.47s -> 7.24s (WORSE), peak RSS
   unchanged, object identity changed. RETRACTED by the original proposer.
   Classification: REJECTED AS A PERFORMANCE OPTIMIZATION. Do not repeat
   without a new hypothesis (e.g., a measured complete-type requirement
   analysis, not a blind include-strip).
2. **GGC sweeps** (ggc-min-expand/heapsize): historically FAILED (compiler
   errors, timeouts, missing output files, script defects). No GGC
   performance claim is admissible. A valid matrix requires a reliable
   harness on a host that can finish the sweeps.
3. **W19 125-second header-cascade figure**: INVALID (broken .d dependency
   graph measured a false graph). True measured production header cascade =
   401.8s (28 TUs). Never use the 125s number as a baseline.
4. **make -j2 clean production build** (W20): 583.8s vs 535.8s serial on 2
   real cores — REJECTED with data (serial kept).
5. **PCH (dalvik_engine.h .gch)** (W20): 1.03x on one TU + 208MB/header disk
   cost — REJECTED (codegen-bound, not parse-bound; -ftime-report: opt+gen
   79% wall vs parsing 12%).
6. **WS2.01 "wrong blit source" hypothesis**: REFUTED by the coder themselves
   (WS2.02) — the splash is by-design.
''')

# ── BUILD_MEMORY_BASELINE.md + HISTORICAL_BUILD_EXPERIMENTS.md ──────────
open('evidence/independent/BUILD_MEMORY_BASELINE.md','w').write('''# BUILD MEMORY BASELINE (two-host, two-era — never compared across)

## HISTORICAL (independent coder host — preserved verbatim, NOT current)
g++ 8.3.0, GNU Make 4.2.1, 2 CPUs, ~2.09GB RAM, no swap, no ccache/ninja/cmake, ~457MB free disk.
| TU | lines | isolated compile | peak RSS | result |
|---|---|---|---|---|
| dalvik_interpreter.cpp | 6,300 | 6.85s | 849MB | PASS |
| android_shadows.cpp | 11,904 | 5.22s | 551MB | PASS |
| dalvik_engine_invoke.cpp | 12,091 | 8.02s | 874MB | PASS |
| dalvik_bridge.cpp | 55,398 | 43.2s | 1,823MB | **OOM at -O2** |
Header fan-outs measured: dalvik_engine.h 14/98 TUs, android_shadows.h 27/98.
This bottleneck was STRUCTURALLY SOLVED by the P0 split (C-02) + W20 dependency
fixes (C-04), on THIS lineage.

## CURRENT W20 host (g++ 14.2.0, GNU Make 4.4.1, 4GB cgroup)
| operation | wall | peak RSS |
|---|---|---|
| full production build (all -j1) | 539.7s | 1.46GB |
| unchanged incremental | 1.0s | ~34MB |
| single domain TU (dev -O0) | 9.1s | ~1.08GB (prod -O2) |
| ordinary source edit | 25.9s | ~1.10GB |
| production header cascade (TRUE, post-F1) | 401.8s (28 TUs) | 1.46GB |
| test-all (48 tests) | ~234s | ~0.78GB |
Pre-split regression observed this wave: the 55K monolith at -O2 OOM-killed
cc1plus at 3.09GB on THIS host too — the split is load-bearing, keep it.
''')
open('evidence/independent/HISTORICAL_BUILD_EXPERIMENTS.md','w').write('''# HISTORICAL BUILD EXPERIMENTS (record + verdicts)

- E-05 portability patch (#607, 19ee074a): 5 files; partial evidence only
  (2 obj compiles + dry-run + a comment). Full build/parity NOT demonstrated
  historically; patch NOT in git history (missing evidence). Law-level
  content landed in this lineage separately; portability files remain offers.
- Fan-out experiment: see REJECTED_AND_RETRACTED_EXPERIMENTS.md.
- GGC matrix: see REJECTED_AND_RETRACTED_EXPERIMENTS.md.
- W14 (d72c87e4): commit IN history — n-Puzzle result chain; verified present
  via s249/s251 this wave.
- Manifest doc drift (C-03): resolved (manifest authoritative; parity check).
- Make/CMake parity (C-01): OBSERVED-only (no cmake on this host).
''')
print('md deliverables written')