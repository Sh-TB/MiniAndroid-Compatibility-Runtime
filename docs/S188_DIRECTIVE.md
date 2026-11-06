# S188 FINAL MASTER DIRECTIVE
# MINIANDROID — UNIFIED RUNTIME INTEGRATION, ROUTE-AWARE EXECUTION GRAPH, AND REAL APPLICATION RECOVERY

**Repository:** `Sh-TB/MiniAndroid-Compatibility-Runtime`

**Mission owner:** Main Coder

**Contributors:** Coders 2–9

**Governing engineering law:** S185 — SQLITE RULE / VEND, DON'T REWRITE

**Execution governance:** S186 — Unified Runtime Integration and Chain Contracts

**Final architecture:** S188 — Route-Aware Unified Execution and Application Recovery

**Priority:** P0 — REAL GRAPHICAL APPLICATION EXECUTION

---

# 0. THIS IS THE FINAL OBJECTIVE

We have already accumulated substantial engineering work.

Coders 2–9 have investigated and implemented improvements in:

- Dalvik execution.
- Java and Kotlin compatibility.
- Android framework APIs.
- AndroidX.
- Activity and Fragment lifecycle.
- Resources and ARSC.
- Bitmap and image decoding.
- FreeType, HarfBuzz and text rendering.
- AssetManager.
- SQLite.
- PackageManager.
- JNI.
- Native library loading.
- libGDX.
- Box2D.
- PortableGL.
- EGL and GLES.
- Concurrency and scheduling.
- Audio.
- ViewTree.
- ListView and Adapter.
- Canvas and rendering.
- Application-specific compatibility.

There is also substantial work in GitHub Issues, existing patches, comments, local branches, test harnesses and experimental builds.

Yet the most important result remains insufficient:

**Too many actual applications and games still fail to display their own complete graphical interfaces.**

The supplied S186i report claimed improvement from 13 to 29 zero-uncaught titles across the 41-title battery, but only two A_RICH results.

This is the central problem we must solve.

We do not want another report showing that 100 methods were added.

We do not want another collection of isolated API tests.

We do not want another library inventory that nobody connects to the runtime.

We do not want applications to reach RESUMED while showing a default background.

We do not want two colors and one font to be classified as a graphical achievement.

We want the main runtime to consume all useful contributor work and actually execute real applications.

**The first concrete target is at least five genuinely small Android applications or games displaying their real graphical interfaces through one integrated main-runtime binary.**

After that, continue recovering the eligible small-title corpus.

Large applications such as Telegram, Dooz and Mindustry remain important advanced targets, but they must not prevent us from recovering many smaller applications first.

---

# 1. THE MOST IMPORTANT ARCHITECTURAL CORRECTION

## NOT EVERY APK HAS THE SAME EXECUTION ROUTE

This is the most important rule of S188.

We must never force every application to pass through one universal linear execution pipeline.

Different applications have different execution paths.

Some use ordinary Java Views.

Some use AndroidX, Fragments and RecyclerView.

Some use Compose.

Some use native game engines.

Some use libGDX.

Some use SDL.

Some use EGL/GLES.

Some use a hybrid of Java Views, native graphics and custom Surface rendering.

Some depend heavily on images, fonts, animation and assets.

Some use background workers, services, providers or networking before producing visible content.

An application may have several execution routes depending on its current screen and state.

**Every application has its own streets and roads. Some roads share intersections, but they do not all follow the same route.**

Examples:

### Application A — Ordinary View application

`APK → Activity → ViewTree → Adapter → getView → Measure → Layout → Canvas → Framebuffer`

### Application B — Simple Bitmap application

`APK → Activity → Resources → AssetManager → BitmapFactory → Drawable → ImageView → Canvas → Framebuffer`

### Application C — libGDX game

`APK → NativeLoader → JNI → libGDX → AssetManager → I18N → EGL/GLES → Texture → DrawCall → Framebuffer`

### Application D — SDL application

`APK → SDLActivity → Native Library → SDL Initialization → Event Loop → Surface → Rendering → Framebuffer`

### Application E — Compose application

`APK → Activity → AndroidComposeView → Composition → Applier → LayoutNode → Measure → Placement → Draw → Framebuffer`

### Application F — Hybrid application

`APK → Activity → AndroidX → ViewTree`
while simultaneously:
`Activity → JNI → Native Engine → EGL/GLES`

