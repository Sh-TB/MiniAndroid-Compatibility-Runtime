# CONT-19 — BASE-FIRST wave 1: #383 verification + #382 final review

Directive: continue from Issue #383 (BASE-FIRST: Establish a Generic Graphical
Runtime Baseline) + its amendment (upstream-source-first investigation); final
review of Issue #382 (A1–A104 knowledge transfer) to wherever it went.

Head under test: `0b019608` (CONT-11 W7 evidence commit; zero engine-source delta
vs CONT-18h `33564067`). Binary: rebuilt this container → sha16
`b4937c81aba0998c` (binary bytes differ across containers — known toolchain
non-determinism; the behavior contract is the screenshot anchors, which are
byte-identical, see §3). Build: `cd miniandroid && timeout 570 make -j1
BUILD_DIR=build` (foreground; -j2 OOMs). Run: `./miniandroid/build/miniandroid
run <apk> --width 1080 --height 1920 --frames 5 --max-seconds 15 -o <dir>`.
Capture: `<out>/screenshot.png`, SHA-256 recorded.

## 1. #383 claim: "full ~6K-line Compose runtime" — REJECTED as stated

- The repository contains **NO local Compose runtime implementation**. There is
  no C++ SlotTable, Composer, Applier, ComposeNode, LayoutNode, or Recomposer.
  Governing rule already on record (docs/runtime/knowledge/campaign009/
  DO_NOT_REINVENT_009.md, rule 5): Compose classes live INSIDE the APK DEX —
  interpret them; bridge only the framework surface; never write a mini-Compose.
- The actual local Compose surface is a **host bridge**: ComposeView /
  AndroidComposeView / WrappedComposition shadow host views plus engine
  accommodations (~330 Compose-referencing lines across dalvik_engine.cpp,
  android_shadows.{cpp,h}, execution_engine.cpp, choreographer_shadow.h).
- The "~6K-line Compose runtime" figure appears **nowhere** in the repo
  (rg across docs/ + evidence/). If it refers to the host-bridge + accommodation
  surface, "runtime" is the wrong word; if it claims an implemented Compose
  runtime, it is unsubstantiated.

## 2. #383 claim: chain Composer → SlotTable → Applier → ComposeNode →
   LayoutNode → measure/layout/draw — verified as the app's OWN execution chain,
   with the earliest break being an ENGINE law, not a Compose primitive

Upstream law (vendored, dooz-pinned compose 1.11.4, `upstream/s43/`):
- `runtime/commonMain/androidx/compose/runtime/Composer.kt` — ComposerImpl
  coordinates slot-table state and Applier operations.
- `runtime/commonMain/androidx/compose/runtime/Composables.kt:290-303` —
  ComposeNode law verbatim: `if (currentComposer.applier !is E)
  invalidApplier(); currentComposer.startNode(); if (currentComposer.inserting)
  currentComposer.createNode(factory) else currentComposer.useNode();
  Updater<T>(currentComposer).update(); currentComposer.endNode()`.

Runtime mapping (dooz v18, R8-obfuscated; identities proven in
evidence/cont11/CONT11_W7_DRAW_ROOT_CAUSE.md against ui-1.11.4 sources):

| Chain stage | Executes? | Evidence |
|---|---|---|
| Composer / SlotTable writes | YES (partial) | composed nodes exist with real kindSets (o6325 kindSet=13 carries the Draw bit); `[TRI-F040] Lqb0;.<init>` (invalidation holder) ×2 healthy constructions |
| Applier ops / ComposeNode | YES (partial) | LayoutNode instances (Lbt0;) composed; 89 isPlaced reads |
| measure/layout/place | **DIES** | F-265: measure-pass death (`[EXC-UNWIND] La; unwound Lzs;.m … depth=17`); place-writers Lbt0;.q0/.r0 = **0 executions** → isPlaced never flips |
| draw | **SKIPPED** | InnerNodeCoordinator.performDraw upstream gate `if(layoutNode.isPlaced) child.draw` skips every content node (child I()=FALSE) → CanvasDrawScope.draw (Lgl0;.c) = **0 invocations** in an 85,838-entry METHOD-TRACE → 0 canvas ops |
| earliest engine-side break | **F-NEW-271** | composition-time: `Lnb0;.S` (CompositionImpl composeContent family) pc=185 reads `this.j` (:Lqb0 invalidation holder) which holds an **alien STRING_REF/0** — outside f141's null domain; bytecode exonerated (both Lqb0 constructions ran healthy o3108/o3131; Lqb0.<init> unconditionally iputs a fresh Lhv0 into e) |

