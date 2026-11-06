"""S188 governing issues — part 1 (master, rules, phases A-F). English only."""

I1 = {
"title": "[S188 MASTER] Unified Runtime Integration, Route-Aware Execution Graph, and Real Application Recovery — BINDING LAW FOR ALL CODERS",
"labels": ["compatibility", "common-runtime", "P0"],
"body": """# S188 FINAL MASTER DIRECTIVE — BINDING FOR ALL CODERS (2–9)

Full text committed to main: **`docs/S188_DIRECTIVE.md`** (commit 7edaa2b6). Read it completely, line by line. Governing engineering law remains S185 (#536).

## Objective

One integrated MiniAndroid runtime that executes real small Android games/apps with their **REAL graphical interfaces**.

**First concrete target: at least five genuinely small apps/games displaying their real application-owned initial interfaces through ONE integrated main-runtime binary.** Then expand across the eligible small-title corpus. Large apps (Telegram, Dooz, Mindustry) stay advanced targets — they must not block small-app recovery.

## We do NOT want (any more)

- Another report counting implemented methods.
- Isolated API tests disconnected from the runtime.
- Library inventories nobody connects to execution.
- RESUMED + default background.
- "Two colors and one font" classified as a graphical achievement.

## Core architectural law

**NOT every APK has the same execution route.** View / Bitmap / libGDX / SDL / Compose / Hybrid apps follow different paths. Never force one linear pipeline onto every APK. Never credit a route because another route in the same APK succeeded.

Required architecture: **one shared capability registry · one unified execution graph (FDT) · one main integration runtime · many independently discovered APK routes · one route-specific evidence record per tested application.**

## Phase issues (execute in order; focused research may run in parallel)

| Phase | Scope |
|---|---|
| A | Reconcile all existing achievements → adoption ledger |
| B | Route-aware FDT execution graph |
| C | Per-APK route profiles |
| D | Main-coder integration pipeline (dual status systems) |
| E | View & draw recovery: gmdice Adapter rows, unote Toolbar |
| F | libGDX & native game routes: TicTacToe, Bouncy, Mindustry |
| G | Cross-coder integration responsibilities (Coder 2–9) |
| H | Route-driven library acquisition (S185 law applies) |
| I | Reproduce S186i & prevent regressions |
| J | Smart recovery priority system (shared roots) |
| K | Small-app recovery battery — **five-title milestone** |
| L | Regression & performance policy — golden anchors |
| Gov | Issues, trackers, dashboard policy |

## ACK REQUIRED

Every Coder 2–9 must comment **`ACK S188`** below stating: (1) "I read `docs/S188_DIRECTIVE.md` fully", (2) the phase(s) they own. Work from coders who have not acknowledged will not be credited toward recovery claims.

**Close only by user order. This issue is the reference the whole campaign cites.**
"""
}

I2 = {
"title": "[S188-RULES] Binding working rules for all coders — UNOBSERVED is never PASS",
"labels": ["compatibility", "common-runtime"],
"body": """# S188 BINDING WORKING RULES — ALL CODERS, NO EXCEPTIONS

Full text: `docs/S188_DIRECTIVE.md` §0, §13, §18. These rules override convenience.

1. **UNOBSERVED is never PASS.** Missing evidence = missing result.
2. **Zero uncaught exceptions ≠ graphical success.** RESUMED + default background is a failure state.
3. **A_RICH is never inferred** from zero exceptions, RESUMED, non-black pixels, unique color count, a loaded font, a library init, a loading background, or a GL clear. It requires the application's own content, proven by visual inspection of the screenshot.
4. **Do not force one route onto every APK.** Discover each APK's real route; record route-specific first divergence. Do not classify an APK as broken because it ignores a subsystem irrelevant to it.
5. **No app-specific branches** to make screenshots look correct. No fake rows. No hardcoded children. No silent null/zero where a real API contract requires behavior.
6. **Never assume two apps share a root because both are blank.** Shared roots require first-divergence evidence.
7. **Dual status systems, never merged:** engineering adoption (DISCOVERED → SUPERSEDED) is separate from runtime impact (UNOBSERVED → REGRESSION_VERIFIED). An integrated fix may still have zero APK consumers; a locally tested patch may still be absent from main.
8. **Never stop after:** reconciliation, building FDT, zero uncaught exceptions, loading a library, or displaying a background/two colors. The deliverable is a real graphical recovery — then the next one.
9. **Three independent runs** for every accepted recovery milestone. Same final binary for all final acceptance evidence. Never mix observations from different binaries into one matrix.
10. **Update existing trackers** (#536, #472, #492, #475, #441, app trackers) after every real result. Never leave an obsolete background-only status. Never close an issue because an API test passed.
11. **Regressions are blocking.** A fix that improves one route but breaks a golden (Bouncy, Dooz, Tower3D, Unote — hashes from current HEAD test definitions, never stale) is not accepted.
12. **Nothing bulky in Git** (S185 #536 law). Scripts + pinned upstream URLs rebuild everything; evidence = verdict JSON + face JPG ≤100 KB.
13. **When a route stays blocked:** document its exact first divergence and immediately continue with the next recoverable route. One hard app must never block the campaign.

Every Coder 2–9 comments **`ACK RULES`** on the master issue after reading this.
"""
}

