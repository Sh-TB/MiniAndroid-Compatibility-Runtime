# A1–A104 Knowledge Transfer: Runtime Findings, Visual Proof, and Review Checklist

> **Purpose:** Transfer the complete knowledge package from the previous investigator to the primary coder. This is NOT a request to start the investigation from zero and NOT permission to rewrite or replace the previous work. The primary coder must first inspect the source, commits, existing evidence, screenshots, and reproduction instructions; then mark each claim ACCEPTED, REJECTED, PARTIAL, or UNVERIFIED with reasons. Re-run tests only where source/evidence review cannot establish the claim or where a claim explicitly requires runtime reproduction.

## Persistent knowledge file

The full current audit ledger and review instructions are also committed in the repository so the coder can read them without relying on issue rendering: [`docs/knowledge-transfer/A1_A104_PRIMARY_CODER_AUDIT.md`](https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/blob/main/docs/knowledge-transfer/A1_A104_PRIMARY_CODER_AUDIT.md) (commit `862ec6297fcae624f4891b14e947d5e1ad84b936`). This file mirrors the current Issue audit body; it is **not** the original ZIP archive.

## 1. Mandatory instructions for the primary coder

- Read `CONSTITUTION_V2.md` first, then `docs/S92_GRAPHICS_VERIFICATION.md`.
- Review this knowledge transfer as prior work to audit, not as an untrusted list to discard and rebuild from scratch.
- For each numbered claim in this Issue, mark one: **[ ] ACCEPTED FROM SOURCE/EVIDENCE  [ ] REJECTED  [ ] PARTIAL  [ ] NEEDS REPRODUCTION**.
- Every decision must include: **reason, source file/function/line, existing evidence inspected, and next action**.
- Do not blindly accept the previous investigator's conclusions. Equally, do not blindly reject them or repeat all tests from zero. Check existing commits, traces, screenshots, hashes, ViewTree evidence and test artifacts first.
- If source and evidence already prove a claim, mark it accepted and cite them. If only a hypothesis, label it PARTIAL/NEEDS REPRODUCTION.
- Keep the original results and historical status. Do not silently rewrite history or promote an app based on an old binary.
- Do not make broad architecture changes or start a multi-week feature implementation as part of this review. This is primarily a **source/evidence review and claim-verification task**.
- Do not close an app's visual failure because its APK loads, lifecycle callbacks fire, a ViewTree exists, a test passes, or a PNG exists.
- If a claim is rejected, explain exactly why and what evidence contradicts it. If the source hint/line differs, record the actual location.
- Update this issue claim-by-claim. At the end, report counts of ACCEPTED, REJECTED, PARTIAL, and NEEDS REPRODUCTION, plus the remaining actual blockers.

## 2. Essential visual-verification law: S92 Verification Ladder

Use these verdicts exactly and do not promote an app without evidence:

- `UNEXECUTED` — no screenshot produced.
- `LOADED` — APK parsed, nothing more.
- `LIFECYCLE_VERIFIED` — onCreate/onStart/onResume dispatched.
- `RENDER_STARTED` — renderer initialized.
- `FRAME_CAPTURED` — screenshot exists but is flat/single-color.
- `VISUALLY_PARTIAL` — few colors, likely only background or incomplete content.
- `VISUALLY_VERIFIED` — multiple colors and real app content.
- `INTERACTION_VERIFIED` — tap dispatched and app state visibly changed.
- `FULLY_VERIFIED` — interaction proof plus three byte-identical runs.

Non-negotiable rules:
1. A screenshot existing does not mean graphics loaded. A flat one-color PNG is FRAME_CAPTURED, not VISUALLY_VERIFIED.
2. A callback firing does not prove interaction. Prove pixel/state change.
3. A ViewTree existing does not prove graphics correctness. Pixels are the truth.
4. Use 1080×1920 by default because the runtime uses density 2.0. At 540×960, glyphs may be drawn outside the framebuffer (reported y=1156 when framebuffer height is 960).
5. The source document reports a CLI resolution correction that changed gmdice from 1 to 113 unique colors and glxy from 1 to 20,421 unique colors.
6. FULLY_VERIFIED requires three runs with byte-identical screenshot SHA256 values.
7. Fresh evidence is required for a changed binary. Never carry old screenshot/test evidence forward to a new binary.
8. Never invent AOSP semantics. If the contract is unknown, preserve UNKNOWN until verified.

Reported classification heuristic in the transferred material:
```python
if unique_colors <= 1:
    verdict = "FRAME_CAPTURED"
elif unique_colors <= 3:
    verdict = "VISUALLY_PARTIAL"
elif unique_colors >= 8 and non_dominant_pixels >= 1000:
    verdict = "VISUALLY_VERIFIED"
```
Check this heuristic against the project's actual S92 law before changing it; do not silently replace the law.

## 3. A1–A104 patch history and findings to audit

### A1–A50: Compose setup (dooz focus)
- Created ComposeView, AndroidComposeView, WrappedComposition.
- Created internal Compose classes c1 and N/a.
- Called LF/A0.a() (Compose setContent).
- Reported outcome: composition did not materialize because SlotTable, Composer, Applier, and LayoutNode were not implemented.
- Treat this as historical implementation context, not proof that Compose now works.

### A51–A52: File null receiver guards
- Reported bug: File.getName() / File.getAbsolutePath() called on a null receiver.
- Reported fix: null-receiver guards in File shadow methods.
- Review the actual source and commit before accepting the fix claim.

### A61: dialog_shadow.cpp null dereference
- Reported bug: `find_node(row_id)->children.push_back(...)` when find_node returned null.
- Reported fix: call `get_or_create_node(row_id)` before accessing children.

### A62: shell injection through popen
- Reported bug: shell command assembled with APK path in `popen("unzip -p '" + apk_path + "'...")`.
- Reported fix: replaced shell execution with an in-process ZIP parser.
- Confirm the current code no longer sends untrusted APK paths through a shell.

### A64: hard-coded /tmp path
- Reported bug: default File path hard-coded to `/tmp/miniandroid/files`.
- Reported fix: use `Storage::package_data_dir()`.

### A68: stale ViewTree after finish()
- Reported bug: Activity.finish() did not clear content_view_id, so renderer kept drawing an old ViewTree.
- Reported fix: clear content_view_id after finish(), reported in `execution_engine.cpp` around line 7490.

