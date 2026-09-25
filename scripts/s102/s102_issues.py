#!/usr/bin/env python3
"""s102_issues.py — S102 issue-per-problem lifecycle.

Creates the S102 frontier tickets (one per distinct remaining root, no
duplicates for the same root law) and posts the wave report to the
master thread #233. Token from MINIANDROID_GH_TOKEN env only.
"""
import json
import os
import sys
import urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
TOKEN = os.environ.get("MINIANDROID_GH_TOKEN", "")
if not TOKEN:
    print("MINIANDROID_GH_TOKEN not set", file=sys.stderr)
    sys.exit(1)


def gh(path, body):
    url = f"https://api.github.com/repos/{REPO}/{path}"
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    with urllib.request.urlopen(req) as r:
        return json.load(r)


ISSUES = [
    {
        "title": "[S102-A] solitaire: R8-merged SavedStateRegistryController — getSavedStateProvider invoked on null registry receiver inside ComponentActivity.<init>",
        "body": """APK: com.vayunmathur.games.solitaire (the only title with genuine androidx/compose stack evidence in the ledger)
Engine head: 6c0d8f5f (S102, all 4 laws landed)

**Status after the S102 laws** — the original chains (SavedStateRegistryImpl.performAttach NPE ← BigInteger.valueOf null; performRestore NPE) are GONE. The ctor now dies one step later:

```
[SYNTH-EXC] f141-null-recv (deferred): NullPointerException
  (Attempt to invoke virtual method 'Lkotlin/text/MatcherMatchResult;.getSavedStateProvider'
   on a null object reference)
  method=Landroidx/activity/ComponentActivity;.<init> pc=224
[EXC-PROPAGATE] uncaught → APP BOUNDARY unwind
```

**Root analysis (evidence-first):** R8 full-mode renamed the savedstate
controller family (the class the dex tools print as
`Lkotlin/text/MatcherMatchResult;` carries savedstate methods
performRestore/getSavedStateProvider — verified: the APK dex has
`Landroidx/savedstate/internal/SavedStateRegistryImpl;` with ONLY
<init>+performAttach, and SavedStateRegistryController is absent under
its original name → renamed/merged). The R8-inlined flow inside
ComponentActivity.<init> reads a null field (the registry impl) at
pc=224 after performAttach succeeded — the heap store/load pairing for
the promoted R8 field is the next divergence to trace (register-level:
what wrote the field, what read it).

**Repro:** `./miniandroid/build/miniandroid run --execution-mode real-dalvik --frames 4 run/s99/apks/com.vayunmathur.games.solitaire.apk` — crash.log chain 1.

**Open->fix->verify->close protocol:** the fix must be a named law (R8
field-promotion identity) with a synthetic-dex battery stage mirroring
f106; close with before/after crash.log chains.
""",
    },
    {
        "title": "[S102-B] compose frontier: 'CompositionLocal LocalDensity not present' — WindowRecomposer host wiring (solitaire, the real compose-runtime root)",
        "body": """APK: com.vayunmathur.games.solitaire (also blocks eu.veldsoft.no.thanks family)
Engine head: 6c0d8f5f

**Evidence (fresh S102 run):**
```
ISE msg="CompositionLocal LocalDensity not present"
  caller=Landroidx/compose/ui/platform/CompositionLocalsKt;.noLocalProvidedFor pc=25
ISE unwound Landroidx/compose/ui/platform/CompositionLocalsKt$LocalDensity$1;.invoke
  ← Landroidx/compose/ui/platform/WindowRecomposer_androidKt;.getWindowRecomposer
  ← Landroidx/compose/ui/platform/AbstractComposeView;.resolveParentCompositionContext
  ← Landroidx/compose/ui/platform/AbstractComposeView;.onMeasure
  ← Landroidx/activity/ComponentActivity;.setContentView
```

**Root:** AbstractComposeView.onMeasure → ensureCompositionCreated →
resolveParentCompositionContext → WindowRecomposer_androidKt requires a
ViewTreeLifecycleOwner/ViewTreeViewModelStoreOwner on the decor chain
upstream (AndroidX source: WindowRecomposer_androidKt.createAndInstall
WindowRecomposer reads `window.decorView.viewTreeLifecycleOwner`), and
the composition host must PROVIDE LocalDensity (computed from
Resources.displayMetrics density + fontScale) before composable
lambdas read it. MiniAndroid executes the composable lambda bodies but
no CompositionLocal provider layer exists yet — `noLocalProvidedFor`
is the honest upstream exception.

**Required semantic subset (RULE 5 — minimum, evidence-backed):**
1. ViewTree*Owner get/set tags on the real ViewShadow tree (dooz
   evidence: the F-023 closure already models the tag read for
   LifecycleOwner — extend to CompositionContext + the SAVEDSTATE owner
   for the S103 wave).
2. CompositionLocal provide/read semantics in the composer interpreter
   (a real ContextMap, NOT a global recompose-everything fake).
3. LocalDensity provider law reusing the existing density laws
   (G05 density matrix — no Compose-specific copy).

Reject static-frame evidence; the gate is E3+ render with state-change
pixels (RULE 7).
""",
    },
    {
        "title": "[S102-C] mentalmath: Hilt DI 'ApplicationContextModule must be set' ISE in DaggerMentalMath_HiltComponents_SingletonC$Builder.build",
        "body": """APK: com.helddertierwelt.mentalmath
Engine head: 6c0d8f5f (S102 — the MULTIDEX-INTERFACE-CLOSURE and
SERVICELOADER laws advanced this chain: the coroutine dispatch chain
and the ServiceLoader NPEs are gone)

**Remaining primary blocker:**
```
ISE msg="dagger.hilt.android.internal.modules.ApplicationContextModule must be set"
  caller=Ldagger/internal/Preconditions;.checkBuilderRequirement pc=28
  ← Lcom/helddertierwelt/mentalmath/DaggerMentalMath_HiltComponents_SingletonC$Builder;.build
  ← Hilt_MentalMath$1.get ← Hilt_MentalMath.generatedComponent
  ← Hilt_MentalMath.hiltInternalInject ← Hilt_MentalMath.onCreate
```

**Root analysis:** the generated Dagger builder flow sets
`applicationContextModule = new ApplicationContextModule(application)`
in one phase and reads it in build(). The engine executes the real dex
but the builder field write/read pair breaks (same family as the
S102-A R8 field-promotion suspicion — both are generated-code field
identity chains; verify against the same law before implementing a
Hilt-specific shim).

**Downstream layer (auto-clears if C fixes):**
`Landroidx/core/splashscreen/SplashScreen$Impl31;.setKeepOnScreenCondition pc=19
NPE 'View.getViewTreeObserver on a null object reference'` — content
view was never set because Hilt injection died first.
""",
    },
    {
        "title": "[S102-D] coroutines: CoroutineScheduler$Worker.tryPark interpreter spin (LockSupport.park has no blocking semantics)",
        "body": """APK: com.helddertierwelt.mentalmath (any app reaching Dispatchers.Default worker threads)
Engine head: 6c0d8f5f

**Evidence:**
```
F084 interpreter halt in callee: Infinite loop at PC=0x8d in
Landroidx/coroutines/scheduling/CoroutineScheduler$Worker;.tryPark
(visited 50001 times in this frame, bytecode_size=64)
```

**Root:** tryPark's real semantics: worker state PARKING →
LockSupport.parkNanos/unpark handshake. Our LockSupport bridge answers
void WITHOUT blocking or unpark bookkeeping, so the dex loop spins
forever. The engine needs the deterministic-subset law: single-thread
park/unpark where park() drains one queued unpark token (or yields a
frame) — reuse the existing PARK-DRAIN machinery (R-NEW-345) rather
than a second scheduler.

**Classification:** COROUTINE capability (modular foundation);
required by every kotlinx.coroutines app that touches
Dispatchers.Default.
""",
    },
]

