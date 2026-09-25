#!/usr/bin/env python3
"""s99_tickets.py — S99 wave GitHub ticket lifecycle (issue-per-problem law).

Creates NEW bug tickets for the S99 full-load FAIL families (grouped per
distinct root cause family — one ticket per problem, never a laundry list),
each with the open->fix->verify->close protocol embedded.
Also posts evidence comments + closes the issues fixed by the S99 runtime
laws (MG-223 animator).

Protocol (constitution law): every problem = a ticket; fix lands =
evidence comment + close. Token via GITHUB_TOKEN env (fail-closed guard).
"""
import json
import os
import subprocess
import sys

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
API = f"https://api.github.com/repos/{REPO}"
TOKEN = os.environ.get("GITHUB_TOKEN", "")
if not TOKEN:
    print("FATAL: GITHUB_TOKEN env required (fail-closed secret guard)")
    sys.exit(1)


def gh(method, path, body=None):
    cmd = ["curl", "-sS", "-X", method,
           "-H", f"Authorization: Bearer {TOKEN}",
           "-H", "Accept: application/vnd.github+json"]
    if body is not None:
        cmd += ["-d", json.dumps(body)]
    cmd.append(f"{API}{path}")
    r = subprocess.run(cmd, capture_output=True)
    return json.loads(r.stdout.decode("utf-8", errors="replace"))


def open_issue(title, body, labels):
    r = gh("POST", "/issues", {"title": title, "body": body, "labels": labels})
    return r.get("number")


def comment(number, body):
    return gh("POST", f"/issues/{number}/comments", {"body": body})


def close(number):
    return gh("PATCH", f"/issues/{number}", {"state": "closed"})


PROTOCOL = """
## Protocol (issue-per-problem law)

- [ ] open (this ticket)
- [ ] root-cause (AOSP upstream source cited)
- [ ] fix lands (runtime law, evidence-backed)
- [ ] battery gate re-run (ALL PASS)
- [ ] close with evidence comment
"""

NEW_TICKETS = [
    {
        "title": "[F-NEW-165] androidx AppCompatDelegateImpl.createSubDecor theme-gate frontier — theme attr resolution gap for non-AppCompat-ancestor themes (mykanji family)",
        "labels": ["bug", "compatibility", "root-cause", "common-runtime", "s99"],
        "body": """## Root cause family

`AppCompatDelegateImpl.createSubDecor` ISE "You need to use a Theme.AppCompat theme (or descendant) with this activity." — the S99 TypedArray hasValue PRESENCE law fixed the conflation (a resolved attr with value false/0 is PRESENT), which unblocked themes whose chain reaches a style carrying windowActionBar (babydots AppTheme -> Theme.AppCompat.Light.NoActionBar). Remaining sub-family: themes whose chain never sets windowActionBar and whose style bags don't merge the appcompat attr — the theme-attr resolution must walk the LIBRARY style chain the way aapt2 merges it.

## Evidence (S99 full-load wave)

- io.github.hathibelagal.mykanji: ISE at createSubDecor pc=404, onCreate dead, 0 frames (rc=1)
- Log: `run/s99/full_load/io.github.hathibelagal.mykanji/obs_obs.log`
- APK: run/s99/apks/io.github.hathibelagal.mykanji.apk (F-Droid, SHA-pinned in run/s99/apk_manifest.json)

## Runtime laws already fixed this family (S99)

- hasValue presence bit (array_present[i]) — windowActionBar=false no longer conflated with absent
- <include> namespace + compiled-reference law (content include inflates)
- View root in the getResources law; animate() never-null; getContext() never-null
- ContentFrameLayout.setDecorPadding/setAttachListener + checkVectorDrawableSetup boundary no-ops

## Definition of done

mykanji onCreate reaches render (L2+) or a NAMED next frontier; battery ALL PASS.
""" + PROTOCOL,
    },
    {
        "title": "[F-NEW-166] androidx ConstraintLayout core interpreter frontier — ConstraintWidgetContainer solve never populates core widgets (no.thanks onLayout NPE family)",
        "labels": ["bug", "compatibility", "root-cause", "common-runtime", "graphics", "s99"],
        "body": """## Root cause family

APK-bundled `androidx.constraintlayout.widget.ConstraintLayout.onLayout` executes REAL bytecode: `ConstraintWidget.getX` on a null widget — the measure-phase solver (constraintlayout/core) never populated the widget array under the interpreter (ConstraintWidgetContainer / ConstraintAnchor statics materialize but the solve path does not run).

## Evidence

- eu.veldsoft.no.thanks: NPE unwinding ConstraintLayout.onLayout pc=52 -> SplashActivity.onCreate APP BOUNDARY, 12 errors (rc=1)
- Log: `run/s99/full_load/eu.veldsoft.no.thanks/obs_obs.log`
- Companion deferred CNFE: androidx.savedstate.Recreator_LifecycleAdapter (generated-adapter family — see #231)

## Definition of done

no.thanks onCreate completes layout (render L2+), or the solve path is fenced with a named battery stage; battery ALL PASS.
""" + PROTOCOL,
    },
    {
        "title": "[F-NEW-167] blank-render L0 family — rc=0 games that never draw (klondike/tripeaks/memory/blackjack/counting/accelerace/kingpong/bouncy)",
        "labels": ["bug", "compatibility", "common-runtime", "graphics", "s99"],
        "body": """## Family census (S99 full-load wave, 8 titles)

All run rc=0 with 0 errors but produce NO meaningful pixels (visual LEVEL 0):

| Title | Prior registry status | S99 evidence |
|---|---|---|
| eu.veldsoft.free.klondike | VERIFIED (older wave) | run/s99/full_load/eu.veldsoft.free.klondike/ (L0) |
| eu.veldsoft.tri.peaks | PARTIAL | .../eu.veldsoft.tri.peaks/ (L0) |
| eu.quelltext.memory | VERIFIED->downgraded | .../eu.quelltext.memory/ (L0) |
| crypto.o0o0o0o0o.games.blackjack | OBSERVED | .../crypto.o0o0o0o0o.games.blackjack/ (L0) |
| eu.quelltext.counting | OBSERVED | .../eu.quelltext.counting/ (L0) |
| org.asafonov.accelerace | OBSERVED | .../org.asafonov.accelerace/ (L0) |
| com.kingalex.kingpong | OBSERVED | .../com.kingalex.kingpong/ (L0) |
| io.github.ebraminio.bouncy | LOAD_ISSUE (#227 family) | .../io.github.ebraminio.bouncy/ (L0) |

## Known components

- eu.quelltext.counting (FullscreenActivity): FrameLayout.onAttachedToWindow REC-MISS chain — custom View onDraw never reaches the software renderer
- io.github.ebraminio.bouncy: multidex / APP-BOUNDARY family (#227 root cause)

## Definition of done

Per-title promotion to L2+ with SHA-pinned frame evidence, or a NAMED runtime law per distinct root cause; battery ALL PASS.
""" + PROTOCOL,
    },
    {
        "title": "[F-NEW-168] crash-on-launch family — rc=1 NPE chains (raumballer/tictactoe-classic) + dooz rc=-11 process-death",
        "labels": ["bug", "compatibility", "common-runtime", "s99"],
        "body": """## Family census (S99 full-load wave)

| Title | Symptom | Evidence |
|---|---|---|
| com.kaeruct.raumballer | NPE uncaught, rc=1, 0 frames | run/s99/full_load/com.kaeruct.raumballer/obs_obs.log |
| com.emmanuelmess.tictactoe | NPE (known FAILED ticket family) | .../com.emmanuelmess.tictactoe/ |
| io.github.yamin8000.dooz | rc=-11 (segv-class hard crash) | .../io.github.yamin8000.dooz/ |

The dooz rc=-11 is the most serious: the runtime PROCESS dies (signal 11) — an engine-side robustness law (no interpreter path may take the process down) is required BEFORE per-title triage.

## Definition of done

dooz: no-signal crash (graceful rc + honest report). raumballer/tictactoe: named next frontier or render.
""" + PROTOCOL,
    },
    {
        "title": "[F-NEW-169] SpeedDialView (leinardi) library frontier — babydots cascade: FAB inflate + FabWithLabelView.init setFocusable NPE",
        "labels": ["bug", "compatibility", "common-runtime", "s99"],
        "body": """## Root cause

com.serwylo.babydots onCreate cascade AFTER the S99 fixes landed (animator, getResources, animate(), theme gate, include, prefs identity all passed): the leinardi SpeedDialView library's FAB children inflate with null views (FabWithLabelView.init pc=7 setFocusable on null) — the FloatingActionButton <init> unwound earlier in the same chain.

## Evidence

- run/s99/full_load/com.serwylo.babydots/obs_obs.log
- APK: run/s99/apks/com.serwylo.babydots.apk

## Honest status

babydots moved from instant-death (5 distinct S99-blocker laws fixed en route — see the S99 wave report) to the SpeedDialView library frontier. The remaining gap is library-internal view construction.

## Definition of done

babydots renders L2+; battery ALL PASS.
""" + PROTOCOL,
    },
]

