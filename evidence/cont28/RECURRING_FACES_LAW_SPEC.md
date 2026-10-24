# CONT-28-RESEARCH-A — RECURRING FACES LAW SPEC: S102 compose-locals + DataStore ENOENT

Agent: research-subagent (read-only; no code, no push). Method: pure-python DEX
disassembly of the affected APKs (scratch tooling in /home/z/tmp_cont28/, NOT in
the repo), engine-law audit by grep, upstream truth from
`upstream/cont12_maven/` (savedstate-compose-android-1.4.0 bytecode,
ui-android-1.11.4 sources). Census sigs from
`evidence/cont14/batch20_census_v2.json`; ledger context
`evidence/cont14/CONT14_BATCH4_LEDGER.md`.

---

## 1. TASK 1 — S102 compose-locals CNF/NSM family

### 1.1 VERDICT UP FRONT: **ART-faithful DECOY — no engine change needed.**

The face is the app's OWN version-compat probe failing exactly as real ART
fails it. The probe is designed to fail; the catch-all is the designed path;
the static field is ALWAYS written with a non-null fallback. Any engine "fix"
that suppressed the CNF/NSM would DIVERGE from ART.

### 1.2 The faces (census sigs, exact)

| app | sig (evidence/cont14/batch20_census_v2.json) |
|---|---|
| matewave | `[SYNTH-EXC] S102-CLASSLOADER (deferred): ClassNotFoundException (androidx.compose.ui.platform.AndroidCompositionLocals_androidKt) method=Lwn0;.<clinit> pc=14 → deferred handler @0x2c type=<catch-all>` |
| sparkledns | `[SYNTH-EXC] F-NEW-219 (deferred): NoSuchMethodException (Landroidx/compose/ui/platform/AndroidCompositionLocals_androidKt;.getLocalSavedStateRegistryOwner(...)) method=Landroidx/savedstate/compose/LocalSavedStateRegistryOwnerKt;.<clinit> pc=18 → deferred handler …` |
| dooz | same CNF variant as matewave (deferred, caught; content-impacting downstream only) |

pc cross-check: 14 decimal = 0x0e = the `ClassLoader.loadClass` invoke;
18 decimal = 0x12 = the `Class.getMethod` invoke — both EXACT per the
disassembly below.

### 1.3 DEX TRUTH (disassembly; scratch tool `/home/z/tmp_cont28/cont28_faces_truth.py`)

**(a) matewave** `upload/fdroid_batch/cc.skysparkle.matewave_2.apk`, single dex:

- `Landroidx/compose/ui/platform/AndroidCompositionLocals_androidKt;` has
  **NO class_def anywhere** (R8 renamed/merged it away). The dotted name
  survives only as string constant #8277.
- `Lwn0;` (= renamed `androidx.savedstate.compose.LocalSavedStateRegistryOwnerKt`)
  declares exactly one method `<clinit>` + static field `a`
  (= `LocalSavedStateRegistryOwner`). Disassembly (90 code units, 1 try):

```
try [0x1,0x38) catch-all → 0x2c
 0x00 const/4 v0, null                      ; the getOrNull() "or null"
 0x01 const-class v1, Lhd1;                 ; renamed SavedStateRegistryOwner
 0x03 invoke-virtual Class.getClassLoader → Object.getClass
 0x0a const-string v2 "androidx.compose.ui.platform.AndroidCompositionLocals_androidKt"
 0x0c const-string v3 "getLocalSavedStateRegistryOwner"
 0x0e invoke-virtual ClassLoader.loadClass  ← pc=14 decimal: CNF THROWN HERE
 0x12 invoke-virtual Class.getMethod        ← NSM (sparkledns path)
 0x16 invoke-virtual AccessibleObject.getAnnotations → Deprecated-annotation scan
 0x2c move-exception v1                     ← CATCH-ALL HANDLER (engine lands here)
 0x2d goto 0x39
 0x39 new-instance v2, Lza1;                ; renamed kotlin.Result$Failure (runCatching)
 0x3b invoke-direct Result$Failure.<init>(throwable)
 0x46 check-cast v1, Lq81;                  ; renamed ProvidableCompositionLocal
 0x48 if-nez v0 → 0x57                      ; probe SUCCEEDED path
 0x4a new-instance v0, Lop;                 ; fallback default-provider lambda
 0x4c const/16 … invoke-direct Lop;.<init>
 0x51 new-instance v1, Lvl1;                ; renamed StaticProvidableCompositionLocal
 0x53 invoke-direct Lq81;.<init>(policy, provider)
 0x57 sput-object → Lwn0;.a                 ; THE PUT ALWAYS HAPPENS, NON-NULL
 0x59 return-void
```

