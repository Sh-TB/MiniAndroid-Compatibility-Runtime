# S115 Telegram — ROOT-062 + ROOT-063 wave (forkgram Classic 12.10.8.0, vc 709208, SHA 3baeecb3)

Per the roadmap: fresh runs at the current HEAD, capture the exact frontier, fix the first
generic divergence, rerun. Zero package checks in every fix.

## Run progression (same APK, same HEAD lineage)

| run | HEAD state | in-flight uncaught | recorded errors | notes |
|---|---|---|---|---|
| run2 (pre-fix) | S115 base | 4 | 0 | frontier captured |
| run3 | + ROOT-062 | 3 | 0 | Recreator assert GONE (2 → 0); created-phase fan-out live |
| run4 | + ROOT-063 | **0** | **0** | **first fully clean forkgram execution (rc=0, 0 warnings)** |

## ROOT-062 — AOSP CREATED-PHASE LIFECYCLE FAN-OUT (generic)

**Failure:** `androidx.savedstate.Recreator.d` threw `AssertionError("Next event must be ON_CREATE")`
uncaught at `LaunchActivity.onCreate` → APP BOUNDARY unwind → login tree never built.

**Trace:** engine F-058 fan-out fired ONLY started/resumed pairs
(onActivityStarted/PostStarted/Resumed/PostResumed ×2) — the CREATED phase
(onActivityPreCreated/onActivityCreated/onActivityPostCreated) never fired in the path that
dispatched onCreate for forkgram (the multi-DEX direct-dispatch site), so the androidx
LifecycleRegistry never gave the Recreator its first (ON_CREATE) event.

**DEX ground truth (this APK):** Recreator.d = `if (event == ON_CREATE) { lifecycle.removeObserver(this); restoreState(); } else throw new AssertionError("Next event must be ON_CREATE")` — verified via the calibrated dalvik walker (const-string@0x7a1a law, 842/844 exact-decode calibration on MessagesStorage).

**Fix:** fire the created-phase pairing around onCreate at the direct-dispatch site
(`miniandroid/src/dex/dalvik_engine.cpp`, mirrors the manifest-class block). Generic — no
package checks. Same family as the 4 sweep tickets (#86 #98-class "Next event must be ON_CREATE").

## ROOT-063 — StaticLayout$Builder / StaticLayout (generic)

**Failure:** `StaticLayout.Builder.setMaxLines` on null — `obtain()` answered REC-MISS null
(TextLayout build in `org/telegram/ui/Components/id$a`).

**Fix:** real Builder materialization: `obtain` never-null with AOSP defaults, fluent
this-returning setters (setText/Alignment/LineSpacing/IncludePad/Ellipsize/MaxLines/
BreakStrategy/HyphenationFrequency/Indents), `build()` → StaticLayout with deterministic
measurement metrics (greedy-wrap estimate from the paint's text size; the render path keeps
using the engine's own G36/G47 TextShaper line boxes). Measurement getters: getHeight/
getLineCount/getWidth/getText/getLineTop|Bottom|Baseline|Ascent|Descent/getLineWidth/
getLineStart|End/getLineForOffset/getEllipsis*.

## Honest status (§21 labels)

- forkgram execution: **EXECUTED, VERIFIED 0-error** (deepest ever: StartMessaging button text
  resolved and set on the login view; created-phase lifecycle law complete)
- forkgram pixels: **NOT RENDERED YET** — the login tree is measured but not painting
  (R$styleable theme attrs + text-draw laws = the known pixel frontier, unchanged)

## Next frontier

1. Login tree paint: R$styleable/TypedArray theme resolution → text draw → framebuffer
2. The empty-SQL SQLiteCursor family (String law under the private JNI bridge — run2 evidence)
3. Re-sweep the 77 after the shared-family fixes
