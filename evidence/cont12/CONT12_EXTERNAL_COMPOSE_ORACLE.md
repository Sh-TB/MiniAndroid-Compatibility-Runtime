# CONT-12 — EXTERNAL REAL-COMPOSE ORACLE EXPERIMENT (Execution Ledger)

Wave: CONT-12 · HEAD at start: `06c9f853` · date: 2026-10-07
Mission answered, measured:

> Does supplying the real, matching Compose runtime make Dooz execute
> farther, and if yes, exactly which generic MiniAndroid runtime/framework
> behavior is responsible for the difference?

**Answer: YES — with the exact matching real Compose artifacts (un-renamed,
D8-only, no R8) the execution advances past THREE earlier walls that the
R8-renamed dooz bundle had silently masked, and the FIRST generic
MiniAndroid law gap (F-NEW-266, invoke-virtual transitive interface-default
dispatch) was isolated, fixed, probed, and proven drift-free on the native
path.** The external runtime remains a TEST-ONLY oracle; nothing was
vendored or permanently integrated.

---

## 0. PHASE 0 — BASELINE LOCK (preserved before any change)

| item | value |
|---|---|
| git HEAD | `06c9f8531866a73b5b2b47076f0404a1d9b572eb` |
| binary (clean rebuild from HEAD) | `0ee46f5a719d2a8c` after the F-266 fix; `4f39ef980fd72309` before |
| binary-lineage note | the pre-reset ledger SHA `d701221b9bb78317` does not reproduce after the container reset (toolchain changed, g++ 14.2.0-19). Semantic lineage was verified the only way that matters: the rebuilt pre-fix binary reproduces the dooz anchor `d602648e8e401895` ×3 byte-identically, and the post-fix binary reproduces every recorded anchor (below). |
| dooz APK SHA256 | `299eab21ac8b3c6192edbd887966554fef84ad026d269b9067310215201b362b` |
| Compose version inside dooz | compose (runtime/ui/foundation/animation) **1.11.4**, material3 **1.4.0**, icons-core **1.7.8**, activity(-compose) **1.13.0**, lifecycle **2.11.0**, navigation(-compose) **2.9.8**, navigationevent **1.0.0**, coroutines **1.9.0**, core **1.19.0**, savedstate **1.4.0** (all from the APK's own `META-INF/*.version` files) |
| registry root count | 573 at lock; **575** at close (F-NEW-266, F-NEW-266a added; none renumbered) |
| F-NEW-265 evidence | re-verified live on the rebuilt binary: `Lzs0.m` measure pass fires 45× under `Lt4.onMeasure`; `Lm7.<init>` receives a null text CharSequence (a1 unset, caller `Lvs0.c`); NPE cascade reaches compose report helper `Lel0.Y` ×11 (now carrying the REAL NPE object — F-264 delivery law works); measure dies → placement never runs → 0 content canvas ops |
| dooz result ×3 | screenshot `d602648e8e401895` ×3, verdict `DEFAULT_BACKGROUND_ONLY` — fallback-free by construction |
| current first divergence | F-NEW-265 (native): measure/layout pass dies mid-flight on the null-text ctor exception cascade → `isPlaced=false` everywhere → draw faithfully skips children |

Expected frontier independently re-confirmed on the locked binary:

```text
real LayoutNodes materialize   ✓ (CONT-10/11 proof holds)
        ↓
measure/layout begins          ✓ (Lzs0.m 45× under Lt4.onMeasure)
        ↓
exception cascade              ✓ (null-text ctor → deferred-throw blast)
        ↓
placement fails                ✓
        ↓
isPlaced=false                 ✓ (draw walk honors it, Lel0.J→Lil0.p→Lbt0.w)
        ↓
draw skips child               ✓ (0 content canvas ops)
        ↓
DEFAULT_BACKGROUND_ONLY        ✓ (d602648e ×3)
```

---

## 1. PHASE 1 — DOOZ_COMPOSE_DEPENDENCY_MATRIX

Full matrix: `evidence/cont12/DOOZ_COMPOSE_DEPENDENCY_MATRIX.md` (+ machine
form `dependency_matrix.json`). Summary:

- **55 real Maven artifacts, 11,767 classes**, zero version mixing — every
  artifact matches the version file inside the dooz APK itself.
- KMP nuance (source-first discovery): the root `androidx.compose.*` AARs on
  Google Maven are EMPTY stubs; the android binaries live at the
  `-android` coordinates (`runtime-android-1.11.4.aar` → classes.jar
  `57a4a22728458b47`, 764 classes). `lifecycle-common` and
  `androidx.collection` publish at `-jvm` coordinates.
- kotlin-stdlib **2.1.20** — the version `runtime-android-1.11.4.module`
  itself declares (dooz's APK carries no stdlib version file; R8-minified).
- **Gap found and fixed mid-wave:** `androidx.collection:collection-jvm:1.5.0`
  (declared by compose-ui/runtime/foundation 1.11.4 modules) was missing
  from the first matrix — dooz carries the family R8-renamed, so no
  `.version` file advertised it. The absence was itself diagnostic: see §3
  step 2.
- Excluded: `androidx.annotation:annotation` (1.4.1 unpublished as binary;
  compile-time metadata only, no runtime behavior).

## 2. PHASE 2 — TEST ARTIFACT CONSTRUCTION (exact procedure)

Two test APKs built, both TEST-ONLY, neither touching MiniAndroid
architecture, neither deleting native compatibility code, no Dooz
hardcodes:

### oracle12.apk — the BOUND oracle (the real experiment)
sha256-16 `f65b13ad446d1a57`, 8,233,173 bytes, 2 dex files. Procedure
(`scripts/cont12_build_oracle.sh`, `scripts/cont12_oracle_res2.sh`):

1. kotlinc **2.1.20** (the exact compiler generation compose 1.11.4
   declares; sha256 `a118197b0de55ffa`) with its bundled
   `compose-compiler-plugin.jar`, `-no-stdlib -no-jdk -jvm-target 1.8`,
   classpath = android-34.jar + the 55 real classes.jars.
   Probe source: `fixtures/cont12_oracle/src/com/probe/oracle12/MainActivity.kt`
   — mirrors dooz's structure: `setContent { MaterialTheme { Surface {
   rememberNavController + NavHost(startDestination) { composable { Column
   { Text ×2 } } + LaunchedEffect } } } }`.
2. **Faithful resource construction (the AGP step raw AAR dexing lacks):**
   `aapt2 compile` every AAR's `res/`, `aapt2 link` all of them
   (`--auto-add-overlay --emit-ids`), producing a merged resources.arsc
   (491,968 bytes, 320 ids) where e.g. `view_tree_lifecycle_owner =
   0x7f05005a`.
3. **Final-R regeneration:** AAR classes.jars carry NO R classes, and
   library code references its OWN package's `R$id` fields via `sget`.
   Generated merged R.java for all 16 R-packages the dex references
   (`androidx.lifecycle.runtime.R`, `androidx.compose.ui.R`, …), ECJ-compiled
   (176 classes) — ids match the merged arsc exactly.
4. D8 `--release --min-api 26 --lib android-34.jar` over probe + 55 jars +
   generated R classes → dexes; fresh re-zip with STORED `resources.arsc`.

Two construction defects were found and fixed by the oracle itself before
any MiniAndroid signal could be read (each is exactly what Phase 8 calls
"external artifact invalid → not a MiniAndroid root"):

| construction defect | oracle face | fix |
|---|---|---|
| manifest-only link (no arsc) | upstream ISE "Composed into the View which doesn't propagate ViewTreeLifecycleOwner!" — engine F-105b could not install the owner (no id in arsc) | full merged resources (§2 step 2) |
| AARs ship no R classes (AGP generates final-R at app build) | `sget R$id.view_tree_lifecycle_owner` resolved to a synthesized-absent default **0** → tag installed under 0x7f05005a, read under 0 → walk found nothing | final-R regeneration (§2 step 3); NOTE: the engine synthesized absent statics silently — flagged as an observation, not patched |
| first merge attempt zip-append (B1) | NO_ROOT (class map shrank, secondary dex never injected) | fresh re-zip; superseded, recorded honestly |

### dooz_b1_merged.apk — the LITERAL Phase 3-B experiment
sha256-16 `a127bb5efd5454f8`, 9,435,488 bytes: dooz classes.dex untouched +
D8-merged real-Compose classes as `classes2.dex` (14,387,764 bytes) +
`classes3.dex` (8,090,028 bytes).

**Result (measured, ×3):** screenshot `d602648e8e401895` ×3, verdict
`DEFAULT_BACKGROUND_ONLY` — **byte-identical to the untouched baseline.**
The binding wall is real: R8 renamed BOTH the app code and its bundled
Compose consistently, so every renamed reference binds to the renamed class;
the real-name classes are unreachable dead code. Supplying real Compose
*without reference rewriting* cannot change anything — which is exactly why
the BOUND oracle (oracle12.apk, real names end-to-end) is the instrument
that can answer the mission question.

## 3. PHASE 3–5 — THE ORACLE CASCADE (first-divergence ladder)

Baseline arm (A): dooz ×3 `d602648e` (above). Each oracle run at
`run/w8/oracle12/` with full trace; every step below is
runtime-evidence-backed (engine `[EXCEPTION]`/`[TAG-TRACE]`/`[CLASS_INIT]`
lines + upstream source read + dex disassembly).

| # | oracle first divergence (upstream face) | root found | class | resolution |
|---|---|---|---|---|
| 1 | `AbstractComposeView.resolveComposeViewContext` ISE "…doesn't propagate ViewTreeLifecycleOwner!" | oracle APK had no merged resources → F-105b owner install skipped | ARTIFACT | fixed in artifact (§2); upstream law read: lifecycle 2.11.0 `ViewTreeLifecycleOwner.android.kt` (`getTag(R.id.view_tree_lifecycle_owner)`) |
| 2 | `getTag key=0` despite arsc id 0x7f05005a | R$id classes absent (AARs don't ship them) + statics read 0 | ARTIFACT | fixed in artifact (final-R regen); verified bytes `5a 00 05 7f` in classes2.dex after |
| 3 | `FontScaleConverterFactory.<clinit>` ISE "You should only apply non-linear scaling to font scales > 1" | `sLookupTables.keyAt(0)` returned 0 because **androidx.collection was missing from the artifact** (put() on a synthesized-absent class is inert) | ARTIFACT + engine observation | fetched real `collection-jvm:1.5.0` (declared by compose modules); upstream law read: `FontScaleConverterFactory.android.kt` init-block check. Engine observation recorded: synthesized-absent guest classes are silent — future honesty-law candidate |
| 4 | `AndroidComposeView.<init>` pc=247 → NPE "invoke interface method `Modifier.then` on null" ×172 → `setContent` dead | **invoke-virtual resolving to a TRANSITIVE SUPERINTERFACE DEFAULT method returned silent null** (API-bridge stub). Chain: `root$1$1.then(other)` → class chain has no `then` → interface `Modifier` default body (size=14) never dispatched (F-023 law existed for invoke-interface only) → chained invoke-interface receiver null | **MINIANDROID ROOT — F-NEW-266** | generic fix, see §4 |

After the F-266 fix the oracle advanced through the remaining walls:

```text
[INTERFACE-DEFAULT-V] Landroidx/compose/ui/Modifier;.then(...) (invoke-virtual
  default-method dispatch, receiver Landroidx/compose/ui/platform/AndroidComposeView$root$1$1;)
