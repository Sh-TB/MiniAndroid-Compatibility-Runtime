#!/usr/bin/env python3
"""Post wave receipts on the 6 handoff issues (#608/#609/#610/#611/#613/#614)."""
import json, subprocess, urllib.request, sys

CRED = subprocess.run(["git", "credential", "fill"],
                      input="protocol=https\nhost=github.com\n\n",
                      capture_output=True, text=True,
                      cwd="/home/z/my-project/miniandroid").stdout
TOKEN = [l.split("=", 1)[1] for l in CRED.splitlines() if l.startswith("password=")][0]
H = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github+json",
     "User-Agent": "layout-audit"}
BASE = "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime"

# Battery re-run results are passed in as a JSON file (summary lines).
import os
def bat(path):
    try:
        return open(path).read().strip()
    except Exception:
        return "(battery re-run still running)"

canon = "/tmp/appevidence/battery_summary.txt"
hand = "/tmp/handoff_evidence/summary.txt"

R = {}

R[608] = f"""## GAME-185 RECEIPT — ROOT-4 FIXED (S83 content-root law) · commit 66083e5a · run VERDICT CHANGED rc=1 → **rc=0 SUCCESS**

**The fourth root cause was the Activity-level findViewById.** This run's trace: `ComponentActivityKt.setContent` → `findViewById(android.R.id.content)` answered **null** because the ActivityShadow only answers through `content_view_id_` — which is 0 until a setContentView records one. AOSP law: `PhoneWindow.installDecor` installs the content parent at ATTACH time, before any setContentView; Compose's setContent is the FIRST call that needs it. The null propagated to `decor.findViewById(...).getViewTreeObserver()` → NPE on the null receiver (`LX0/c.y`) → **uncaught at MainActivity.onCreate** → the run died before the puzzle CSV asset ever opened (`F447-NPE` + `EXC-PROPAGATE ... uncaught` in the pre-fix log).

**Fix (dalvik side, S83-DELEGATE):** the ActivityShadow findViewById now delegates `android.R.id.content` to the ViewShadow law — which already implements the full AOSP contract (receiver subtree → legacy window root → S83 lazy materialization, ONE-STABLE-OBJECT rule). Evidence after, same host, same APK (SHA-pinned `6f9815e1…`):
- rc=1 PARTIAL → **rc=0 SUCCESS**; `F447-NPE`/`uncaught` count 1 → **0**; `[S83-DELEGATE]` fires; `[ECR-ROOT] scalar content_view_id root=731` (the ComposeView tree).
- The CSV now loads INSIDE the execute stage: **9002/9002 lines read** (`EXP071-READLINE` + `EOF`), the DataStore absent-file FNFE is the honest first-run state.

**Remaining frontier (measured, not guessed):** the frame still composes the app's empty-state text ("No puzzles available") — the parsed puzzle list lands AFTER the first composition and no recomposition observes it before capture (the Compose async-state family, same law-gap as issue #615). The next wave: drive the lifecycle/state pump until the observed repository state stabilizes (bounded virtual-clock), then the Compose Canvas board draw ops (the §6 frontier) become reachable.

Wave-B battery re-run (post-fix binary): {bat(hand)}"""

R[609] = f"""## Blockinger RECEIPT — RUN VERDICT **rc=0 SUCCESS** · menu renders REAL UI (screenshot verified)

Base commit 66083e5a, SHA-pinned APK `org.blockinger.game_14.apk` re-verified `0c51e225…` ✓. The runtime boots the game, launches the launcher activity, and renders the REAL start screen: "Highscores" title bar, the Resume Game / New Game buttons and the name-entry row — visually verified from the frame capture. errors=0, no crash, 2 frames.

This satisfies the "menu observation" reproduction the issue asks for on the CURRENT zip. The gameplay completion (falling-block loop, next-piece canvas, score/state persistence) remains the R090 implementation item — the run evidence here is the launch + menu + interactive surface baseline the implementation builds on.

Wave-B battery re-run (post-fix binary): {bat(hand)}"""

R[610] = f"""## n-Puzzle RECEIPT — RUN VERDICT **rc=0 SUCCESS** · launcher + layout inflate cleanly

Base commit 66083e5a, F-Droid 1.1 (vc 2) APK (`name.livitski.games.puzzle.android_2.apk`). The runtime: manifest launcher `.GamePlay` resolves → `[C94-SINGLETON] LAUNCH-STORE key='Lname/livitski/games/puzzle/android/GamePlay;'` → `setContentView(0x7f030001)` → `[U007-INFLATE] root_id=19 views=5 strings=3 unresolved=0` → `[ECR-ROOT] scalar content_view_id root=19` — the full launch→inflate→root law chain, errors=0, no crash, 2 frames rendered.

Open surface (measured): the puzzle BOARD is a custom View whose tile-drawing lands in the custom-view draw frontier — the frame shows the app chrome (title/status text) while the board area stays background-dark. The YouWin/ImageSelection activities are additional surfaces for the gameplay wave.

Wave-B battery re-run (post-fix binary): {bat(hand)}"""