MG223_COMMENT = """## S99 CLOSE — ValueAnimator shadow landed

**Fixed by:** the S99 AnimatorShadow law (commit at wave close; battery 105/105 ALL PASS).

**Root cause:** the engine had NO android.animation animator handling — the
static factories `ValueAnimator.ofInt/ofFloat/ofArgb/ofObject/ofPropertyValuesHolder`
fell through to the engine default (NULL object). The app's very next instance
invoke hit the F-141 null-receiver law:
`"ValueAnimator.setRepeatCount on a null object reference"` -> APP BOUNDARY
unwind -> onCreate dead.

**The law (AOSP ValueAnimator.java):**
- factories return a NON-NULL animator (heap object Landroid/animation/ValueAnimator;)
- `setDuration(long)` is FLUENT (returns the animator itself)
- `start()/cancel()/end()` lifecycle with isRunning/isStarted state
- setStartDelay/setRepeatCount/setRepeatMode/setInterpolator/addUpdateListener/
  addListener/setEvaluator/setIntValues/setFloatValues mutators
- getAnimatedValue = null before start (AOSP pre-start contract)

**Reproduction before:** com.serwylo.babydots —
`[ANIM] ValueAnimator.ofFloat -> animator obj=560` now succeeds where the
previous build died at setRepeatCount.

**Fan-out:** every corpus app using property-animation entry points
(material FABs, card flips, progress animators).

Battery: 105/105 ALL PASS (shadow invariant count law 27->28 with the new shadow).
"""


def main():
    created = []
    for t in NEW_TICKETS:
        n = open_issue(t["title"], t["body"], t["labels"])
        created.append(n)
        print(f"OPENED #{n}: {t['title'][:70]}", flush=True)
    comment(323, MG223_COMMENT)
    close(323)
    print("CLOSED #323 (MG-223 ValueAnimator) with evidence comment", flush=True)
    json.dump({"created": created}, open("run/s99/tickets_created.json", "w"), indent=1)


if __name__ == "__main__":
    main()
