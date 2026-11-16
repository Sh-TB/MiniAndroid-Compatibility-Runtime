#!/usr/bin/env python3
"""Post the APP-LOAD VERIFICATION receipt on #606 + open the new issue
for the late-launch starvation family."""
import json, subprocess, urllib.request

CRED = subprocess.run(["git", "credential", "fill"],
                      input="protocol=https\nhost=github.com\n\n",
                      capture_output=True, text=True,
                      cwd="/home/z/my-project/miniandroid").stdout
TOKEN = [l.split("=", 1)[1] for l in CRED.splitlines() if l.startswith("password=")][0]
H = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github+json",
     "User-Agent": "layout-audit"}
BASE = "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime"

VERIFY = """## #606 SUPPLEMENT — REAL APP-LOAD VERIFICATION BATTERY (18 canonical APKs, 0 crashes)

The "do the apps actually load" question, answered with evidence. Battery: every APK in `upload/canonical_apks/` through `run <apk> --max-seconds 60`, host 2-CPU/3.9GiB, base commit 11597cd2 (the #606 FINAL solver wave). **Result: 5/18 full SUCCESS with real rendered UI, 13/18 honest PARTIAL, 0 crashes/SIGSEGV anywhere.**

### ✅ Apps that genuinely load and render (screenshots verified visually)
- **de.duenndns.gmdice_8** — dice dialog (8 items) + 1d6/1d20 button bar rendered as the real app screen.
- **com.darkempire78.opencalculator_53** — full calculator keypad (√ π ∧ ! AC ÷ × − + = ⌫) with real colors/layout.
- **app.varlorg.unote_30**, **dubrowgn.microtimer_8**, **opmt_v0.1.2** — SUCCESS, rendered content, errors=0.

### ⚠️ The 13 PARTIALs decomposed (each verified to root cause)
1. **Activity-less app (1: com.github.muellerma.stopwatch_6)** — a RAW AXML walk of its manifest proves **ZERO `<activity>` elements** (service/receiver/provider only — a QuickSettings Tile app). There is nothing to launch; the blank screen is the CORRECT graceful degradation, no crash.
2. **ARM-only native-engine games (11: gomoku, tictactoe/libgdx, rttt/SDL, freebloks, fishrings, tripeaks, dooz×2, stack.tower3d, bouncy×2)** — the Java side launches (LAUNCH-STORE + onCreate dispatched in the logs) but the APKs ship only armeabi-v7a/arm64-v8a `.so` files; the x86_64 host refuses them ("wrong ELF class"). The dlopen refusal is honest — that native code physically cannot run here.
3. **REAL ENGINE BUG — late-launch starvation (1: org.secuso.privacyfriendlymemory_100)** — a pure-Java app that SHOULD render. SplashActivity launches and onPause fires, but the next activity's onCreate + setContentView (MainMenu — 13 views with NavigationView/DrawerLayout inflate successfully! root_id=560) lands **AFTER the render_frame and capture_output stages**: log line 1474 `BOOT-ORDER 7/7 capture_output ok=1` → line 2922 `U007-INFLATE root_id=560 views=13`. The frame composes with `ECR-ROOT scan root=0 candidates=0 cur_act=20` — blank. Filed separately with the full evidence trace (below).

Verdict: the loader itself is healthy (18/18 boot → inflate → frame → screenshot, zero crashes); the remaining honest gap is issue #613 (late-launch starvation) plus the ABI boundary that is not a loader defect. Full report: `app_load_verification_report.md` (workspace download)."""

NEW_ISSUE = {"title": "LATE-LAUNCH STARVATION — next-activity onCreate/setContentView lands after render_frame+capture (blank frame despite successful inflate)",
    "body": """## Evidence wave: the 18-canonical-APK app-load battery (#606 supplement, commit 11597cd2)

**Repro:** `build/miniandroid run upload/canonical_apks/org.secuso.privacyfriendlymemory_100.apk -o /tmp/secuso --max-seconds 60` (host: 2 CPU / 3.9 GiB, gcc 14.2)

**Symptom:** pure-Java app, SplashScreen → MainMenu. The frame renders BLANK (uniform background) although inflation succeeds: `[U007-INFLATE] root_id=560 views=13 strings=2 ids=0 unresolved=0` (MainMenu layout with material NavigationView/DrawerLayout).

**Root trace (log line numbers from the battery run):**
1. L871/872 — `U0113-ACTIVITY #20 SplashActivity recorded` + `[C94-SINGLETON] LAUNCH-STORE key='Lorg/secuso/privacyfriendlymemory/ui/SplashActivity;' id=20` — execute stage (5/7).
2. L1250-1256 — onCreate dispatched through the AppCompat chain (still inside 5/7, ms=1700).
3. L1470/1474 — `BOOT-ORDER 6/7 render_frame ok=1 ms=48` → `7/7 capture_output ok=1` — **frames captured here**.
4. L1478 — `[ECR-ROOT] scan root=0 candidates=0 cur_act=20` — the render-time root discovery finds no content (correct: nothing was set yet).
5. L1479-1480 — `[FRAGMENT-LIFECYCLE] method=onPause` on SplashActivity + `[G08-LIFECYCLE] dispatched:true` — the splash advances AFTER capture.
6. L1481-2922 — the NEXT activity's full <init>+onCreate chain (receiver=259) executes, and L2922/2923 records `[U007-INFLATE] root_id=560 views=13` + `[P0-1-ORDER] setContentView(res) root=560 recorded` — **after the pipeline already rendered and captured**.

**Law gap:** the boot pipeline composes frames at looper quiescence (tick=0, empty queue — `[F100-STATE] quiescence`), but the activity-to-activity advance (splash finish → startActivity → onCreate of the next activity) is not part of the drained/pumped work before render. AOSP renders the NEXT activity's first frame only after its onCreate/onResume traversal completes; here the pipeline's frame budget elapses during the FIRST activity's window and the successor's content never gets a frame.

**Expected direction (AOSP ActivityThread law):** between execute_application and render_frame the engine should drive the lifecycle pump until EITHER a content root exists for the current activity (`effective_content_root_()` non-zero) OR an honest no-content verdict is recorded — bounded (virtual-clock budget), never wall-clock sleeps. Contrast working app (gmdice): `[P0-1-ORDER] setContentView root=41 recorded` at log line 79 — long before render — because its launcher's onCreate calls setContentView synchronously inside the execute stage.

**Scope:** affects at least org.secuso.privacyfriendlymemory_100; the other blank PARTIALs in the battery are the honest ARM-only-ABI class (separate, not this bug). Fix should be pinned by a battery law: inflate-after-capture must be impossible — e.g. a law test asserting `ECR-ROOT` never runs with `cur_act!=0 && root==0` while a recorded pending attach exists."""}

req = urllib.request.Request(BASE + "/issues/606/comments",
    data=json.dumps({"body": VERIFY}).encode(), headers=H, method="POST")
with urllib.request.urlopen(req, timeout=30) as r:
    print("606 receipt:", json.loads(r.read().decode())["id"])

req2 = urllib.request.Request(BASE + "/issues",
    data=json.dumps(NEW_ISSUE).encode(), headers=H, method="POST")
with urllib.request.urlopen(req2, timeout=30) as r:
    print("new issue:", json.loads(r.read().decode())["number"])
