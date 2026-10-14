# CONT-26 / TRACK B — SIMPLE CALCULATOR ANDROIDX STARTUP/THEME ROOT

Wave: CONT-26 dual-track runtime root extraction. Track B isolates the
earliest AndroidX/AppCompat divergence of Simple Calculator against the
fnew253_probe positive control, tests the historical
materialAlertDialogTheme/colorSurface hypothesis, and lands the minimal
generic fix supported by execution evidence.

**VERDICT UP FRONT:** Simple Calculator still renders NO app-owned pixels
(screenshot byte-identical to its own baseline). The wave's concrete
advance: the historical theme hypothesis is REJECTED by execution order
(theme resolution is never reached), a NEW generic P0 root
(F-NEW-280 — exact-descriptor overload authority as a hierarchy law) was
root-caused, fixed, and regression-proven, and Simple Calculator's first
divergence MOVED from "MainActivity.onCreate dies at its FIRST invoke
(AppCompat delegate creation)" to "full AppCompat startup + theme +
setContentView + real Toolbar measure/layout run; Toolbar ctor-context/
int[] init is the next divergence" — honestly reported as PARTIAL.

---

## 0. TRUTH LOCK (Phase 0)

| item | value |
|---|---|
| binary | e980887e39aee977 (pre-fix baseline) → 1ff06737f7b12ad4 (final, all fixes) |
| Simple Calculator APK | F-Droid archive `com.simplemobiletools.calculator` vc8, sha256 `68da25fd9fdf54b4...` (`tmp/cont26_apks/simplecalc_8.apk`; vc7/vc6 also captured) |
| positive control | `fixtures/fnew253_probe` rebuilt via `scripts/w4_build_probes.sh` → `tmp/w4_probebuild/fnew253_probe/fnew253_probe.apk` |
| historical investigation | issue #381 §C/H/I-J claims (committed `tmp/issue381.json`); PROGRESS.md/WORKING_APP_ROOTS.md/fnew253_api_roots.txt are container-local files lost in the reset — NOT in git history (recorded honestly); the CONT18G review had already marked the old SimpleCalc chain SUPERSEDED-BY-EVIDENCE (artifact-dependent) |

---

## 1. B1 — DUAL CONTROL AT THE PRE-FIX BINARY (directive E-B1)

**Positive control** (`run/cont26/f253_control/`): fnew253_probe executes
and renders its own report — screenshot `7602563f52cce823`, **147 PASS /
0 FAIL** rows in the run log (the 21-row probe echoed across renders).
The engine renders real app-built view content at this binary.

**Failing target** (`run/cont26/simplecalc_base1/`): Simple Calculator
launches, MainActivity.onCreate dies — screenshot `7960bce447ac6d8f`
(white/blank), rc=1, uncaught faces:

```text
1. IAE   "Window callback may not be null"
         Landroid/support/v7/view/n;.<init> pc=9   ← FIRST DIVERGENCE
         chain: u.onCreate → ac.a → ad.<init> → ab.<init> → y.<init> → n.<init>
2. NPE   Context.getResources on null — La/a/a/a;.<init> pc=22 (downstream of #1)
3. ISE   "No host" — Landroid/support/v4/a/af;.a pc=11 (FragmentActivity host machinery)
```

## 2. B3 — THE THEME HYPOTHESIS: REJECTED BY EXECUTION ORDER

The directive hypothesis (materialAlertDialogTheme / colorSurface lookups
poisoning the startup path) is **REJECTED**: every uncaught face sits in
`MainActivity.onCreate` BEFORE any theme/style attribute resolution
(faces #1–#3 are delegate-creation, Context-wrapper construction, and
Fragment-host wiring). The `materialAlertDialogTheme` lookup is only
reachable via dialog/show paths that require a LIVING, composed view tree —
execution never got there. Per directive §E-B3: when execution stops before
the lookup, the theme family cannot be the root. No theme claim is made.

## 3. B2/B5 — FIRST-DIVERGENCE DECODE + THE GENERIC ROOT (F-NEW-280)

**Face** (name-level): `n.<init>` disassembly
(`scripts/cont26_dex_method_disasm.py`):

```text
Landroid/support/v7/view/n;.<init> (WindowCallbackWrapper):
  invoke-direct {v2}, Ljava/lang/Object;.<init>
  if-nez v3, -> ok          ← v3 = the wrapped-callback ARGUMENT
  new-instance IAE "Window callback may not be null"
  throw v0
```