### A91: onPostCreate dispatch (PARTIAL / wrong path)
- Reported issue: games such as minos create GameView in onPostCreate, not onCreate.
- Initial patch put onPostCreate dispatch in Path A (multi-DEX index lookup, around line 2083), not Path B (single-DEX around line 1814).
- This patch did not cover most single-DEX apps.

### A92: framebuffer resolution mismatch (verification-tooling fix; no source change)
- Reported issue: 540×960 framebuffer with density 2.0 clipped glyphs outside the framebuffer.
- Required default: `--width 1080 --height 1920`.
- Reported effect: gmdice 1→113 unique colors; glxy 1→20,421 unique colors.
- Review the screenshots and actual invocation evidence before accepting those promotions.

### A93: onPostCreate dispatch in Path B
- Reported fix: add dispatch in the single-DEX Path B too, between onActivityCreated and onActivityPostCreated.
- File: `miniandroid/src/dex/dalvik_engine.cpp`, reported around line 1864; log marker `[A93-POSTCREATE]`.
- Reported effect: minos reaches createGame(); IMPLEMENTED API count rose from 137 to 256.

### A94: Display.getWidth/getHeight
- Reported issue: minos DisplayUtils.getDisplaySize called missing Display.getWidth/getHeight; zero dimensions caused empty maze dimensions and Random.nextInt(0).
- Reported fix: stubs return 1080/1920, consistent with existing getMetrics/getSize device profile; also added Display.getDisplayInfo safety net.
- File: `miniandroid/src/dex/dalvik_engine.cpp`, reported around line 35665.

### A95: View.getWidth/getHeight before layout
- Reported issue: View.post() runnables queued during onCreate drain before the first traversal/layout. GameView constructor read container width=0, producing zero cell size and zero maze dimensions.
- Reported fallback order:
  1. measured_right - measured_left if positive;
  2. measured_width if positive;
  3. if width == -1 (MATCH_PARENT), parent's measured_width or screen width (1080);
  4. explicit positive width;
  5. otherwise zero.
- File: `miniandroid/src/framework/android_shadows.cpp`, reported around line 4330.
- Reported effect: minos container 1080×1920, cols=6, rows=10, cellSize=180; IMPLEMENTED APIs rose from 262 to 688.

### A101: HashMap.size() always returned zero
- Reported bug: HashMap.size() was a stub returning zero regardless of entries.
- Reported fix: count real `key_`-prefixed fields in the heap object, excluding `__` internal fields.
- File: `miniandroid/src/dex/dalvik_engine.cpp`, reported around line 44238.
- Primary coder must inspect how this interacts with the actual HashMap storage/dispatch path.

### A102: ArrayDeque/LinkedList omitted from collection class-name gate
- Reported bug: ArrayList handler recognized ArrayList/List-like names but missed ArrayDeque and LinkedList; minos uses ArrayDeque for maze cells.
- Reported fix: add ArrayDeque and LinkedList to the handler gate around line 44793 in `miniandroid/src/dex/dalvik_engine.cpp`.
- The source document includes this implementation sketch:
```cpp
if (class_name == "Ljava/util/ArrayList;" ||
    class_name.find("ArrayList") != std::string::npos ||
    class_name.find("List;") != std::string::npos ||
    class_name == "Ljava/util/ArrayDeque;" ||
    class_name.find("ArrayDeque") != std::string::npos ||
    class_name == "Ljava/util/LinkedList;" ||
    class_name.find("LinkedList") != std::string::npos) {
```
- Verify the actual committed implementation and ensure dispatch does not shadow or misclassify other collection classes.

### A102 investigation: Map.keySet returns a view with the wrong class (OBSERVED / NOT FIXED)
- Reported observation: `CollectionShadow::dispatch` F-064, around line 1036 of `android_shadows.cpp`, creates a HashSet view with view_elements copied from map entries.
- It allocates `Ljava/util/HashSet;`, but later the receiver's class_descriptor is reported as `Ljava/util/ArrayList;`.
- hasNext then checks `state->view_elements`, which is empty for the ArrayList-classed object.
- Reported downstream chain: minos MazeFactory.getUnvisitedNeighbours returns an empty collection; Random.nextInt(0) throws IllegalArgumentException; zero pixels.
- Status in source package: deep shadow-dispatch bug observed, not fixed. Do not promote minos based on A102's collection-gate fix.
- Candidate explanations in source package: heap object ID reuse or iterator handler around line 914 returning the wrong class. These are hypotheses, not established facts.

### A103: three-run repeatability verification
- Reported method: run each of seven INTERACTION_VERIFIED apps three times at 1080×1920, frames=5, max-seconds=15, and compare SHA256 of screenshot.png.
- Reported result: all seven produced byte-identical screenshots across all three runs; together with interaction proof, promoted to FULLY_VERIFIED.
- Apps reported: 2048, snake_deluxe, tetris, tictactoe_deluxe, minicraft, snakeneon, gmdice.
- Primary coder should inspect existing hash records and binary identity first; rerun only if evidence is missing, stale, or tied to a different binary.

### A104: dooz (TicTacToe) — Compose Navigation boundary
- APK: io.github.yamin8000.dooz v18.
- SHA256 reported: `d81292cd346dcb23b04488bca400ca95af0f6eaa4aefefd31f847fe535cbdc17`.
- Reported execution: 20,166 IMPLEMENTED APIs; 253 STUBBED; 0 MISSING; 0 ERROR.
- ViewTree: ComposeView → AndroidComposeView, 0 children, 0 draw ops.
- Screenshot: one unique color, RGB (250,250,250), white background.
- Reported cause: NavHost calls addNavigator("composable", ComposableNavigator()) during composition, but composition never materializes because Compose runtime internals are missing: SlotTable, Composer, Applier, LayoutNode.
- Reported error: could not find Navigator with name "composable".
- Honest verdict: FRAME_CAPTURED, not visually verified. The transferred material estimates full Compose runtime as WAVE 8 / multi-week work. The coder's task here is to verify this boundary and evidence, not to begin implementing Compose.

## 4. Final reported verification state at A104

These are transferred claims to audit, not automatically accepted facts:

