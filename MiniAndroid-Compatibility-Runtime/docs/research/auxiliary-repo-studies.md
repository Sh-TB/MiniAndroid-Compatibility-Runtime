# Auxiliary Repository Studies — Task 5 (source-level, exact-URL law)

Campaign: MINIANDROID REPOSITORY RESEARCH (Task ID 5, 2026-09-05).
Law: exact URL only, identity verified before study, revision locked (shallow
clone into `../../../research-clones/`), no repository substituted, license
checked from the LICENSE file in the clone. MiniAndroid source untouched;
this is the only docs/research/*.md file created or modified by this task.

Prior-studied repositories (external-repositories.md rows 1–24) were NOT
re-studied. All 5 targets below are new.

| # | Project | Exact URL | Branch | Revision studied (HEAD SHA) | License | Status |
|---|---------|-----------|--------|----------------------------|---------|--------|
| 1 | Android-RRO | https://github.com/mirzachi/android-rro | main | `a113f0a56a4ea680f41a0dd0c9522b3ab022c47b` (2021-09-23, "Update README.md") | MIT | REVIEWED |
| 2 | Android-Dex | https://github.com/Shrey113/Android-Dex | main | `c57cbc803929b5b12cb865f63efa67c7b9c2f410` (2026-08-27, "set zo[") | NONE (closed source per README badge; no LICENSE file) | REVIEWED |
| 3 | dexterpreter | https://github.com/vimalloc/dexterpreter | master | `b83d151355d09ffe47f0bd9a775d57f45dcf4445` (2012-11-01, "Make store lookup a fp,var pair") | NONE (no LICENSE file) | REVIEWED (URL verified, not URL_UNVERIFIED) |
| 4a | Robolectric | https://github.com/robolectric/robolectric | master | `fc357fec8ef3157f2ac1a30743d15f4b96090736` (2026-08-31) | MIT | REVIEWED |
| 4b | Paparazzi | https://github.com/cashapp/paparazzi | master | `716755fb5ebe5fa852386d7531ac74717104b144` (2026-09-04) | Apache-2.0 | REVIEWED |
| 4c | Roborazzi | https://github.com/takahirom/roborazzi | main | `6abd5fc0a780e2ee8c4509917c33f62682df8ccc` (2026-08-25) | Apache-2.0 | REVIEWED |
| 4d | Shot | https://github.com/Karumi/Shot | master | `e102d797d87fe212c52b235f71954f08ca502cb2` (2026-01-16) | Apache-2.0 | REVIEWED |
| 4e | Dropshots | https://github.com/dropbox/dropshots | main | `70b8cbfd587b5c251cb9ca3cb22745d33309a632` (2026-06-26) | Apache-2.0 | REVIEWED |
| 5 | sim-use | https://github.com/SimulaVR/sim-use | — | — | — | **REPOSITORY_UNAVAILABLE** (retry recorded, §5) |

Clone/access notes: full shallow clones for android-rro, Android-Dex,
dexterpreter, paparazzi, roborazzi, Shot, dropshots. Robolectric is a
blobless partial clone (`--filter=blob:none --no-checkout`); cited files read
via `git show HEAD:<path>`. GitHub REST API (`api.github.com`) returned HTTP
403 (anonymous rate limit for this IP) for the whole session — repository
metadata was therefore obtained from the clones themselves, `git ls-remote`,
and GitHub HTML pages.

---

## §1 Android-RRO — https://github.com/mirzachi/android-rro

Branch `main`, HEAD `a113f0a`, 2021-09-23. License: MIT
(`LICENSE`, "Copyright (c) 2021 mirzachi").

Identity verification: README first paragraph self-identifies — "This
repository is a collection of diagrams and other resources that explain the
internals of the Android´s Runtime Resource Overlay (RRO) mechanism."
IMPORTANT DISAMBIGUATION: this is a DIFFERENT project from
`MartinStyk/Android-RRO` (mentioned without URL in an earlier campaign
worklog). The mandated URL `mirzachi/android-rro` was cloned; no substitution.

Repo nature: documentation-only (README.md ~15 KB + `images/*.png|svg` +
`puml/*.puml` PlantUML sources). There is no executable code, so every
mechanism citation below points at README sections and the verbatim AOSP
struct excerpts embedded in the .puml diagrams.

### RRO-001 — Overlay package format and target declaration
- WHAT IT DOES: an RRO is "a regular APK with a few caveats": no bytecode;
  overlayed resources must carry the SAME resource names as the target APK;
  the manifest contains an `<overlay>` tag naming the target package.
- WHERE IMPLEMENTED (in this repo): README.md, section "### Format" (lines
  ~228–235) + `images/resources4.png`.
- FUNCTION: N/A (doc repo) — the three caveats are the contract.
- WHY IT MATTERS TO MINIANDROID: it pins what would need to be accepted if
  overlay support were ever attempted; also proves overlays never contain
  DEX, so an overlay APK would only exercise MiniAndroid's resource runtime.
- CAN WE ADAPT IT: NO for now.
- HOW: record the contract in the reference matrix; revisit only if
  MiniAndroid ever ships an installable-package layer.
- LICENSE: MIT. TEST NEEDED: none (not transferred).

### RRO-002 — Overlay precedence at equal configuration
- WHAT IT DOES: "For resources with the same qualifiers, the system prefers
  the overlayed resource always" (README "### Lookup"); the note in
  `puml/getResource.puml` (AssetManager2::FindEntry, lines 76–82) states the
  precise rule: "First the normal packages are searched, then overlayed and
  it is then compared whether the overlayed is a better match than the normal
  one. The configuration of the entry for the overlay must be equal to or
  better than the target configuration to be chosen as the better value."
- WHERE IMPLEMENTED (upstream, as documented here): androidfw
  AssetManager2::FindEntry / PackageGroup search order.
- FUNCTION: FindEntry(id, …) — best-match across PackageGroup; overlay wins
  ties, never loses on equal config.
- WHY IT MATTERS TO MINIANDROID: this is a two-part law MiniAndroid's
  resource runtime should keep in its res_config best-match implementation:
  (a) explicit tie-break (equal config ⇒ later/higher-priority package wins),
  (b) the "equal or better" comparison is asymmetric, not a score.
- CAN WE ADAPT IT: CONCEPT ONLY today.
- HOW: when MiniAndroid gains multi-APK resource support (split APKs,
  `ApplicationInfo.resourceDirs` analog), reuse exactly this search order and
  tie-break; until then, assert single-package determinism (our current
  corpus never has equal-config duplicates).
- LICENSE: MIT. TEST NEEDED: a two-APK fixture at the time split-APK support
  is built.

### RRO-003 — idmap reverse mapping
- WHAT IT DOES: overlay package resource ids differ from target ids; the
  `idmap`/`idmap2` tool computes, per overlay entry, the mapping to the
  target's numeric id "using the resources.arsc to perform the reverse
  mapping, name and type to target unique numerical qualifier" (README
  "### Lookup"); `puml/AssetManager.puml` models `AssetManager2.IdmapResMap`
  inside `ConfiguredOverlay` ("a mapping of target resource ids to a values
  or resource ids that should overlay the target"); `ApkAssets` holds
  `idmap_asset_` + `loaded_idmap_` (quoted struct in `puml/getResource.puml`
  lines 28–39).
- WHERE IMPLEMENTED (upstream): frameworks/base/cmds/idmap2; androidfw
  LoadedIdmap (as excerpted in the diagrams).
- FUNCTION: idmap generation = name+type → target id resolution at overlay
  install; lookup = per-target-id indirection into the overlay package.
- WHY IT MATTERS TO MINIANDROID: none for single-APK compatibility; the
  reverse-mapping idea (resolve by name+type, cache id→id) is exactly the
  mechanism a future overlay or shared-library support would need.
- CAN WE ADAPT IT: NO (REJECTED with reason: requires an overlay
  installation model MiniAndroid does not have).
- HOW: keep the citation for the deferred multi-APK milestone.
- LICENSE: MIT. TEST NEEDED: none.

### RRO-004 — PackageGroup / ConfiguredPackage / ConfiguredOverlay model
- WHAT IT DOES: `PackageGroup` = logical package with same name/id: vectors
  of `ConfiguredPackage` (immutable `LoadedPackage*` +
  `filtered_configs_` pre-filtered to the current configuration — an
  optimization "to avoid checking every single candidate configuration"),
  per-package cookies, `overlays_` (ConfiguredOverlay with IdmapResMap), and
  a `DynamicRefTable` for build→runtime package id remapping (shared
  libraries). Quoted verbatim in `puml/AssetManager.puml` lines 40–75.
- WHY IT MATTERS TO MINIANDROID: two transferable data-structure ideas:
  (a) pre-filtering type configs against the device configuration at load
  time (what `res_config` could cache instead of re-scanning per lookup);
  (b) the DynamicRefTable concept (package-id remapping) is what
  `TYPE_DYNAMIC_REFERENCE` values (0x07) in real ARSCs need when apps use
  shared libraries.
- CAN WE ADAPT IT: (a) ADAPTABLE as an optimization when ARSC lookups become
  hot; (b) REJECTED for now (no shared-library APKs in the corpus).
- HOW: (a) memoize matched-config lists per type chunk during arsc parse.
- LICENSE: MIT. TEST NEEDED: perf-only; differential ARSC fixtures already
  queued (arsc-resource-study.md ARSC-003) would catch regressions.

### RRO-005 — Overlay deployment flow (OMS/PMS/AMS) and resource reload
- WHAT IT DOES: full sequence in `puml/oms-interactions.puml`:
  setEnabled → handleIncomingUser → enforceActor → updateInternalState →
  PMS.setEnabledOverlayPackages (PackageSetting/PackageUserState) →
  affectedTargets → AMS.scheduleApplicationInfoChanged → PMS.getApplicationInfo
  → app.handleApplicationInfoChanged → diff ApplicationInfo → new
  ResourcesImpl (new AssetManager with new ApkAssets; cached APKs reused,
  overlay APKs loaded from disk) → ResourcesManager->
  applyNewResourceDirsLocked → reset caches → onConfigurationChanged →
  relaunch all activities with windows preserved (README "### RROs on the
  system level", lines 237–267). `ApplicationInfo.resourceDirs` (paths to
  runtime overlays) is the field that carries overlay paths into the app.
- WHY IT MATTERS TO MINIANDROID: MiniAndroid will never need OMS, but the
  *reload protocol* is the upstream answer to "what must happen when the
  set of resource APKs changes at runtime": rebuild ResourcesImpl, swap
  atomically, keep windows. Not applicable to our single-shot replay model.
- CAN WE ADAPT IT: NO (REJECTED — no lifecycle service layer).
- LICENSE: MIT. TEST NEEDED: none.

### RRO-006 — Res_value model and string/file double-lookup (confirmation)
- WHAT IT DOES: README lines 75–210 quote `Res_value` verbatim from
  androidfw ResourceTypes.h (TYPE_* enum incl. DYNAMIC_REFERENCE 0x07 /
  DYNAMIC_ATTRIBUTE 0x08; COMPLEX_UNIT_* / COMPLEX_RADIX_* layouts;
  DATA_NULL_UNDEFINED/EMPTY) and state the lookup chain: strings = data is
  offset into the string pool (+1 lookup); files = data → string pool entry
  → path inside APK (+2 lookups).
- WHY IT MATTERS TO MINIANDROID: independent confirmation of the resolution
  chain already pinned in arsc-resource-study.md ARSC-005 — including the
  two nuance fields we had not previously cited: `DATA_NULL_EMPTY` (explicit
  empty value) and `TYPE_DYNAMIC_REFERENCE` (deferred resolution).
- CAN WE ADAPT IT: ADAPTABLE as test vectors.
- HOW: add (1) a `TYPE_NULL/data=DATA_NULL_EMPTY` fixture (our parser must
  not treat it as string offset 1), (2) a `TYPE_DYNAMIC_REFERENCE` probe to
  the ARSC differential fixture plan (currently unimplemented semantics —
  same family as the queued SPARSE/OFFSET16 gap).
- LICENSE: MIT. TEST NEEDED: two fixtures above (queued).

### §1 verdict
Transfer decision: REJECTED for RRO proper (needs an OMS/PMS/AMS system
service layer + idmap tooling that is out of MiniAndroid's scope, and
real apps in the corpus never invoke RRO semantics). Carried over as
REFERENCE for a future split-APK/multi-APK milestone (RRO-002/004/005
semantics), and RRO-006 adds two concrete test vectors to the existing ARSC
fixture queue. Answer to the study question: **MiniAndroid's resource
runtime does NOT need RRO semantics for the current single-APK corpus; it
does need the RRO-006 Res_value edge semantics (NULL-empty,
dynamic-reference) which apply to ordinary ARSCs.** Status: REVIEWED.

---

## §2 Android-Dex — https://github.com/Shrey113/Android-Dex

Branch `main`, HEAD `c57cbc8`, 2026-08-27. License: NONE — README badge
"License: Closed Source"; no LICENSE file in the clone. ZERO code import
permitted; methodology observations only.

Identity verification: README self-identifies — "Android DEX is a free,
closed-source desktop application for Windows, Linux, and macOS that lets
you run Android apps in resizable desktop-style windows … all using
high-performance ADB and companion services over USB or Wi-Fi." Multi-platform
execution confirmed by the three download rows (Windows/Linux/macOS zips).
Releases checked per mandate: tags Android-Dex-v.0.3 → v.1.2; newest release
v.1.2 (releases page, newest-first expanded_assets list); project actively
maintained (HEAD commit 2026-08-27).

CRITICAL CLASSIFICATION (mandated): Android-Dex is a device companion /
desktop-shell product. Apps execute **directly on the user's physical Android
hardware** (README "Gaming Mode (No Emulator Detection)": "games execute
directly on your physical Android hardware"; doc/ARCHITECTURE.md Layer
diagram: everything runs through ADB against a real device). Per campaign
law this is **NOT compatibility-runtime proof of any kind** — no APK is
re-implemented, interpreted, or translated by Android-Dex. It maps to
MiniAndroid only as *tooling methodology* for our runner/diagnostics.

Architecture (doc/ARCHITECTURE.md): three layers —
(1) Windows-side orchestrator (Flutter UI, ADB lifecycle, four inbound
TCP/WebSocket servers, scrcpy embedding as Win32 child windows);
(2) Logic Engine: a Java JAR pushed to `/data/local/tmp/` and launched via
`adb shell app_process` (shell-UID privileges: ActivityManager.startActivity/
forceStopPackage, PowerManager, AudioManager);
(3) Feature Hub: a Kotlin companion APK in the app context
(NotificationListenerService, MediaSessionManager, BatteryManager broadcasts).
Reverse-port-forwarded TCP/WS with JSON handshakes. doc/scrcpy.md is a
vendored copy of upstream scrcpy v4.1's README (mirroring is scrcpy's).

### DEXAPP-001 — Two-tier error messaging law
- WHAT IT DOES: "Technical information stays in dev logs. Plain English
  reaches the user" (doc/ERROR_HANDLING.md). Dev tier: raw stderr, exit
  codes, paths. User tier: actionable messages, one table row per failure
  site (AdbProvider, JarManager, AppManager, ReconnectionManager, ...).
  Pipeline: exception → strip `"Exception: "` prefix → `_log(isError)` →
  `Stream<AppEvent>`/`Stream<JarEvent>` → `_ErrorBox` in UI.
- FUNCTION: complete message reference table, ERROR_HANDLING.md
  "Complete Error Message Reference".
- WHY IT MATTERS TO MINIANDROID: our probe/runner reports
  (docs/campaign014_evidence/*/report.md + api_trace.json) already split
  machine JSON from human report; Android-Dex's per-failure-site message
  table is the same discipline formalized — most directly applicable to the
  runner CLI's failure prints (load fail vs exec fail vs frame-mismatch).
