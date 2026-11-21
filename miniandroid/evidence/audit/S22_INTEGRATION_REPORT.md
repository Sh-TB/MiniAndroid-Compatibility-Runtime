# S22 MASTER RUNTIME INTEGRATION REPORT — issue mining, recovery, and the compose LocalContext provider law — 2026-11-21

**Start HEAD `4d35dd84` (verified == origin/main after a sandbox snapshot restore; the S21 commits are on main). Final HEAD: the S22 commit (2 source files + evidence + parsers). Host: 2 cores / 3 GB RAM / 6.3 GB disk / g++ 14.2.**

## 1. Baseline verification (PH0)

The sandbox recycled to a stale snapshot (local HEAD = `c5a1efa6` W23-D, build/ and apk_cache/ wiped, working tree polluted). Recovery: `git reset --hard origin/main` → `4d35dd84` (S21 present, gate change verified in-tree); the 4 target APKs re-downloaded from their original F-Droid release URLs (dooz 1,749,880 B; freebloks 5,831,028 B; rttt 23,386,246 B; dicer 2,901,531 B); handoff APKs re-copied; clean build 6m38–7m48.

## 2. Issue discovery map (the verified statuses this session)

| Issue | Contribution | S22 status (evidence, not title-based) |
|---|---|---|
| #612 | F-GLZ-3 GL ordering | **ALREADY_IN_MAIN — verified**: the implementation lives under F-GLSUB-1/GP583-GLES-009 naming in `ExecutionEngine::stage_gl_surfaces` (subclass-aware pump via `is_subclass_of(GLSurfaceView)`, ancestor-translation/scroll/clip geometry law, F-GLZ-1 safety net, called at `execution_engine.cpp:3449`). S21's "label not found" was a naming-only gap |
| #676 | F058 lifecycle chain | **ALREADY_IN_MAIN + reachable** (S21 verification stands; live fan-out observed) |
| #376/#690 | Wave-3 F-CSW-* | **PENDING** (repo-external content; API rate-limited) |
| #520/#521/#472 | Coder 7/9 ledger rows | **PARTIAL** — ledger remains the inventory; no rewrites |
| #484 | PF-2048/ViewPager | **PENDING** (APK not fetched this session) |
| #633/#634 | vector/animated drawables | **BLOCKED** (fixture + document-loader) |
| NEW (this session) | dooz compose chain | **ROOT NAMED at bytecode level + first provider law implemented** (below) |

## 3. Recovered/runtime findings (PHASE 2/3 chain map)

- **freebloks' real dependency is Compose, not GL**: its content view `o710 = ComposeView` (`setContentView` → `[F023-PARENTLINK] content view=710`); `Freebloks3DView extends GLSurfaceView` is created INSIDE the Compose interop and never materializes as a ViewShadow node — so the (working) GL pump cannot see it. The GL pump itself is verified working for direct GLSurfaceView subclasses (bouncy, F-GLSUB-1 evidence).
- **The dooz compose first-divergence chain (fully measured, bytecode-level)**:
  1. `AndroidComposeView.onMeasure` (DEX) calls the R8-mangled direct method `.z` at invoke_pc=24.
  2. `.z` = a MeasureSpec guard: `MeasureSpec.getMode` + `getSize` then `new IllegalStateException` + `throw` at pc=31 (decoded from the dex: 45 code units; scripts/dex_method_bytes.py).
  3. The thrown ISE carries the AOSP message **"CompositionLocal LocalContext not present"** ×25 per run (LF/v;.s ×4, LF/l;.R ×3, LF/A0;.a ×2, Ly1/j;.getValue, AndroidComposeView-related sites).
  4. The composition never installs the `LocalContext provides context` provider scope (AbstractComposeView.setContent law) — the accessor's default executes.
  5. The compose LayoutNode tree stays EMPTY (`isEmpty` on the R8-mangled TreeSet-backed walk) → `dispatched=YES ops=0` → blank face. freebloks' menu Compose is the same family.
  6. **Conclusion: the compose unlock = the CompositionLocalProvider scope model (B1-scale)** — not a gate, not a single local.

## 4. Implemented this session (2 source files)