| App | Reported verdict | Unique colors | Tap pixel change | Reported 3-run SHA prefix |
|---|---|---:|---:|---|
| 2048 | FULLY_VERIFIED | 81 | 14.32% at UP button | 59ca1526611c4622 ×3 |
| snake_deluxe | FULLY_VERIFIED | 132 | 0.81% at START button | 34a712689ce66e58 ×3 |
| tetris | FULLY_VERIFIED | 135 | 1.85% at START button | f360daa244cfca8d ×3 |
| tictactoe_deluxe | FULLY_VERIFIED | 227 | 1.76% at button 5 | af6094295ecb50e3 ×3 |
| minicraft | FULLY_VERIFIED | 128 | 0.20% at UP button | b0876952f41e4af2 ×3 |
| snakeneon | FULLY_VERIFIED | 61 | 0.91% at UP button | cc986d4b4d3ec3f3 ×3 |
| gmdice | FULLY_VERIFIED | 113 | 0.81% at 3D20 button | f3b483fe7b7cf51b ×3 |
| blockbuster | VISUALLY_VERIFIED | 83 | n/a (WebView) | — |
| glxy | VISUALLY_VERIFIED | 20,421 | n/a (GLSurfaceView) | — |
| dooz | FRAME_CAPTURED | 1 | n/a | — |
| minos | FRAME_CAPTURED | 1 | n/a | — |
| bullseye | FRAME_CAPTURED | 1 | n/a | — |
| battleship | FRAME_CAPTURED | 1 | n/a | — |

Reported total: 7 FULLY_VERIFIED + 2 VISUALLY_VERIFIED + 4 FRAME_CAPTURED = 13 apps. **The source document elsewhere says “5 FRAME_CAPTURED” and “14 apps”; this arithmetic/list discrepancy must be explicitly reconciled by inspecting the actual artifacts. Do not silently fix the report or choose one number without evidence.**

## 5. Known boundaries / next technical work (not authorization to start coding immediately)

### Boundary 1: Compose runtime internals — WAVE 8
Affected: dooz, battleship, other Jetpack Compose apps.
Missing internals listed: SlotTable, Composer, Applier, LayoutNode. AndroidComposeView.dispatchDraw reportedly has zero draw operations and composition never materializes.
Proposed future approach: port/implement the needed behavior from AOSP androidx.compose.runtime and androidx.compose.ui sources. This is a substantial project; first verify the current boundary and evidence.

### Boundary 2: AppCompat setContentView(int) inflation
Affected: bullseye.
Reported cause: AppCompatDelegateImpl.setContentView(resId) inflates XML (52 views reported), but the inflated root is not attached as a child of ContentFrameLayout.
Reported ViewTree: FitWindowsLinearLayout → ViewStubCompat + ContentFrameLayout (0 children).
Proposed investigation: trace AppCompatDelegateImpl.setContentView → LayoutInflater.inflate and verify the inflated root is attached to contentParent.

### Boundary 3: Map.keySet view class / iterator bug
Affected: minos.
Reported chain: HashSet view allocated; later receiver class descriptor becomes ArrayList; hasNext checks an empty view_elements state; empty neighbours cause Random.nextInt(0) and zero pixels.
Investigate why class_descriptor changes and trace object identity through keySet, iterator, hasNext and next. The suggestion that heap object ID reuse or the iterator handler is responsible is a hypothesis.

### Boundary 4: WebView HTML5/JS pipeline — WAVE 10+
Affected: blockbuster (partial).
Reported state: WebView chrome renders but HTML5 game canvas does not. QuickJS exists, but DOM/JS/Canvas pipeline remains partial.
Future work: complete WebView HTML5/Canvas rendering pipeline after verifying the current state.

## 6. Architecture map and source-reading order

1. `CONSTITUTION_V2.md` — engineering laws; read first.
2. `docs/S92_GRAPHICS_VERIFICATION.md` — graphics verification ladder.
3. `miniandroid/src/dex/dalvik_engine.cpp` — main interpreter; start at `execute_apk_with_activity` around line 1556.
4. `miniandroid/src/framework/android_shadows.cpp` — shadow layer; start at `CollectionShadow::dispatch` around line 263.
5. `miniandroid/src/runtime/execution_engine.cpp` — render traversal; start at `stage_render_frame`.
6. `root_registry.json` — source document reports 540 catalogued root causes.
7. `miniandroid/APK_REGISTRY.json` — source document reports 22 test APKs.

Architecture concepts from the transferred material:
- `try_recursive_invoke(class, method, args, ...)`: tries DEX bytecode then falls back to bridge_to_api.
- `bridge_to_api(class_name, method, args, ...)`: framework API bridge/stub layer.
- `try_shadow_dispatch(class_name, method, ...)`: dispatches to shadow classes such as CollectionShadow, ViewShadow, ActivityShadow.
- `throw_deferred(exc_class, message, ...)`: sets pending_exception_ and redirects to catch handler or unwinds frame.
- Shadows: ActivityShadow (lifecycle/content), ViewShadow (tree/measure/layout/draw/getWidth/getHeight), CanvasShadow (draw-op recording), CollectionShadow (List/Map/Set), HandlerShadow (Handler/Looper), TouchDispatcher.
- Render traversal: attach wave → measure → layout → draw-op recording → pixel copy to framebuffer.
- Heap objects have object_id, class_descriptor, and fields; DalvikValue may be INT32, FLOAT, OBJECT_REF, STRING_REF, CLASS_REF, BOOLEAN, etc.
- APK registry catalogs test APKs and stores metadata; APKs must not be committed to the repository (zero-APK policy); APKs live in external cache.

## 7. Reproduction commands from the transferred document

Build:
```bash
cd miniandroid
make -j 1
```

Run a target APK at the correct default resolution:
```bash
./miniandroid/build/miniandroid run <apk_path> \
  --width 1080 --height 1920 \
  --frames 5 --max-seconds 15 \
  -o /tmp/verify_<app>
sha256sum /tmp/verify_<app>/screenshot.png
```

Three-run repeatability:
```bash
for run in 1 2 3; do
  ./miniandroid/build/miniandroid run <apk_path> \
    --width 1080 --height 1920 \
    --frames 5 --max-seconds 15 \
    -o /tmp/repeat_${run}
  sha256sum /tmp/repeat_${run}/screenshot.png
done
```
For FULLY_VERIFIED, all three SHA256 hashes must be identical and interaction evidence must also exist.

