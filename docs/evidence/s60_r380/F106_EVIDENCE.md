# F-106 (S60) — R-NEW-380 closure: the reflection-surface law family

## R-NEW-380 (as registered at S59)

> Dooz next frontier (post F-105): ViewModelProvider create chain falls to the
> throwing factory fallback — `RuntimeException "Cannot create an instance of "`
> (class-name portion EMPTY) caller=Leo;.n pc=53 depth=81; chain
> Lyd0;.b → Ltf1;.b → Lt32;.b → Lt32;.d → Leo;.n while constructing the app
> GameViewModel after the Lwl0;.containsKey Class-key guard PASSES (F-105c).

## Root cause (DEX + runtime ground truth, S60)

The v23 APK's GameViewModel is `@HiltViewModel` (upstream source, tag 1.0.23:
`class GameViewModel @Inject constructor(settings: SettingsRepository)`) — it has
exactly ONE constructor `<init>(Lql1;)V` (Lql1; = SettingsRepository) and NO
no-arg constructor. Three independent generic engine gaps produced the S59 face:

1. **Reflection-surface typed-zeros (F-086 family: missing handler → typed-zero →
   wrong branch).** `Class.getDeclaredConstructor` (the legacy bridge at
   dalvik_engine.cpp:18241) minted a Constructor record keyed on
   `args[0].class_desc` — for the F-103 heap-backed Class token that is
   `Ljava/lang/Class;` — the referent identity was LOST. `Constructor.getModifiers()`
   and `Modifier.isPublic(I)Z` had NO handlers → STUBBED typed-zero 0 → the
   androidx NewInstanceFactory DEX (`Leo;.n`):
   `if (!Modifier.isPublic(ctor.getModifiers())) throw RuntimeException("Cannot
   create an instance of " + modelClass)` ALWAYS took the throw branch.
   DEX ground truth: scripts/s60_r380_forensic.py (Leo;.n @0x0006 getDeclaredConstructor
   → @0x000e getModifiers → @0x0016 isPublic → @0x001e if-eqz → @0x004e new
   RuntimeException → @0x0070 throw).
2. **`Collections.unmodifiableMap` missing.** The Hilt ViewModelStore-key binding
   (`Lls;.a()`: LinkedHashMap{hb0, bm1} → unmodifiableMap → `new Lwl0;(map)`) got a
   NULL backing map → `Lwl0;.containsKey(hb0-token)` answered FALSE →
   ViewModelProviderImpl fell to the DEFAULT factory chain (Ltf1; SavedState chain
   → AndroidViewModelFactory → NewInstanceFactory) instead of the app's Hilt
   factory. [INSTANCEOF-DIAG] Lwl0;.containsKey pc=0 guard=TRUE yet result FALSE
   (run/s60_r380_post2_stderr.log:246016).
3. **`Long.toString(J, I)` missing.** The Compose rememberSaveable key is
   `Long.toString(compositeKeyHash, 36)` (Lpm;.W pc=0x0e). Typed-zero "" →
   `DisposableSaveStateRegistry.registerProvider("")` → IAE "Registered key is
   empty or blank" (Ldf1;.a, depth 21) — the face exposed after (1)+(2) were fixed
   (run/s60_r380_post3_stderr.log:247877).

Diagnostic gap: no `Class.toString()` law → the exception message rendered an
EMPTY class name ("Cannot create an instance of " + nothing).

## Fix (F-106 law family — all generic, app-agnostic)

- **F-106a** `Class.getDeclaredConstructor/getConstructor` full upstream contract
  (dalvik_engine.cpp): referent resolution through `__referent_desc` (F-103
  authority); the (possibly null) Class[] parameter argument selects the ctor by
  EXACT parameter descriptor list; getConstructor requires ACC_PUBLIC; no match →
  **NoSuchMethodException** via throw_deferred (the OpenJDK law — the caller's
  catch block is the designed path); match → the record carries
  class_desc=REFERENT, `__reflect_mods` (raw DEX access flags) and
  `__reflect_params`.
- **F-106a** `Constructor.getModifiers()I` (reads __reflect_mods; legacy records
  resolve the no-arg ctor from the DEX) + `Constructor.getParameterTypes()` (a
  real Class[] from __reflect_params — serves the androidx findMatchingConstructor).
- **F-106** `java.lang.reflect.Modifier` static bit family (isPublic/isPrivate/
  isProtected/isStatic/isFinal/isSynchronized/isVolatile/isTransient/isNative/
  isInterface/isAbstract/isStrict — JVM/DEX shared bit positions).
- **F-106** `Class.toString()` (OpenJDK law: "class "/"interface " + getName()) in
  the Class-token section AND in the StringBuilder `stringify_arg` law (CLASS_REF
  + heap-token shapes — the literal mechanism behind the EMPTY name).
- **F-106b** `Collections.unmodifiableMap/unmodifiableSet/unmodifiableCollection`
  — the unmodifiable view delegates every read to the backing container
  (single-threaded engine: return the backing container; the unmodifiableList
  precedent).
- **F-106c** `Long.toString(J)` / `Long.toString(J, I)` — signed 64-bit, radix
  2..36, digits 0-9a-z, Long.MIN_VALUE-safe magnitude, out-of-range radix → IAE.

Harness (S60): `--max-seconds N` wall-clock soft budget (graceful stop identical
to the instruction budget — the end-of-run evidence pipeline still runs); the
always-on EXP093-APUT per-op trace and the always-on parser dumps are now
env-gated (MINIANDROID_EXP093_APUT_TRACE / MINIANDROID_PARSE_VERBOSE) per the
F-074 hygiene law — bounds/store semantics unchanged.

## Proof

- Semantic regressions 32/32 (six new f106 records in
  tests/semantic_long_cmp_conv_test.cpp, incl. the discriminating
  f106_newinstancefactory_full_chain: const-class → getDeclaredConstructor(null)
  → getModifiers → Modifier.isPublic → newInstance → the REAL <init> body → 127;
  and f106_getdeclaredconstructor_missing_throws_nsm: the no-arg lookup on a
  class with only <init>(I)V unwinds with NoSuchMethodException).
- dooz v23 pre-fix face: `RuntimeException "Cannot create an instance of class
  hb0"` at Leo;.n/Ljb1;.g (see pre_f106_face.log).
- dooz v23 post-fix (run/s60_r380_post7, --max-seconds 480):
  - ZERO exceptions before the budget stop (THROWABLE-MSG count 0);
  - the create chain resolves through the app's OWN Hilt factory: Lk2;.b case-1
    (SavedStateHandle machinery, Lqs;/Lxd0; attach OK obj#5385),
  - the GameViewModel instance constructs (Lq32;.c ViewModel closeable
    registration + the game-state class inits from the ctor body),
  - the run reaches the healthy frame loop (MainActivity.onStart/onResume
    dispatched; Choreographer machinery alive) and ends at the wall-clock
    budget with the evidence artifacts on disk (post_f106_keylines.log).
- dooz v18 regression (run/s60_v18_reg, --max-seconds 330): 0 errors, the
  Choreographer doFrame loop alive — the healthy face preserved, deeper than S58.
- BATTERY GATE: ALL PASS (96 stages) at this HEAD; semantic label 26 → 32.

## Remaining honest face (successor frontier)

The dooz v23 first frame is still dark (same face as the S59 post2 evidence) —
the composition + Hilt creation now run end-to-end with zero exceptions, and the
next gap is the Compose DRAW path (the UI content does not reach pixels yet).
Registered as the successor frontier — see ROADMAP_STATUS §3.