- CAN WE ADAPT IT: YES (methodology).
- HOW: give every runner failure site a stable short label + one-line user
  meaning + dev detail line, mirroring the table shape.
- LICENSE: NONE (closed source) — methodology only, no code/text copied.
- TEST NEEDED: none (documentation convention).

### DEXAPP-002 — Deterministic boot ladder with handshake timeouts
- WHAT IT DOES: fixed 11-step APP progress ladder (0.02→1.00, one stable
  user message per step: doc/BOOT_FLOW.md table) + an independent 7-step JAR
  ladder; each blocking step has an explicit timeout (jar.hello/apk.hello
  handshakes: 15 s, with dedicated timeout messages). Two independent event
  streams feed two progress bars; UI unlocks only at both 1.00.
- FUNCTION: `AppManager.initializeSystem()` emits `AppEvent{message,
  progress,isError}` per step (doc/MODULES.md "AppManager"); `JarManager`
  `jarReady: Completer<void>` completes on handshake.
- WHY IT MATTERS TO MINIANDROID: our runner phases (parse → link → execute →
  render → frame) could adopt named progress steps with stable labels so
  logs across corpus runs are diffable, and bounded-wait semantics for
  external interactions.
- CAN WE ADAPT IT: YES (methodology).
- HOW: define the runner's step ladder as data (step id, label, failure
  label), emit per-step events into the report JSON.