Verdict: the historical A1–A50/A104 narrative "composition never materializes
because SlotTable/Composer/Applier/LayoutNode are not implemented" is
**SUPERSEDED BY EVIDENCE** — those primitives execute from the APK's own DEX.
The earliest evidence-backed missing piece is **F-NEW-271 (P0): an engine heap/
field-state corruption (alien STRING_REF/0 in a typed object field on o2838)** —
a generic interpreter/heap-identity law, exactly the kind of shared Base root
#383 Phase 4 prioritizes. Next arms already registered: heap-dump the failing
iget source; R-NEW-414/F-NEW-251 field-key audit for single-letter R8 fields;
Lnb0 ownership check.

## 3. #383 amendment: audit of the "7 FULLY_VERIFIED targets with no regression"

Battery (scripts/cont19_seven_target_battery.sh; §7 invocation; 1080×1920,
frames 5, 15 s; ×3 runs each; binary b4937c81aba0998c, head 0b019608):

| Target | APK sha256 (16) | Screenshot SHA-16 ×3 | vs A103 claim | Colors | Non-dom px |
|---|---|---|---|---:|---:|
| 2048 (g2048) | c933b5b821920875 | 59ca1526611c4622 ×3 | MATCH | 236 | 1,175,625 |
| tetris | 700a3dcf9a98b26e | f360daa244cfca8d ×3 | MATCH | 259 | 1,144,478 |
| snake_deluxe | 551eca798f88c1bb | 34a712689ce66e58 ×3 | MATCH | 477 | 1,425,075 |
| snakeneon | b36885c181a323ab | cc986d4b4d3ec3f3 ×3 | MATCH | 240 | 172,635 |
| tictactoe_deluxe | d04d92eab8dbbb11 | af6094295ecb50e3 ×3 | MATCH | 761 | 1,071,286 |
| minicraft | 77b9629ee111b968 | b0876952f41e4af2 ×3 | MATCH | 202 | 885,148 |
| gmdice (real F-Droid) | 1621eda11b5dbc0c | f3b483fe7b7cf51b ×3 | MATCH | 445 | 163,612 |
| dooz (anchor, context) | 299eab21ac8b3c61 | d602648e8e401895 ×3 | MATCH | 1 | 0 (FRAME_CAPTURED, honest) |

Findings:
1. **All seven A103 hash claims are RE-PROVEN byte-identical ×3 at the current
   binary** — "7 FULLY_VERIFIED with no regression" = ACCEPTED with fresh
   evidence. Full SHA-256s in run/cont19/battery/cont19_metrics.json.
2. **The snakeneon contradiction resolves in favor of A103**: the transfer
   claimed `cc986d4b4d3ec3f3 ×3`; evidence/cont15/sixgame_validation.json
   recorded `24fb7694eb64634a ×3`; the current-binary battery reproduces
   `cc986d4b4d3ec3f3 ×3`. The cont15 snakeneon row is the outlier
   (mis-provenanced record) — superseded.
3. Provenance honesty: six of the seven are in-house `com.miniandroid.*`
   builds; gmdice is the only third-party app in the set. The real-app Base
   proof is the anchor corpus (dooz, microtimer, unote, gmdice, opencalc,
   chess — all F-Droid, ×3 byte-identical at every regression wave). gmdice's
   re-proof here extends the anchor set into this container.
4. Cross-container binary bytes differ (`f882ca1832b955e3` recorded →
   `b4937c81aba0998c` rebuilt from identical source) while **every screenshot
   anchor is byte-identical** — re-confirming that behavior anchors, not binary
   SHA, are the portable contract (consistent with the CONT-18f zip-timestamp
   law).

## 4. #382 final review — where it went, and the closed audit

#382 has exactly two owner comments (the transfer + the ZIP). **No primary-
coder claim-by-claim audit was ever posted.** This wave closes that gap at
source level (all key A-items grepped at HEAD) + runtime level (battery §3):

