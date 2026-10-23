#!/usr/bin/env python3
"""cont11_issue.py — create the SEPARATE WORK TASK issue: recurring
cross-app loading blockers (the user directive: problems repeated across
several apps/games must be registered as their own task and executed)."""
import json
import subprocess


def token():
    out = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        capture_output=True, text=True).stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("no github credential")


REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"

TITLE = "CONT-11 RECURRING TASK: cross-app loading-screen blockers — register, root-cause, fix, re-census"

BODY = """## The task (directive)

Problems that repeat across SEVERAL apps and games are registered here as ONE separate work task: root-cause the recurring root, fix it GENERICALLY (no app-specific code), re-census the whole pool, and repeat until titles at least reach the loading screen.

## Method

`scripts/cont11_loading_census.py` — install every pooled APK (121 titles: fdroid_batch + cont73/50/54/11 + canonical) into a FRESH per-APK store, run a bounded launch window, extract the honest final-uncaught signature (last `EXC-PROPAGATE … uncaught at caller` + the `SYNTH-EXC` before it + verdict), then group by the recurring API anchor inside the exception message. Cluster: `scripts/cont11_cluster2.py` / `cont11_reparse.py`.

## Fresh census (121 titles) — recurring families

| family (final uncaught anchor) | titles | state |
|---|---|---|
| `NPE Object.getClass` (16) | peri, uturn, wocheneinkauf, matewave, goodtime, aurora, awagam, lumolight, webstack, k9, notepad, readrops, audiobook, netguard, andstatus2048, composeStopwatch | **3 roots closed this wave (F-NEW-272/273/274)** — survivors advanced to their next face (F-NEW-275) |
| IAE `Unknown authority: org.fossify.android.provider` (7) | fossify calendar/clock/math/messages/musicplayer/notes/phone | **F-NEW-276 registered** (coroutine-boundary unwind) |
| `NPE List.size` (5) | bouncy ×2, dmfs tasks, surgeengine, +1 | **F-NEW-277 registered** |
| `NPE Function1.invoke` (4) | peri, uturn, sparkledns, connectbot (compose 1.7 Lookahead) | **ROOT-CAUSED-FIXED (F-NEW-272)** |
| `NPE Thread$UEH.uncaughtException` (3) | floatdeck, sparkledns, +1 | **ROOT-CAUSED-FIXED (F-NEW-273)** |
| `NPE WindowMetrics.getBounds` (2+) | lumolight, librecontactsbackup | **ROOT-CAUSED-FIXED (F-NEW-274)** |
| `NPE ViewDragHelper.continueSettling` (2) | drawer-layout titles | F-NEW-277 backlog |
| libGDX `AndroidInput.onResume` (2) | surge-family | F-NEW-277 backlog (kin of F-NEW-157 EGL) |
| CNF/NSM singles + verdict=NO_ROOT (7) | guandan, tictactoe, lrceditor, … | F-NEW-277 backlog |

## Roots closed this wave (all generic, probe-first)

| ROOT | FILE | FIRST DIVERGENCE | ROOT CAUSE | GENERIC FIX | PROBE |
|---|---|---|---|---|---|
| F-NEW-272 | dalvik_engine.cpp (execute_invoke_interface) | compose Lookahead `placeChildren` NPE `Function1.invoke` on null (`$placementBlock` UNSET — FIELD-TRACE obj#2258 proof) | runtime-first interface dispatch answered a same-name **different-descriptor** method via the lenient arity path → 4-arg call site ran the 5-arg body with a truncated window (the interface's 4-arg DEFAULT with code was never consulted) | `runtime_chain_has_exact_descriptor()` gate — runtime-first only answers exact (name,proto); falls through to declared-interface / F-023 default / F-091b signature walks (ART order) | cont11_probe F272-A/A-block/B PASS |
| F-NEW-273 | android_shadows.cpp (ThreadShadow) + bridge_to_api | kotlinx fallback `Lv1;.x` NPE `uncaughtException on a null` | instance `getUncaughtExceptionHandler` was a handled_void no-op; statics REC-MISS unbridged; AOSP RuntimeInit installs KillApplicationHandler at boot → the getter NEVER answers null on a live process | per-thread map + lazy-minted engine default (stable identity) + static storage law + chained `uncaughtException` accepted honestly | cont11_probe F273-A1..A5/B PASS |
| F-NEW-274 | dalvik_engine.cpp (bridge_to_api) | `WindowMetrics.getBounds on a null object reference` | `getCurrentWindowMetrics`/`getMaximumWindowMetrics` unbridged (WindowManagerImpl fields are final upstream — never null); `getBounds()` returns a fresh Rect copy | WindowMetrics singleton + fresh Rect(0,0,1080,1920) per call (device-profile law) | cont11_probe F274-A/B PASS |

## Census effect (before → after, same binary lineage, zero regressions)

- **APP-BOUNDARY crash GONE (3):** ac.stresa.uturn (Lookahead face) → DEFAULT_BACKGROUND_ONLY; app.floatdeck (UEH face) → DEFAULT_BACKGROUND_ONLY; com.ashkanrafiee.librecontactsbackup (WindowMetrics face) → **Status SUCCESS** (fb 1,714,113 non-white px).
- **Advanced to next face (4+):** peri/notepad/netguard past Lookahead+WindowMetrics → the WindowInsetsCompat/LocalView face (F-NEW-275); lumolight past WindowMetrics → its next null-producer.
- **NEW CRASHES: 0.**

## Regression battery at the fixed binary

- anchors 5/5 ×3 **byte-identical** vs recorded lineage (opencalc a976d2f9*, chess b5a7a35d, dooz d602648e, microtimer da73010a, unote 4f1a9e4e) — *opencalc keeps the W6 recorded changed-anchor (REAL_APP_CONTENT retained)*
- negatives **19/19** PASS (gate A probe rebuilt edaf60fc, probe results 99 rows)
- reinstall-identity **5/5** PASS (source SHA == installed SHA == pkgaudit live hash)
- cont11 probe **12/12** PASS (real aapt2/ECJ/D8 fixture)

## Next faces (this task stays OPEN)

1. **F-NEW-275** — WindowInsetsCompat/LocalView compose-locals chain (the remaining `Object.getClass` cluster: notepad, peri, netguard, sparkledns, connectbot, …).
2. **F-NEW-276** — Fossify 7-title family: exception unwind across collapsed coroutine frames must consult the logical chain's deferred handlers (kin of F-NEW-217).
3. **F-NEW-277** — List.size-on-null family + ViewDragHelper + libGDX + NSM singles backlog.

Every fix here is generic platform law (no app-specific or R8-specific code anywhere); evidence: `run/cont11_census/`, `fixtures/cont11_probe/`, `scripts/cont11_*.py`, registry F-NEW-272..277.
"""

tok = token()
r = subprocess.run(
    ["curl", "-s", "-X", "POST",
     f"https://api.github.com/repos/{REPO}/issues",
     "-H", f"Authorization: token {tok}",
     "-H", "Accept: application/vnd.github+json",
     "-d", json.dumps({"title": TITLE, "body": BODY})],
    capture_output=True, text=True)
resp = json.loads(r.stdout)
print("issue #", resp.get("number"), resp.get("html_url", resp.get("message")))
