# REAL APK IMPACT (S104)

Mechanical before/after rows for every runtime change this wave. All runs:
`run --execution-mode real-dalvik --frames 8 --frame-delay 300 --max-seconds 240`,
screenshot metrics from the repo visual auditor, battery = the 105-stage gate.

## FIX-005 — SWITCH-KEY-WIDENING (commit 4feaaeda)

Root R-009: packed/sparse-switch key must widen BYTE/CHAR/SHORT (R8 merged-class
classId dispatch ran the wrong branch).

### com.vayunmathur.games.solitaire (real APK, SHA e87536851b7e9edc…)

```text
APK impact:
before (S103 HEAD) = 12 errors, crash family: MatcherMatchResult.
                    getSavedStateProvider NPE (ComponentActivity.<init>)
                    -> process death at saved-state wiring
after  (S104)      =  0 errors, 3/3 runs, screenshot SHA 59fdbfcd60b86a23
                    identical across runs
improved           = 12 -> 0 census error rows; first divergence moved past
                    the entire saved-state wiring into the compose draw path
                    (LocalSavedStateRegistryOwnerKt clinit executes; chain
                    reaches AndroidComposeView.updatePositionCacheAndDispatch)
```

Runtime-trace proof (env-gated probes, committed):
- pre-fix `[S104-SW] key=0 target=3 dest=5` (wrong branch — BYTE register collapsed)
- post-fix `[S104-SW] key=5 target=9 dest=11` + `key=4 target=3 dest=5` (both correct)
- pre-fix `[NULLFIELD] MatcherMatchResult->input UNSET (iput never ran)`; absent post-fix

### name.boyle.chris.sgtpuzzles (2nd `$r8$classId` APK)

```text
before = 0 errors (fast clean load, blank visual — pre-existing state)
after  = 0 errors, unchanged
regression = none
```

### Regression battery

```text
battery: 105/105 ALL PASS (re-run twice this wave: after FIX-005, after R-004)
```

## R-004 — CLASS-IDENTITY real-descriptor inflation (this wave)

Pixel-identical BEFORE/AFTER on all measured affected titles (the law is
render-neutral by design; identity semantics only):

```text
title                        errors before/after   colors   nonbg   text   widget
de.georgsieber.ballbreak     0 / 0                 13/13    404/404 0/0    64/64
io.github.hathibelagal.myk.  27 / 27               35/35    14668   5504   5952
crypto.o0o0o0o0o.blackjack   0 / 0                 1/1      0/0     0/0    0/0
com.sanskritbasics.memory    28 / 28               2/2      23520   0/0    192/192
com.willie.mancala           32 / 32               2/2      23520   0/0    192/192
jwtc.android.chess           7 / 7                 2/2      23520   0/0    192/192
```

Measured static fan-out (corrected — bytecode-accurate scan, operand tuple
carries the type string): **60/201 APKs** bundle AND statically type-test
(instance-of/check-cast) the androidx/material family; census subset = the
S103 22/59 claim (presence was misread as type-testing; both now on file).

## io.github.yamin8000.dooz (lambda-family close-out attempt, FIX-005)

```text
errors: 18 -> 18 (different mix)
before family: Handler.postAtFrontOfQueue NPE (census row)
after:  12 caught CNFE probes (app-expected runCatching/reflection),
        old PFQ crash GONE at the original site;
        NEW uncaught site: Lr;.onAttachedToWindow pc=50
        Handler.postAtFrontOfQueue null-recv (compose host wiring)
```

The switch law is fixed (probe-proven); the lambda-specific ticket stays
PARTIAL because the family's next divergence (compose
onAttachedToWindow Handler null) is a separate root, now queued as the
highest-value NEXT ROOT.

## Corpus census distribution

```text
61-title distribution: unchanged this wave (14 INTERACTIVE-EVIDENCE /
2 RENDERED-L2+ / 38 PARTIAL / 7 FAIL) — identity/switch fixes were
error-path and identity-path changes; zero census regressions.
```

## GL demand (GL_NEED_LEDGER, measured)

```text
GLES20/30 method refs corpus-wide: 0
EGL10 setup-only demand: 6/54 APKs (libGDX family renders via native
libgdx.so, not Java GLES) -> GL bridge stays demand-gated (demand = 0)
```