Interaction test:
```bash
./miniandroid/build/miniandroid run <apk_path> \
  --width 1080 --height 1920 \
  --frames 15 --max-seconds 30 \
  --tap <x>,<y>@<frame> \
  -o /tmp/tap_test
```
Inspect the actual tap-dispatch marker and compare pre-tap/post-tap pixels. Do not accept callback logs alone.

The original document lists APK paths from a prior investigator's environment under `/home/z/my-project/upload/`, `/home/z/my-project/games_test/apks/`, and `apk_cache/`. These paths may not exist in the primary coder's environment; do not assume they do. Check the registry/cache and preserve the zero-APK repository policy.

## 8. Common pitfalls learned from the campaign

1. Always use 1080×1920 by default with density 2.0; wrong framebuffer size can create misleading flat screenshots.
2. HashMap.size must count actual entries, not return a fixed zero.
3. Collection dispatch gates must include actual collection implementations, but avoid broad gates that accidentally misclassify classes.
4. Shadow view objects must preserve the class they were allocated with; the keySet view class mismatch remains a reported bug.
5. onPostCreate dispatch must exist in both multi-DEX Path A and single-DEX Path B.
6. View.getWidth during pre-layout Runnables can be zero; inspect the measured-size/MATCH_PARENT fallback against the intended law.
7. Reproducible pixel-level proof is stronger than a successful exit code.
8. Three byte-identical runs are mandatory for FULLY_VERIFIED.
9. New binary means new evidence; stale screenshots are not proof for a new build.
10. Never invent API semantics; unknown remains unknown.

## 9. Screenshots and visual artifacts supplied with this transfer

The source ZIP contains:
- `screenshots_v4/FINAL_MOSAIC.png`
- `screenshots_v4/2048.png`
- `screenshots_v4/snake_deluxe.png`
- `screenshots_v4/tetris.png`
- `screenshots_v4/tictactoe_deluxe.png`
- `screenshots_v4/minicraft.png`
- `screenshots_v4/snakeneon.png`
- `screenshots_v4/dooz.png`

The source document additionally refers to prior-environment artifacts:
- `/home/z/my-project/download/screenshots_v4/FINAL_MOSAIC_FULLY_VERIFIED.png`
- `/home/z/my-project/download/screenshots_final/INTERACTION_PROOF.png`
- `/home/z/my-project/download/screenshots_v4/REPEATABILITY_PROOF.md`
- `/home/z/my-project/download/screenshots_final/` before/after tap pairs
- `/home/z/my-project/download/repeatability/` SHA stamps

The ZIP's screenshots are not automatically attached to this GitHub Issue by this action. The primary coder must inspect the supplied source package/screenshots available to them, compare them with current binary provenance, and attach or link the actual image files in GitHub if the repository workflow supports it. Do not claim that images are attached to this Issue unless the GitHub UI confirms that they are.

## 10. Reported next-step sequence (A105 onward)

These are candidate work items, but first verify their source/evidence and report acceptance/rejection:
- **A105:** investigate/fix Map.keySet view class bug; trace class_descriptor/object ID from keySet through iterator/hasNext/next.
- **A106:** investigate/fix AppCompat setContentView(int) inflation; prove root is attached to ContentFrameLayout.
- **A107+:** Compose runtime internals (SlotTable, Composer, Applier, LayoutNode); major WAVE 8 effort.
- **A108+:** complete WebView HTML5/JS/Canvas pipeline for blockbuster.

## 11. Claim-by-claim review checklist

For every claim above and every specific result in the knowledge transfer, add/update a record in the comments using this format:

```text
Claim/section:
Decision: ACCEPTED FROM SOURCE/EVIDENCE / REJECTED / PARTIAL / NEEDS REPRODUCTION
Source: file :: function/class :: line(s)
Existing evidence inspected: commit / trace / screenshot / hash / ViewTree / test
Reason:
Does this require a new runtime test? YES/NO
If YES, why is existing source/evidence insufficient?
Next action:
Reviewer:
```

Prioritize **source inspection and existing evidence review first**. Do not rerun every app from scratch unless evidence is absent, stale, contradictory, or does not identify the binary. Any new run must record commit/build identity, APK SHA, command, runtime trace, screenshot SHA, unique-color/non-dominant-pixel metrics, ViewTree/provenance, and interaction pixel diff where applicable.

## 12. Required final audit report

- Claims accepted from source/evidence:
- Claims rejected (with reasons):
- Claims partially supported:
- Claims requiring targeted reproduction:
- Any source/evidence contradictions:
- Verified screenshot/image artifacts and their exact locations:
- Binary/commit provenance for each visual verdict:
- Corrected app-count arithmetic:
- Confirmed A105/A106 root cause(s), if already provable from source:
- Remaining blockers:
- Next smallest, highest-value verification step:

**Do not say “all verified” or “fixed” unless the exact claims, source locations, and existing or new evidence justify it. The task is to transfer and audit the previous investigator's knowledge—not to discard it and restart.**
---

# ADDENDUM: PRIMARY CODER MUST AUDIT, NOT REPEAT THE INVESTIGATION

## A. What this task is (and is not)

This is a knowledge-transfer audit. The previous investigator already supplied a technical path, candidate fixes, exact source locations for several changes, runtime results, screenshots, and verification commands. The primary coder must reuse that work first.

**Do not start 104 experiments from scratch. Do not implement A105+ features in this audit. Do not rerun all apps by default.** Start with the cheapest high-confidence checks:
1. Read the transferred knowledge and project laws.
2. Inspect current git log and commit diffs for the listed A-items.
3. Confirm whether the cited code is present at the cited locations (line numbers may have moved).
4. Check whether existing screenshots, SHA records, test results, and binary identity are already available.
5. Mark claims ACCEPTED / REJECTED / PARTIAL / NEEDS REPRODUCTION / SOURCE GAP.
6. Run only the small number of tests needed to settle material uncertainty or stale/missing evidence.

For each decision, record the exact changed file/function/line or commit diff, evidence inspected, and a short reason. If source confirms a patch and existing regression/evidence proves it, do not rerun it just to repeat the work. If source confirms a patch but behavior is unproven, mark PARTIAL and name the smallest confirming test.

## B. Source-backed patch locations already supplied