**(b) sparkledns** `cc.skysparkle.sparkledns_10006.apk` (NOT minified — the
clean reference read of the same code):

- `AndroidCompositionLocals_androidKt` **IS defined** in the dex, but its ONLY
  methods are `<clinit>`, `ProvideAndroidCompositionLocals`,
  `access$noLocalProvidedFor`, `getLocalLifecycleOwner` —
  **`getLocalSavedStateRegistryOwner` is genuinely ABSENT** (this APK bundles an
  older compose-ui with a newer savedstate-compose — the exact mismatch the
  shim exists for).
- `LocalSavedStateRegistryOwnerKt;.<clinit>` — byte-identical structure to
  matewave's (same try [0x1,0x38) catch-all→0x2c), with UNRENAMED names:
  fallback = `new AppShellKt$$ExternalSyntheticLambda0` +
  `new StaticProvidableCompositionLocal(lambda)` →
  `sput-object LocalSavedStateRegistryOwnerKt.LocalSavedStateRegistryOwner`.

**(c) dooz** `io.github.yamin8000.dooz_23.apk` — `scripts/cont28_dooz_gq0_truth.py`
output confirms: "NO CLASS_DEF for target — string is only a Class.forName
constant (R8 keep-name)"; `Lgq0;.<clinit>` carries the SAME two const-strings
and the SAME loadClass/getMethod reflective chain. CNF variant, same contract.

### 1.4 UPSTREAM TRUTH (source + bytecode)

- `upstream/cont12_maven/raw/savedstate-compose-android-1.4.0.aar` →
  `androidx/savedstate/compose/LocalSavedStateRegistryOwnerKt.class` constant
  pool contains exactly: `"androidx.compose.ui.platform.
  AndroidCompositionLocals_androidKt"`, `"getLocalSavedStateRegistryOwner"`,
  `kotlin/Result` + `ResultKt.createFailure` + `isFailure-impl`
  (= `runCatching { … }.getOrNull()`), and the fallback:
  `IllegalStateException` + message
  **"CompositionLocal LocalSavedStateRegistryOwner not present"** +
  `CompositionLocalKt.staticCompositionLocalOf`. So the real source is:

  ```kotlin
  val LocalSavedStateRegistryOwner: ProvidableCompositionLocal<SavedStateRegistryOwner> =
      runCatching {  // reflect into compose-ui (older versions kept it there)
          SavedStateRegistryOwner::class.java.classLoader
              .loadClass("androidx.compose.ui.platform.AndroidCompositionLocals_androidKt")
              .getMethod("getLocalSavedStateRegistryOwner")   // + @Deprecated guard
              .invoke(null) as ProvidableCompositionLocal<SavedStateRegistryOwner>
      }.getOrNull()
      ?: staticCompositionLocalOf { error("CompositionLocal LocalSavedStateRegistryOwner not present") }
  ```

- `upstream/cont12_maven/ui-android-1.11.4-sources.jar`
  `AndroidCompositionLocals.android.kt` confirms the modern shape: the
  compose-ui accessor is a `@Deprecated` forwarder to savedstate-compose —
  the shim is the version-compat mechanism, and failing it is DESIGNED
  behavior.

### 1.5 Engine-law parity audit (miniandroid/src/dex/dalvik_engine.cpp)