These are different routes.

Do not assume that a fix for one route must improve every other route.

Do not declare a route successful because another route in the same APK succeeded.

Do not classify an APK as broken merely because it does not use a subsystem that is irrelevant to it.

## REQUIRED ARCHITECTURE

Create:

**One shared capability registry.**

**One unified execution graph infrastructure.**

**One main integration runtime.**

**Many independently discovered APK execution routes.**

**One route-specific evidence record for every tested application.**

The graph must support shared nodes and independently branching paths.

A common capability may have many consumers, but every consumer must be observed using that capability before its recovery is credited.

This is the most important distinction in the entire project.

---

# 2. PHASE A — RECONCILE ALL EXISTING ACHIEVEMENTS

Start immediately.

Inspect the actual current repository HEAD.

Read every relevant achievement, including old Issues that contributors continue updating.

At minimum:

- #536 — S185 SQLite Rule.
- #529 and #530 — Coder D source audit and related work.
- #472 — Achievement Ledger.
- #519 and #533 — Coder 8.
- #520 — Coder 7.
- #521 — Coder 9.
- #528, #534 and #538 — Coder 4.
- #537 and #540 — Coder 3.
- #539 — main integration and application recovery.
- #475 — TicTacToe.
- #441 and #470 — Mindustry.
- #492 — Main dashboard.
- S107/S115 incomplete-title evidence.
- All relevant linked Issues, patch comments, commits and test records.

Do not limit discovery to newly created Issues.

Find achievements hidden in:

- Updated Issue bodies.
- Existing Issue comments.
- Local commit references.
- Patch attachments.
- Existing branches.
- Worklogs.
- Test output.
- Existing source files.
- Build scripts.

For every contribution establish:

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

Do not reimplement something that already exists.

Do not integrate the same fix twice.

Do not apply stale patches.

Do not assume `INTEGRATION_READY` means integrated.

Create or extend a machine-readable adoption ledger.

---

# 3. PHASE B — BUILD ONE SHARED EXECUTION GRAPH

Create or extend the existing FDT system.

Suggested location:

`tools/fdt/`

Do not build a second competing tracer.

Every APK execution must have:

- APK identity.
- APK SHA256.
- Runtime commit.
- Runtime binary SHA256.
- Run ID.
- Route ID.
- Active execution paths.
- Observed capabilities.
- Causal relationships.
- First divergence per path.
- Final graphical result.
- Input result.
- Regression result.

Use one graph per APK execution.

The graph must contain nodes and edges.

Node types may include:

- APK.
- CLASS_LOAD.
- METHOD_CALL.
- API_DISPATCH.
- OBJECT_STATE.
- RESOURCE.
- ASSET.
- VIEW.
- ADAPTER.
- LAYOUT.
- DRAW.
- NATIVE_LOAD.
- JNI.
- EGL.
- GLES.
- AUDIO.
- INPUT.
- STATE_MUTATION.
- FRAMEBUFFER.
- SCREENSHOT.

Edge types may include:

- CALL.
- DATA_FLOW.
- DEPENDS_ON.
- ATTACHES.
- CREATES.
- CONSUMES.
- RENDERS_TO.
- CAUSES.
- REPLACES.
- SCHEDULES.

Every important node must preserve provenance.

A resource node must tell us where its bytes came from.

A Bitmap node must identify the actual decoder and its consumer.

A View node must identify its parent and lifecycle.

A Draw node must identify the renderer and destination.

A GLES node must identify the context, target surface and actual framebuffer.

## First-divergence rules

Do not classify every NPE or null return as the root cause.

Check actual Android contracts.

Distinguish:

- Valid null.
- Invalid null.
- Unimplemented API.
- Wrong overload.
- Incorrect return value.
- Missing side effect.
- Incorrect dispatch.
- Wrong object identity.
- Incorrect state propagation.
- Missing consumer.
- Rendering failure.
- Screenshot/capture failure.

Every divergence must have:

- Exact method.
- Caller.
- Callee.
- Relevant arguments.
- Receiver identity.
- Expected contract.
- Actual result.
- Source location when available.
- Downstream effect.
- Confidence.
- Owner.

`UNOBSERVED` must never be treated as `PASS`.

Support multiple independent divergences in one APK.

A View route and Native route must not overwrite one another's diagnostics.

---

