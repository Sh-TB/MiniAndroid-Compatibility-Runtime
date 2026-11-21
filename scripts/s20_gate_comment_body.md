**S20 EXECUTION GATE — baseline + plan submitted for approval (no implementation started)**

Per the directive: no new audit cycle; this is the evidence-backed gate response. Full report: `download/S20_execution_gate_report.md` (all anchors, commands, measurements).

**1. HEAD/tree (verified):** `2466a240` (main, clean, pushed); `build/` absent (recycle); g++ 14.2.0, nproc=2; no `/usr/bin/time`, no ccache/lld/mold.

**2. S19/S20 runtime-active changes: NONE.** `git diff --stat 3cfb3786~1..2466a240 -- src/` is empty — everything was tests/docs/scripts/planning (the S19 commit's 14 files: Makefile test registration + s19_grid_scroll_laws_test + evidence). The "7 remaining rows" were settled by the S20 audit closure (`3358d97b`) — but zero runtime code changed, which is exactly the directive's point. Live-vs-dormant verified: `software_renderer.cpp`/`vector_decode.cpp` COMPILE (core_sources.manifest; `make -n`); `view_renderer.cpp` in DORMANT_SOURCES (:624); the 94K-line `dalvik_engine.cpp` monolith is the DALVIK_SPLIT=0 fallback — the 5 split TUs are the live path.

**3. Five APK targets (all already-reproduced evidence; no new claims):**
- **T1 dooz** (`io.github.yamin8000.dooz`, F-Droid URL in tests/corpus/apks.json): ROOT-LOCATED F-020 — `SnapshotKt.readError` ISE at `LP/l;.q` (setContent→mutableStateOf chain) + S210's kotlinx Segment corruption → process-death → blank.
- **T2 rttt** (`org.kirkezz.rttt`): rc=0 but EMPTY frame — Compose frontier family.
- **T3 freebloks** (`de.saschahlusiak.freebloks`): boots clean to RESUMED, 31 frames, verdict **DEFAULT_BACKGROUND_ONLY**, `first_missing_stage=APP_DRAW_OPS` — the draw-op walk never runs.
- **T4 itsfrz** (`com.itsfrz.tictactoe_5`, handoff APK): RESUMED then ISE escaping at `MainActivity.onCreate`, unwind through `androidx/navigation/NavHostFragment;.<init>` — navigation-fragment init semantics missing.
- **T5 PF-Dicer** (`org.secuso.privacyfriendlydicer`): SplashActivity.onCreate → ISE app boundary, empty frame.
Blocker: none of T1/T2/T3/T5 are locally cached (handoff has only the 15 older APKs) — re-fetch via `scripts/download_test_apks.py` (SHA-verified, external cache) is task T0.

**4. Three shared bottlenecks (live TUs only):**
- **B2 — APP_DRAW_OPS draw-walk gap** (highest leverage): rendering stops after the window background — freebloks proven; every blank=1.0 frame is consistent. Likely `software_renderer.cpp` + draw shadows. One fix plausibly moves ALL blank-frame targets.
- **B1 — Compose snapshot/state frontier**: T1 (two independent root-causes: F-020 + S210) + T2.
- **B3 — androidx boundary semantics family**: T4 (NavHostFragment) + T5 (+dicerroller dialog, antimine) — per-app gaps sharing the androidx dispatch path.
Priority: **B2 > B1 > B3** (impact across multiple APKs, not ease).

**5. Integration classification (ledger, 69 rows, validator PASS):** INTEGRATED 27 (with call path + test each), PARTIALLY 5, NOT-INTEGRATED 10, DOCUMENTED-ONLY 7, BLOCKED 8, REJECTED-EXPERIMENT 8, SUPERSEDED 3, N/A 6. #633 = BLOCKED-at-mini-ARSC-fixture (live read `vector_inflater.cpp:356`); #634 = feature-class (no animated-vector branch, no drawable-doc loader, grep=0). Neither counts as integration.

**6. Build baseline — MEASURED this session (exact commands in the full report):**
- Clean `make -j2 all`: **6m38.4s** (89 TUs, `-g -O2`, binary 119.8 MB)
- No-change rebuild: **1.05s** (0 recompiles — `-MMD -MP` dep tracking HEALTHY)
- One-TU incremental (layout_inflater.cpp): **11.98s** (1 big TU ~10s + link)
- Link-only: **0.98s** (verified by mtime)
Diagnosis: the delay is the COLD build after recycle wipes, not incremental pathology. Levers (to be A/B-measured, correctness preserved): ccache install; `-g1` default (profile-gated at Makefile:40, W23-profiled, not default); fix the Makefile:273/289 duplicate-recipe warning.

**7. Task sequence for approval:** T0 baseline refresh (pin URLs, re-fetch 5 APKs, re-run at HEAD → fresh tsv baselines) → **T1 = B2 draw-walk fix** (reproduce freebloks → root-cause → one shared fix + law test + mutation → battery green → frame-sha before/after ×3 runs + SHA-256 screenshots → cross-impact on ≥2 blank-family apps) → T2 = B1 Compose snapshot minimum semantics (dooz past F-020, RTTT frame) → T3 build efficiency A/B → T4 = B3 per-target semantics (last). NEW-26 one-liner (text_shaper.cpp:619, s98 text laws guarding) rides along. #633/#634 and the exec-budget pair (2048/Lexica 540s timeout) stay out of S20.

**8. Blockers:** target APKs not cached + 3 URLs unpinned (T0 resolves); 2-core/no-ccache (~10–25 min per full proof cycle); network reachability for f-droid fetches; hypotheses flagged as such (W21 blank=1.0 Compose membership unverified per-app; T5's exact ISE site to re-confirm; B2's root-cause site to be proven by T1's repro).

**Awaiting approval. No implementation has started; no APK improvement claimed.**