| A-item | Reported change | Reported source location | Minimum audit action |
|---|---|---|---|
| A51–A52 | File.getName / File.getAbsolutePath null receiver guards | File shadow methods; exact line not supplied | Inspect current methods and relevant diff; no broad test suite |
| A61 | dialog shadow null dereference fixed with get_or_create_node | dialog_shadow.cpp; exact line not supplied | Inspect diff and guard |
| A62 | Shell injection removed; in-process ZIP parser replaces popen/unzip | APK ZIP reading code; exact line not supplied | Inspect diff and confirm no shell interpolation remains |
| A64 | package-specific storage path replaces hard-coded /tmp path | Storage::package_data_dir() | Inspect diff/call site |
| A68 | Clear content_view_id after Activity.finish() | execution_engine.cpp ~7490 | Inspect finish path and existing test/log |
| A91 | onPostCreate added to Path A only; PARTIAL | dalvik_engine.cpp ~2083 | Confirm why Path B was missed; preserve historical partial status |
| A92 | 1080×1920 verification invocation; no source change | CLI/test commands | Inspect old command + pixel metrics; do not call this a code patch |
| A93 | onPostCreate added to Path B | dalvik_engine.cpp ~1864; [A93-POSTCREATE] | Inspect dispatch ordering and existing minos evidence |
| A94 | Display.getWidth/getHeight and Display.getDisplayInfo | dalvik_engine.cpp ~35665 | Inspect return values against device-profile law |
| A95 | pre-layout View.getWidth/getHeight fallback | android_shadows.cpp ~4330 | Inspect fallback ordering and existing minos dimensions |
| A101 | HashMap.size counts actual key_ fields, excluding __ internals | dalvik_engine.cpp ~44238 | Inspect storage representation and implementation |
| A102 | ArrayDeque/LinkedList added to collection class gate | dalvik_engine.cpp ~44793 | Inspect gate/diff; do not confuse with separate keySet bug |
| A102 unresolved subfinding | Map.keySet view allocated as HashSet but class_descriptor later observed as ArrayList | android_shadows.cpp F-064 ~1036; iterator handler candidate ~914 | Inspect existing trace/object identity; do not call this fixed |
| A103 | Three-run SHA256 repeatability for seven apps | Existing repeatability records/screenshots | Check hashes and binary identity first; rerun only if missing/stale |
| A104 | dooz Compose Navigation boundary | dooz_problems.md and screenshots_v4 | Inspect screenshot/ViewTree/report; do not implement Compose here |

## C. Full sequential A1–A104 ledger

Use this ledger to ensure no number is skipped. An undocumented A-number is not permission to invent a patch or spend hours rediscovering it. Search commit history/worklogs briefly; if the supplied package does not describe it and history does not recover it, mark SOURCE GAP/BLOCKED and move on.