# 4. PHASE C — EVERY APK GETS ITS OWN ROUTE PROFILE

This is mandatory.

Create a per-APK route profile.

Suggested:

`reports/apk_routes/<package_id>.json`

Example:

```json
{
  "apk": {
    "package": "example.game",
    "sha256": "..."
  },
  "route_profiles": [
    {
      "route_id": "main-screen-view",
      "type": "VIEW",
      "nodes": [],
      "edges": [],
      "first_divergence": "ADAPTER"
    },
    {
      "route_id": "background-media",
      "type": "MEDIA",
      "nodes": [],
      "edges": [],
      "first_divergence": null
    }
  ],
  "capabilities": [],
  "route_status": "PARTIAL",
  "visual_status": "UNVERIFIED"
}
```

This is illustrative; adapt to the actual runtime model.

Discover routes through actual execution.

Do not infer them exclusively from package names.

A single application may have:

- Startup route.
- Main-screen route.
- Login route.
- Menu route.
- Game scene route.
- Background task route.
- Media route.
- Input route.

Each route must be tested when relevant.

## Shared route intersections

A single capability such as `ViewGroup.addView` may be used by many applications.

A capability such as `EGLContext` may serve multiple native games.

A capability such as `AssetManager.open` may serve View applications and native game engines.

Shared capabilities must be centrally implemented and reused.

But each application must independently demonstrate that its route actually consumes them.

Do not assume the same downstream behavior merely because two APKs call similarly named APIs.

---

# 5. PHASE D — MAIN CODER MUST ACTIVELY INTEGRATE EVERY USEFUL CONTRIBUTION

This is a critical ownership requirement.

The helper coders are not independent MiniAndroid projects.

They are contributors to the same runtime.

Main coder must actively retrieve and consume their work.

Implement the following process:

`DISCOVERY → EVIDENCE REVIEW → PATCH VERIFICATION → MAIN SOURCE INTEGRATION → MAIN BUILD → REAL APK EXECUTION → REGRESSION → TRACKER UPDATE`

## Separate two independent status systems

### Engineering adoption

`DISCOVERED`
`EVIDENCE_VERIFIED`
`REVIEWED`
`ACCEPTED`
`SOURCE_INTEGRATED`
`BINARY_INTEGRATED`
`BLOCKED`
`REJECTED`
`SUPERSEDED`

### Actual runtime impact

`UNOBSERVED`
`NO_CHANGE`
`LOCAL_CONTRACT_VERIFIED`
`CHAIN_ADVANCED`
`PARTIAL_CHAIN`
`CROSS_APP_VERIFIED`
`VISUAL_VERIFIED`
`INTERACTIVE_VERIFIED`
`REGRESSION_VERIFIED`

An integrated implementation may still have no demonstrated APK consumer.

A locally tested patch may still be absent from the main runtime.

Keep the two statuses separate.

For every useful fix, record:

- Contributor.
- Source Issue.
- Source SHA.
- Base SHA.
- Patch hash.
- Capability ID.
- Affected route types.
- Consuming APKs.
- Main integration commit.
- Main binary identity.
- Before/after FDT.
- Actual result.
- Remaining blockers.

Main coder is the integration authority.

But evidence, not authority alone, determines acceptance.

---

# 6. PHASE E — RECOVER THE ACTUAL VIEW AND DRAW PIPELINE

Prioritize actual incomplete View applications.

Start with gmdice and unote.

However, do not assume they have identical routes.

## gmdice

Follow:

`Activity → ListActivity → ListView → Adapter → getView → Row Inflation → addView → Measure → Layout → Draw`

Investigate:

- setListAdapter.
- Adapter identity.
- getCount.
- getItem.
- getItemId.
- getView.
- Row resource.
- LayoutInflater.
- convertView.
- child ownership.
- child attachment.
- notifyDataSetChanged.
- LayoutParams.
- actual drawing.
- Scroll behavior.

The known problem is that adapter data can grow while actual visible rows remain zero.

Fix the lowest shared root.

Do not manufacture rows for this application.

The real Adapter must produce real Views.

## unote

Investigate:

- Toolbar construction.
- Toolbar children.
- Custom child insertion.
- LayoutParams.
- Child ownership.
- Drawing traversal.
- Canvas propagation.
- render-task creation.
- Framebuffer delivery.

The existence of a Toolbar child is not evidence that it was rendered.