I3 = {
"title": "[S188 Phase A] Reconcile all existing achievements — machine-readable adoption ledger",
"labels": ["compatibility", "common-runtime"],
"body": """# PHASE A — RECONCILE ALL EXISTING ACHIEVEMENTS

Start immediately against current `main` HEAD. Do not rely on old binaries, old branches, stale issue descriptions or previous reports.

## Inspect (minimum set)

#536, #529, #530, #472, #519, #533, #520, #521, #528, #534, #538, #537, #540, #539, #475, #441, #470, #492, plus all linked issues, patch comments, commits, branches, worklogs, test output and build scripts. Achievements hide in **updated issue bodies and comments** — not only new issues.

## For every contribution establish (10 checks)

1. Original author and Issue.
2. Exact source commit or patch.
3. Base commit SHA.
4. Whether already present in current main.
5. Whether it compiles in the authoritative build.
6. Whether its tests pass.
7. Whether real-dalvik can reach it.
8. Whether a real APK consumes it.
9. Which APK execution routes depend on it.
10. Which additional roots remain blocked.

## Do not

Reimplement what exists · integrate the same fix twice · apply stale patches · assume `INTEGRATION_READY` means integrated.

## Deliverable

`reports/s188/adoption_ledger.json` — per contribution: contributor, source issue/SHA, base SHA, patch hash, present-on-main, compile/test/reachable/consumed booleans, routes affected, blockers. Phase ends with **one authoritative baseline binary** identified.

Owner: Main Coder. Status: OPEN.
"""
}

I4 = {
"title": "[S188 Phase B] Route-aware FDT execution graph — one graph per APK run",
"labels": ["compatibility", "common-runtime"],
"body": """# PHASE B — BUILD ONE SHARED EXECUTION GRAPH (FDT)

Extend the existing FDT system (`tools/fdt/`). **Do not build a second competing tracer.**

## One graph per APK execution, containing

APK identity + SHA256 · runtime commit · runtime binary SHA256 · run ID · route ID · active execution paths · observed capabilities · causal relationships · first divergence per path · final graphical result · input result · regression result.

## Node types

APK, CLASS_LOAD, METHOD_CALL, API_DISPATCH, OBJECT_STATE, RESOURCE, ASSET, VIEW, ADAPTER, LAYOUT, DRAW, NATIVE_LOAD, JNI, EGL, GLES, AUDIO, INPUT, STATE_MUTATION, FRAMEBUFFER, SCREENSHOT.

## Edge types

CALL, DATA_FLOW, DEPENDS_ON, ATTACHES, CREATES, CONSUMES, RENDERS_TO, CAUSES, REPLACES, SCHEDULES.

## Provenance requirements

Resource nodes record byte origin · Bitmap nodes identify decoder + consumer · View nodes identify parent + lifecycle · Draw nodes identify renderer + destination · GLES nodes identify context, surface, framebuffer.

## Contract-aware first divergence

Distinguish: valid null / invalid null / unimplemented API / wrong overload / incorrect return / missing side effect / incorrect dispatch / wrong object identity / incorrect state propagation / missing consumer / rendering failure / capture failure. Every divergence records: exact method, caller, callee, args, receiver identity, expected contract, actual result, source location, downstream effect, confidence, owner. **An early missing API returning null beats a later NPE as the root cause.**

## Hard rules

- `UNOBSERVED` is never `PASS`.
- Multiple independent divergences per APK supported; View-route and Native-route diagnostics never overwrite each other.
- FDT OFF has no measurable overhead beyond baseline variability.
- First implementation must run on **real executions** of gmdice, TicTacToe, Mindustry. No documentation-only wave.

Owner: Main Coder + Coder 3. Status: OPEN.
"""
}

I5 = {
"title": "[S188 Phase C] Per-APK route profiles — reports/apk_routes/<package_id>.json",
"labels": ["compatibility", "common-runtime"],
"body": """# PHASE C — EVERY APK GETS ITS OWN ROUTE PROFILE

Mandatory for every tested APK: `reports/apk_routes/<package_id>.json` with:

- `apk`: package + sha256
- `route_profiles[]`: route_id, type, nodes, edges, first_divergence
- `capabilities[]`
- `route_status`, `visual_status`

## Rules

- Routes are **discovered through actual execution**, not inferred from package names.
- One app may have startup / main-screen / login / menu / game-scene / background-task / media / input routes. Test each when relevant.
- Shared intersections (`ViewGroup.addView`, `EGLContext`, `AssetManager.open`) are centrally implemented and reused — but **every consumer must independently demonstrate its route consumes them** before recovery credit.
- Never assume identical downstream behavior because two APKs call similarly named APIs.

Owner: Main Coder. Status: OPEN.
"""
}

