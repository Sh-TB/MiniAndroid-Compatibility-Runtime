# BASE-FIRST wave 1 report — Phase 0 lock + the two demanded verifications (Compose chain, 7 FULLY_VERIFIED audit)

Workflow used: READ LOCAL SOURCE → READ UPSTREAM SOURCE → VERIFY → TARGETED TEST (one battery) → RECORD. Full record: `evidence/cont19/CONT19_BASE_FIRST.md`. No code changes, no architecture changes this wave (verification-first, per the issue).

## Phase 0 — Base lock (recorded)

- HEAD `0b019608` (zero engine-source delta vs the regression-green CONT-18h); binary rebuilt in-container sha16 `b4937c81aba0998c`; build `timeout 570 make -j1 BUILD_DIR=build`; run `run <apk> --width 1080 --height 1920 --frames 5 --max-seconds 15`; capture `screenshot.png` + SHA-256.
- Working base at lock: **7 FULLY_VERIFIED** (re-proven below) + real-app anchors ×3 byte-identical (dooz, microtimer, unote, gmdice, opencalc, chess — all F-Droid) + WebView/HTML5 blockbuster (VISUALLY_VERIFIED; chrome renders, HTML5 canvas partial).
- Cross-container note: binary bytes differ from the recorded CONT-18h build on identical source, while **every screenshot anchor reproduces byte-identically** — anchors are the portable contract.

## Verification 1 — the claimed "full ~6K-line Compose runtime": **REJECTED as stated**

- The repo contains **no local Compose runtime**: no C++ SlotTable/Composer/Applier/ComposeNode/LayoutNode/Recomposer exists. Standing governing rule (campaign009 DO_NOT_REINVENT, rule 5): Compose classes live inside the APK DEX — interpret them, bridge the framework surface, never write a mini-Compose.
- The real local surface is a **host bridge** (ComposeView/AndroidComposeView/WrappedComposition shadow hosts + engine accommodations, ~330 Compose-referencing lines). The "~6K-line runtime" figure appears nowhere in the repository.

## Verification 2 — the real chain Composer → SlotTable → Applier → ComposeNode → LayoutNode → measure/layout/draw: **verified as the app's OWN DEX execution chain; earliest break is an engine law, not a Compose primitive**

Upstream law read from the dooz-pinned vendored sources (compose 1.11.4, `upstream/s43/`): `Composer.kt` (ComposerImpl coordinates slot-table state + Applier ops) and `Composables.kt:290-303` (ComposeNode: `startNode → inserting ? createNode(factory) : useNode → update → endNode`, applier-type-checked).

Runtime mapping (dooz v18, R8-obfuscated, identities proven against ui-1.11.4 in `evidence/cont11/CONT11_W7_DRAW_ROOT_CAUSE.md`):

| Chain stage | State | Runtime evidence |
|---|---|---|
| Composer / SlotTable writes | RUNS (partial) | composed nodes with real kindSets (o6325 kindSet=13 has Draw bit); invalidation holder Lqb0.<init> ran healthy ×2 (o3108/o3131) |
| Applier / ComposeNode | RUNS (partial) | LayoutNode instances composed; 89 isPlaced reads |
| measure/layout/place | **DIES** | measure-pass unwind (`Lzs;.m` depth=17); place-writers `Lbt0;.q0/.r0` = **0 executions** → isPlaced never flips |
| draw | **SKIPPED** | upstream gate `if(layoutNode.isPlaced) child.draw` skips content (child I()=FALSE) → CanvasDrawScope.draw `Lgl0;.c` = **0 invocations** in an 85,838-entry METHOD-TRACE → 0 canvas ops |
| **Earliest missing piece (engine-side)** | **F-NEW-271 (P0)** | `CompositionImpl` (Lnb0).S pc=185 reads `this.j` (:Lqb0) holding an **alien STRING_REF/0** — engine heap/field-state corruption; bytecode exonerated source-first |

So the historical "SlotTable/Composer/Applier/LayoutNode not implemented" conclusion is **SUPERSEDED**: those primitives already execute from the app's own classes. The first primitive actually missing is a **generic engine heap/field-identity law** (F-NEW-271) — a shared Base root under Phase 4, not Compose work. Next arms (already registered): heap-dump probe at the failing iget; R-NEW-414/F-NEW-251 field-key audit; Lnb0 ownership check.

## Verification 3 — the reported "7 FULLY_VERIFIED with no regression": **ACCEPTED, re-proven ×3 at the current binary**

One targeted battery (24 runs, documented §7 invocation, 1080×1920):

| Target | APK sha256-16 | Screenshot SHA-16 ×3 | Colors | Non-dom px | Verdict |
|---|---|---|---:|---:|---|
| 2048 | c933b5b821920875 | `59ca1526611c4622` | 236 | 1,175,625 | re-proven |
| tetris | 700a3dcf9a98b26e | `f360daa244cfca8d` | 259 | 1,144,478 | re-proven |
| snake_deluxe | 551eca798f88c1bb | `34a712689ce66e58` | 477 | 1,425,075 | re-proven |
| snakeneon | b36885c181a323ab | `cc986d4b4d3ec3f3` | 240 | 172,635 | re-proven |
| tictactoe_deluxe | d04d92eab8dbbb11 | `af6094295ecb50e3` | 761 | 1,071,286 | re-proven |
| minicraft | 77b9629ee111b968 | `b0876952f41e4af2` | 202 | 885,148 | re-proven |
| gmdice (real F-Droid) | 1621eda11b5dbc0c | `f3b483fe7b7cf51b` | 445 | 163,612 | re-proven |
| dooz (anchor, context) | 299eab21ac8b3c61 | `d602648e8e401895` | 1 | 0 | FRAME_CAPTURED (honest) |

Findings: (1) all seven claimed hashes reproduce **byte-identically ×3** — zero regression; (2) a local contradictory record (cont15's snakeneon `24fb7694eb64634a`) is settled **in favor of the reported claim** — the old record was the outlier, superseded; (3) provenance honesty: six of the seven are in-house `com.miniandroid.*` builds, so the *real-app* Base proof remains the F-Droid anchor corpus — this matters for Phase 1 selection below.

## Phase 1 — baseline selection (proposed, recorded)

Native game 1: 2048 (View/Canvas) · Native game 2: glxy (GLSurfaceView — different path) · Native app 1: opencalc · Native app 2: unote (filesystem/persistence) · HTML5/WebView: blockbuster · Boundary test (not a Base milestone): dooz. All APK sha256 + screenshot SHA records already in-repo; interaction/state-change proofs for the Phase 5 gate are next-wave targeted tap runs.

## Decision gate (Phase 7) — recommendation

Continuing the dooz frontier's next fix (F-NEW-271) **is** shared-Base work: the root is a generic heap/field-identity law, and the chain it unblocks exercises measure/layout/draw laws every View-based target shares. A C++ Compose implementation beyond what app DEX already executes remains unjustified by cross-app evidence. Order: F-NEW-271 arms → F-265 measure-pass completion → F-267 tap bridge, each with the focused regression set (anchors + this battery).