Trace the exact point where the child disappears from the rendering path.

## Shared View system

Complete generic behavior:

- View construction.
- ViewGroup child management.
- LayoutParams.
- MeasureSpec.
- onMeasure.
- requestLayout.
- onLayout.
- dispatchDraw.
- invalidation.
- backgrounds.
- Drawable bounds.
- padding and margins.
- visibility.
- text rendering.
- image rendering.
- clipping.
- transforms.
- scrolling.
- Z-order where required.

Use AOSP contracts.

Do not implement isolated screenshot-specific fixes.

---

# 7. PHASE F — COMPLETE THE LIBGDX AND NATIVE GAME ROUTES

Use TicTacToe and Bouncy as priority reproductions.

Follow the actual game execution path:

`DEX → Native Engine → JNI → AssetManager → AsyncExecutor → I18N → Texture → GL → Framebuffer`

Investigate and integrate:

- StringBuilder packed implementations.
- replaceAll.
- Stack.
- ExecutorService.submit.
- Future.
- AsyncExecutor.
- FileHandle.
- AssetManager.
- I18NBundle.
- Native loading.
- JNI registration.
- EGL.
- GLES.
- Texture upload.
- Shader compile/link.
- Render loop.
- Input callbacks.

The S187 changes must reach the actual main runtime.

Do not stop when `AssetManager.open` starts working.

Do not stop when an I18N file is opened.

Do not stop when the GL context is created.

Require an actual game menu or scene.

For Mindustry, continue the existing Native GL work independently.

A loading Grid is a useful intermediate result.

It is not a completed game.

---

# 8. PHASE G — OTHER REAL APPLICATION ROUTES

Integrate the work of all contributors where it benefits actual APKs.

### Coder 2 — Framework / AndroidX

- Activity.
- Fragment.
- FragmentManager.
- Lifecycle.
- ViewModel.
- SavedState.
- ViewTree owners.
- AndroidX dependencies.
- Real framework implementation reuse.

### Coder 4 — Java / Kotlin / API semantics

- Collections.
- Strings.
- StringBuilder.
- UUID.
- ParcelUuid.
- Exception identity.
- SQLite callbacks.
- PackageManager API behavior.
- Other verified shared laws.

### Coder 6 — Native / Graphics / Audio

- libGDX.
- SDL.
- Box2D.
- Arc.
- SoLoud.
- Native loader.
- EGL/GLES.
- Audio engines.
- Native application compatibility.

### Coder 7 — Storage / Package Manager

- SQLite.
- Package index.
- Cross-package resolution.
- SharedPreferences.
- URI.
- File paths.
- Database persistence.
- Android component behavior.

### Coder 8 — Concurrency

- Thread.
- ExecutorService.
- Future.
- Handler.
- Looper.
- CompletableFuture.
- Locks.
- Queues.
- Scheduled work.
- Actual scheduling semantics.

### Coder 9 — Resources

- ARSC.
- Bitmap.
- BitmapFactory.
- Drawable.
- AssetManager.
- Font resources.
- Density.
- Resource configuration.
- NinePatch.
- VectorDrawable.

Main coder must connect all these areas.

A resource implementation must be accessible to ImageView.

An Executor implementation must be accessible to libGDX.

A native-library implementation must be accessible to the real APK loader.

An AndroidX lifecycle fix must be usable by every applicable application.

Do not let contributor boundaries become runtime boundaries.

---

# 9. PHASE H — LIBRARY ACQUISITION MUST BE ROUTE-DRIVEN

Follow S185.

Do not add every famous library.

Inspect the failing application route first.

If an existing implementation is present and correct, reuse it.

If it exists but is unreachable, repair the connection.

If there is a genuine capability gap, search for an upstream implementation and evaluate it.

Potential candidates include:

- Skia for actual 2D raster operations.
- Mesa/llvmpipe for a suitable software GL route.
- GL4ES for applicable legacy OpenGL compatibility.
- SDL2/SDL3 for SDL-based application routes.
- FFmpeg for real media consumers.
- libyuv for pixel-format conversion.
- libzip/minizip-ng for ZIP and asset access.
- libcurl for HTTP networking.
- OpenAL Soft for native spatial audio.
- AndroidX source for missing framework/component behavior.

None of these must be imported without a verified consumer and missing capability.

For each integrated library:

