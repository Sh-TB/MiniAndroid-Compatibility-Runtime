#!/usr/bin/env python3
"""s183_post.py — honest fine audit of #11/#12 + graphics-depth re-adjudication.
Posts precise comments, reopens both issues, and posts the census to #472."""
import json, subprocess, os, urllib.request

def token():
    out = subprocess.run(["git", "credential", "fill"],
                         input="protocol=https\nhost=github.com\n",
                         capture_output=True, text=True).stdout
    return [l.split("=", 1)[1] for l in out.splitlines() if l.startswith("password=")][0]

TOK = token()
REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
RAW = "https://raw.githubusercontent.com/Sh-TB/MiniAndroid-Compatibility-Runtime"

C11 = """**S183 FINE AUDIT (user challenge: «مگه اینا لود کامل نوشتی؟») — the body's DONE is OVERSTATED; reopened with precise evidence.**

The challenge is correct on every point. Three precise corrections, each with hard evidence:

**1. All visuals in this issue are the GOLDEN FIXTURE, not the real APK.**
`docs/evidence/visual_forensics/tictactoe/run1/` and the `s74_ops/tictactoe_golden_fixture/` frames are `tictactoe_golden` — the in-repo self-built replica (introduced de5f370e). The real `com.emmanuelmess.tictactoe` vc3 APK was NEVER driven to a win state. The dossier even words it "no GL surface **in the proven path**" — the proven path is the fixture.

**2. The fixture graphics are NOT full graphics — measured.**
Pixel forensics of the issue's own evidence frames (1080×1920):
- `win_full.png`: **97.71% one flat blue** `(111,168,220)` + 2.21% white + 0.04% dark = X/O glyphs. That is a colored page + one font — exactly the user's words, confirmed by measurement.
- launch / mid / win: same composition (97.6–97.7% flat).

**3. The REAL APK on today's main (5d7edcdb34b1502c) is blank — root cause now precisely decoded** (evidence: [S183_PROOF_STRIP.png](https://raw.githubusercontent.com/Sh-TB/MiniAndroid-Compatibility-Runtime/main/evidence/s183_audit1112/S183_PROOF_STRIP.png)):
- Face `b5a7a35d5fe0564b` = DEFAULT_BACKGROUND_ONLY, **1 unique color, 0 app-owned pixels, 0 draw ops**, 8 uncaught.
- Exact failure chain (dex-decoded + runtime trace):
  1. `AndroidApplication.<clinit>` → `GdxNativesLoader.load()` → `SharedLibraryLoader.load` → `System.loadLibrary("gdx")`
  2. G-4 extraction works: `libgdx.so` x86_64 extracted (sha16 `553c8769776ff741`)
  3. **host dlopen FAILS: `/lib/x86_64-linux-gnu/libm.so: invalid ELF header`** — the .so's bionic `DT_NEEDED libm.so` collides with the host glibc *linker script* of the same name. A real Android device never hits this (bionic libm.so is an ELF there).
  4. libGDX wraps the failure: `GdxRuntimeException` unwinds `AndroidApplication.<clinit>` → `AndroidLauncher.<init>` dies → `AndroidGraphics.<init>` NPEs on the `createGLSurfaceView` path.
- The APK ships real content we never load: `assets/fonts/Roboto-Medium.ttf`, `assets/images/restart_game.png`, `libgdx.so / libgdx-box2d.so / libgdx-freetype.so` — i.e. **neither its graphics nor its custom font ever loads**.

**Status: REOPENED.** Honest ladder: fixture DONE (stays, labeled FIXTURE_ONLY) / real APK BLOCKED at (B1) Android-ELF vs host-glibc dlopen collision + (B2) GL/EGL surface absent. B1 is now the campaign's next law (see #472 S183 census) — it unblocks every libGDX-family game (#11 real APK, stacktower3d, emmanuelttt family).
"""

