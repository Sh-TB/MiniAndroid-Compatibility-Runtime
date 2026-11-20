# CMAKE GRAPH MEASUREMENT — 2026-11-20 (AUD-52, restores AUD-06's blocked measurement)
cmake 4.4.5 (pip wheel) + ninja 1.13; configure rc=0 both graphs; base 56ba5842 + AUD-51/MG-011 working tree.

## Default graph (BUILD_TESTS OFF — the shipping default)
- edges in `all`: 99 (ninja -n all)
- executable links in `all`: **1** (miniandroid) — the B2 claim "default all links 52" is FALSE for the default graph
- QuickJS compile: ONCE (miniandroid_quickjs OBJECT, 5 edges)
- MINIANDROID_HAVE_WEBP: **0 occurrences** in compile flags (Makefile production path has 4) — AUD-07 divergence CONFIRMED at generated-graph level
- test executables in `all`: 0 (whole test block behind `option(BUILD_TESTS ... OFF)`, CMakeLists.txt:395)

## Test-enabled graph (-DBUILD_TESTS=ON)
- edges in `all`: 204
- executable links in `all`: **50** (miniandroid + 49 battery executables; claim said ~52 — measured 50)
- battery executables have NO EXCLUDE_FROM_ALL (loop at CMakeLists.txt:494) → they join default `all` when BUILD_TESTS=ON — AUD-01/B19/B22 CONFIRMED-with-condition
- QuickJS compile: **2× (10 edges = 5 sources × 2 OBJECT libs: miniandroid_quickjs :298 + miniandroid_test_native :459)** — AUD-02/B20 CONFIRMED-with-condition (not in the default graph)
- simple_test + s130_laws_test + gp582_engine_probe_test + w15_dalvik_lit_from16_law_test + g04/g06g08_hostile_test + resource_hostile_test + lifecycle_law_test ... (50 measured)

## Honest limits
- Peak memory / OOM during a full cmake test build: NOT measured this session (no full BUILD_TESTS=ON compile run; dry-run counts are graph facts, not runtime facts).
- The coder's "~52 links" vs measured 50: 2-executable delta unexplained; may include the two exp executables (exp018/exp019 :555/:565) which carry EXCLUDE_FROM_ALL — checked: they do NOT join all.
- Ledger impact: AUD-01 CONFIRMED (condition documented), AUD-02 PARTIALLY CONFIRMED (2× only with BUILD_TESTS=ON), AUD-06 REJECTED as stated for the DEFAULT graph (1 link, not ~52) — the claim's real scope is the test-enabled graph.