- Pin revision.
- Verify license.
- Build reproducibly.
- Keep bulky source and binaries outside Git.
- Record build provenance.
- Prove runtime loading.
- Prove real APK consumption.
- Measure resource cost.

The objective is maximum compatibility improvement, not maximum dependency count.

---

# 10. PHASE I — REPRODUCE S186i AND PREVENT FURTHER REGRESSIONS

The supplied S186i report is an important baseline.

Reproduce:

- Exact hybrid source.
- Exact build configuration.
- The 41-title battery.
- The claimed 29 zero-uncaught results.
- Both A_RICH results.
- The new generic laws.
- The regression comparison.
- Bouncy and unote golden pins.
- All remaining incomplete titles.

Do not combine observations from multiple binary revisions.

Use one identified final integration binary for each final matrix.

Preserve the known S186h ARITY regression findings.

If a fix improves one route but breaks another, identify the exact causal relationship.

The S186i experiment must be independently validated.

If any part cannot be reproduced, record it as unverified rather than assuming success.

However, do not allow this reproduction task to block new high-value graphical recovery work.

---

# 11. PHASE J — BUILD A SMART RECOVERY PRIORITY SYSTEM

This is where the system becomes much more powerful.

Do not select the next task by whichever coder submitted the most recent report.

Do not choose the easiest API to implement.

For each incomplete APK, calculate:

- Route type.
- Current maximum stage reached per route.
- First divergence per active route.
- Common capabilities already available.
- Missing capabilities.
- Shared root candidates.
- Expected recovery probability.
- Required engineering effort.
- Existing regression risk.
- Expected number of other APK consumers.

Group applications by confirmed shared roots.

Example:

```text
Root: Adapter row materialization

Affected:
    gmdice
    application-B
    application-C

Required:
    getView
    layout inflation
    child attachment
    layout
    draw

Owner:
    Coder 3

Integration:
    Main
```

A different group:

```text
Root: libGDX packed StringBuilder

Affected:
    TicTacToe
    application-D
    application-E

Required:
    correct StringBuilder behavior
    I18N parsing
    asset consumption

Owner:
    Coder 4 / Coder 3

Integration:
    Main
```

A graphics group must remain distinct from a View/Adapter group unless evidence establishes a shared lower-level defect.

**Never assume that two applications share a root merely because both display a blank screen.**

The first-divergence evidence must establish the relationship.

When a generic fix advances only some consumers, record exactly which routes advanced and identify the new blockers for the others.

This is not a failed global fix.

It is useful information about the diversity of application routes.

---

# 12. PHASE K — SMALL APPLICATION RECOVERY BATTERY

Start with a representative group of small applications and games.

Required diagnostic paths:

- gmdice — Adapter/View.
- TicTacToe — libGDX/Asset/I18N.
- Mindustry — Native GL.
- Bouncy — established rendering regression anchor.

Select at least ten eligible corpus titles from S107/S115 for initial route discovery.

Possible targets:

- uturn.
- pfsolitaire.
- foehnix.widget.
- aoc_normal.
- queens.
- tarok.
- astroloop.
- nightbell.
- newsblur.
- opentopo.
- taz.
- gnubg.
- boxcars.
- halma.
- p9.
- other genuinely small titles present in the verified corpus.

Re-check their actual APKs and versions before testing.

Do not force all of them through the same route.

Select at least five recovery targets from different route families when feasible.

For example:

- View/Adapter application.
- Simple Canvas game.
- libGDX game.
- Native graphics game.
- AndroidX or Resource-heavy application.

The exact five must be selected using current evidence, not guesses.

## The first milestone

At least five small applications/games must display their actual application-owned initial graphical interfaces on the SAME integrated runtime binary.

This must include:

- Real application interface.
- Correct visible content.
- Real text where applicable.
- Real resources and images where applicable.
- Real ViewTree or native scene.
- No unexplained default-background-only state.
- No two-color-and-font false success.
- No relevant uncaught failure on the tested path.
- Correct framebuffer provenance.
- At least one meaningful interaction where the application supports it.

Perform three independent recovery runs.

Do not require a complete long gameplay session for the first milestone, but prove a real application state transition for interactive titles.

After the initial five, continue across all eligible small titles.

Do not stop after five.

---

# 13. A_RICH MUST MEAN REAL GRAPHICAL RECOVERY

