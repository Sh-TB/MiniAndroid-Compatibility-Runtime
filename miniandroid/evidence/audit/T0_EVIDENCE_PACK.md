# T0 EVIDENCE PACK — S20 approved scope (T0 + B2 verification) — 2026-11-21

**Scope honored: T0 + B2 verification ONLY. No implementation. B2-3 proposal submitted for approval (§6).**
Binary: HEAD `513d006e` (restored after a 5th sandbox recycle; hard reset to origin/main). Runner: `timeout 90 ./build/miniandroid run --max-seconds 60 --frames 30 --data-root … -o … --execution-mode real-dalvik <apk>` (the W21 runner shape, from `evidence/w21/runtime_perf/*/runner.json`).

## 1. APK recovery (original sources, SHA-256 recorded)

| Target | Version | Original source | SHA-256 (first 24) | Size |
|---|---|---|---|---|
| dooz | `io.github.yamin8000.dooz_18.apk` | F-Droid repo (URL recorded in `tests/corpus/apks.json`) | `d81292cd346dcb23b04488bc` | 1,749,880 B |
| rttt | `org.kirkezz.rttt_3.apk` | F-Droid repo (pinned this session from the package page) | `704fa51869ad7ff441edb88` | 23,386,246 B |
| freebloks | `de.saschahlusiak.freebloks_186.apk` | F-Droid repo (pinned this session) | `831e8d5d5fc34900e43986` | 5,831,028 B |
| dicer | `org.secuso.privacyfriendlydicer_101.apk` | F-Droid repo (pinned this session) | `f2b4d3f021c3a6207c3c9e` | 2,901,531 B |
| itsfrz | `com.itsfrz.tictactoe_5.apk` | Main-Coder handoff set (`upload/handoff_apks/`) | `2a057a9a519acd81dc54af` | 17,726,235 B |

**Provenance proof: dooz's SHA-256 MATCHES the manifest exactly** (`d81292cd…`, recorded size 1,749,880 — same APK as the original F-020 evidence). No APK rebuilt from source; cache lives OUTSIDE the repo (`/home/z/my-project/apk_cache/`, zero-APK policy honored). rttt/freebloks/dicer version codes are the current F-Droid publications (the UNIFIED_011 session logs did not record version codes — flagged honestly; faces reproduced identically regardless).

## 2. Fresh baselines — 5 targets × 3 runs at exact HEAD (deterministic)

| APK | wall (r1) | rc | snapshot sha16 (r1=r2=r3) | census verdict | first_missing_stage |
|---|---|---|---|---|---|
| dooz | 5.43s | 1 | `d602648e8e401895` | DEFAULT_BACKGROUND_ONLY | **APP_DRAW_OPS** |
| rttt | 4.66s | 1 | `b5a7a35d5fe0564b` | DEFAULT_BACKGROUND_ONLY | **APP_DRAW_OPS** |
| freebloks | 6.95s | 1 | `b5a7a35d5fe0564b` | DEFAULT_BACKGROUND_ONLY | **APP_DRAW_OPS** |
| dicer | 5.38s | 1 | r1 `31ffa499…` (splash); r2=r3 `b5a7a35d…` | (crash pre-census — §4) | — |
| itsfrz | 6.31s | 1 | `d55056a8928a26ff` | DEFAULT_BACKGROUND_ONLY | APP_PIXELS |

- **Reproducibility: every APK's 3 runs produce byte-identical snapshot hashes** (dicer r2=r3 after its r1 splash frame).
- freebloks' face `b5a7a35d5fe0564b` **equals the recorded s138 face** (1-color `48,48,48`) — the registry status reproduces exactly at HEAD.

## 3. B2-1 — the exact first-divergence point (active call path, live TUs)

Per-frame trace in EVERY blank run (31 lines = 30 frames + census):

```
[C013-CUSTOMVIEW] unrendered custom view RECORDED (not painted): Landroidx/appcompat/widget/ContentFrameLayout; at (0,0 1080x1920)   ← freebloks
[C013-CUSTOMVIEW] unrendered custom view RECORDED (not painted): Landroidx/compose/ui/platform/AndroidComposeView; at (0,0 1080x1920) ← dooz
[C013-CUSTOMVIEW] surface-family: placeholder SUPPRESSED for Lorg/libsdl/app/SDLSurface; (F-NEW-162)                                  ← rttt
```