I6 = {
"title": "[S188 Phase D] Main-coder integration pipeline — dual status systems, never merged",
"labels": ["compatibility", "common-runtime"],
"body": """# PHASE D — MAIN CODER MUST ACTIVELY INTEGRATE EVERY USEFUL CONTRIBUTION

Helper coders are contributors to **one runtime**, not independent projects. Process:

`DISCOVERY → EVIDENCE REVIEW → PATCH VERIFICATION → MAIN SOURCE INTEGRATION → MAIN BUILD → REAL APK EXECUTION → REGRESSION → TRACKER UPDATE`

## Two independent status systems (never merged)

**Engineering adoption:** DISCOVERED / EVIDENCE_VERIFIED / REVIEWED / ACCEPTED / SOURCE_INTEGRATED / BINARY_INTEGRATED / BLOCKED / REJECTED / SUPERSEDED.

**Actual runtime impact:** UNOBSERVED / NO_CHANGE / LOCAL_CONTRACT_VERIFIED / CHAIN_ADVANCED / PARTIAL_CHAIN / CROSS_APP_VERIFIED / VISUAL_VERIFIED / INTERACTIVE_VERIFIED / REGRESSION_VERIFIED.

An integrated implementation may still have no demonstrated APK consumer. A locally tested patch may still be absent from the main runtime.

## Record per fix

Contributor · source Issue · source SHA · base SHA · patch hash · capability ID · affected route types · consuming APKs · main integration commit · main binary identity · before/after FDT · actual result · remaining blockers.

Main coder is the integration authority — but **evidence, not authority alone, determines acceptance**.

Owner: Main Coder. Status: OPEN.
"""
}

I7 = {
"title": "[S188 Phase E] View & draw pipeline recovery — gmdice real Adapter rows, unote Toolbar children",
"labels": ["compatibility", "common-runtime", "P0"],
"body": """# PHASE E — RECOVER THE ACTUAL VIEW AND DRAW PIPELINE

Start with gmdice and unote. Do not assume identical routes.

## gmdice (Adapter/View route)

Chain: `Activity → ListActivity → ListView → Adapter → getView → row inflation → addView → measure → layout → draw`.

Investigate: setListAdapter · adapter identity · getCount/getItem/getItemId · getView · row resource · LayoutInflater · convertView · child ownership · child attachment · notifyDataSetChanged · LayoutParams · actual drawing · scroll behavior.

**Known defect:** adapter data can grow (0→1→2) while actual visible rows remain zero. Fix the lowest shared root. The real Adapter must produce real Views. **Do not manufacture rows.**

## unote (Toolbar route)

Toolbar construction → children → custom child insertion → LayoutParams → child ownership → drawing traversal → Canvas propagation → render-task creation → framebuffer delivery. The existence of a Toolbar child is NOT evidence it was rendered. **Trace the exact point the child disappears from the rendering path.**

## Shared View system (generic, AOSP contracts)

View construction · ViewGroup child management · LayoutParams · MeasureSpec · onMeasure · requestLayout · onLayout · dispatchDraw · invalidation · backgrounds · Drawable bounds · padding/margins · visibility · text rendering · image rendering · clipping · transforms · scrolling · z-order. No screenshot-specific isolated fixes.

Owner: Coder 2 + Coder 3, integration by Main Coder. Status: OPEN.
"""
}

I8 = {
"title": "[S188 Phase F] libGDX & native game routes — TicTacToe, Bouncy, Mindustry",
"labels": ["compatibility", "common-runtime", "P0"],
"body": """# PHASE F — COMPLETE THE LIBGDX AND NATIVE GAME ROUTES

Priority reproductions: **TicTacToe, Bouncy**. Chain: `DEX → Native Engine → JNI → AssetManager → AsyncExecutor → I18N → Texture → GL → Framebuffer`.

## Investigate & integrate

StringBuilder packed implementations · replaceAll · Stack · ExecutorService.submit · Future · AsyncExecutor · FileHandle · AssetManager · I18NBundle · native loading · JNI registration · EGL · GLES · texture upload · shader compile/link · render loop · input callbacks.

## Hard rules

- S187 changes (String.replaceAll, Stack, ExecutorService.submit laws) must reach the **actual main runtime** — not stay in a harness.
- Do not stop when `AssetManager.open` works. Do not stop when an I18N file opens. Do not stop when the GL context is created. **Require an actual game menu or scene.**
- Mindustry continues its existing native-GL work independently. A loading grid is an intermediate result, not a completed game.
- Bouncy golden behavior preserved (pin hash from current HEAD definitions).

Owner: Coder 4 + Coder 6 + Coder 8, integration by Main Coder. Status: OPEN.
"""
}

ISSUES_PART1 = [I1, I2, I3, I4, I5, I6, I7, I8]