Inspect the project's canonical A_CLEAN and A_RICH definitions before applying them.

Preserve existing classification semantics.

A_RICH must not be inferred from:

- Zero exceptions alone.
- Activity RESUMED alone.
- Non-black pixels alone.
- High unique color count alone.
- A loaded font.
- A successful library initialization.
- A loading background.
- A successful GL clear operation.

A real graphical result requires the application's own content.

For View applications, prove:

- Expected ViewTree.
- Actual attached children.
- Measurement.
- Layout.
- Draw operations.
- Actual application text/images/components.
- Framebuffer contribution.

For native games, prove:

- Actual engine execution.
- Real render calls.
- Required resources.
- Correct texture or geometry contribution.
- Actual framebuffer content.
- Application-specific scene/menu content.

Inspect screenshots.

Metrics supplement visual verification; they do not replace it.

For every accepted graphical result, retain:

- Screenshot.
- SHA256.
- Application identity.
- Runtime binary identity.
- Route graph.
- Resource provenance.
- ViewTree or native scene summary.
- Draw summary.
- Framebuffer provenance.
- Three-run comparison.

---

# 14. PHASE L — REGRESSION AND PERFORMANCE

Do not run the complete corpus after every trivial edit.

Use:

- Focused contract tests after a patch.
- Relevant APK tests after the integration.
- Full 30-title battery for release candidates.
- Full affected group after a shared-root fix.
- Three independent executions for each accepted recovery milestone.

Preserve the current canonical golden anchors:

- Bouncy.
- Dooz.
- Tower3D.
- Unote.
- Other established goldens discovered in current HEAD.

Retrieve their exact hashes from current test definitions.

Do not invent or reuse stale hashes.

Benchmark:

- Build time.
- Startup.
- DEX execution.
- API dispatch.
- ViewTree construction.
- Measure/layout.
- Drawing.
- Native initialization.
- Frame time.
- Memory.

FDT OFF should have no measurable overhead beyond baseline variability.

Measure enabled trace modes instead of inventing performance ratios.

Keep instrumentation bounded.

The runtime must remain usable on constrained CPU/RAM environments.

Use the authoritative current build configuration.

Verify the Makefile/CMake relationship rather than assuming either is correct.

Use the precise source list.

Do not compile unrelated translation units.

A clean checkout must reproduce the required dependency bootstrap and integrated runtime build.

---

# 15. ISSUE AND WORKLOG GOVERNANCE

Do not create a new GitHub Issue for every small improvement.

Update existing living trackers.

Use:

- #536 for S185/S186/S188 governing rules.
- #472 for the achievement ledger.
- #492 for the main dashboard.
- #475 for TicTacToe.
- #441 for Mindustry.
- Relevant existing application trackers for every recovered title.
- Existing coder worklogs for implementation history.

A tracker must reflect the latest actual runtime result.

When an application improves, update its existing Issue immediately.

Do not leave old Background-only status after a real graphical recovery.

Do not close an Issue because an API test passed.

Maintain:

- Current status.
- Exact source SHA.
- Main binary SHA.
- Current route.
- First divergence.
- Recent progress.
- Remaining blocker.
- Actual graphical acceptance evidence.

The main dashboard must show the real recovered application count, not the total number of successful API tests.

---

# 16. EXECUTION ORDER — START WORK, NOT ANOTHER PLANNING PHASE

Run these phases in sequence while allowing independently useful research and focused tests to proceed in parallel.

### PHASE A — RECONCILIATION

1. Inspect current main.
2. Reconcile all relevant Coder 2–9 achievements.
3. Verify S186i.
4. Identify existing and missing integrations.
5. Create the shared adoption ledger.
6. Establish one authoritative baseline binary.

### PHASE B — ROUTE-AWARE FDT

1. Define the graph schema.
2. Implement minimal instrumentation.
3. Implement contract-aware divergence classification.
4. Implement multiple paths per APK.
5. Implement causal relationships.
6. Implement route-level first divergence.
7. Implement root-cause aggregation.
8. Test gmdice, TicTacToe and Mindustry.

Do not spend an entire wave writing documentation.

The first FDT implementation must work on real runtime executions.

### PHASE C — HIGHEST-IMPACT VIEW RECOVERY

1. Finish gmdice's real Adapter rows.
2. Complete unote Toolbar child rendering.
3. Verify actual measure/layout.
4. Verify Draw propagation.
5. Capture application-owned framebuffer content.