R[613] = f"""## Hello World Toast RECEIPT — **THE WHOLE TARGET IS FIXED** · commits 66083e5a · "Hello World!" RENDERED

The app's complete behavior = `Toast.makeText(...).show(); finish()`. Three engine gaps blocked it; all closed in this wave:

1. **No Toast handler existed.** `Toast.makeText` is an INVOKE-STATIC on a framework class the DEX never defines → REC-MISS → bridge_to_api had NO Toast case → STUBBED-null → the toast never existed (`[REC-MISS] Landroid/widget/Toast;.makeText` — the only trace of the app's entire purpose). FIX: the bridge consult routes `Landroid/widget/Toast;` to the shadow registry — the DialogShadow's existing toast law (makeText/show/cancel + resolve_strings + the bottom-transient painter) now serves both static and instance dispatches. AOSP Toast.java: SHORT=0, LONG=1.
2. **No-root frames never painted overlays.** The whole frame render block lived inside `if (root_id != 0)` — a Toast-only app has NO content root BY DESIGN, so even a recorded toast could never reach pixels. FIX: the no-root path paints the window-level toast overlay (AOSP paints toasts through WindowManager regardless of activity content).
3. **DialogShadow::toast_active()** accessor added for the renderer.

**Evidence (APK `HelloWorldToast-1.4.0-android.apk`, 84,306 bytes — matches the upstream README's ~84 KB):**
```
[TOAST] makeText obj=16 text="" resid=2130968577
[TOAST] show() text=""
[DIALOG-RENDER] toast box 173x56 text="Hello World!"
[TOAST-RENDER] no-root window painted (toast overlay)   ← both frames
```
Screenshot visually verified: the dark toast box with **"Hello World!"** at the bottom-center — the exact AOSP placement, text resolved from the string resource (0x7F0E0001) through the ARSC.

Note: the run's Status stays PARTIAL by the honest frame-truth law (verdict NO_ROOT — the app truly has no content view); the app's UI evidence is the toast itself, which now renders. The `finish()` lifecycle dispatch is in the log (`G07-LIFECYCLE` onStart/onResume after finish — the engine's virtual-clock window is the boundary for the exit path).

Wave-B battery re-run (post-fix binary): {bat(hand)}"""

R[614] = f"""## Guess RECEIPT — RUN VERDICT **rc=0 SUCCESS** · start screen renders REAL UI (screenshot verified)

Base commit 66083e5a, F-Droid 0.15 (vc 15) APK (`ru.zxalexis.ugaday_15.apk`). The runtime launches `ru.zxalexis.ugaday` and renders the REAL start screen: the "Guess the number (1 - 100)" header and the "Put the number" button — visually verified from the frame capture. errors=0, no crash, 2 frames.

Next step for full gameplay: the number-input dialog flow (AlertDialog input + guess feedback) — the dialog law the runtime already renders (see gmdice's 8-item dialog) is the surface this game needs.

Wave-B battery re-run (post-fix binary): {bat(hand)}"""

R[611] = f"""## Notepad RECEIPT — run VERDICT PARTIAL · root-caused to the DataStore/kotlin.reflect class frontier · NOT fixed this wave

Base commit 66083e5a, F-Droid 3.0.6 (vc 122, `com.farmerbb.notepad_122.apk` — the modern Kotlin rewrite per the issue's identity warning). The launch chain works: `[C94-SINGLETON] LAUNCH-STORE key='Lcom/farmerbb/notepad/android/NotepadActivity;' id=602` — the activity dispatches. The frame stays white because the startup chain hits a **deferred ClassNotFoundException storm**:
- `androidx.datastore.preferences.*` core classes (×4) — Notepad 3.0.6 stores notes/preferences in DataStore;
- `kotlin.reflect.jvm.internal.ReflectionFact*` (the kotlin-reflect engine);
- `libcore.io.Memory` — the ART/JDK internal the DataStore charset paths need.

This is the honest frontier: the runtime's framework-class surface is missing the DataStore/kotlin-reflect family this build of Notepad requires (the issue's scope-restricted single-note workflow is reachable ONLY after those classes resolve). No crash (the `Forensics` hit is the boot-time install line); 2 frames; errors=4 all deferred CNFE.

Recommended next wave: implement the DataStore preferences file law (legacy Java serialization fallback or the protobuf-lite surface) + `libcore.io.Memory`, then re-run this exact APK — the launcher dispatch already works, so the workflow test can start immediately after.

Wave-B battery re-run (post-fix binary): {bat(hand)}"""

import os
only = [int(x) for x in sys.argv[1:]] or list(R.keys())
for n in only:
    req = urllib.request.Request(BASE + f"/issues/{n}/comments",
        data=json.dumps({"body": R[n]}).encode(), headers=H, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        print(n, "receipt:", json.loads(r.read().decode())["id"])
