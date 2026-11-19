# INDEPENDENT REGRESSION REPORT — W20-K (cODER-ohc knowledge transfer)

Base for this wave: tree restored to `671d2577` (the W20-P2 verified-green
state) after the sandbox recycle rolled HEAD back to the pre-split `4c562943`
(tree inconsistency: 748-line coordinator + 55K monolith mixed with
untracked domain TUs — resolved by full restore + scripted re-application of
every W20-K integration; the re-application script set is
scripts/w20_reapply_k{,2,3,4}.py, each edit exactly-once asserted).

## Integrations (all verified against HEAD first — Part D procedure)
| Finding | Files | Regression test | Result |
|---|---|---|---|
| WS5 sqlite column law | src/storage/sqlite_shadow.{h,cpp} | s248 (10 rows) | **10/10 PASS** |
| WS6 adapter position | src/dex/dalvik_bridge_domain_app_runtime.cpp (+null row) | s249 (4 rows) | **4/4 PASS** |
| WS7 dialog lifecycle | src/framework/dialog_shadow.{h,cpp} + dalvik_engine.h + runtime/execution_engine.cpp (drain + frame pump) + dalvik_bridge.cpp (entry) | s250 (8 rows) | **8/8 PASS** |
| WS8 activity result | src/framework/android_shadows.h + runtime/execution_engine.cpp | s251 (4 rows) | **4/4 PASS** |
| WS9 view state flags | src/framework/android_shadows.{h,cpp} + state_list.{h,cpp} + execution_engine.cpp (render caller) | s252 (9 rows) | **9/9 PASS** |
| SolitaireCG h=-1 | src/dex/dalvik_bridge_domain_ui_graphics.cpp | APK re-run (queued this session) | PATCHED |
| Frozen Bubble inScaled | src/dex/dalvik_opcodes_invoke.cpp + dalvik_engine.cpp (both copies) | APK re-run (queued) | PATCHED |
| WS4 2048 input (env-gated) | src/webview/webview_engine.cpp + runtime/execution_engine.cpp | gated runs | PATCHED (default OFF) |

## Battery
- Full build: exit=0, wall=539.7s, peak 1.46GB (integrated tree).
- test-all: **48 tests** wired (43 prior + 5 new contract tests); after the
  fixture fixes: s248 10/10, s249 4/4, s250 8/8, s251 PASS, s252 PASS.
- The two PRE-EXISTING font-env failures (s98/s106) are unchanged lineage
  failures, NOT regressions (coder's own battery noted the same on main).

## What is contract-level vs live-APK evidence
- WS5-WS9: contract level (the exact code the DEX call reaches), per the
  coder's own honest scope notes. Live-APK deltas were NOT fabricated.
- SolCG/Frozen: source patches + queued APK re-runs (results in
  evidence/w20/k_apk/ when this session's check completes).
- WS4: env-gated, default-off — pristine behavior byte-identical.

## SUPERSEDED / no-patch dispositions preserved
- WS2.02: SolitaireCG splash = by-design (no patch; not a runtime failure).
- WS6 harness decoder note: a test-harness gap on the coder's lineage, not a
  runtime change (their s235 does not exist on this lineage).