| step | engine law | site | ART parity |
|---|---|---|---|
| `ClassLoader.loadClass(missing)` → deferred CNF | S102-CLASSLOADER | :55683–55701 (result null + `throw_deferred`) | YES — PathClassLoader has no such class in the dex → CNF |
| `Class.getMethod(missing)` → deferred NSM | F-NEW-219 walk of the dex method table | :31186–31259 | YES — method genuinely absent (dex-verified) → NSM |
| `Class.forName(unknown)` → deferred CNF | R350-FORNAME | :24293–24321 | YES (not on this path, but same family) |
| deferred exception → typed/catch-all handler dispatch, pc → handler (move-exception) | `throw_deferred` + `exc_redirect_` | :19087–19134, :18467–18469 | YES |
| handler body: `Result$Failure.<init>`, lambda `<init>`, `StaticProvidableCompositionLocal.<init>`, `sput-object` | generic interpreter paths | — | YES (apps proceed: matewave run `run/c154/cc.skysparkle.matewave.out` shows post-face compose composition errors, verdict DEFAULT_BACKGROUND_ONLY) |

### 1.6 Answers to the LAW QUESTIONS

**(a) After the CNF is caught, what is stored?** NOT null, NOT skipped. The
catch path wraps the throwable in `kotlin.Result$Failure` (runCatching),
`.getOrNull()` yields null, and the `?:` arm CONSTRUCTS a fresh fallback
`staticCompositionLocalOf { error("CompositionLocal LocalSavedStateRegistryOwner
not present") }` and `sput-object`s it into the static. The composition-local
static is non-null in every outcome (reflective hit, CNF, NSM, or
deprecated-guard).

**(b) Does the engine differ from ART?** NO. In real ART the SAME probe fails
the SAME way on THESE APK bytes: matewave/dooz — the class is genuinely absent
from the dex (R8 removed/renamed it), so `loadClass` throws CNF on device too;
sparkledns — the class is present but the method genuinely absent (older
compose-ui bundled), so `getMethod` throws NSM on device too. The engine's
deferred CNF/NSM lands on the same catch-all/typed handler at the same pc
(handler @0x2c verified against the dex try table).

**(c) Conclusion:** S102 is a **NO-OP face (decoy)**. The deferred+caught CNF/NSM
is the honest observation of androidx's own compat shim failing under R8
minification / version skew, and real ART behaves identically. Law spec:
**no engine change; reclassify the census face as "expected-handled
(upstream compat-probe)". Downstream content impact of matewave/dooz lives in
the APP_DRAW_OPS draw-path family, not here.**

---

## 2. TASK 2 — DataStore ENOENT family (awagam, compose_stopwatch)

### 2.1 VERDICT UP FRONT: **ART-faithful — the FNFE is the designed first-launch
contract and the engine ALREADY routes it correctly. No engine change.**

### 2.2 The faces (census sigs, exact)

- awagam: `[SYNTH-EXC] STREAM-OPEN (deferred): FileNotFoundException
  (/data/data/com.awagam.android/files/datastore/settings.preferences_pb (open
  failed: ENOENT)) method=Lsv;.s pc=57 → deferred handler @0x52 type=…`
- compose_stopwatch: same shape, `…/files/datastore/preference.preferences_pb`,
  `method=Lx2;.p pc=57 → deferred handler @0x52 …`.

pc cross-check: 57 decimal = 0x39 = the `FileInputStream.<init>` invoke inside
`Lsv;.s` / `Lx2;.p` (both APKs carry structurally identical obfuscated
datastore read state-machines).

### 2.3 DEX TRUTH (awagam `Lsv;.s`, code_off=0x120864, 240 units, 14 tries)

```
try [0x35,0x3c) Ljava/io/FileNotFoundException;@0x52   ← TYPED catch, covers pc=0x39
 0x35 new-instance v0, Ljava/io/FileInputStream;
 0x37 iget-object Lj70;.a                    ; the store File
 0x39 invoke-direct FileInputStream.<init>   ← pc=57 decimal: FNFE(ENOENT) on first launch
 …
 0x52 iget-object Lj70;.a                    ← THE FNFE HANDLER BODY
 0x54 invoke-virtual Ljava/io/File;.exists   ← handler re-checks the file
 0x58 if-eqz → 0x90                          ; file ABSENT (first launch) → empty-store path
 0x5a/0x5e new FileInputStream…<init>        ; file PRESENT but open failed → retry/rethrow arm
 0x7f/0x81 move-exception; instance-of FileNotFoundException; if-eqz → rethrow other
 0x83 invoke-virtual File.getParent; 0x8b invoke-static Lx82;.X(parent, fnfe); 0x8f throw
 0x90 new-instance v8, Lv21;                 ; ABSENT-file arm: construct the EMPTY-STATE
 0x92 invoke-direct Lv21;.<init>             ;   object (no-arg <init>, plain Object subclass)
 0x96 return-object v8                       ; RETURN it (no throw) → default data
```