[INTERFACE-DEFAULT-V] Landroidx/compose/ui/node/DelegatableNode;.onDensityChange()V
uncaught past-app-frame exceptions: 44 (run 1) → 5 → 2
setContent → composition created → Recomposer started → NavHost chain executes:
  "No @Navigator.Name annotation found for NavGraphNavigator" ×5  ← NEXT divergence
  kotlin-reflect ReflectionFactoryImpl CNFE ×20                   ← NEXT divergence
  kotlin Function1.invoke null receiver ×22                       ← NEXT divergence
```

The oracle now dies inside **navigation-compose's real Navigator-registry
machinery** (annotation lookup on R8-free classes) — three further
divergences precisely bounded for the next wave. None were patched this
wave (no speculative patch families).

## 4. PHASE 6 CASE A — THE REQUIRED LOOP (executed once, completely)

```text
External Oracle            oracle12.apk: real Compose 1.11.4 + real deps,
                           real names, exact versions
      ↓
Successful behavior        upstream: Modifier.then default body must compose
      ↓
Trace comparison           native: R8 inlines/bridges the default bodies —
                           law never exercised; oracle: silent null
      ↓
FIRST DIVERGENCE           invoke-virtual → transitive superinterface
                           default method → silent-null stub
      ↓
Source law                 JVMS 5.4.5 / ART ArtMethod resolution —
                           resolution continues into superinterfaces when
                           the class chain has no implementation
      ↓
