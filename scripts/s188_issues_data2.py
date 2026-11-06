"""S188 governing issues — part 2 (phases G-L + governance). English only."""

I9 = {
"title": "[S188 Phase G] Cross-coder integration responsibilities — contributor boundaries must not become runtime boundaries",
"labels": ["compatibility", "common-runtime"],
"body": """# PHASE G — OTHER REAL APPLICATION ROUTES (CODER 2–9 AREAS)

Integrate every contributor's work where it benefits actual APKs.

## Areas

- **Coder 2 — Framework/AndroidX:** Activity, Fragment, FragmentManager, Lifecycle, ViewModel, SavedState, ViewTree owners, AndroidX dependencies, real framework implementation reuse.
- **Coder 4 — Java/Kotlin/API semantics:** Collections, Strings, StringBuilder, UUID, ParcelUuid, exception identity, SQLite callbacks, PackageManager API behavior, other verified shared laws.
- **Coder 6 — Native/Graphics/Audio:** libGDX, SDL, Box2D, Arc, SoLoud, native loader, EGL/GLES, audio engines, native application compatibility.
- **Coder 7 — Storage/PackageManager:** SQLite, package index, cross-package resolution, SharedPreferences, URI, file paths, database persistence, component behavior.
- **Coder 8 — Concurrency:** Thread, ExecutorService, Future, Handler, Looper, CompletableFuture, locks, queues, scheduled work, actual scheduling semantics.
- **Coder 9 — Resources:** ARSC, Bitmap, BitmapFactory, Drawable, AssetManager, font resources, density, resource configuration, NinePatch, VectorDrawable.

## The law

Main coder connects all these areas:

- A resource implementation must be accessible to ImageView.
- An Executor implementation must be accessible to libGDX.
- A native-library implementation must be accessible to the real APK loader.
- An AndroidX lifecycle fix must be usable by every applicable application.

**Do not let contributor boundaries become runtime boundaries.** A fix from one coder must be usable by every application that needs it — prove consumption per APK route.

Owner: all coders, integration by Main Coder. Status: OPEN.
"""
}

I10 = {
"title": "[S188 Phase H] Route-driven library acquisition — no library without a verified consumer",
"labels": ["compatibility", "open-source"],
"body": """# PHASE H — LIBRARY ACQUISITION MUST BE ROUTE-DRIVEN (S185 LAW APPLIES, #536)

Do not add every famous library. Inspect the failing application route first:

1. Existing implementation present and correct → **reuse it**.
2. Present but unreachable → **repair the connection**.
3. Genuine capability gap → search upstream, evaluate.

## Candidate pool (evaluate only with a demonstrated gap)

Skia (2D raster) · Mesa/llvmpipe (software GL) · GL4ES (legacy OpenGL translation) · SDL2/SDL3 (SDL routes) · FFmpeg (real media consumers) · libyuv (pixel-format conversion) · libzip/minizip-ng (ZIP/asset access) · libcurl (HTTP) · OpenAL Soft (native spatial audio) · AndroidX source (missing framework/component behavior).

## Per integrated library — all mandatory

- Pin revision.
- Verify license.
- Build reproducibly.
- Keep bulky source and binaries outside Git.
- Record build provenance.
- Prove runtime loading.
- **Prove real APK consumption.**
- Measure resource cost.

Objective: **maximum compatibility improvement, not maximum dependency count.**

Owner: Coder 6 + Coder 7 + Coder 9, integration by Main Coder. Status: OPEN.
"""
}

I11 = {
"title": "[S188 Phase I] Reproduce S186i exactly — one final binary per matrix, unverified ≠ success",
"labels": ["compatibility", "common-runtime"],
"body": """# PHASE I — REPRODUCE S186i AND PREVENT FURTHER REGRESSIONS

The S186i report (41-title battery, 13→29 zero-uncaught, two A_RICH) is an important **baseline — not a final target**. Reproduce:

- Exact hybrid source revision.
- Exact build configuration.
- The complete 41-title battery.
- The claimed 29 zero-uncaught results.
- Both A_RICH results.
- The new generic laws (TextUtils.join, LocaleList, String.split).
- The regression comparison.
- Bouncy and unote golden pins.
- All remaining incomplete titles.

## Rules

- **One identified final integration binary per final matrix.** Never combine observations from multiple binary revisions. Never count an interim binary as the final hybrid.
- Preserve the S186h ARITY regression findings.
- If a fix improves one route but breaks another, identify the exact causal relationship.
- If any part cannot be reproduced, record it as **UNVERIFIED** — do not assume success.
- Graphical success is never inferred from zero exceptions.
- This reproduction must **not block** new high-value graphical recovery work.

Owner: Main Coder. Status: OPEN.
"""
}