`Lx2;.p` in compose_stopwatch has the byte-identical try/catch table
(`try [0x35,0x3c) FileNotFoundException@0x52` first in its table too).

**This IS the androidx datastore first-read contract, seen from the app's own
bytes:** `SingleProcessDataStore`/preferences read catches
`FileNotFoundException`, checks `File.exists()`, and on first launch (absent
file) returns the empty-store state so the DataStore answers `defaultData`;
the file (and parent dirs) are created on first WRITE. The engine's census
sig proves the deferred FNFE was routed to the typed handler @0x52 — i.e. the
routing the CONT-14 ledger wished for ("route the deferred FNFE to the
DataStore coroutine chain's handler") is ALREADY the observed behavior.

### 2.4 Engine-law audit and fix location (if ever needed)

- The FNFE is raised at the `FileInputStream(File)` ctor absent-file branch:
  **`miniandroid/src/dex/dalvik_engine.cpp:32239–32247`**
  (`throw_deferred("Ljava/io/FileNotFoundException;", p+" (open failed: ENOENT)",
  "STREAM-OPEN")` — the message format matches libcore's
  `IoBridge.open` errno→FNFE text exactly). Same contract law at
  `Context.openFileInput` **:32765–32793** (absent → FNFE) and
  `ContentResolver.openInputStream` **:34419–34454**.
- The handler body needs `File.exists()` to answer honestly — the law lives at
  **`miniandroid/src/dex/dalvik_engine.cpp:61014–61056`** (`File.exists` →
  real `std::filesystem::exists` through the ONE `resolve_android_path` law)
  and first-write creation is covered by `Context.openFileOutput` parent
  mkdir (:32738–32745) and `File.mkdirs`/`createNewFile` (:61203–61266).
- **A fix WOULD go at :32239–32247 only if** the engine ever needed to
  *not* throw — and it must NOT: AOSP `FileInputStream.open` on an absent file
  throws FNFE; the app-layer catch must receive the exception it expects.

### 2.5 LAW SPEC statement (one sentence, generic)

**First-launch missing DataStore/preferences file is an EXPECTED condition: the
engine must throw the AOSP `FileNotFoundException ("open failed: ENOENT")`
deferred so the app's typed catch observes it (never swallow silently, never
crash), while the sandbox file layer must auto-create parent dirs on first
write — this is already implemented; the face is non-killing noise and both
apps' real frontier is the APP_DRAW_OPS draw-path family.**

---

## 3. TASK 3 — remaining named faces census (from CONT14_BATCH4_LEDGER.md + batch20_census_v2.json)

| face (sig family) | apps | class | verdict / generic-fix likelihood |
|---|---|---|---|
| S102 compose-locals CNF/NSM | matewave, sparkledns, dooz | recurring ×3 | **DECOY (§1)** — ART-faithful; no fix |
| DataStore first-read ENOENT | awagam, compose_stopwatch | recurring ×2 | **DECOY (§2)** — typed catch already routed; no fix |
| FitWindowsFrameLayout.makeOptionalFitsSystemWindows NSM (F-NEW-219) | fossify_math, fossify_clock, k9 (+ fossify_notes pre-F-NEW-519) | recurring ×3–4 | **DECOY — dex-verified this session**: the method is genuinely ABSENT from k9's and fossify_math's dex (class defined, only `<init>/fitSystemWindows/setOnFitSystemWindowsListener`), so real ART's `getMethod` NSMs identically and the appcompat probe catches NSM by design (ledger: "upstream-caught"). No engine fix. |
| f141 null-recv `Object.getClass` NPE | aurora, webstack, audiobook (identical face), fossify_calendar (`Lu30;.r`, obfuscated) | recurring ×3 (×4 shape) | **REAL family — top fix candidate.** One framework API returns null where AOSP returns non-null; needs the per-caller truth pass (which API produced the receiver). Generic likelihood MEDIUM-HIGH. |
| f141 null-contract singles | prism (Cursor.moveToNext), wocheneinkauf (TrustManagerFactory.init), goodtime (`Lap2;.a`), dmfs_tasks (getPagePosition), surgeengine (List.size), notepad (Insets.left iget) | singles ×6 | individual roots; low per-fix genericity, high raw count |
| R350-FORNAME kotlin-reflect CNF (`ReflectionFactoryImpl`) | netguard | single (will recur on kotlin-reflect apps) | deferred+caught shape; needs dex-truth pass before any law |
| Koin NoDefinitionFoundException | k9 | single | service-registry family |
| NO_ROOT / WINDOW_ROOT | goodtime, surgeengine | shape-recurring ×2 | separate root (window attach), not a per-app face |
| (retained real-content) bouncy, netguard, fossify_math/calendar | 4 | — | not faces |