| Claim | Verdict | Basis at HEAD |
|---|---|---|
| A1–A50 Compose setup narrative | PARTIAL (historical) → cause SUPERSEDED | host bridges exist (android_shadows.cpp:4088/5534/5615); "internals missing" contradicted by §2 |
| A51/A52 File null guards | PARTIAL / SUPERSEDED | no per-method guard at cited site; engine-wide f141 null-receiver law (F-270-hardened) now covers all shadow calls |
| A61 dialog get_or_create_node | ACCEPTED | dialog_shadow.cpp:97,103,130 |
| A62 in-process ZIP / no popen | ACCEPTED | dalvik_engine.cpp:4702,49387 (law comments); zero live popen calls |
| A64 Storage::package_data_dir | ACCEPTED | storage/data_root.h:78; dalvik_engine.cpp:27122 |
| A68 finish clears stale ViewTree | PARTIAL | mechanism now G07 `request_finish` cascade + F-NEW-174 finisher identity (android_shadows.cpp:4447); no direct content_view_id clear; stale-tree absence supported by reinstall matrix 8/8 |
| A91 Path-A-only onPostCreate | ACCEPTED (as historical PARTIAL) | superseded by A93 |
| A92 1080×1920 verification tooling | ACCEPTED | S92 law; battery §3 uses it |
| A93 onPostCreate Path B | ACCEPTED | `[A93-POSTCREATE]` marker at dalvik_engine.cpp:1993 |
| A94 Display.getWidth/getHeight + getDisplayInfo | REJECTED (absent at HEAD) | zero hits for the claimed patch in the current tree; only Resources.getDisplayMetrics law (dalvik_engine.cpp:38719). If a target needs it, re-implement as a new root |
| A95 ViewShadow pre-layout fallback | ACCEPTED | android_shadows.cpp:6158–6165 measured_right-first fallback |
| A101 HashMap.size counts entries | ACCEPTED (dual-route note) | CollectionShadow map size = map_entries + map_string_entries (android_shadows.cpp:1790–1793); stub-0 remains only in the no-registry bridge_to_api fallback (dalvik_engine.cpp:47482 — its own comment: NEVER reached when CollectionShadow handles the call) |
| A102 ArrayDeque/LinkedList gate | ACCEPTED | handles_class: LinkedList (android_shadows.h:2390), ArrayDeque (2464, LAW-D CONT-18) |
| A102-unresolved Map.keySet view class | PARTIAL — CARRIED | allocation/law comments at F-064 sites; no live repro this wave; minos stays FRAME_CAPTURED; do not promote |
| A103 seven-app three-run SHA256 | ACCEPTED — re-proven | §3 battery: 7/7 MATCH ×3 at current binary; snakeneon contradiction resolved for A103 |
| A104 dooz Compose boundary | PARTIAL → boundary re-proven, cause superseded | anchor d602648e8e401895 ×3 (1 color, FRAME_CAPTURED honest); cause = §2 chain (F-271/F-265), not "Compose not implemented" |
| A53–A60, A63, A65–A67, A69–A90, A96–A100 (48 ids) | SOURCE GAP (as instructed) | not individually described in the transfer; no invention |

Arithmetic reconciliation (#382 §4): **14 apps = the 13-row table + blockblast**
(com.sidhant.blockblast, FAILURE report evidence/diff366/root_a/
blockblast_com.sidhant.blockblast/report.md — the 5th FRAME_CAPTURED). Counts:
9 ACCEPTED, 6 PARTIAL, 1 REJECTED, 48 SOURCE GAP (of the individually
described set).

## 5. #383 Phase 0 — Base lock (no architecture changes made)

- HEAD/build/run/capture recorded (header above). Working examples recorded:
  7 FULLY_VERIFIED (§3) + real-app anchors ×3 (dooz, microtimer, unote, gmdice,
  opencalc, chess) + WebView/HTML5 blockbuster (VISUALLY_VERIFIED per #382 §4;
  WebView chrome renders, HTML5 canvas remains partial — Boundary 4).
- Reuse: all existing anchors/fcol/negative batteries were NOT rerun wholesale;
  only the targeted 7-target battery ran (amendment: "reuse their evidence").
- Registry unchanged this wave (580 roots; queue 256/324) — verification-only
  wave, zero engine source changes, zero regression risk by construction.

## 6. #383 Phase 1 — baseline selection proposal (recorded for next wave)

| Slot | Candidate | Rendering path | Reason |
|---|---|---|---|
| Native game 1 | 2048 (g2048) | View/Canvas draw ops | FULLY_VERIFIED ×3, real state/input proof pending re-run at gate |
| Native game 2 | glxy | GLSurfaceView (different lightweight path) | VISUALLY_VERIFIED 20,421 colors |
| Native app 1 | opencalc | View/GUI app | anchor ×3 |
| Native app 2 | unote (state/resources/files: notes) | View + filesystem/persistence | anchor ×3 |
| HTML5/WebView | blockbuster | WebView/HTML5 | existing WebView path evidence |
| Boundary test | dooz | Compose (DEX-interpreted) | research evidence; NOT a Base milestone |

All with APK sha256 + screenshot SHA-16 records already in the repo
(cont19_metrics.json + anchors). Interaction/state-change re-proofs for the
Phase 5 gate are the next-wave targeted runs (taps per §7 interaction command).

## 7. Decision gate (#383 Phase 7 answer)

The Dooz frontier's next fix (F-NEW-271) is a **generic heap/field-identity
law**, not a Compose port — continuing it is shared-Base work under Phase 4,
compatible with BASE-FIRST. Compose-specific implementation beyond what the
APK's own DEX already executes remains unjustified (no cross-app evidence that
a C++ Compose subset would unlock more corpus targets than fixing the generic
engine laws the chain already exercises). Recommended order: (1) F-NEW-271 arms
(heap-dump probe at the failing iget; R-NEW-414/F-NEW-251 field-key audit);
(2) F-265 measure-pass completion; (3) F-267 tap bridge — each with cross-target
regression (anchors + battery §3 as the reusable focused set).