C12 = """**S183 FINE AUDIT (user challenge) — reopened; two precise corrections.**

1. **Scope was overstated by the title.** The S51 evidence card is honest that the game is `connectfour_golden` (fixture), but the title "[EXEC] ConnectFour — APK Execution & Gameplay Proof" + DONE reads as a real app being executed. **No real-world Connect Four APK exists in the corpus** — only the self-built fixture was ever measured. Corrected status: `FIXTURE_DONE / REAL_APP_NOT_MEASURED`.
2. **The visuals are NOT full graphics — measured.** Pixel forensics of the issue's own evidence (1080×1920): `01_launch.png` = **95.42% flat gray** `(225,225,225)` + 2.21% white + 2.12% blue fill + 0.13% dark glyphs; midgame/win identical composition (95.1–95.3% flat). A colored page + a font — the user's exact description, confirmed by measurement.

Side-by-side honest comparison (fixture evidence vs the 5 real-app faces we had labeled REAL that are actually one-text-line-on-white, vs the 10 genuinely rich faces): [S183_PROOF_STRIP.png](https://raw.githubusercontent.com/Sh-TB/MiniAndroid-Compatibility-Runtime/main/evidence/s183_audit1112/S183_PROOF_STRIP.png)

**Next executable step for THIS issue:** fetch a real Connect Four APK (F-Droid), install fresh-store on main, measure it, and post its verdict here — the fixture DONE stays as a toolchain proof only.
"""

C472 = """**S183 — graphics-depth re-adjudication of every face we call REAL_APP_CONTENT (the user's bar: full graphics, not two colors + a font).**

Census method (honest, mechanical): every REAL-labeled face measured for unique colors, non-background share, ink share, smooth-gradient (image/asset-like) share, edge density → tiers:
- **A_RICH (10):** snake_deluxe, librecontactsbackup, tetris, g2048, ttt_deluxe, minicraft, peri, balance, snakeneon, dooz — genuinely multi-color (23–74% non-bg).
- **B_STRUCTURED (14):** opmt, bouncy, opencalc, microtimer, tripeaks, klondike, tangram, gmdice, unote, wocheneinkauf, fishrings, memory, pfsolitaire, uturn — real UI but FLAT fills, ~0 image assets (grad 0–1.5%): structure without decoded bitmaps.
- **C_TEXT_ON_FLAT (5): textpad, terminightor, pfdicer, telegram, forkgram — the user is right: one text line on a white/flat page (0.15–1.13% non-bg). Relabeled REAL_APP_CONTENT_TEXT_ONLY.**

Proof: [S183_PROOF_STRIP.png](https://raw.githubusercontent.com/Sh-TB/MiniAndroid-Compatibility-Runtime/main/evidence/s183_audit1112/S183_PROOF_STRIP.png) — fixture-#11 vs real-#11, the 5 C-tier faces, and A/B-tier contrast. Data: `evidence/s183_audit1112/S183_GRAPHICS_DEPTH.json`.

**The base problem, now located per family with exact evidence:**
- **B1 — Android-ELF vs host-glibc dlopen collision (libGDX game family; the biggest games blocker).** `System.loadLibrary("gdx")`: extraction works, then host dlopen fails `"/lib/x86_64-linux-gnu/libm.so: invalid ELF header"` — bionic `DT_NEEDED` names collide with glibc linker scripts. Same root for stacktower3d/emmanuelttt/#11-real. **Next law: bionic→host ELF dependency mapping (DT_NEEDED rewrite or shim namespace), then dlopen succeeds for the whole family.**
- **B2 — GL/EGL surface absent** (libGDX rendering path `AndroidGraphics.createGLSurfaceView`).
- **B3 — Compose init** (stopwatch ComposeView class-index, sparkledns kotlin-reflect, tusky).
- **B4 — androidx lifecycle/coroutines clinit NPE storms** (sunpiano, sopadeletras, awagam, webstack...).
- **B5 — missing framework classes at claimed API** (android.graphics.Insets — bmi; kotlin-reflect).
- **B6 — bitmap-asset flatness (new observation from this census):** B-tier UIs render structure with ~0 decoded image assets — the BitmapFactory path needs a real-asset decode audit across the B-tier set.
"""

def api(method, url, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    r = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"token {TOK}", "User-Agent": "s183-audit",
        "Accept": "application/vnd.github+json"})
    return json.load(urllib.request.urlopen(r))

if __name__ == "__main__":
    base = f"https://api.github.com/repos/{REPO}"
    import sys
    n = int(sys.argv[1]); body = {"11": C11, "12": C12, "472": C472}[sys.argv[1]]
    if n == 472:
        url = f"{base}/issues/472/comments"
    else:
        url = f"{base}/issues/{n}/comments"
    r = api("POST", url, {"body": body})
    print(f"comment posted on #{n}: {r['html_url']}")
    if n in (11, 12):
        r2 = api("PATCH", f"{base}/issues/{n}", {"state": "open"})
        print(f"#{n} reopened: state={r2['state']}")