Call path (all live, verified compiled): measure/layout complete → `draw_walk_ran=true` → the draw walk visits the app's root content view → the dispatch ladder in `src/runtime/execution_engine.cpp` (text-base / surface-family / T4-PAINTGAP) → **the T4-PAINTGAP last-resort real-draw dispatch is closed by a NAME-PREFIX provenance gate**:

```cpp
// src/runtime/execution_engine.cpp:5100-5104
bool cv_framework =
    cv_cls.rfind("Landroid/", 0) == 0 ||
    cv_cls.rfind("Landroidx/", 0) == 0 ||
    cv_cls.rfind("Lcom/google/", 0) == 0;
if (!cv_framework && task.view_id != 0 && dalvik_engine_.get_heap().has_object(task.view_id)) {
    // dispatch_custom_view_draw(task.view_id) → replay ops  ← NEVER REACHED for androidx classes
}
```

→ `!drew_real` → the view is only RECORDED (`:5156`) → `app_draw_ops=0 ∧ app_owned_px=0` → census `APP_DRAW_OPS` / verdict `DEFAULT_BACKGROUND_ONLY` (`:7069-7076`).

**Divergence from AOSP:** the AOSP `View.draw()` template runs background → onDraw → dispatchDraw → foreground with **no class-provenance gate**. These apps bundle their OWN androidx classes in their DEX (freebloks ships its own appcompat) — the class is a live heap object with a real draw contract; the engine declines it purely by name.

## 4. B2-2 — the same root cause in ≥2 independent APKs (proven)

- **Pair 1 (the exact same gate, same trace line, same terminal census): freebloks (`ContentFrameLayout`) + dooz (`AndroidComposeView`)** — two unrelated APKs, both declined at `execution_engine.cpp:5100-5104`, both `APP_DRAW_OPS`/`DEFAULT_BACKGROUND_ONLY`.
- rttt shares the terminal census state via its own DOCUMENTED branch (surface-family suppression, F-NEW-162) — a **separate chain** (SDL surface pixels), correctly not claimed as the same root cause.
- dicer: crashes pre-census (ExceptionHandler at `Lorg/secuso/pfacore/application/PFModelApplication;.onCreate`, no census verdict) — a B3 androidx-boundary case, not B2.
- itsfrz: reaches `APP_PIXELS` (draw ops run, pixels not app-owned) — also outside B2.

## 5. Regression checks vs previously working APKs — PASS (byte-identical)

| APK | W21 recorded sha16 | Today's sha16 (HEAD `513d006e`) | Result |
|---|---|---|---|
| HelloWorldToast-1.4.0 | `acdd9f05dc9c7ece` | `acdd9f05dc9c7ece` | **IDENTICAL** |
| notepad_122 (blank=0.0) | `31ddd4d5b8e6d18e` | `31ddd4d5b8e6d18e` | **IDENTICAL** |
| randomix_42 (blank=0.0) | `31ddd4d5b8e6d18e` | `31ddd4d5b8e6d18e` | **IDENTICAL** |
| chess_5022 (rc=124, 60s budget) | `d602648e8e401895` rc=124 | `d602648e8e401895` rc=124 | **IDENTICAL** |

No regression on any previously-working face.

## 6. B2-3 — the exact proposed source change + regression plan (FOR APPROVAL — NOT IMPLEMENTED)

**File:** `src/runtime/execution_engine.cpp`, the T4-PAINTGAP gate at `:5100-5104`.

**Change (contract-based gate replacing the name-prefix gate):**