Generic MiniAndroid fix    F-NEW-266: try_interface_default_invoke() —
                           12-hop extends chain + 64-interface closure +
                           positive/negative memo, wired into BOTH
                           execute_invoke_virtual and the 3rc range path
                           (after runtime-class and declaring-class tries,
                           before the bridge). No app, package, or R8-name
                           knowledge; framework refs gated out (zero hot-path
                           cost for android.* receivers).
      ↓
Remove Oracle              native dooz (no external classes anywhere):
                           regression below
      ↓
Native reproduction        the law is masked on dooz by R8 inlining —
                           reproduced natively via the SYNTHETIC probe
                           (fixtures/f266_probe) which encodes the same
                           shape the oracle hit; dooz anchor byte-identical
                           (no behavior change where the law was never
                           reachable — exactly as ART semantics predict)
```

Registry: **F-NEW-266 ROOT-CAUSED-FIXED**; **F-NEW-266a CLASSIFIED**
(the probe's negative row exposed a null-receiver law gap: typed-null
invoke-interface of a DEX default method dispatched the body instead of
NPE — registered honestly, not patched).

## 5. REGRESSION (§16 contract) at the fixed binary `0ee46f5a719d2a8c`

| gate | result |
|---|---|
| anchors ×3 | opencalc `a976d2f9fb675cb3` / chess `b5a7a35d5fe0564b` / dooz `d602648e8e401895` / microtimer `da73010a37dd0189` / unote `4f1a9e4e8f64fae8` — **5/5 byte-identical** |
| negatives | **19/19 PASS** |
| skill selftest | **13/13 PASS** |
| f259 probe | **7/7 PASS** |
| f259g probe | **11/13 PASS** (the 2 registered honest FAILs 259g-a/259g-b unchanged) |
| gate A multiapp | **3/3 available families PASS** (simple/storage-heavy/game; pre=0 post=0). `memory_34` + `blockblast_43` corpus APKs ABSENT since container reset — paths updated in the script with the recorded reason (same BLOCKED-APK-ABSENT family as CONT-11) |
| f266 probe | **5/6 PASS** + 1 honest FAIL → F-NEW-266a |
| fallback status | fallback-free by construction; no suppression; no app-specific code |

## 6. PHASE 9 — MULTI-APP VALIDATION

The independent-Compose consumers (sudokusolver `d114d479df66b0f6`,
blockblast `64589a3a7e5c0f73`) remain BLOCKED-APK-ABSENT (F-Droid fetch
stalled; re-fetch script in place). Status: **PENDING, deferred with
reason.** Note the oracle probe itself is a second, independently
constructed Compose consumer (different app code, real names, no R8) — it
exercises the same generic laws — but Phase 9's 3-consumer proof
(Dooz + Independent A + Independent B) awaits the corpus refetch.

## 7. DECISIONS

1. **External Compose remains TEST-ONLY oracle** — it cannot replace the
   native path: the binding wall (§2, B1) makes bare artifact supply inert,
   and reference-rewriting a R8 build without its mapping is not
   engineering, it is guessing. As an oracle it already paid for itself:
   one P0 generic law (F-266) + one P1 law gap (F-266a) + a bounded
   3-divergence next-wave ladder + two honesty observations about silent
   synthesis of absent guest classes/statics.
2. **Native MiniAndroid path continues** (consistent with CONT-11 §14/E).
3. The native F-NEW-265 frontier (null-text measure cascade) is UNCHANGED
   and remains the highest-ROI native root; the oracle's next divergences
   (annotation lookup, Function1 null receiver) are queued behind the
   Phase-7 discipline: fix only roots demonstrated by first-divergence
   evidence in the APPS THAT MATTER.

## 8. NEXT-WAVE QUEUE (exact, evidence-bounded)

1. F-NEW-266a: null-receiver NPE gate on the interface-default dispatch
   path (probe row D already encodes the contract).
2. Oracle ladder continues: `@Navigator.Name` annotation lookup on
   real-name classes (navigation-compose 2.9.8) → likely the same family as
   dooz's own NavHost chain → maps onto native F-NEW-253/259 lineage.
3. Refetch independent Compose corpus → Phase 9 three-consumer proof.
4. Honesty-law candidate: silent synthesis of absent guest classes /
   statics (oracle face: `SparseArrayCompat` as a no-op ghost) — must be
   either renamed-loud (diagnostic) or erroring per ART ClassNotFound law.

## 9. REGISTRY STATUS VOCABULARY (§11 compliance)

- F-NEW-266 — **IMPLEMENTED, TESTED** (ROOT-CAUSED-FIXED)
- F-NEW-266a — **CLASSIFIED** (probe-negative proven, not implemented)
- oracle12 / B1 artifacts — **TEST-ONLY, OBSERVED** (no permanent integration)
- Phase 9 — **PENDING** (BLOCKED-APK-ABSENT, deferred with reason)
- native F-NEW-265 — unchanged, remains the single highest-ROI root