MASTER_REPORT = """## S102 — COMPOSE FAMILY ROOT-CAUSE SWEEP + SAVEDSTATE PREPARATION: wave report

**Scope correction (evidence-first, the most important finding):** the
S101 ledger's "COMPOSE family: 46 games" was a REGEX FALSE-POSITIVE —
the family rule matched the phrase "snapshot was taken" in unrelated
engine diagnostics. Real androidx/compose stack evidence: **1 title**
(com.vayunmathur.games.solitaire). The rule is now tightened to
androidx/compose frames; the honest compose family is 6 titles.

### Root laws landed (each committed separately, battery green per commit)

| law | commit | what it fixes |
|---|---|---|
| MULTIDEX-INTERFACE-CLOSURE | d963ff1e | F-103 interface index was DEX-0-only: 10,002 secondary-DEX classes in mentalmath (4,708 declaring interfaces) failed castability to their own interfaces — AndroidDispatcherFactory as MainDispatcherFactory CCE at FastServiceLoader.loadMainDispatcherFactory killed Dispatchers.Main |
| SERVICELOADER-APK-ENTRY | ab003d6e | ClassLoader.getResources + URL.openStream + java.util.ServiceLoader over META-INF/services (real provider materialization through dex <init>); fixed 'ServiceLoader.iterator on a null object reference' + 'list(...) must not be null' NPEs — the coroutine uncaught-exception handler chain is alive |
| BIGINT-VERSION-PARSE | 6c0d8f5f | java.math.BigInteger subset (valueOf(J)/shiftLeft(I)/or/compareTo): valueOf-null NPE killed SavedStateRegistryImpl.performAttach ← ComponentActivity.<init> — the compose title died in its CONSTRUCTOR |
| LONG-BITMATH-64 | 6c0d8f5f | Long 64-bit static family for androidx.collection MutableScatterMap probe math (numberOfTrailingZeros etc. answered null → slot-0 corruption vector) |

### Measured impact (fresh 61-title census on the final tree, identical S99/S101 protocol)

* census: INTERACTIVE-EVIDENCE **14** (was 13), RENDERED-L2+ **2**, PARTIAL **38** (was 39), FAIL **7** (unchanged)
* flip table: org.secuso.privacyfriendlymemory PARTIAL → INTERACTIVE-EVIDENCE; **zero regressions**
* solitaire: 4 failure chains → 2 distinct remaining roots (the performAttach + performRestore chains are GONE)
* mentalmath: coroutine dispatch + ServiceLoader chains GONE; remaining: Hilt DI ISE (#C) + scheduler park (#D)
* battery: **105/105 ALL PASS** on the final tree (32/32 long/cmp/conv relinked green)

### New frontier tickets (one per distinct root, no duplicates)

* #S102-A solitaire R8-merged SavedStateRegistryController field identity (getSavedStateProvider null receiver)
* #S102-B **the real compose frontier**: CompositionLocal provide/read semantics + ViewTree*Owner host wiring ('LocalDensity not present' ← getWindowRecomposer)
* #S102-C Hilt generated-builder field identity ('ApplicationContextModule must be set') — same R8 field-promotion family as A
* #S102-D LockSupport park/unpark deterministic subset for CoroutineScheduler.tryPark

### SavedState preparation (RULE 16 map)

* COMPOSE_REQUIRED only: solitaire (AbstractComposeView chain)
* BOTH: mentalmath (savedstate registry + Hilt/SavedStateHandle), solitaire
* SAVEDSTATE_REQUIRED (19-title family, unchanged): firestrike, babydots, blidraughts, mancala, ballbreak, klondike, no.thanks, mykanji, chess, secuso family…
* S103 should start with the shared R8 field-identity law (A+C) — one law, two families — then the compose host wiring (B).
"""


def main():
    created = []
    for iss in ISSUES:
        out = gh("issues", {"title": iss["title"], "body": iss["body"],
                            "labels": []})
        created.append((iss["title"][:40], out.get("number"),
                        out.get("html_url")))
        print(f"created #{out.get('number')}: {iss['title'][:60]}")
    if created:
        lines = "\n".join(f"* #{n} — {t}" for t, n, u in created)
        body = MASTER_REPORT + "\n### Tickets filed this wave\n\n" + lines
        out = gh("issues/233/comments", {"body": body})
        print("wave report:", out.get("html_url"))


if __name__ == "__main__":
    main()
