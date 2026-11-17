#!/usr/bin/env python3
"""Follow-up comments for the #614/#617 runs."""
import json, subprocess, re

cfg = subprocess.run(["git", "config", "--list"], capture_output=True, text=True,
                     cwd="/home/z/my-project").stdout
tok = re.search(r"github_pat_[A-Za-z0-9_]*", cfg).group(0)
REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"

def post(n, body):
    url = f"https://api.github.com/repos/{REPO}/issues/{n}/comments"
    out = subprocess.run(
        ["curl", "-s", "-X", "POST", "-H", f"Authorization: Bearer {tok}",
         "-H", "Content-Type: application/json",
         "-d", json.dumps({"body": body}), url],
        capture_output=True, text=True).stdout
    d = json.loads(out)
    print(f"#{n}: {d.get('html_url', d.get('message', 'ERR'))}")

post(614, """## #614 Guess (ru.zxalexis.ugaday 0.15) — RUN DONE: real start screen rendered, SUCCESS

**Artifact:** `upload/handoff_apks/ru.zxalexis.ugaday_15.apk` (F-Droid naming; identity recorded).
**Runtime:** fresh `make -j1` rebuild of commit `93721416` (+ this session's laws), binary sha16 `e365418536fa10b4`.
**Run:** boot → inflate → render — **Status: SUCCESS ✅, Errors: 0**, frames captured.

**Pixel-verified start screen** (screenshot in `evidence/batch614_guess/screenshot.png`):
- Title bar: **"Guess the number (1 – 100)"** — the app's real string resource
- The number-entry row (EditText field)
- The **"Put the number"** button — the app's real submit control

The whole plain-Activity surface this issue targeted (single Activity, string resources, EditText, Button, dark theme) inflated, laid out and painted with zero exceptions — **no first divergence exists at boot**. Next session step (queued): typed number + tap on "Put the number" through the TouchDispatcher → result `TextView`/`Toast` state delta receipt. Status moves to OBSERVED (start screen, interaction battery pending).""")

post(617, """## #617 Minos (de.tcrass.minos 1.0.4) — run done: boot reached, TWO first-divergences found (blank frame)

**Artifact:** official F-Droid `de.tcrass.minos_10004.apk`, SHA-256 `af769233…` ✓ (exact cross-check match).
**Runtime:** fresh `make -j1` rebuild of commit `93721416`, binary sha16 `e365418536fa10b4`.
**Run result:** PARTIAL SUCCESS, Errors: 0, but the captured frame is the dark theme background only (content view never populated beyond root LinearLayout+FrameLayout) — the exact late-launch-starvation FACE, but with a REAL app-side exception chain behind it:

1. **`java.lang.IllegalArgumentException (bound must be positive)`** at `Lde/tcrass/minos/model/factory/MazeFactory;.createMaze pc=33` — `Random.nextInt(bound)` got a non-positive bound. The bound derives from the app's resource/config values; the engine answered a value ≤ 0 where ART would answer the real configured size, so onCreate's maze construction died and the maze view never attached. (generic law needed: F-086 resource-bound audit on this path — next session closes it with the exact resource id printed.)
2. **`java.lang.ClassNotFoundException ("android.util.Log")`** at `Lorg/greenrobot/eventbus/android/AndroidLogger;.<clinit> pc=3` — the R350 `Class.forName` law currently resolves ONLY against the loaded app-DEX class index; framework classes like `android.util.Log` exist in the shadow world and must resolve (or the law must distinguish bootstrap-class references from app-DEX references). EventBus's logger init then degraded.

**Why this is not "app broken":** on ART both paths succeed — `nextInt` receives the real configured bound, and `android.util.Log` is always present. Both divergences are generic runtime contracts, listed honestly here per the first-divergence protocol. Fix queue (next session): R350-FORNAME framework-class resolution + the MazeFactory resource-bound trace; re-run → maze render → drag hit-testing battery. Evidence kept in `evidence/batch617_minos/` (log + view tree + screenshot).""")
print("DONE")