### PHASE D — GAME ENGINE RECOVERY

1. Finish TicTacToe StringBuilder and I18N.
2. Complete real asset loading.
3. Complete required native registration.
4. Complete GL execution.
5. Verify actual menu/game scene.
6. Preserve Bouncy golden behavior.
7. Continue Mindustry independently.

### PHASE E — CROSS-APPLICATION RECOVERY

Apply the verified generic framework, Java, AndroidX, Resource, Native and Concurrency fixes to their actual consumers.

After every shared fix:

- Re-run the relevant consumer routes.
- Identify newly exposed root causes.
- Do not assume all affected APKs advanced equally.

### PHASE F — FIVE-TITLE ACCEPTANCE

Achieve five genuine small-title graphical recoveries.

All five must use the same main-runtime binary.

Run three independent executions.

Preserve existing goldens.

### PHASE G — FULL ELIGIBLE CORPUS

Expand from the five-title milestone to all eligible small titles.

Cluster by confirmed root cause.

Continue until each title is:

- VISUAL_VERIFIED.
- INTERACTIVE_VERIFIED where applicable.
- BLOCKED with an exact reproducible root cause.
- REJECTED because of verified APK incompatibility or another explicit reason.

Do not silently abandon difficult titles.

---

# 17. FINAL DELIVERABLES

The main coder must produce:

1. `runtime_capabilities.json` — one shared capability registry.
2. Shared-Fix Adoption Ledger.
3. Route-aware FDT implementation.
4. Contract-aware divergence classifier.
5. One execution graph per tested APK run.
6. Route profiles for the recovery cohort.
7. First-divergence aggregation.
8. Chain ownership matrix.
9. Chain acceptance rubric.
10. Reproducible clean-checkout build.
11. Exact S186i reproduction results.
12. Unified integrated binary identity.
13. Updated existing application trackers.
14. A list of verified generic fixes and their real consumers.
15. A complete five-title graphical recovery evidence package.
16. The remaining incomplete-title matrix.
17. A prioritized next-root report.

The final report must separate:

- Source-only achievements.
- Harness-only achievements.
- Main-binary integrations.
- Real APK execution.
- Visual recovery.
- Interactive recovery.
- Three-run verified recovery.

No double counting.

No unsupported success claims.

---

# 18. THE FINAL RULE — WHAT YOU ARE ACTUALLY BEING ASKED TO DO

You have many useful people working on different parts of the project.

Your responsibility is to make their work converge.

Do not make every APK follow the same route.

Discover the real route of each APK.

Connect shared capabilities where they genuinely intersect.

Keep different execution paths independent where they differ.

When an application advances, identify its next actual blocker.

When a shared fix advances several applications, prove which ones benefited.

When a fix does not help another application, do not force the same fix into that unrelated route. Investigate its own first divergence.

The purpose of FDT is to expose the actual route.

The purpose of the capability registry is to make existing work reusable.

The purpose of Chain Contracts is to prevent false success.

The purpose of the Adoption Ledger is to ensure contributor work reaches the main binary.

The purpose of the main integration process is to make the application work.

**DO NOT STOP AFTER RECONCILIATION.**

**DO NOT STOP AFTER BUILDING FDT.**

**DO NOT STOP AFTER ZERO UNCAUGHT EXCEPTIONS.**

**DO NOT STOP AFTER LOADING A LIBRARY.**

**DO NOT STOP AFTER DISPLAYING A BACKGROUND, TWO COLORS OR A FONT.**

Complete the first real graphical recovery, then the second, then the third, until at least five different small applications and games genuinely display their own interfaces through one unified runtime.

Then continue across the eligible corpus.

Use all existing achievements.

Use all relevant contributors.

Reuse existing libraries.

Fix shared roots.

Preserve regressions.

Update old Issues.

Produce working code.

Prove actual execution.

**The objective is to transform MiniAndroid from a collection of partially successful subsystems into one integrated runtime capable of executing real Android applications and games.**

Start executing against the current repository state now.

Do not ask for another confirmation.

Do not return only a plan.

Do not end the work with another report describing possible solutions.

Deliver integrated code, actual application recovery, and reproducible graphical evidence. If an individual route remains blocked, document its exact first divergence and immediately continue with the next recoverable route rather than letting one difficult application block the entire campaign.