- LICENSE: NONE. TEST NEEDED: none.

### DEXAPP-003 — Failure-taxonomy classifier gating recovery
- WHAT IT DOES: boot screen decides whether to offer recovery ("Open ADB
  Manager") by keyword-classifying the error message: `_isConnectionError`
  matches connect/device/adb/network/refused/timeout/unreachable/bridge
  (doc/ERROR_HANDLING.md "Connection Error Detection", code quoted).
  Connection-class errors → recovery affordance; other classes → terminal
  message only.
- WHY IT MATTERS TO MINIANDROID: mirrors our diagnostic-taxonomy finding
  (dex-runtime-study.md DEX-007: "ends at reflection is a NORMAL healthy
  stop, not a bug"). The pattern — classify the failure, then choose the
  affordance — is exactly what our probe reports should do when deciding
  between "retry", "file bug", and "expected stop".
- CAN WE ADAPT IT: YES (methodology).
- HOW: classify runner stop reasons (PARSE/LINK/API/REFLECTION/TIMEOUT/
  RENDER/ASSERT) and print the taxonomy class in report.md so stop points
  are machine-greppable.
- LICENSE: NONE. TEST NEEDED: none.

### DEXAPP-004 — Reconnection ladder (graded retry, bounded)
- WHAT IT DOES: doc/RECONNECTION.md: watchdog on two connection notifiers;
  Phase 1 quick reconnect (re-`adb connect`, re-`adb reverse`, wait for both
  channels, no re-deploy) → Phase 2 full restart (stopJar→killJar→pushJar→
  startJarRuntime→startServerService, up to 2 attempts) → permanent FAILED
  state with distinct messages for clean disconnect vs unexpected failure.
  `_busy` flag prevents concurrent recovery.
- WHY IT MATTERS TO MINIANDROID: a bounded, graded retry policy with
  distinct user-facing states is a good shape for runner re-runs and for
  future device-in-the-loop validation, but MiniAndroid's deterministic
  replay mostly needs "fail fast, keep artifacts" — so only the *shape*
  transfers.
- CAN WE ADAPT IT: PARTIAL (methodology).
- HOW: if/when the runner gains a re-run mode: quick re-run (reuse parsed
  artifacts) before full re-parse; cap attempts; distinct terminal state.
- LICENSE: NONE. TEST NEEDED: none.

### DEXAPP-005 — Screenshot capture / UI / backend-frontend separation
- WHAT IT DOES: screen content is obtained by embedding **scrcpy v4.1**
  windows (H.264 over ADB) into the desktop app; UI is Flutter; backend
  (device side) and frontend (desktop side) communicate over JSON TCP/WS
  with hello-handshakes. No on-app screenshot/pixel-compare logic of its own
  was found in the docs (doc/scrcpy.md = upstream scrcpy README).
- WHY IT MATTERS TO MINIANDROID: none for frame hashing (scrcpy is a live
  video path, lossy by design — the opposite of our deterministic
  framebuffer SHA-256 pins).
- CAN WE ADAPT IT: NO (REJECTED with reason: lossy transport; also
  physical-device execution is explicitly not compatibility proof).
- LICENSE: NONE (scrcpy itself is Apache-2.0, but we take nothing).
- TEST NEEDED: none.

### §2 verdict
Transfer decision: ADAPTABLE (methodology only: DEXAPP-001/002/003, partial
004); REJECTED as a runtime claim (physical-device execution) and REJECTED
for its capture path. No code import (no license). Runner/diagnostics
conventions are worth folding into the next runner iteration. Status:
REVIEWED (doc-level; sources are closed).

---

## §3 dexterpreter — https://github.com/vimalloc/dexterpreter

URL DISCOVERY (mandated): canonical URL was not supplied; discovery required.
- GitHub REST API search was UNAVAILABLE this session: `api.github.com`
  returns HTTP 403 anonymous rate-limit (IP 8.212.10.159) — recorded, not
  worked around with credentials.
- Discovery evidence used instead (both law-compatible):
  1. HISTORY-FIRST: MiniAndroid's own prior record
     (`docs/research/dex-runtime-study.md`, Sources section) already names
     "vimalloc/dexterpreter" — the established §18 discovery rule.
  2. FRESH SEARCH: GitHub HTML repository search
     `https://github.com/search?q=dexterpreter&type=repositories` (HTTP 200)
     yields exactly ONE repository result: `/vimalloc/dexterpreter`.
- IDENTITY VERIFIED: `git ls-remote` succeeds; README says exactly
  "dexterpreter — A Dalvik bytecode (.dex) interpreter". No ambiguity; no
  substitution. Status is therefore REVIEWED, not URL_UNVERIFIED.

Branch `master`, HEAD `b83d1513` (2012-11-01 — dormant for ~14 years).
License: NONE (no LICENSE/LICENSE.md/COPYING in tree).

Repo nature: academic Racket prototype, tiny:
- `dexterpreter.rkt` (90 lines incl. comments) — the whole interpreter.
- `JDex2Sex/` — a fork of Pall Gábor's **dedexer** (package
  `hu.uw.pallergabor.dedexer`, ~40 Java sources) extended with
  `SExpStyleCodeGenerator.java` ("Code generator for S-expression-style DEX
  code") emitting one `.sxddx` s-expression file per class.
- `sexps-hello-world/` — the output corpus: a real hello-world APK
  (com/example/myfirstapp + the whole android.support.v4 tree) disassembled
  to .sxddx, plus a `dex.log` hex dump (magic `dex\n035\0`, header fields).

### DXTP-001 — Opcode coverage (mandated question)
- WHAT IT DOES: the CESK `step` transition function implements exactly THREE
  opcode forms: `return`, `return-wide`, `return-object` (via the
  `return` match-expander that unions the three). The rest of the file is a
  COMMENT TODO list of opcode families ("move / return / const / monitor /
  switch / instance-of / array-length / new-array / throw / goto / compare /
  conditions/branches / array get|put / instance get|put / static get|put /
  invoke / conversion / arithmetic / *-quick"), referencing
  pallergabor.uw.hu's dalvik_opcodes page.
- WHERE IMPLEMENTED: `dexterpreter.rkt`, `(define (step expr ρ σ κ) ...)`.
- FUNCTION: `step` — single transition; `apply-kont` — continuation apply.
- WHY IT MATTERS TO MINIANDROID: confirms the prior campaign's README-only
  assessment at source level: opcode coverage ≈ 3/226; **no comparison or
  conversion edge cases implemented at all** (the mandated question's answer
  is negative — nothing to compare against our cmp/conv semantics; our
  interpreter is strictly ahead).
- CAN WE ADAPT IT: NO code (no license, and nothing to take).
- HOW: n/a.
- LICENSE: NONE. TEST NEEDED: none.

### DXTP-002 — CESK machine formalization (interesting structure, unusable code)
- WHAT IT DOES: models the interpreter as a state `(struct state {stmts fp
  store kont})` where `kont` frames denote "procedure return contexts AND
  exception handlers" (header comment); store is keyed by `(fp, var)` pairs
  (`lookup σ fp var`; commit message "Make store lookup a fp,var pair");
  `extend*` allocates fresh gensym addresses per binding.
- WHY IT MATTERS TO MINIANDROID: the explicit treatment of exception
  handlers as continuation frames is a clean formal model of what our
  exception_system + frame stack does imperatively; useful only as a
  semantic cross-check when reviewing our handler-search ordering
  (DEX-006).
- CAN WE ADAPT IT: CONCEPT ONLY.
- HOW: cite as a formal reference in dex-runtime-study follow-ups.
- LICENSE: NONE. TEST NEEDED: none.

### DXTP-003 — DEX→s-expression pipeline (the one transferable idea)
- WHAT IT DOES: dedexer is extended so a whole APK disassembles into
  per-class s-expression files (`.sxddx`): `(class … (super …) (source …)
  (implements …) …)` (SExpStyleCodeGenerator.generate()). The corpus proves
  it scales to a full support-library app.
- WHERE IMPLEMENTED: `JDex2Sex/src/hu/uw/pallergabor/dedexer/SExpStyleCodeGenerator.java`
  (implements `CodeGenerator`); produced corpus under `sexps-hello-world/`.
- WHY IT MATTERS TO MINIANDROID: a canonical, human-diffable intermediate
  form is a cheap differential oracle: if MiniAndroid's DEX parser can emit
  the same shape (classes → methods → instructions → operands), then for any
  corpus APK we can diff our dump against dedexer's/JADX's and the mismatch
  names the method. This folds into the already-queued DEX-008 opcode-table
  artifact and DEX-009 round-trip methodology — it is an *additional output
  format*, not a new dependency.
- CAN WE ADAPT IT: YES (methodology; emit our own format, no code).
- HOW: extend the planned `dump_dex_method`-style tooling to a tree-wide
  s-expression dump; diff against a dedexer-generated corpus as a one-off
  validation.
- LICENSE: NONE for dexterpreter; dedexer's own licensing (upstream
  project) would need checking before generating/committing any corpus.
  TEST NEEDED: one corpus APK (e.g., the tictactoe golden) round-tripped
  through both dumps.

### DXTP-004 — Test strategy
- WHAT IT DOES: the only "test" is the fixture corpus; there is NO test
  runner, no assertions, no expected outputs anywhere in the tree.
- WHY IT MATTERS TO MINIANDROID: negative evidence — a disassembly corpus
  without executable expectations never validates semantics; our fixtures
  (expected output per .dex) remain the right shape.
- CAN WE ADAPT IT: NO (anti-pattern documented).
- LICENSE: NONE. TEST NEEDED: n/a.

### §3 verdict
Transfer decision: REFERENCE ONLY (no license → zero import; 3 opcodes;
2012 vintage). The sexp-dump differential idea (DXTP-003) is the sole
transferable methodology and merges into queued DEX-008/009 work. This
closes the prior "README single line, no license" uncertainty with real
source-level evidence. Status: REVIEWED.

---

## §4 Screenshot / deterministic-testing ecosystem (5 canonical repos)

Access: full shallow clones (paparazzi 83 MB, Shot 35 MB, roborazzi 6 MB,
dropshots 1.5 MB); Robolectric via blobless partial clone with targeted
`git show`. All studied at README + source level.

### §4.1 Robolectric — https://github.com/robolectric/robolectric
master `fc357fec` (2026-08-31). License: MIT (`LICENSE`, "Copyright (c) 2010
Xtreme Labs, Pivotal Labs and Google Inc."). 2,929 tracked files.

RB-001 — Shadow architecture (map + provider + picker)
- WHAT IT DOES: framework classes are instrumented in a sandbox class
  loader; a `ShadowMap` (class-name → shadow-class, plus shadowPickerMap)
  is built from `ShadowProvider`s generated by the annotation processor
  from `@Implements` annotations; `ShadowPicker`s select among multiple
  shadow implementations per config.
- WHERE IMPLEMENTED: `sandbox/src/main/java/org/robolectric/internal/bytecode/ShadowMap.java`
  (`createFromShadowProviders`, constructor over
  defaultShadows/overriddenShadows/shadowPickers);
  `processor/src/main/java/org/robolectric/annotation/processing/generator/ShadowProviderGenerator.java`;
  `annotations/src/main/java/org/robolectric/annotation/GraphicsMode.java`;
  shadow selection example: `shadows/framework/src/main/java/org/robolectric/shadows/ShadowView.java`
  `useRealGraphics()` (line ~1108: `graphicsMode == Mode.NATIVE && apiLevel >= O`).
- WHY IT MATTERS TO MINIANDROID: MiniAndroid's `shadow_registry`
  (miniandroid/src/framework/shadow_registry.*) is the same idea in C++
  (API-name → handler). Robolectric's picker pattern (multiple
  implementations per API chosen by config) is the model for our
  legacy-vs-real-graphics split (we already have both paths).
- CAN WE ADAPT IT: CONCEPT ONLY (their machinery is Java-classloader-
  specific; our dispatch is a table).
- HOW: add a `picker` layer to shadow_registry keyed by a graphics-mode
  config, so a test can force the software/legacy path deterministically.
- LICENSE: MIT. TEST NEEDED: registry-level unit test when implemented.

RB-002 — Dual graphics modes: LEGACY (record/replay) vs NATIVE (real code)
- WHAT IT DOES: `GraphicsMode.Mode { LEGACY, NATIVE }` — LEGACY shadows are
  "no-ops and fakes" that RECORD operations (legacy `ShadowCanvas` exposes
  `visualize(Canvas)` returning the recorded drawing ops as text, and
  `appendDescription`); NATIVE shadows call REAL Android native graphics
  code loaded from a bundled native runtime
  (`nativeruntime/src/main/java/org/robolectric/nativeruntime/DefaultNativeRuntimeLoader.java`,
  natives like `BaseRecordingCanvasNatives.java`, `CanvasNatives.java`).
- WHERE IMPLEMENTED: `annotations/.../GraphicsMode.java`;
  `robolectric/src/main/java/org/robolectric/plugins/GraphicsModeConfigurer.java`;
  `shadows/framework/.../ShadowCanvas.java` (`visualize`, line 15).
- WHY IT MATTERS TO MINIANDROID: two independent validations of the same
  architecture decision MiniAndroid already made (software rendering +
  trace/observatory). The LEGACY `visualize()` text form of drawing history
  is a diagnostics idea: a golden *drawing-op log* is more debuggable than a
  pixel diff when a frame diverges (names the exact op).
- CAN WE ADAPT IT: YES (methodology).
- HOW: alongside frames_manifest SHA-256 pins, optionally record a compact
  op-log (canvas calls + args) per frame for triage artifacts.
- LICENSE: MIT. TEST NEEDED: none (diagnostic-only artifact).

RB-003 — Deterministic hardware-path screenshot capture
- WHAT IT DOES: `HardwareRenderingScreenshot.takeScreenshot(View, Bitmap)`
  renders the view through `HardwareRenderer` into an `ImageReader`
  (RGBA_8888, 1 buffer) surface and copies the result into a bitmap;
  comment states it "mirrors the behavior of LayoutLib's
  RenderSessionImpl.renderAndBuildResult()". Gated by `canTakeScreenshot`
  (API ≥ P, system property `robolectric.pixelCopyRenderMode`,
  `useRealGraphics()`, view display-list capability). Reuses
  HardwareRenderer per ViewRootImpl via WeakHashMap to avoid recycling
  hazards. Consumed by `ShadowPixelCopy` and `ShadowUiAutomation`.
- WHERE IMPLEMENTED: `shadows/framework/src/main/java/org/robolectric/shadows/HardwareRenderingScreenshot.java`
  (functions `canTakeScreenshot`, `takeScreenshot`; properties
  `PIXEL_COPY_RENDER_MODE`, `USE_EMBEDDED_VIEW_ROOT`).
- WHY IT MATTERS TO MINIANDROID: upstream, in-JVM, *synchronous* pixel
  capture through the real render pipeline — the same guarantee class as
  our framebuffer dump; the property-gated fallback
  (`pixelCopyRenderMode=legacy|hardware`) is a good escape-hatch pattern
  when a renderer change would churn golden pins.
- CAN WE ADAPT IT: CONCEPT ONLY (we own the whole pipeline already).
- HOW: if MiniAndroid grows a second render backend, gate capture per
  backend with a property and keep goldens per (backend, app, frame).
- LICENSE: MIT. TEST NEEDED: none.

RB-004 — Deterministic scheduling (paused looper)
- WHAT IT DOES: `ShadowLooper` puts the main looper in a paused state where
  posted tasks only run under explicit control (`pause/unPause`,
  `runToEndOfTasks`, idle), giving reproducible async order; the API
  documents that tasks "will not run at all before your test" advances the
  clock.
- WHERE IMPLEMENTED: `shadows/framework/src/main/java/org/robolectric/shadows/ShadowLooper.java`
  (pauseLooper/unPauseLooper/pauseMainLooper/unPauseMainLooper/
  runToEndOfTasks family, lines ~105–145).
- WHY IT MATTERS TO MINIANDROID: same principle as our deterministic replay:
  the clock and the event queue are part of the pinned state. Reminder for
  frames_manifest evolution: pin not only frame hashes but also the
  input/clock schedule that produced them (we already pin interactions in
  the manifest — keep doing so).
- CAN WE ADAPT IT: ALREADY ALIGNED (no change).
- LICENSE: MIT. TEST NEEDED: none.

RB-005 — Golden pixel comparison with precision floor (their own tests)
- WHAT IT DOES: `BitmapUtils.compareBitmaps(bmp1, bmp2)` — dimension +
  config precheck first (logs which check failed), then exact per-pixel
  compare; the 3-arg overload takes `minimumPrecision` (e.g. 0.99 = "at
  least 99% of the pixels should match"), counts mismatches, logs the first
  10 mismatch coordinates, computes actualPrecision and compares. Golden
  PNGs stored as drawable resources
  (`integration_tests/nativegraphics/src/main/res/drawable-nodpi/*_golden.png`).
- WHERE IMPLEMENTED: `integration_tests/nativegraphics/src/test/java/org/robolectric/shadows/BitmapUtils.java`
  (`compareBasicBitmapsInfo`, `compareBitmaps`, 3-arg `compareBitmaps`,
  `saveBitmap`, `logIfBitmapSolidColor`).
- WHY IT MATTERS TO MINIANDROID: the *precheck order* (dims → config →
  pixels) yields a precise failure taxonomy (sizes don't match vs pixels
  don't match) instead of one generic mismatch; the capped mismatch log
  ("Let's not spam logcat...") is good hygiene for our diff reports;
  `logIfBitmapSolidColor` catches the classic "all frames are blank" class
  of bug.
- CAN WE ADAPT IT: YES (methodology).
- HOW: when a frame hash mismatches, run the same ladder: dimension check →
  per-pixel diff count → first-N differing coordinates in report.md.
- LICENSE: MIT. TEST NEEDED: none.

### §4.2 Paparazzi — https://github.com/cashapp/paparazzi
master `716755fb` (2026-09-04). License: Apache-2.0 (`LICENSE.txt`).

PPZ-001 — Device-free rendering via layoutlib
- WHAT IT DOES: renders real Android layouts (Views and Compose) inside the
  JVM using the AOSP layoutlib bridge: `Bridge.prepareThread`, Renderer over
  `Environment`/`DeviceConfig`, `RenderAction.getCurrentContext()`;
  `inflate(@LayoutRes)`, `snapshot(view|composable)`, `gif(view, start,
  end, fps)` with frame count `(duration*fps)/1000 + 1` ("we want our last
  frame"). Honesty policy: README — Paparazzi "does not set
  `LocalInspectionMode` globally to ensure that the snapshot represents the
  true production output", mirroring `View.isInEditMode` overrides.
- WHERE IMPLEMENTED: `paparazzi/src/main/java/app/cash/paparazzi/PaparazziSdk.kt`
  (functions `render`/`inflate`/`snapshot`/`gif`/`takeSnapshots`; layoutlib
  imports lines 65–70).
- WHY IT MATTERS TO MINIANDROID: same design point as MiniAndroid (render
  real views without an emulator). The frame-count formula (+1 inclusive
  last frame) is a subtle off-by-one we should copy into any multi-frame
  capture we do.
- CAN WE ADAPT IT: METHODOLOGY (layoutlib itself is not portable to us).
- HOW: adopt inclusive-frame-count convention in runner captures.
- LICENSE: Apache-2.0. TEST NEEDED: none.

PPZ-002 — Pluggable differs incl. per-channel tolerance (OffByTwo)
- WHAT IT DOES: `Differ` interface with sealed `DiffResult {Identical(delta),
  Similar(delta, numSimilarPixels), Different(delta, percentDifference,
  numDifferentPixels)}`; six selectable implementations selected by system
  property `app.cash.paparazzi.differ`: PixelPerfect, **OffByTwo (default)**,
  Mssim (structural similarity), Sift, Flip, DeltaE2000 (CIEDE2000 color
  difference). OffByTwo: identical ⇒ gray delta; fully transparent pixels on
  both sides ignored; per-channel |Δ| ≤ 2 (A/R/G/B) ⇒ "similar" (blue in
  delta map); otherwise "different" (delta color map = expected | delta |
  actual composite).
- WHERE IMPLEMENTED: `paparazzi/src/main/java/app/cash/paparazzi/Differ.kt`
  (interface + sealed result);
  `paparazzi/src/main/java/app/cash/paparazzi/internal/differs/OffByTwo.kt`
  (`compare`: tolerance `abs(deltaR) <= 2 …` etc.); selector
  `SnapshotVerifier.kt` `determineDiffer()` (line ~112).
- WHY IT MATTERS TO MINIANDROID: our SHA-256 pin is binary. When a pin
  breaks, a *graded* diff (how many pixels, how far off, where) turns
  "mismatch" into actionable triage (font raster drift vs layout shift vs
  total divergence). The transparent-pixel special case and the delta-map
  artifact are directly reusable ideas.
- CAN WE ADAPT IT: YES (reimplement tolerance math ourselves; ~50 LOC).
- HOW: implement an OffByTwo-style differ in the runner's diff tool for
  mismatch triage only (never to relax the pin).
- LICENSE: Apache-2.0 (adaptable with attribution if copied).
- TEST NEEDED: a synthetic before/after PNG pair with known deltas.

PPZ-003 — Threshold + failure-artifact conventions
- WHAT IT DOES: verify-mode `SnapshotVerifier(maxPercentDifference, root,
  differ)`; default threshold from property
  `app.cash.paparazzi.maxPercentDifferenceDefault` = **0.01** (1%) via
  `detectMaxPercentDifferenceDefault()`; missing golden ⇒ a stub image is
  compared so failure output still renders (and a git-LFS pointer-file
  confusion is detected with a specific error message); every failure
  writes `delta-<golden>.png` into a dedicated failures dir
  (`paparazzi.failures.dir`).
- WHERE IMPLEMENTED: `SnapshotVerifier.kt` (ctor, `newFrameHandler`,
  `handle`, companion `failureDir`); threshold default
  `SnapshotHandler.kt` line ~30.
- WHY IT MATTERS TO MINIANDROID: (a) failure artifacts next to the test
  report is a convention our frames work should adopt (currently a mismatch
  proves nothing visually unless someone re-runs and eyeballs);
  (b) the git-LFS-pointer detection shows they hardened against a real
  operational failure — our corpus uses raw PNGs in git, but the same
  "golden unreadable ⇒ distinct error class" idea applies to truncated
  PNGs.
- CAN WE ADAPT IT: YES.
- HOW: on hash mismatch, write golden vs actual vs delta into
  run/<app>/frames_diff/ and reference from report.md; add a
  "golden-corrupt" distinct error code.
- LICENSE: Apache-2.0. TEST NEEDED: none.

PPZ-004 — Per-frame animated goldens (APNG verifier)
- WHAT IT DOES: for animated snapshots, `newFrameHandler(snapshot,
  frameCount, fps)` returns a handler that, when fps != -1, wraps an
  `ApngVerifier(expected, failurePath, fps, frameCount, maxPercentDifference,
  differ)` and verifies EACH frame (`verifyFrame`) with `assertFinished()`
  on close — i.e., per-frame golden verification of an animated PNG.
- WHERE IMPLEMENTED: `SnapshotVerifier.kt` `newFrameHandler`/`handle`/`close`
  (ApngVerifier lines ~54–97); `paparazzi/src/main/java/app/cash/paparazzi/internal/apng/ApngVerifier.java`
  (implementation).
- WHY IT MATTERS TO MINIANDROID: frames_manifest.json already pins
  per-frame SHA-256 for interaction sequences; Paparazzi proves the
  industry-standard shape of the same idea (frameCount/fps recorded with the
  golden, frame-indexed failure artifacts). If we ever capture at a fixed
  fps, record fps+frameCount next to hashes so the manifest self-describes.
- CAN WE ADAPT IT: YES (metadata convention).
- HOW: add optional `fps`/`frame_count` fields to frames_manifest entries.
- LICENSE: Apache-2.0. TEST NEEDED: none.

### §4.3 Roborazzi — https://github.com/takahirom/roborazzi
main `6abd5fc0` (2026-08-25). License: Apache-2.0 (`LICENSE`).

RBZ-001 — record / verify / compare as first-class task modes
- WHAT IT DOES: three Gradle tasks (`recordRoborazziDebug`,
  `verifyRoborazziDebug`, `compareRoborazziDebug`) mapping to system
  properties (`roborazzi.test.record|verify|compare`) so plain
  `testDebugUnitTest` becomes mode-aware; plus `verifyAndRecord` (verify,
  then re-record on difference — explicitly labeled for "update goldens
  without removing previous diffs" workflow). Mode type:
  `RoborazziTaskType` in options.
- WHERE IMPLEMENTED: README "Run tasks" section (lines ~204–295);
  `include-build/roborazzi-core/src/commonMain/kotlin/com/github/takahirom/roborazzi/RoborazziOptions.common.kt`
  (`taskType: RoborazziTaskType`).
- WHY IT MATTERS TO MINIANDROID: our runner effectively has record and
  verify; an explicit third `compare` verb (produce artifacts, do not fail)
  plus a `verifyAndRecord` (update pins while preserving the old diff as an
  artifact) would make golden updates auditable instead of magical.
- CAN WE ADAPT IT: YES (CLI verb design).
- HOW: add `--frames-mode=record|verify|compare` to the runner; compare
  mode always writes diff artifacts and exits 0.
- LICENSE: Apache-2.0. TEST NEEDED: none.

RBZ-002 — Comparator + validator policy objects
- WHAT IT DOES: `CompareOptions(imageComparator = DefaultImageComparator,
  resultValidator = DefaultResultValidator)` where
  `DefaultImageComparator = SimpleImageComparator(maxDistance = 0.007F)`
  (from Dropbox's `com.dropbox.differ`) and `DefaultResultValidator =
  ThresholdValidator(0F)`; an alternative constructor
  `ThresholdValidator(changeThreshold)` wires a percent threshold.
  Comparison goes through the `DifferBufferedImage` adapter, which fixes a
  real-world encoding quirk: "WebP images return r=1,g=0,b=0,a=0 for
  transparent pixels" → normalized to (0,0,0,0) before compare; out-of-bounds
  pixels read as transparent (size-difference tolerance at the Image level).
- WHERE IMPLEMENTED: `RoborazziOptions.common.kt` lines 108–153;
  `roborazzi-painter/src/commonJvmMain/kotlin/com/github/takahirom/roborazzi/DifferBufferedImage.kt`
  (`getPixel`).
- WHY IT MATTERS TO MINIANDROID: two lessons: (a) separate the *measurer*
  (comparator) from the *decider* (validator) — exactly the split to keep if
  we ever add tolerance; (b) input normalization quirks (alpha/WebP) can
  fake pixel differences — our PNG decoder path should normalize
  transparent-pixel encodings before hashing... but note: hashing raw
  decoded bytes is also fine as long as it is deterministic; the adapter is
  needed only if we compare PNGs produced by different encoders.
- CAN WE ADAPT IT: CONCEPT ONLY.
- HOW: document the measurer/decider split in the frames tooling README.
- LICENSE: Apache-2.0. TEST NEEDED: none.

RBZ-003 — Machine-readable diff sidecars
- WHAT IT DOES: verify/compare writes a comparison image
  `[original]_compare.png` (golden | actual | highlighted diff strip,
  generated via `AwtRoboCanvas.generateCompareCanvas` with dp-scaled layout)
  AND "a JSON file containing the diff information"; every capture can emit
  a `CaptureResult` (recorded/failed etc.) through a `CaptureResultReporter`;
  an experimental `UiTreeSidecar` writes a `.uitree.json` next to each
  captured image ("machine-readable UI tree of the current run"), enabled
  via `roborazzi.dumpUiTree=true`.
- WHERE IMPLEMENTED: `roborazzi/src/main/java/com/github/takahirom/roborazzi/Roborazzi.kt`
  (`processOutputImageAndReportWithDefaults`, comparisonCanvasFactory);
  `RoborazziOptions.common.kt` (UiTreeSidecar doc comment lines ~20–24);
  README lines ~250–252.
- WHY IT MATTERS TO MINIANDROID: the `.uitree.json` sidecar is the
  strongest idea here for us: a frame hash proves pixels, a UI-tree sidecar
  proves *structure* (view tree with ids/bounds/text) — combined they
  disambiguate "same pixels, wrong tree" vs "different pixels, same tree",
  and give our reports something greppable when hashes diverge.
- CAN WE ADAPT IT: YES.
- HOW: when a frames_manifest entry mismatches, dump the view tree
  (bounds + resource ids) at that frame into the diff artifacts.
- LICENSE: Apache-2.0. TEST NEEDED: none.

### §4.4 Shot — https://github.com/Karumi/Shot
master `e102d797` (2026-01-16). License: Apache-2.0 (`LICENSE.txt`).
Core is Scala (`core/src/main/scala/com/karumi/shot/`); device-side
instrumented capture (`shot-android`), comparison on the JVM after
`adb pull`.

SH-001 — Comparison ladder with honest tolerance disclosure
- WHAT IT DOES: `ScreenshotsComparator.compare(screenshots, tolerance)`:
  parallel over suite; per screenshot: golden file exists?
  (`ScreenshotNotFound`) → dimensions equal? (`DifferentImageDimensions`)
  → fast path `oldScreenshot == newScreenshot` → else zip pixel streams,
  count differing pixels, `percentageOutOf100 > tolerance` ⇒
  `DifferentScreenshots`. When tolerance masks changes it prints an explicit
  warning: "⚠️ There are some pixels changed … but we consider the
  comparison correct because tolerance is configured to N % and the
  percentage of different pixels is M %" (`Config.defaultTolerance`
  exempted).
- WHERE IMPLEMENTED: `core/src/main/scala/com/karumi/shot/screenshots/ScreenshotsComparator.scala`
  (functions `compare`, `compareScreenshot`, `imagesAreDifferent`,
  `haveSameDimensions`).
- WHY IT MATTERS TO MINIANDROID: the ladder (exists → dims → exact →
  percent) matches RB-005 and confirms the industry-standard failure
  taxonomy. The tolerance warning is the "honest UI" principle applied to
  thresholds — if we ever allow tolerance, we must print exactly this kind
  of disclosure.
- CAN WE ADAPT IT: YES (taxonomy + disclosure convention).
- HOW: frame-mismatch reports should state which ladder step failed; if any
  tolerance mode is ever added, require the warning line.
- LICENSE: Apache-2.0. TEST NEEDED: none.

SH-002 — Diff artifacts and reporting
- WHAT IT DOES: on failure, `ScreenshotsDiffGenerator.generateDiffs` writes
  a diff PNG composed with `RedComposite` (actual over golden tinted red)
  plus a base64-embedded copy for inline HTML reporting; HTML verification
  index (`HtmlExecutionReporter` + `VerificationIndexTemplate`) lists every
  comparison with golden/actual/diff.
- WHERE IMPLEMENTED: `core/src/main/scala/com/karumi/shot/screenshots/ScreenshotsDiffGenerator.scala`
  (`generateDiffs`, `generateDiff`); `core/src/main/scala/com/karumi/shot/reports/HtmlExecutionReporter.scala`.
- WHY IT MATTERS TO MINIANDROID: same convention as PPZ-003; the red-tint
  overlay is the cheapest visual diff that survives a screenshot-based
  report (we can do pixel-exact XOR/abs-diff instead).
- CAN WE ADAPT IT: YES (artifact shape).
- HOW: include a red-tinted or abs-diff image in frames-diff artifacts.
- LICENSE: Apache-2.0. TEST NEEDED: none.

### §4.5 Dropshots — https://github.com/dropbox/dropshots
main `70b8cbfd` (2026-06-26). License: Apache-2.0 (`LICENSE.txt`).
Small library (~373 LOC main); instrumented-test oriented; comparison uses
Dropbox's `com.dropbox.differ` (the same library Roborazzi adopts).

DS-001 — ResultValidator as a first-class policy abstraction
- WHAT IT DOES: `typealias ResultValidator = (ImageComparator.ComparisonResult)
  -> Boolean` with two provided policies: `CountValidator(count)` ("fails if
  more than `count` pixel differences") and `ThresholdValidator(threshold)`
  ("fails if more than `threshold` percent of pixels are different",
  0.0–1.0, computed as `pixelDifferences <= pixelCount * threshold`).
- WHERE IMPLEMENTED: `dropshots/src/main/java/com/dropbox/dropshots/ResultValidator.kt`
  (whole file, 33 lines); used by `Dropshots.kt` `assertSnapshot` overloads
  (comparator + validator + optional mask parameters, lines ~80–190).
- WHY IT MATTERS TO MINIANDROID: the cleanest formulation of the
  measurer/decider split (cf. RBZ-002): our frames validation stays
  `ThresholdValidator(0)` (exact) today, but a named policy object is where
  a future "advisory mode" (report-only tolerance) would live without
  weakening the default.
- CAN WE ADAPT IT: YES (interface shape only).
- HOW: if/when tolerance is contemplated, implement it as a named policy
  with default = exact, never as a global flag.
- LICENSE: Apache-2.0. TEST NEEDED: none.

DS-002 — Record/verify-by-existence + failure diff images
- WHAT IT DOES: recording mode detected by a flag file/system property
  (`isRecordingScreenshots`); verify mode: missing golden ⇒ write reference
  (record-on-first-run semantics); on mismatch ⇒ `generateDiffImage`
  written to the screenshots dir and the assertion fails with a message
  carrying reference/actual dimensions; supports an optional comparison
  `mask` region.
- WHERE IMPLEMENTED: `dropshots/src/main/java/com/dropbox/dropshots/Dropshots.kt`
  (`apply`, `assertSnapshot` (4 overloads), `writeReferenceImage`,
  `writeDiffImage`, `generateDiffImage`, `isRecordingScreenshots`,
  `defaultRootScreenshotDirectory`).
- WHY IT MATTERS TO MINIANDROID: "record-on-first-run with an explicit
  record mode" is our existing behavior; the mask idea (ignore a region —
  e.g., a clock) is the only sound way to compare frames containing
  genuinely nondeterministic content; not needed while our content is fully
  deterministic.
- CAN WE ADAPT IT: CONCEPT ONLY.
- HOW: document mask as the future escape hatch; keep default full-frame.
- LICENSE: Apache-2.0. TEST NEEDED: none.

### §4.6 Synthesis — what strengthens MiniAndroid's frames_manifest.json

Current MiniAndroid state: per-frame SHA-256 pins in
docs/evidence/tictactoe_golden/frames_manifest.json; deterministic replay;
runner reports per corpus app (report.md + api_trace.json + frames).

Ranked methodology transfers (ideas only, no dependencies):

1. KEEP the exact hash pin as the primary oracle (all five projects that
   support exact comparison default to or support it; Roborazzi's default
   validator is literally `ThresholdValidator(0F)`).
2. MISMATCH TRIAGE LADDER (RB-005/SH-001): on hash mismatch → dimension
   check → config check → pixel-diff count → first-N differing coordinates.
   Names the failure class instead of a bare "hash differs".
3. FAILURE ARTIFACTS DIR (PPZ-003/SH-002/RBZ-003): golden + actual + delta
   image (abs-diff or red-tint) + a small JSON (percent difference,
   numDifferentPixels, first-N coords) written under run/<app>/frames_diff/
   and linked from report.md.
4. UI-TREE SIDECAR (RBZ-003): dump the view tree per failing frame —
   structure evidence alongside pixel evidence; maps directly onto our
   view/layout runtime.
5. MEASURER/DECIDER SPLIT (DS-001/RBZ-002): comparator (how different) is
   separate from validator (is this a failure); default validator = exact.
   Any future tolerance must be a named policy + Shot-style disclosure
   warning (SH-001).
6. OP-LOG TRIAGE (RB-002): optional per-frame drawing-op log (Robolectric's
   LEGACY `visualize()` idea) — for canvas-level divergence, names the op
   that diverged; complements our Execution Observatory.
7. MODE VERBS (RBZ-001): record / verify / compare (advisory, exit 0,
   artifacts always) / verifyAndRecord (update pins, keep old diff as
   artifact) — makes golden evolution auditable.
8. MANIFEST SELF-DESCRIPTION (PPZ-004): record fps/frame_count/inclusive
   last-frame convention (+ PPZ-001's frameCount formula) next to hashes so
   animated captures are self-describing.
9. INPUT NORMALIZATION QUIRKS (RBZ-002's WebP alpha quirk): if we ever
   compare across encoders, normalize transparent-pixel encodings first;
   within our own pipeline, hashing deterministic decoded bytes suffices.
10. HEALTHY-STOP TAXONOMY (DEXAPP-003/DEX-007): stop reasons classified and
    printed, so a reflection-stop in a probe is read as expected behavior,
    not a failure — same discipline the frame diff should have.

NOT transferred: emulators/instrumented-device capture paths (Shot's adb
pull, Dropshots' androidTest), layoutlib/scrcpy transports (lossy or
foreign), and any dependency on Gradle test infrastructure.

---

## §5 sim-use — https://github.com/SimulaVR/sim-use — RETRY (mandated)

Retry method (mandated: retry once via `git ls-remote`):
`git ls-remote https://github.com/SimulaVR/sim-use HEAD` →
`fatal: could not read Username for 'https://github.com': No such device or
address` — GitHub's repository-not-found behavior (git prompts for
credentials when a repo does not exist or is inaccessible).

This is the SECOND documented failure of this URL: the previous campaign
recorded HTTP 404 + credential-prompt on two retries
(external-repositories.md row 16). No substitution made; `lycorp-jp/sim-use`
remains a DIFFERENT project and was not touched.

STATUS: **REPOSITORY_UNAVAILABLE** (retry recorded). License/HEAD: n/a.

---

## §6 Consolidated status table

| Repository | Status | Transfer decision | Key carry-over |
|---|---|---|---|
| mirzachi/android-rro | REVIEWED | REJECTED (RRO proper) / REFERENCE (multi-APK future) | RRO-006 Res_value edge tests (NULL-empty, dynamic-reference) → ARSC fixture queue |
| Shrey113/Android-Dex | REVIEWED | ADAPTABLE (methodology only; runtime claim REJECTED) | two-tier error taxonomy; boot ladder + timeouts; failure classifier |
| vimalloc/dexterpreter | REVIEWED | REFERENCE ONLY | DEX→sexp differential dump (DXTP-003) → folds into DEX-008/009 |
| robolectric/robolectric | REVIEWED | ADAPTABLE (methodology) | triage ladder; op-log visualize; determinism alignment |
| cashapp/paparazzi | REVIEWED | ADAPTABLE (methodology) | OffByTwo differ for triage; failure artifacts; APNG per-frame goldens; frameCount+1 |
| takahirom/roborazzi | REVIEWED | ADAPTABLE (methodology) | mode verbs; UI-tree sidecar; measurer/decider split |
| Karumi/Shot | REVIEWED | ADAPTABLE (methodology) | comparison ladder; honest tolerance disclosure; diff artifacts |
| dropbox/dropshots | REVIEWED | ADAPTABLE (methodology) | ResultValidator policy shape; record-on-first-run; mask concept |
| SimulaVR/sim-use | UNAVAILABLE | n/a | retry recorded; second consecutive session unavailable |

BLOCKED items: none for this task. (GitHub API rate-limit 403 was worked
around lawfully via HTML search + ls-remote; no URL invented.)