```cpp
// BEFORE (provenance-based — the B2 divergence):
bool cv_framework = cv_cls.rfind("Landroid/", 0) == 0 ||
                    cv_cls.rfind("Landroidx/", 0) == 0 ||
                    cv_cls.rfind("Lcom/google/", 0) == 0;
if (!cv_framework && task.view_id != 0 && dalvik_engine_.get_heap().has_object(task.view_id)) {

// AFTER (contract-based — dispatch iff the class REALLY overrides the draw chain):
bool cv_draw_override =
    dalvik_engine_.chain_overrides_method(cv_cls, "draw") ||
    dalvik_engine_.chain_overrides_method(cv_cls, "onDraw") ||
    dalvik_engine_.chain_overrides_method(cv_cls, "dispatchDraw");
if (task.view_id != 0 && dalvik_engine_.get_heap().has_object(task.view_id) && cv_draw_override) {
```

Everything else (canvas-size S83/S109 laws, the replay path, the census counters, the text-base and surface-family branches ABOVE this branch, the 21-P0-5 authoritative-frame purity) stays untouched. The existing guard comment's own law is preserved: "Nothing fires unless the app's own draw produced ops" — a dispatch that returns 0 ops still leaves the diagnostic recording.

**Why safe:** the dispatch fires only when the loaded DEX (the app's own bundled androidx included) genuinely overrides the draw chain; honest-blank framework views (no override) keep the diagnostic path; the two upstream branches that legitimately suppress (text-empty, surface-family) are not modified.

**Regression plan (executed before any claim):**
1. Full battery green at the changed HEAD (s246 layout closure + all law families).
2. The four working-APK faces byte-identical to §5's shas (no-regression contract).
3. freebloks + dooz re-runs ×3: expected CHANGE — the trace flips from `RECORDED (not painted)` to a dispatched-draw line; census moves off `APP_DRAW_OPS` (to `APP_PIXELS`/`REAL_APP_CONTENT` or better). **Honest expectation stated now:** ContentFrameLayout's own onDraw (foreground-only) may still yield 0 ops — freebloks' board is a GLSurfaceView child whose pixels belong to the surface pipeline; the fix's success criterion is the CENSUS DIVERGENCE MOVING with trace evidence, not necessarily a full game render in one step.
4. Screenshots with dimensions + SHA-256 before/after; three independent post-change runs per target.
5. Negative mutation: re-instate a broad provenance refusal → the C013 lines return exactly (mutation check documented in the log).
6. itsfrz/dicer recorded unchanged (their chains are B1/B3).

**Risks:** draw-chain dispatch on heavyweight androidx views could slow frames (bounded by the existing draw budget/`PARTIAL_RENDER_BUDGET` guard); Compose views may dispatch into an unimplemented ui pipeline and return 0 ops (honest-no-change for dooz until B1 lands).

## 7. Build findings (provisionally accepted; not claimed solved)

| Scenario | Command | Wall |
|---|---|---|
| Clean (2nd measurement) | `rm -rf build && { time make -j2 all; }` | **6m46.0s** (1st: 6m38.4s — ~±2% noise) |
| No-change | `{ time make -j2 all; }` | **1.05s** (0 compiles) |
| TU #1 incremental | touch `layout_inflater.cpp` → make | **11.98s** (1 TU + link) |
| TU #2 incremental | touch `android_shadows.cpp` → make | **16.23s** (1 TU + link) |
| Link-only | extracted link cmd timed alone | **0.98s** |

**Incremental-correctness proof:** the §5 regression faces were captured against binaries produced through these incremental rebuilds — all four byte-identical to the W21 recorded faces. Two representative runtime TUs benchmarked (11.98s / 16.23s); correctness preserved. Levers (ccache, `-g1` default, Makefile:273/289 duplicate recipe) remain PENDING, unmeasured.

## 8. Blockers / PENDING (honest)

- **PENDING per gate:** B1 (Compose snapshot), T2 (build efficiency levers), T3 (T4/B3 androidx-boundary family), T4 (itsfrz `APP_PIXELS`/NavHost chain, dicer `PFModelApplication.onCreate` crash).
- **rttt** needs the surface-pipeline chain (F-NEW-162 family) — out of B2's scope.
- **dicer**'s crash site is recorded but not root-caused this session.
- The full 52-test battery was NOT re-run this session (the correctness evidence is the byte-identical regression faces + the unchanged census behavior); the battery run is part of B2-3's regression plan.
- UNIFIED_011 version codes for rttt/freebloks/dicer were not pinned in older evidence; this session pins the current F-Droid publications with full SHAs.
