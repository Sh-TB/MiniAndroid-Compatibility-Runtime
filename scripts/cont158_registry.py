#!/usr/bin/env python3
"""cont158_registry.py — CONT-158 registry append: F-NEW-497/498/499.
Both mirrors (root_registry.json + canonical/root_cause_registry.json)
must stay id-unique and equal (main==mirror law)."""
import json, sys

MAIN = 'root_registry.json'
MIRROR = 'canonical/root_cause_registry.json'

def load(p):
    with open(p) as f: return json.load(f)

def save(p, roots):
    with open(p, 'w') as f: json.dump(roots, f, ensure_ascii=False, indent=1)

NEW = [
 {
  "id": "F-NEW-497",
  "title": "F-NEW-497 — post-capture drain-to-deadline (AOSP MessageQueue.next poll-timeout parity for the END of the capture window) — ROOT-CAUSED-FIXED: the canonical frame pass reaches only N×300ms of Looper life; every app whose first real transition is a future-dated Timer/Handler delay (fishrings/tripeaks 5000ms splash Timer, klondike 5000ms splash→MenuActivity) never left its launch screen — capture pinned the app at ~1500ms of app life while the harness already promises --max-seconds of app-life window",
  "status": "ROOT-CAUSED-FIXED",
  "priority": "P1",
  "layer": "framework-handler",
  "evidence": {
   "decode": "[QUEUE] fishrings+tripeaks: Runnable id=27 enqueued (delay=5000ms, ready_at=5000ms virtual, source=Timer.schedule) — frames 1-4 runnables_fired=0 (5×300ms=1500ms virtual << 5000ms); [F100-STATE] DEFERRED-UI-PENDING (earliest ready_at=5000ms); F-117 comment itself documented 'FreeKlondike's MenuActivity only exists after the 5s splash Timer'. APK law check: fishrings/tripeaks have NO assets/ dir at all (unzip -l) — the splash WebView banner.html 404 is artifact-faithful; the REAL transition is the Timer→startActivity, not the banner.",
   "fix": "execution_engine.cpp stage_frame_sequence: after the frame loop, while queue holds future-dated work and virtual_now < max_wall_seconds×1000: poll-timeout advance to next_ready, drain due runnables, dispatch via invoke_handler_runnable (same path as per-frame law), one compose pump per boundary (F-050), consume_pending_intent()+consume_finish_cascade() at EVERY round boundary (the launch intent may pend while the queue is already empty — without it the GameActivity cascade strands until the G07 final boundary, AFTER the end-of-window screenshot); one final render + frame_497_drain.png manifest entry. Deterministic (deadline read from the DECLARED budget, applied to the ONE virtual clock; zero wall-clock input), uniform (no app checks), launch-frame contract untouched (pass runs AFTER the last rendered frame; GATE H/G07 goldens frozen). Bounds = §18 storm law: 512 rounds absolute, 64 consecutive no-progress rounds.",
   "run": "run/c158/fixtest/fr5.log — [F497-DRAIN] 0 runnable(s) fired, 1 activity launch(es), virtual_now=5000ms; G08-LAUNCH Leu/veldsoft/fish/rings/GameActivity; fishrings face b5a7a35d(1 color uniform splash)→a341e3ad(100% non-white, 3310 distinct colors — the Rings game board); tripeaks b5a7a35d→e2a290ab (130 colors; visible_texts: 'Welcome to the Tri Peaks Solitaire for Android!' + New Game/About Us/Help/Exit buttons); klondike 31ddd4d5→a77038da (136 colors; MenuActivity: New Game/View Help/About Game/Check for Updates/Exit)",
   "honest-frontier": "tictactoe unchanged (b5a7a35d — libGDX GL boundary F-NEW-498); dooz/dooz_top at the 31ddd4d5 draw-op boundary (F084 throughput wall, F-NEW-481 cohort — unchanged); chess a0319686 uniform grey-254 (Resources$NotFoundException 0xFFFFFFFF XML chain — decode pending); tower3d 11a38a5a uniform black (decode pending). Wall: 9/9 anchors — 8 MATCH (incl. unote at its true CONT-155+ anchor 7481e9b4; the 90a67cc1 c129-era list entry was stale) + klondike JUSTIFIED RE-BASE 31ddd4d5→a77038da (REAL_APP_CONTENT advance: the app's own menu, category = CONT-157 dooz/telegram re-bases); negatives 19/19 (probe_store session-state re-run per CONT-156 law — the initial 9/19 was missing session state from the stale-snapshot reset, NOT a fix regression); selftest 13/13. memory face 807a0cca→6da289aa = app-initiated MainActivity relaunch (same menu texts, bg 28→48 grey) → F-NEW-499."
  }
 },
 {
  "id": "F-NEW-498",
  "title": "F-NEW-498 — tictactoe libGDX GL/native boundary (CLASSIFIED, not engine-fixed): GATEA-NATIVE libgdx.so extracted (260696B, sha16 553c8769776ff741) but real dlopen faulted (SIGSEGV/SIGBUS inside the loader, post-probe residual); GdxNativesLoader catches the GdxRuntimeException; then AndroidGraphics.preserveEGLContextOnPause NPEs on null Gdx.app (interface Application.log on null receiver) → APP BOUNDARY unwind at AndroidLauncher.onCreate; face stays b5a7a35d (uniform grey-48, RelativeLayout children=0)",
  "status": "CLASSIFIED",
  "priority": "P2",
  "layer": "native-bridge",
  "evidence": {
   "decode": "run/c158/battery/tictactoe.log — [SYNTH-EXC] GATEA-NATIVE (deferred) UnsatisfiedLinkError 'gdx' dlopen faulted; [EXC-PROPAGATE] GdxRuntimeException caught at GdxNativesLoader.load; [SYNTH-EXC] F-NEW-219 NSME GLSurfaceView20.setPreserveEGLContextOnPause (deferred, handled); f141-null-recv NPE ×2 (Application.log, AndroidInput.onResume on null) → uncaught at AndroidLauncher.onCreate invoke_pc=26/37.",
   "fix": "none — honest boundary row. Named levers: (a) the dlopen SIGSEGV inside the loader for a REAL extracted x86_64 libgdx.so (UPP-001 family — the loader probe law); (b) libGDX GLSurfaceView/EGL shadow family (the GL boundary behind F-NEW-219's NSME). Both app-generic but each a multi-train program; registered as the tictactoe frontier.",
   "run": "run/c158/battery/tictactoe.log (CONT-158 battery, binary b7b193b5+)",
   "honest-frontier": "rc=1 with 4 deferred exc; face b5a7a35d shared with fishrings/tripeaks pre-fix (those two CROSSED via F-NEW-497; tictactoe's b5a7a35d is the RelativeLayout-uniform-grey face — the two faces share the sha because the splash WebView and the empty RelativeLayout both paint the same uniform grey)."
  }
 },
 {
  "id": "F-NEW-499",
  "title": "F-NEW-499 — activity-RELAUNCH theme rebind gap (CLASSIFIED): secuso memory's own restart flow startActivity(MainActivity) inside the F-NEW-497 drain re-created the activity (B view root 512) but the relaunch renders the default grey-48 window background instead of the app theme's grey-28 — same menu content (texts identical), face hash changed 807a0cca→6da289aa",
  "status": "CLASSIFIED",
  "priority": "P3",
  "layer": "framework-activity",
  "evidence": {
   "decode": "run/c158/battery/memory.log — G08-LAUNCH Lorg/secuso/privacyfriendlymemory/ui/MainActivity; (stack depth 1, B view root 512); frame_497_drain texts == frame_004 texts (Easy/New Game); distinct colors 74→86; top color (40,40,40)-family→48-grey 99.5%.",
   "fix": "none yet — named lever: the relaunch path must re-apply the launch-theme binding (F-NEW-484 setTheme law) for B-view-root activity #2+; the launch theme IS bound for activity 1 (S124 law) — the second dispatch skips it.",
   "run": "run/c158/battery/memory (CONT-158 battery)",
   "honest-frontier": "content preserved (no regression — same visible_texts); cosmetic theme delta on relaunch only."
  }
 }
]

for path in (MAIN, MIRROR):
    roots = load(path)
    ids = {r['id'] for r in roots}
    for n in NEW:
        assert n['id'] not in ids, f"{n['id']} already in {path}"
        roots.append(n)
    save(path, roots)
    print(f"{path}: {len(roots)} roots")

# id-unique + main==mirror verification
a, b = load(MAIN), load(MIRROR)
ia = [r['id'] for r in a]; ib = [r['id'] for r in b]
assert len(ia) == len(set(ia)), "main not id-unique"
assert len(ib) == len(set(ib)), "mirror not id-unique"
assert a == b, "main != mirror"
print("id-unique OK; main==mirror OK; total:", len(a))