1. [ ] **A1** — Grouped A1–A50 Compose runtime setup. The supplied source document does not provide an individual description/diff for this A-number; inspect existing history only, do not recreate the work.
2. [ ] **A2** — Grouped A1–A50 Compose runtime setup. The supplied source document does not provide an individual description/diff for this A-number; inspect existing history only, do not recreate the work.
3. [ ] **A3** — Grouped A1–A50 Compose runtime setup. The supplied source document does not provide an individual description/diff for this A-number; inspect existing history only, do not recreate the work.
4. [ ] **A4** — Grouped A1–A50 Compose runtime setup. The supplied source document does not provide an individual description/diff for this A-number; inspect existing history only, do not recreate the work.
5. [ ] **A5** — Grouped A1–A50 Compose runtime setup. The supplied source document does not provide an individual description/diff for this A-number; inspect existing history only, do not recreate the work.
6. [ ] **A6** — Grouped A1–A50 Compose runtime setup. The supplied source document does not provide an individual description/diff for this A-number; inspect existing history only, do not recreate the work.
7. [ ] **A7** — Grouped A1–A50 Compose runtime setup. The supplied source document does not provide an individual description/diff for this A-number; inspect existing history only, do not recreate the work.
8. [ ] **A8** — Grouped A1–A50 Compose runtime setup. The supplied source document does not provide an individual description/diff for this A-number; inspect existing history only, do not recreate the work.
9. [ ] **A9** — Grouped A1–A50 Compose runtime setup. The supplied source document does not provide an individual description/diff for this A-number; inspect existing history only, do not recreate the work.
10. [ ] **A10** — Grouped A1–A50 Compose runtime setup. The supplied source document does not provide an individual description/diff for this A-number; inspect existing history only, do not recreate the work.
11. [ ] **A11** — Grouped A1–A50 Compose runtime setup. The supplied source document does not provide an individual description/diff for this A-number; inspect existing history only, do not recreate the work.
12. [ ] **A12** — Grouped A1–A50 Compose runtime setup. The supplied source document does not provide an individual description/diff for this A-number; inspect existing history only, do not recreate the work.
13. [ ] **A13** — Grouped A1–A50 Compose runtime setup. The supplied source document does not provide an individual description/diff for this A-number; inspect existing history only, do not recreate the work.
14. [ ] **A14** — Grouped A1–A50 Compose runtime setup. The supplied source document does not provide an individual description/diff for this A-number; inspect existing history only, do not recreate the work.
15. [ ] **A15** — Grouped A1–A50 Compose runtime setup. The supplied source document does not provide an individual description/diff for this A-number; inspect existing history only, do not recreate the work.
16. [ ] **A16** — Grouped A1–A50 Compose runtime setup. The supplied source document does not provide an individual description/diff for this A-number; inspect existing history only, do not recreate the work.
17. [ ] **A17** — Grouped A1–A50 Compose runtime setup. The supplied source document does not provide an individual description/diff for this A-number; inspect existing history only, do not recreate the work.
18. [ ] **A18** — Grouped A1–A50 Compose runtime setup. The supplied source document does not provide an individual description/diff for this A-number; inspect existing history only, do not recreate the work.
19. [ ] **A19** — Grouped A1–A50 Compose runtime setup. The supplied source document does not provide an individual description/diff for this A-number; inspect existing history only, do not recreate the work.
20. [ ] **A20** — Grouped A1–A50 Compose runtime setup. The supplied source document does not provide an individual description/diff for this A-number; inspect existing history only, do not recreate the work.
21. [ ] **A21** — Grouped A1–A50 Compose runtime setup. The supplied source document does not provide an individual description/diff for this A-number; inspect existing history only, do not recreate the work.
22. [ ] **A22** — Grouped A1–A50 Compose runtime setup. The supplied source document does not provide an individual description/diff for this A-number; inspect existing history only, do not recreate the work.
23. [ ] **A23** — Grouped A1–A50 Compose runtime setup. The supplied source document does not provide an individual description/diff for this A-number; inspect existing history only, do not recreate the work.
24. [ ] **A24** — Grouped A1–A50 Compose runtime setup. The supplied source document does not provide an individual description/diff for this A-number; inspect existing history only, do not recreate the work.
25. [ ] **A25** — Grouped A1–A50 Compose runtime setup. The supplied source document does not provide an individual description/diff for this A-number; inspect existing history only, do not recreate the work.
26. [ ] **A26** — Grouped A1–A50 Compose runtime setup. The supplied source document does not provide an individual description/diff for this A-number; inspect existing history only, do not recreate the work.
27. [ ] **A27** — Grouped A1–A50 Compose runtime setup. The supplied source document does not provide an individual description/diff for this A-number; inspect existing history only, do not recreate the work.
28. [ ] **A28** — Grouped A1–A50 Compose runtime setup. The supplied source document does not provide an individual description/diff for this A-number; inspect existing history only, do not recreate the work.
29. [ ] **A29** — Grouped A1–A50 Compose runtime setup. The supplied source document does not provide an individual description/diff for this A-number; inspect existing history only, do not recreate the work.
30. [ ] **A30** — Grouped A1–A50 Compose runtime setup. The supplied source document does not provide an individual description/diff for this A-number; inspect existing history only, do not recreate the work.
31. [ ] **A31** — Grouped A1–A50 Compose runtime setup. The supplied source document does not provide an individual description/diff for this A-number; inspect existing history only, do not recreate the work.
32. [ ] **A32** — Grouped A1–A50 Compose runtime setup. The supplied source document does not provide an individual description/diff for this A-number; inspect existing history only, do not recreate the work.
33. [ ] **A33** — Grouped A1–A50 Compose runtime setup. The supplied source document does not provide an individual description/diff for this A-number; inspect existing history only, do not recreate the work.
34. [ ] **A34** — Grouped A1–A50 Compose runtime setup. The supplied source document does not provide an individual description/diff for this A-number; inspect existing history only, do not recreate the work.
35. [ ] **A35** — Grouped A1–A50 Compose runtime setup. The supplied source document does not provide an individual description/diff for this A-number; inspect existing history only, do not recreate the work.
36. [ ] **A36** — Grouped A1–A50 Compose runtime setup. The supplied source document does not provide an individual description/diff for this A-number; inspect existing history only, do not recreate the work.
37. [ ] **A37** — Grouped A1–A50 Compose runtime setup. The supplied source document does not provide an individual description/diff for this A-number; inspect existing history only, do not recreate the work.
38. [ ] **A38** — Grouped A1–A50 Compose runtime setup. The supplied source document does not provide an individual description/diff for this A-number; inspect existing history only, do not recreate the work.
39. [ ] **A39** — Grouped A1–A50 Compose runtime setup. The supplied source document does not provide an individual description/diff for this A-number; inspect existing history only, do not recreate the work.
40. [ ] **A40** — Grouped A1–A50 Compose runtime setup. The supplied source document does not provide an individual description/diff for this A-number; inspect existing history only, do not recreate the work.
41. [ ] **A41** — Grouped A1–A50 Compose runtime setup. The supplied source document does not provide an individual description/diff for this A-number; inspect existing history only, do not recreate the work.
42. [ ] **A42** — Grouped A1–A50 Compose runtime setup. The supplied source document does not provide an individual description/diff for this A-number; inspect existing history only, do not recreate the work.
43. [ ] **A43** — Grouped A1–A50 Compose runtime setup. The supplied source document does not provide an individual description/diff for this A-number; inspect existing history only, do not recreate the work.
44. [ ] **A44** — Grouped A1–A50 Compose runtime setup. The supplied source document does not provide an individual description/diff for this A-number; inspect existing history only, do not recreate the work.
45. [ ] **A45** — Grouped A1–A50 Compose runtime setup. The supplied source document does not provide an individual description/diff for this A-number; inspect existing history only, do not recreate the work.
46. [ ] **A46** — Grouped A1–A50 Compose runtime setup. The supplied source document does not provide an individual description/diff for this A-number; inspect existing history only, do not recreate the work.
47. [ ] **A47** — Grouped A1–A50 Compose runtime setup. The supplied source document does not provide an individual description/diff for this A-number; inspect existing history only, do not recreate the work.
48. [ ] **A48** — Grouped A1–A50 Compose runtime setup. The supplied source document does not provide an individual description/diff for this A-number; inspect existing history only, do not recreate the work.
49. [ ] **A49** — Grouped A1–A50 Compose runtime setup. The supplied source document does not provide an individual description/diff for this A-number; inspect existing history only, do not recreate the work.
50. [ ] **A50** — Grouped A1–A50 Compose runtime setup. The supplied source document does not provide an individual description/diff for this A-number; inspect existing history only, do not recreate the work.
51. [ ] **A51** — File.getName null-receiver guard; inspect File shadow and original diff.
52. [ ] **A52** — File.getAbsolutePath null-receiver guard; inspect File shadow and original diff.
53. [ ] **A53** — Not individually described in the supplied knowledge document. Search existing commits/worklogs briefly; if no record exists, mark SOURCE GAP/BLOCKED rather than inventing a fix or rerunning a broad investigation.
54. [ ] **A54** — Not individually described in the supplied knowledge document. Search existing commits/worklogs briefly; if no record exists, mark SOURCE GAP/BLOCKED rather than inventing a fix or rerunning a broad investigation.
55. [ ] **A55** — Not individually described in the supplied knowledge document. Search existing commits/worklogs briefly; if no record exists, mark SOURCE GAP/BLOCKED rather than inventing a fix or rerunning a broad investigation.
56. [ ] **A56** — Not individually described in the supplied knowledge document. Search existing commits/worklogs briefly; if no record exists, mark SOURCE GAP/BLOCKED rather than inventing a fix or rerunning a broad investigation.
57. [ ] **A57** — Not individually described in the supplied knowledge document. Search existing commits/worklogs briefly; if no record exists, mark SOURCE GAP/BLOCKED rather than inventing a fix or rerunning a broad investigation.
58. [ ] **A58** — Not individually described in the supplied knowledge document. Search existing commits/worklogs briefly; if no record exists, mark SOURCE GAP/BLOCKED rather than inventing a fix or rerunning a broad investigation.
59. [ ] **A59** — Not individually described in the supplied knowledge document. Search existing commits/worklogs briefly; if no record exists, mark SOURCE GAP/BLOCKED rather than inventing a fix or rerunning a broad investigation.
60. [ ] **A60** — Not individually described in the supplied knowledge document. Search existing commits/worklogs briefly; if no record exists, mark SOURCE GAP/BLOCKED rather than inventing a fix or rerunning a broad investigation.
61. [ ] **A61** — dialog_shadow.cpp: replace unsafe find_node(row_id)->children access with get_or_create_node(row_id).
62. [ ] **A62** — Security fix: remove shell-based popen/unzip path; use in-process ZIP parser.
63. [ ] **A63** — No separate entry for this A-number appears in the supplied knowledge document. Check existing git history/worklogs; do not infer a patch. If not recoverable quickly, mark SOURCE GAP/BLOCKED.
64. [ ] **A64** — File default path: replace hard-coded /tmp/miniandroid/files with Storage::package_data_dir().
65. [ ] **A65** — No separate entry for this A-number appears in the supplied knowledge document. Check existing git history/worklogs; do not infer a patch. If not recoverable quickly, mark SOURCE GAP/BLOCKED.
66. [ ] **A66** — No separate entry for this A-number appears in the supplied knowledge document. Check existing git history/worklogs; do not infer a patch. If not recoverable quickly, mark SOURCE GAP/BLOCKED.
67. [ ] **A67** — No separate entry for this A-number appears in the supplied knowledge document. Check existing git history/worklogs; do not infer a patch. If not recoverable quickly, mark SOURCE GAP/BLOCKED.
68. [ ] **A68** — Activity.finish(): clear content_view_id; reported execution_engine.cpp around line 7490.
69. [ ] **A69** — No separate entry for this A-number appears in the supplied knowledge document. Check existing git history/worklogs; do not infer a patch. If not recoverable quickly, mark SOURCE GAP/BLOCKED.
70. [ ] **A70** — No separate entry for this A-number appears in the supplied knowledge document. Check existing git history/worklogs; do not infer a patch. If not recoverable quickly, mark SOURCE GAP/BLOCKED.
71. [ ] **A71** — No separate entry for this A-number appears in the supplied knowledge document. Check existing git history/worklogs; do not infer a patch. If not recoverable quickly, mark SOURCE GAP/BLOCKED.
72. [ ] **A72** — No separate entry for this A-number appears in the supplied knowledge document. Check existing git history/worklogs; do not infer a patch. If not recoverable quickly, mark SOURCE GAP/BLOCKED.
73. [ ] **A73** — No separate entry for this A-number appears in the supplied knowledge document. Check existing git history/worklogs; do not infer a patch. If not recoverable quickly, mark SOURCE GAP/BLOCKED.
74. [ ] **A74** — No separate entry for this A-number appears in the supplied knowledge document. Check existing git history/worklogs; do not infer a patch. If not recoverable quickly, mark SOURCE GAP/BLOCKED.
75. [ ] **A75** — No separate entry for this A-number appears in the supplied knowledge document. Check existing git history/worklogs; do not infer a patch. If not recoverable quickly, mark SOURCE GAP/BLOCKED.
76. [ ] **A76** — No separate entry for this A-number appears in the supplied knowledge document. Check existing git history/worklogs; do not infer a patch. If not recoverable quickly, mark SOURCE GAP/BLOCKED.
77. [ ] **A77** — No separate entry for this A-number appears in the supplied knowledge document. Check existing git history/worklogs; do not infer a patch. If not recoverable quickly, mark SOURCE GAP/BLOCKED.
78. [ ] **A78** — No separate entry for this A-number appears in the supplied knowledge document. Check existing git history/worklogs; do not infer a patch. If not recoverable quickly, mark SOURCE GAP/BLOCKED.
79. [ ] **A79** — No separate entry for this A-number appears in the supplied knowledge document. Check existing git history/worklogs; do not infer a patch. If not recoverable quickly, mark SOURCE GAP/BLOCKED.
80. [ ] **A80** — No separate entry for this A-number appears in the supplied knowledge document. Check existing git history/worklogs; do not infer a patch. If not recoverable quickly, mark SOURCE GAP/BLOCKED.
81. [ ] **A81** — No separate entry for this A-number appears in the supplied knowledge document. Check existing git history/worklogs; do not infer a patch. If not recoverable quickly, mark SOURCE GAP/BLOCKED.
82. [ ] **A82** — No separate entry for this A-number appears in the supplied knowledge document. Check existing git history/worklogs; do not infer a patch. If not recoverable quickly, mark SOURCE GAP/BLOCKED.
83. [ ] **A83** — No separate entry for this A-number appears in the supplied knowledge document. Check existing git history/worklogs; do not infer a patch. If not recoverable quickly, mark SOURCE GAP/BLOCKED.
84. [ ] **A84** — No separate entry for this A-number appears in the supplied knowledge document. Check existing git history/worklogs; do not infer a patch. If not recoverable quickly, mark SOURCE GAP/BLOCKED.
85. [ ] **A85** — No separate entry for this A-number appears in the supplied knowledge document. Check existing git history/worklogs; do not infer a patch. If not recoverable quickly, mark SOURCE GAP/BLOCKED.
86. [ ] **A86** — No separate entry for this A-number appears in the supplied knowledge document. Check existing git history/worklogs; do not infer a patch. If not recoverable quickly, mark SOURCE GAP/BLOCKED.
87. [ ] **A87** — No separate entry for this A-number appears in the supplied knowledge document. Check existing git history/worklogs; do not infer a patch. If not recoverable quickly, mark SOURCE GAP/BLOCKED.
88. [ ] **A88** — No separate entry for this A-number appears in the supplied knowledge document. Check existing git history/worklogs; do not infer a patch. If not recoverable quickly, mark SOURCE GAP/BLOCKED.
89. [ ] **A89** — No separate entry for this A-number appears in the supplied knowledge document. Check existing git history/worklogs; do not infer a patch. If not recoverable quickly, mark SOURCE GAP/BLOCKED.
90. [ ] **A90** — No separate entry for this A-number appears in the supplied knowledge document. Check existing git history/worklogs; do not infer a patch. If not recoverable quickly, mark SOURCE GAP/BLOCKED.
91. [ ] **A91** — onPostCreate dispatch initially added only to Path A (multi-DEX, ~2083); PARTIAL/wrong path.
92. [ ] **A92** — Verification-tooling fix only: use 1080x1920; no source change. Reported gmdice 1→113 colors, glxy 1→20,421.
93. [ ] **A93** — Add onPostCreate dispatch to Path B (single-DEX), dalvik_engine.cpp around line 1864; marker [A93-POSTCREATE].
94. [ ] **A94** — Add Display.getWidth/getHeight returning 1080/1920 and Display.getDisplayInfo safety net; dalvik_engine.cpp around line 35665.
95. [ ] **A95** — ViewShadow getWidth/getHeight fallback for pre-layout Runnables; android_shadows.cpp around line 4330.
96. [ ] **A96** — No separate entry for this A-number appears in the supplied knowledge document. Check existing git history/worklogs; do not infer a patch. If not recoverable quickly, mark SOURCE GAP/BLOCKED.
97. [ ] **A97** — No separate entry for this A-number appears in the supplied knowledge document. Check existing git history/worklogs; do not infer a patch. If not recoverable quickly, mark SOURCE GAP/BLOCKED.
98. [ ] **A98** — No separate entry for this A-number appears in the supplied knowledge document. Check existing git history/worklogs; do not infer a patch. If not recoverable quickly, mark SOURCE GAP/BLOCKED.
99. [ ] **A99** — No separate entry for this A-number appears in the supplied knowledge document. Check existing git history/worklogs; do not infer a patch. If not recoverable quickly, mark SOURCE GAP/BLOCKED.
100. [ ] **A100** — No separate entry for this A-number appears in the supplied knowledge document. Check existing git history/worklogs; do not infer a patch. If not recoverable quickly, mark SOURCE GAP/BLOCKED.
101. [ ] **A101** — HashMap.size counts actual key_-prefixed fields excluding __ internals; dalvik_engine.cpp around line 44238.
102. [ ] **A102** — Add ArrayDeque/LinkedList to collection handler class gate; dalvik_engine.cpp around line 44793. Separate unresolved Map.keySet class-descriptor mismatch in F-064 (~android_shadows.cpp line 1036); do not conflate these.
103. [ ] **A103** — Three-run SHA256 repeatability report for seven apps; first inspect existing hash records and binary identity.
104. [ ] **A104** — dooz v18 Compose boundary: 20,166 IMPLEMENTED, 253 STUBBED, zero MISSING/ERROR; ComposeView→AndroidComposeView has 0 children/0 draw ops; screenshot one color; FRAME_CAPTURED only.