**Ranking by (apps affected × fix genericity):**
1. **f141 `Object.getClass` null-recv family** — 3 exact + 1 shape; the only family where an engine law actually diverges from AOSP today (a framework producer answers null).
2. **S102 compose-locals** — 3 apps, but the "fix" is the one-time reclassification to expected-handled (decoy) — unblocks 3 ledger rows for free.
3. **FitWindows NSM** — 3–4 apps, same decoy reclassification (dex-proof banked here).
4. **DataStore ENOENT** — 2 apps, decoy reclassification (dex-proof banked here).
5. **f141 singles pool** — 6 singles, each its own root; batch them per-API-truth waves.
6. **NO_ROOT WINDOW_ROOT** — 2 apps, separate window-attach root family.

---

## 4. SURPRISES

1. **The census's two "named next-wave" families (S102, DataStore) are both
   ART-faithful decoys.** The real blocker behind all these apps is the shared
   `first_missing=APP_DRAW_OPS` draw-path frontier, exactly as the ledger's
   draw-path note suspected. The 20-by-20 "recurring face" ledger should grow a
   new state: `EXPECTED-HANDLED (upstream probe)` so caught-by-design faces
   stop occupying the fix queue.
2. **The DEX spec gotcha:** `encoded_method.method_idx_diff` restarts from 0
   for EACH list (direct AND virtual); a continuous-index parser (including
   `scripts/cont28_dooz_gq0_truth.py` and my first draft) misparses any class
   with direct methods followed by virtual methods — it desyncs and reads
   garbage method names/pcs. All "single-method <clinit>" parses in the prior
   records are unaffected; future truth scripts must restart the index.
3. **sparkledns is the live demonstration of the androidx shim's purpose:**
   it bundles an OLD compose-ui (accessor absent) with a NEW savedstate-compose —
   on real ART the probe NSMs and the fallback local is built; the engine now
   provably does the same.
4. **The fallback local's default provider throws**
   `IllegalStateException("CompositionLocal LocalSavedStateRegistryOwner not
   present")` — matewave's later "ComposeInternal: Error was captured in
   composition" log line is the ART-faithful downstream of that designed ISE,
   NOT an engine bug.
5. `run/c154` matewave/sparkledns outputs show the compose-locals face costs
   nothing: both runs reach PARTIAL SUCCESS with the draw stage as the first
   missing stage.

## 5. NEXT ACTIONS (for the main agent)

1. Land the census reclassification: S102 → EXPECTED-HANDLED, DataStore ENOENT
   → EXPECTED-HANDLED, FitWindows NSM → EXPECTED-HANDLED (dex-proof in §3).
2. Open the ONE real recurring root: identify the framework API whose null
   receiver feeds `Object.getClass` in aurora/webstack/audiobook (f141
   producer pass), then write the AOSP non-null law.
3. Keep the file-layer laws untouched (they are the AOSP contract).
4. Scratch truth tooling from this session lives outside the repo at
   `/home/z/tmp_cont28/` (cont28_faces_truth.py, cont28_datastore_truth.py) —
   promote into scripts/ only if wanted, with the method_idx_diff restart fix.