1. **`src/dex/dalvik_interpreter.cpp` — the S22-LC-PROVIDE law**: at the interpreter's throw site, when the thrown exception carries the exact AOSP message "CompositionLocal LocalContext not present" and the method has no handler for it, the accessor RETURNS the runtime's current Activity object (`ActivityShadow::current_activity_id()`) — exactly what the provider would have installed. App-agnostic (keyed on the AOSP error string, never APK names); every substitution logged `[S22-LC-PROVIDE]`. **Measured: deterministic 1×/run in dooz ×3 (returns o120 = MainActivity); 0 fires in the 4 other targets (correct — they never reach that accessor); ALL faces byte-identical to golden. Honest label: PARTIAL — 1 of 25 sites (the catch-all-routed re-throws still abort the composition); the full fix is the provider-scope model.**
2. **`src/dex/dalvik_engine_core.cpp` — S22-WS2 diagnostic extension**: env-gated (`MINIANDROID_S21_CHAIN_DUMP=<class>`) one-time dump of the runtime-parsed declared method table of a queried class (ground truth for R8-minified resolution hunts; the dooz dump proved AndroidComposeView declares `dispatchDraw` (111 methods) — resolution is NOT the dooz blocker).

New tooling: `scripts/dex_method_bytes.py` (dex method bytecode decoder matching the runtime's DexMethodId model), `scripts/dex_methods.py` (method-table dumper).

## 5. Cross-APK matrix (PHASE 5) — 3-run evidence, original F-Droid APKs

| APK | rc ×3 | snapshot sha16 ×3 | census/status |
|---|---|---|---|
| dooz | 1,1,1 | `d602648e…` ×3 | APP_DRAW_OPS; LC law 1×/run; compose provider gap mapped |
| rttt | 1,1,1 | `b5a7a35d…` ×3 | surface-family branch (documented F-NEW-162) |
| freebloks | 1,1,1 | `b5a7a35d…` ×3 | ComposeView menu front; GL pump verified (needs compose interop) |
| dicer | 1,1,1 | r1 `31ffa499` (splash), r2/r3 `b5a7a35d` | cold/warm state difference preserved |
| itsfrz | 1,1,1 | `d55056a8…` ×3 | APP_PIXELS |
| HelloWorldToast | 1 | `acdd9f05…` | golden |
| notepad / randomix | 1 | `31ddd4d5…` | golden |
| chess-clock | 124 | `d602648e…` | golden (60s budget face) |

**Zero pixel regressions across the entire matrix.** One earlier itsfrz empty-snapshot was an artifact of the recycle wiping apk_cache (the file, not the runtime).

## 6. Regression battery (PHASE 6) — sequential batches (build+run+delete per test)

**10/10 law tests rc=0**: lifecycle, linear_layout (24/24), g10_layout (23/23), s98_text (21/21), gp583_gles (31/31), r25_dispatch_matrix (14/14), resource_core, input_pipeline, s98_scroll_transform, g11_ctor. The remaining ~42 tests of the 52-test battery did NOT run this session (5.8 GB of test binaries vs 6.3 GB disk with the build tree resident — sequential batching ran the 10 most law-critical; the exact list of unrun tests is the Makefile TEST_CORE/TEST_LAW set minus the above). Not claimed as a full-battery pass.

## 7. Build-time comparison (this host, this tree)

no-change 13.5s (S21, objects survived recycle) | 1-TU 24.8–37.1s | clean 6m38–7m48 (2 runs) | law-test batch builds ~40–60s each | ccache absent (no package access) | test-binary disk cost 5.8 GB (the battery constraint).

## 8. Remaining blockers (exact)

1. **CompositionLocalProvider scope model** (B1-scale): installs LocalContext/LocalLifecycleOwner/LocalSavedStateRegistryOwner/LocalDensity around the compose content — THE compose unlock for dooz AND freebloks' menu. Evidence chain complete (§3).
2. F-GLZ-3 label reconciliation / F-CSW-* verification needs repo-external issue content.
3. 5.7–6.3 GB disk < 5.8 GB full battery; ccache unavailable.
4. #633 fixture, #634 document-loader — unchanged BLOCKED.

## 9. Delivery

Commits pushed to origin/main; report archived `evidence/audit/S22_INTEGRATION_REPORT.md`; #635 updated with the evidence comment. Honest success statement: S22 names the dooz/freebloks compose frontier at bytecode level, implements the first AOSP provider-law emulation with zero regressions across 8 APKs and 10 law batteries, and verifies F-GLZ-3/F058 as ALREADY_IN_MAIN — while stating plainly that the compose faces require the provider-scope model (the next mission's centerpiece).