## D. Known outcomes to accept only after inspecting existing evidence

- A92 is tooling, not a source-code fix. Use 1080×1920 by default (density 2.0). The supplied report says gmdice changed from 1 to 113 unique colors and glxy from 1 to 20,421 after correcting resolution.
- A91 is partial because it modified Path A only; A93 is the reported Path B correction.
- A94/A95 are a reported chain for minos reaching game creation: display dimensions then pre-layout view dimensions. Existing report says IMPLEMENTED API count rose 137→256 at A93 and later 262→688 at A95; inspect old evidence before deciding whether these counters are comparable.
- A101 HashMap.size() and A102 collection class gate are separate from the unresolved Map.keySet() view-class/iterator problem. Do not merge their claims.
- A103 reports 7 apps FULLY_VERIFIED only when interaction proof and 3/3 identical screenshot hashes exist for the same binary.
- A104 dooz is FRAME_CAPTURED, not visually verified. The reported white single-color screenshot and zero draw ops support a Compose-runtime boundary; they do not prove general rendering is fixed.
- The transferred table/list has a reported count discrepancy (13 listed apps versus a note elsewhere saying 14 apps / 5 FRAME_CAPTURED). Record the mismatch; do not silently reconcile it.

## E. Minimal confirmation test policy

1. Source/commit check for each claimed fix.
2. Existing artifact check: logs, ViewTree, screenshot, pixel metrics, SHA, test report, APK SHA and runtime commit.
3. One targeted test for a material uncertain behavior.
4. One real-APK rerun only if evidence is stale/missing or the source change makes it necessary.
5. Three runs only for a FULLY_VERIFIED claim where binary identity/evidence does not already prove repeatability.

