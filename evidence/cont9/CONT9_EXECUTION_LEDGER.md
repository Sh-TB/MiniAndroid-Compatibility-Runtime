# CONT-9 WAVE 5 EXECUTION LEDGER — Issue #379 (CONT-9 / WAVE 5)

HEAD: fda41b78f2535484fe654895c2ad9ceb737df3f1 (local; parent e3ae6a62 = CONT-8 W4 push record)
Binary: c0fa65ccc7f284e7 — clean source rebuild reproduced the frozen W3/W4 lineage byte-identically.
Dooz APK: upload/canonical_apks/io.github.yamin8000.dooz_23.apk
SHA-256: 299eab21ac8b3c6192edbd887966554fef84ad026d269b9067310215201b362b

## §0 — Phase 0 (HEAD / binary / APK truth)

- Issue #379 body consumed from the directive (GitHub API rate-limited, same as W4 — recorded honestly; the issue text is embedded in the directive).
- Engine rebuilt from source (container reset lost the binary); the rebuild reproduced the frozen W3/W4 binary byte-identically (`c0fa65ccc7f284e7`) — clean lineage proof.
- Registry F-NEW-256 (564 roots) present and verified in-tree; W4 evidence (evidence/cont8/*) reconciled before any change.
- dooz baseline ×1 full + x3 anchor: `d602648e8e401895` byte-identical, verdict `DEFAULT_BACKGROUND_ONLY`, 0 fatal / 6 recorded `La;` unwind errors — exactly the W4 state, zero drift.
- Fallback audit: **no F-NEW-260 hardcoded fallback exists in the current engine tree** (only doc-comments citing dooz as evidence for generic laws). This wave's dooz runs are fallback-free by construction.

## §B — F-NEW-256: first divergence re-proven (the wave's core)

1. **W4's refined face is REFUTED.** W4 claimed the change list applies mid-content-pass (trace line 43094 inside Ld;.i's "span" 31698..44545). `[METHOD-IN]` traces print entries only — Ld;.i has THREE entries (31695, 44543, 44660); W4 read entry#1..entry#2 as a span.
2. **Caller-frame proof** (new generic `MINIANDROID_CL_TRACE` diagnostic): the apply runs at **depth 16** under `Lt4;.setOnReadyForComposition → Ls7;.i → Lwo;.A(Lj90;) → Lfb1;.a → Lwo;.d → Lwo;.e(Lli;) → Lnb0;.z → Lli;.L → Ls21;.Y(o2809) → La21;.a → Ls21;.Y(o2874) → Ly11;.a`, while the content pass ran at **depth 44**. Different stacks ⇒ the apply runs AFTER the content lambda returns — upstream Compose order CONFIRMED, W4 face REFUTED.
3. **The change-list machinery is correct end-to-end**: records (`Lbo;.Q`) go into SlotWriter-owned per-group lists (o2874/o2878); the composition-level list (o2809) executes them lazily/nested at apply; the node factory runs at apply (`Lel0;.<init>` under `Ly11;.a`); the applier inserts (`Lv02;.f/.c → Lel0;.B`) correctly. Only ONE node insert exists because the app content recorded only ONE node emission (the composition root).
4. **App structure discovered**: dooz = **Compose + androidx.navigation.compose NavHost** (destination registration `Llo;.t(Lqx0;,String,Lom;)` → `Lpn;` entries; literal deep-link strings in `Lmx0;.a`; NavBackStackEntry ctor chain `Le; → Lir1; → Lnq; → Lne;` constructed in the post-apply LaunchedEffect coroutine — the same `Le;`-family the directive Phase 8 flags).
5. **REFINED FIRST DIVERGENCE**: the frame-driven recomposition pass (#2: `Lj9;.doFrame → Ldb1;.i → Lwo;.w → Lnb0;.n` at line 49187) ran 335 slot-table reader ops + 32 invalidation-group walks (`Lnb0;.o`) but invoked **ZERO ComposableLambdas** (`Lom;.h` = 0 in pass #2; all 6 whole-run entries are in pass #1). No invalidated scope was re-invoked ⇒ the NavHost destination content lambda never runs ⇒ the tree stays at root+1 node ⇒ dispatchDraw faithfully draws it ⇒ 0 content ops.
6. Repair surface: the **recompose-scope re-invocation chain** (invalidated-scope → scope-lambda invoke) — the generic blocker for every Compose app whose first content arrives via side effects (navigation, LaunchedEffect, produceState).

## §4/§8/§9 — directive Phase 4/8/9 evidence

- `La;` CancellationException cascade: happens at trace lines 6880-6900 — **SETUP phase, before composition** — unwinding `La7;.m → Lse1;.m → Let;.a` back to `Lat;.a` (the crash.log's 6 EXC-UNCAUGHT-TOP rows). It is NOT the composition/draw blocker; global suppression remains REFUTED as a fix (directive Phase 1A).
- `Le;` hierarchy (`Le; → Lir1; → Lnq; → Lne; → Object`): this is the **ctor delegation chain** of the nav/window setup family (Le; instances constructed during MainActivity.onCreate and in the nav coroutine), not a framework shadow corruption per se — recorded for the R8-identity work; no runtime receiver change made.

## §C — Regression battery (evidence/cont9/w5_regression_battery.json)

- Anchors 5/5 ×3 byte-identical (opencalc e364b001ee7abd66, chess b5a7a35d5fe0564b, dooz d602648e8e401895, microtimer da73010a37dd0189, unote 4f1a9e4e8f64fae8) — proves the wave's diagnostics are semantic-neutral.
- Six-game controls (§H: 3 of 6 independently re-run): 2048 `7ad9a8bdefba539b`, mini-tetris `26ccfce917c0e24c`, minicraft `ce27f331770f6979` — ALL match the recorded CONT-6 anchors ×3, REAL_APP_CONTENT. snake-deluxe/snake-neon/tictactoe-deluxe untouched this wave (zero semantic changes; recorded anchors stand).
- Gate A probe APK **rebuilt and restored** (`scripts/cont9_rebuild_gate_a_probe.sh`; aapt2+ECJ+D8+gcc; STORED assets per the W4 metadata lesson): **98 PASS / 0 FAIL / 1 INFO** (stricter than the recorded 97/0/2 — the real-load NAT rows now genuinely execute).
- Negatives **19/19**, reinstall **8/8**, skill **13/13** (restored from 1/13 by the probe rebuild), goldens **4/4** REAL_APP_CONTENT.
- FishRings: not re-run — zero engine semantic changes; the CONT-8 scheduling classification stands.

## §E — Compose fan-out

- The corpus currently contains exactly ONE Compose consumer (dooz). FairyMahjong/BlockBlast (other Compose-family APKs) were lost in the container reset (W4: ARTIFACT-LOST, re-supply pending). No independent Compose APK was available this wave — recorded honestly; the KB-derived acquisition item stays PENDING.

## §F/G — External KB

- Archive bytes ABSENT this container (unchanged since W3's honest record; re-supply contract in research/external-root-kb/current/MANIFEST.md). No SHA consumable at runtime; no bulk import performed (per directive §F). Phase clustering remains blocked on re-supply.

## Engine changes

- `MINIANDROID_CL_TRACE="Lcls;,...,Lcls;.meth,..."` — env-gated caller-frame trace (class prefixes + class;method tokens, 4 caller frames, bounded 8000 lines, read-only).
- `MINIANDROID_FIELD_TRACE` qualified form `"Lcls;.field"` — exact declaring-class + field-name filter (read-only).
- Both live in `dalvik_engine.cpp`'s method-entry region; no semantics touched (anchors byte-identical is the proof).

## Artifacts

- evidence/cont9/{CONT9_EXECUTION_LEDGER.md, fnew256_w5_refutation.json, w5_regression_battery.json}
- scripts/{cont9_dexdump.py, cont9_w5_trace_analyze.py, cont9_rebuild_gate_a_probe.sh}
- run/w5/* (8 trace runs + anchors + six-game runs) — bounded, reproducible
- gate_a_probe.apk restored at repo root (probe store regenerable)

## Remaining frontier (single highest-ROI root)

**Recompose-scope re-invocation in frame-driven recomposition passes** — the first generic semantic divergence between MiniAndroid and upstream Compose on the real-UI path. It blocks dooz's real content AND every future Compose app whose UI materializes after a side effect (the navigation/LaunchedEffect pattern = most of the Compose ecosystem).