I12 = {
"title": "[S188 Phase J] Smart recovery priority system — group by confirmed shared roots, never by blank screens",
"labels": ["compatibility", "common-runtime"],
"body": """# PHASE J — BUILD A SMART RECOVERY PRIORITY SYSTEM

The next task is NOT chosen by the most recent coder report, nor by the easiest API.

## Per incomplete APK, calculate

Route type · max stage reached per route · first divergence per active route · capabilities available · capabilities missing · shared-root candidates · expected recovery probability · engineering effort · regression risk · expected number of other APK consumers.

## Group by CONFIRMED shared roots (evidence-established), e.g.

```text
Root: Adapter row materialization
Affected: gmdice, application-B, application-C
Required: getView, layout inflation, child attachment, layout, draw
Owner: Coder 3 · Integration: Main
```

```text
Root: libGDX packed StringBuilder
Affected: TicTacToe, application-D, application-E
Required: correct StringBuilder behavior, I18N parsing, asset consumption
Owner: Coder 4 / Coder 3 · Integration: Main
```

## Rules

- A graphics group stays distinct from a View/Adapter group **unless evidence establishes a shared lower-level defect**.
- **Never assume two applications share a root merely because both display a blank screen.** First-divergence evidence must establish the relationship.
- When a generic fix advances only some consumers, record exactly which routes advanced and the new blockers for the others. That is useful route-diversity information — not a failed global fix.

Owner: Main Coder. Status: OPEN.
"""
}

I13 = {
"title": "[S188 Phase K] Small application recovery battery — FIRST MILESTONE: five real graphical recoveries on one binary",
"labels": ["compatibility", "common-runtime", "P0"],
"body": """# PHASE K — SMALL APPLICATION RECOVERY BATTERY

## Required diagnostic paths

- **gmdice** — Adapter/View route.
- **TicTacToe** — libGDX/Asset/I18N route.
- **Mindustry** — Native GL route.
- **Bouncy** — established rendering regression anchor.

## Initial route-discovery cohort (≥10 from S107/S115)

uturn · pfsolitaire · foehnix.widget · aoc_normal · queens · tarok · astroloop · nightbell · newsblur · opentopo · taz · gnubg · boxcars · halma · p9 · other genuinely small verified titles.

Re-check actual APKs and versions before testing. Do not force all through one route. Select ≥5 recovery targets from **different route families** (View/Adapter, simple Canvas game, libGDX game, native graphics game, AndroidX/resource-heavy) using current evidence, not guesses.

## THE FIRST MILESTONE

**At least five small apps/games display their actual application-owned initial graphical interfaces on the SAME integrated runtime binary**, including:

- Real application interface · correct visible content.
- Real text / resources / images where applicable.
- Real ViewTree or native scene.
- No unexplained default-background-only state.
- No two-color-and-font false success.
- No relevant uncaught failure on the tested path.
- Correct framebuffer provenance.
- At least one meaningful interaction where the application supports it.

Three independent recovery runs. Real state transition proven for interactive titles.

**Then continue across all eligible small titles. Do not stop after five.**

Owner: Main Coder + all coders. Status: OPEN.
"""
}

I14 = {
"title": "[S188 Phase L] Regression & performance policy — golden anchors from current HEAD, tiered testing",
"labels": ["compatibility", "common-runtime"],
"body": """# PHASE L — REGRESSION AND PERFORMANCE

## Test tiers (do not run the full corpus after every trivial edit)

1. Focused contract tests after a patch.
2. Relevant APK tests after integration.
3. Full 30-title battery for release candidates.
4. Full affected group after a shared-root fix.
5. Three independent executions for each accepted recovery milestone.

## Golden anchors

Bouncy · Dooz · Tower3D · Unote · other established goldens discovered in current HEAD. Retrieve exact hashes from **current test definitions** — never invent or reuse stale hashes.

## Benchmark

Build time · startup · DEX execution · API dispatch · ViewTree construction · measure/layout · drawing · native init · frame time · memory.

FDT OFF ≈ baseline (no measurable overhead beyond variability). Measure enabled trace modes instead of inventing performance ratios. Keep instrumentation bounded; the runtime must remain usable on constrained CPU/RAM.

## Build discipline

Authoritative current build configuration · verify the Makefile/CMake relationship · precise source list · no unrelated translation units · a clean checkout must reproduce dependency bootstrap and the integrated runtime build.

Owner: Main Coder. Status: OPEN.
"""
}

I15 = {
"title": "[S188 Governance] Issues, trackers & dashboard — dashboard shows recovered app count, not API test count",
"labels": ["compatibility", "common-runtime"],
"body": """# S188 GOVERNANCE — ISSUE AND WORKLOG POLICY

Do not create a new issue for every small improvement. **Update existing living trackers:**

- #536 — S185/S186/S188 governing rules.
- #472 — achievement ledger.
- #492 — main dashboard.
- #475 — TicTacToe · #441 — Mindustry.
- Relevant existing application trackers for every recovered title.
- Existing coder worklogs for implementation history.

## Rules

- A tracker must reflect the **latest actual runtime result**.
- When an application improves, update its existing issue **immediately**.
- Never leave an old background-only status after a real graphical recovery.
- Never close an issue because an API test passed.

## Maintain per tracker

Current status · exact source SHA · main binary SHA · current route · first divergence · recent progress · remaining blocker · actual graphical acceptance evidence.

**The main dashboard (#492) shows the real recovered application count — not the total number of successful API tests.**

Owner: Main Coder. Status: OPEN.
"""
}

ISSUES_PART2 = [I9, I10, I11, I12, I13, I14, I15]