The argument was NULL — but the engine's S134 Window.getCallback law HAD
answered the live activity (`[S134-GCB] ... reg=Y act=12`).
MINIANDROID_ARG_TRACE (`run/cont26/logs/simplecalc_tr2.log`) resolves the
paradox — `ac.a` is invoked TWICE:

```text
#1 ac;.a (Landroid/view/Window$Callback;)Callback  caller=x.<init>
   p2 obj=12 (the activity)         → wrapper chain #1 OK
#2 ac;.a (Landroid/os/Bundle;)V     caller=u.onCreate   p1=NULL (legal:
   delegate.onCreate(savedInstanceState=null))
   → ad.<init> p2 tag=8 NULL_REF    → n.<init> v3=null → IAE
```

The second call site requested `(Landroid/os/Bundle;)V` — the
`AppCompatDelegateImpl.onCreate(Bundle)` override living in the
SUPERCLASS `aa`. The runtime class `ac` declares ONLY
`a(Landroid/view/Window$Callback;)` (wrapWindowCallback). The engine's
name-based dispatch accepted the same-name wrong-shape overload and
executed it with the Bundle null in the callback slot.

**Upstream law**: JVMS 5.4.5 / dalvik invoke resolution selects by the
(name, proto) pair and continues into the superclass chain; a same-name
method with a different proto is never a candidate. The engine's OWN
S108 ROOT-019 law (dalvik_engine.cpp) already states this — but the strict
skip was default-OFF with a recorded blocker (call-site descriptors that
reference methods existing NOWHERE; hard-filtering selected nothing and
ctors never ran — the v6.q→u.<init> family).

**Fix (F-NEW-280, blocker-safe middle path)**: in try_recursive_invoke(),
when the call site carries a concrete descriptor and the runtime class has
NO exact (name, descriptor, non-empty-code) match, run the F-074 super-walk
for the EXACT match FIRST; only when no ancestor declares it either does
the legacy lenient selection run unchanged. The recorded bogus-descriptor
family keeps byte-identical behavior (bogus descriptors match locally
nowhere AND up-chain nowhere), while the ac.a family resolves to the true
ancestor override. Diagnostic [F280-SUPERWALK] env-gated.

**Post-fix** (binary 1ff06737f7b12ad4, `run/cont26/simplecalc_r1..3`):

```text
- "Window callback may not be null": 0 occurrences (was 2 chains)
- AppCompat delegate startup:        COMPLETES (theme resolution runs,
                                     setContentView runs)
- Real AppCompat view tree:          Toolbar constructed + MEASURED +
                                     LAID OUT (Toolbar.onMeasure /
                                     Toolbar.onLayout dispatch)
- verdict:                           still DEFAULT_BACKGROUND_ONLY —
                                     screenshot 7960bce447ac6d8f ×3
                                     (deterministic, unchanged — NO app
                                     pixels claimed)
- NEXT divergence (recorded, not fixed):
   [V6-CTX-FALLBACK] view=obj#76 cls=Toolbar; ctor-context MISSING (x4)
   → Toolbar's int[] measure-scratch fields never initialized (the ctor
     that initializes them never executed through the engine's ctor path)
   → aput-null NPE in Toolbar.onMeasure pc=152 / onLayout pc=44
   → uncaught ×2 → APP BOUNDARY → white screen persists
```

**3-run determinism**: `7960bce447ac6d8f` ×3, uncaught=2 ×3,
Toolbar.onMeasure lines=2 ×3 (`run/cont26/simplecalc_r1..r3`).

## 4. CROSS-APP IMPACT (directive E-B6/§F)

F-NEW-280 is a generic invoke-resolution law (zero app/package/R8-name
knowledge — grep-audited diff). The full anchor+control suite (8 targets
×3, byte-identical) at the patched binary proves neutrality where the law
was never reachable; the fixed path is exercised by Simple Calculator
(support-v7 family) and any R8-minified multi-overload class whose
override lives in an ancestor. The positive control re-runs green at the
same binary.

## 5. STATUS LEDGER

| item | status |
|---|---|
| Positive control reproduced (147 PASS/0 FAIL) | TESTED |
| Simple Calculator white-screen baseline reproduced | TESTED |
| Theme hypothesis tested | REJECTED (execution order) — lookup never reached |
| F-NEW-280 root-caused + fixed + regression-proven | IMPLEMENTED+TESTED |
| Real app-owned Simple Calculator pixels | NOT ACHIEVED (PARTIAL — divergence moved, next one recorded) |
| Second independent APK tested on the changed layer | TESTED (fnew253_probe + the 8-target anchor suite, all green) |
| Next divergence recorded with evidence | [V6-CTX-FALLBACK] ctor-context MISSING → Toolbar.onMeasure aput-null |