Do not run the entire corpus just to accept a source-level patch. Do not fix anything during this review. If a test reveals a regression, document the smallest failing path and request a separate implementation task.

## F. Screenshot and knowledge-file transfer status — be honest

The supplied source archive is named MiniAndroid_A1_A104_Complete.zip. It contains KNOWLEDGE_TRANSFER_A1_A104.md, dooz_problems.md, screenshots_v4/FINAL_MOSAIC.png, 2048.png, snake_deluxe.png, tetris.png, tictactoe_deluxe.png, minicraft.png, snakeneon.png, and dooz.png.

The archive is present in the ChatGPT conversation but has not been uploaded as a GitHub binary attachment. Do not claim those PNGs are attached/rendered in this issue unless the repository/issue visibly contains them. The available GitHub connector exposes UTF-8 text-file creation but no binary issue-attachment upload action; do not fabricate image URLs. The primary coder should inspect the original archive if it is available to them, otherwise explicitly record that the PNG payloads are unavailable in the GitHub issue.

## G. Required audit result

- A1–A104 ledger with every number present and a status;
- exact current source line / diff / commit for each claimed code fix;
- accepted claims backed by existing evidence;
- rejected claims with contradicting evidence;
- partial claims and the smallest test needed to settle them;
- source gaps that cannot be recovered from available history;
- which existing screenshots and hashes were inspected;
- only the new tests actually needed, with reason;
- confirmation that no code was changed during this audit.

The objective is to transfer knowledge and make the primary coder a reviewer and minimal tester, not to make them repeat the previous investigator's hours of discovery.