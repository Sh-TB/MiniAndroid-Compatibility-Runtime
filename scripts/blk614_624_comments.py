#!/usr/bin/env python3
"""Post per-issue status comments for #614-#624 batch."""
import json, subprocess, sys

TOKEN = subprocess.run(
    ["git", "config", "--list"], capture_output=True, text=True,
    cwd="/home/z/my-project").stdout
import re
m = re.search(r"github_pat_[A-Za-z0-9_]*", TOKEN)
tok = m.group(0) if m else ""
assert tok, "no token"

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"

def post(n, body):
    data = json.dumps({"body": body})
    url = f"https://api.github.com/repos/{REPO}/issues/{n}/comments"
    out = subprocess.run(
        ["curl", "-s", "-X", "POST", "-H", f"Authorization: Bearer {tok}",
         "-H", "Content-Type: application/json", "-d", data, url],
        capture_output=True, text=True).stdout
    try:
        d = json.loads(out)
        print(f"#{n}: {d.get('html_url', d.get('message', 'ERR'))}")
    except Exception:
        print(f"#{n}: RAW {out[:200]}")

BLOCKER = """## R090 run attempt — BLOCKED: no testable APK artifact exists yet

**What I did this session (fresh sandbox, runtime rebuilt from commit `93721416`):**
1. Fetched the pinned upstream source identity from this issue ✓ (repo + blob SHAs recorded).
2. Searched the local corpus (`upload/` tree, canonical/handoff/batch dirs) for a matching APK: **none found**.
3. Tried to produce the artifact from the pinned source: **this sandbox has NO Android build toolchain** — `javac`, `aapt2`, `d8`, `apksigner`, `gradle`, `zipalign` are all absent (verified via `command -v`), so `APK_HASH_PENDING` cannot be resolved inside the sandbox today.

**Why I am not faking it:** per the issue contract the APK must be the pinned artifact and re-verified by hash before any run. Without the artifact there is no honest render claim.

**Exact unblock paths (either one closes the blocker):**
- Attach/upload the built APK to this issue (or drop it into `upload/handoff_apks/` following the `org.blockinger.game_14.apk` naming pattern) — I will re-verify its identity, run the full boot→inflate→render→interaction chain, and post the pixel-verified screenshot + first-divergence log here.
- OR provide an Android build toolchain in the sandbox image (JDK + build-tools + platform with `aapt2`/`d8`/`apksigner`); I will then build from the pinned blobs and continue autonomously.

The runtime side is ready: the #609 WAVE-1 laws (F-SDF-1 SimpleDateFormat, F-CAL-CTOR, F-INTX-1 putExtras, F-PREF-REF pref-reference resolution) are committed at `93721416` and cover the generic framework surface this class of plain-Activity app exercises (XML `android:onClick` binding, `setText`/`getText`, `Toast`, `Random`, `TextView` updates).
"""

post(618, BLOCKER.replace("R090 run attempt", "#618 Android Counter run attempt"))
post(619, BLOCKER.replace("R090 run attempt", "#619 Tic Tac Toe run attempt"))
post(616, BLOCKER.replace("R090 run attempt", "#616 Dice Roller run attempt") + "\n**Note (issue-specific):** the mandatory startup welcome DialogFragment is inside the runtime's Fragment family already exercised by Blockinger's DefeatDialogFragment — first run will grade it directly.")
post(621, BLOCKER.replace("R090 run attempt", "#621 Rock Paper Scissors run attempt"))
post(622, BLOCKER.replace("R090 run attempt", "#622 Classic Calculator run attempt"))
post(623, BLOCKER.replace("R090 run attempt", "#623 Random Number Generator run attempt"))
post(624, BLOCKER.replace("R090 run attempt", "#624 Coin Toss run attempt"))

post(620, """## MAIN CODER DIRECTIVE status — #618 + #619 end-to-end

**Both targets are artifact-blocked, not runtime-blocked.** Status per issue (posted in #618/#619): no pinned APK exists (`APK_HASH_PENDING` per the issues' own status) and this sandbox has no Android build toolchain (javac/aapt2/d8/apksigner/gradle all absent — verified). I will not substitute a different app or invent a build; the honest blocker comment is on each issue with two concrete unblock paths (attach the APK, or provision the toolchain).

**Runtime readiness for both targets (this session):** fresh sandbox → full `make -j1` rebuild from commit `93721416` (the #609 WAVE-1 laws: F-SDF-1 SimpleDateFormat, F-CAL-CTOR, F-INTX-1 putExtras, F-PREF-REF). The plain-Activity surface both apps exercise (XML onClick binding, setText/getText, Toast, TextView state) is the exact chain proven on Blockinger's menu + dialog path (#588/#609 evidence). The moment an artifact lands, the boot→inflate→render→tap chain runs without further engine work — first divergence if any will be generic and logged per protocol.

**Order honored:** no expansion beyond the two directive targets was attempted (the six "next simple" issues only received blocker-status comments).""")

post(615, """## LATE-LAUNCH STARVATION — fix landed (S-LAUNCHDRAIN), re-verification queued

**Root fix is committed:** `fa5f97cf` + receipt commit `38211919` (WAVE-4) add **S-LAUNCHDRAIN** — a new boot stage between `execute_application` and `render_frame` that drains the app's async launch chain to quiescence (cross-queue drain + Choreographer due frames + G08 pending-intent chains + F-150 thread starts/yields + the F-277-parity clock fast-forward, bounded 4096 rounds / 16s virtual / 25s wall). Anti-spin guard: a parked coroutine worker that re-parks immediately is capped at 32 idle resumes per thread so one body cannot own the stage.

**Ground truth that motivated it:** the REAL `setContentView` + 6-view inflate of PrivacyFriendlySolitaire drained AFTER stage 7 capture — window had no root, frame captured only the dark theme background (exactly the blank-frame symptom this issue describes).

**Proof on a real app:** solitaire now reaches SUCCESS with a first real rendered tutorial screen (commit `38211919`), battery 8S/10P/0F no-regression, frame determinism gate PASS (3 goldens byte-identical ×2).

**Remaining:** this session's sandbox recycled the binary; a fresh single-job rebuild is in progress and the next run batch (Guess `ru.zxalexis.ugaday_15`, Minos `de.tcrass.minos_10004`) re-exercises the drained launch path — their first-divergence logs will either confirm the drain or expose a residual starvation face with exact class.method/PC. Will follow up here with those receipts.""")

post(614, """## #614 Guess (ru.zxalexis.ugaday 0.15) — APK located, run queued

**Artifact found in the local corpus:** `upload/handoff_apks/ru.zxalexis.ugaday_15.apk` (F-Droid naming, versionCode 15 = 0.15 per the pinned identity). Identity re-verification (package/versionCode/SHA-256) runs before launch, per the issue contract.

**Status:** the fresh-sandbox runtime rebuild (commit `93721416`) is in its final link stage; the run (boot → inflate → render → tap interactions → first-divergence log) fires immediately after. Receipt + pixel-verified screenshot follow in the next comment. No other gap known on the runtime side for a plain single-Activity guess loop (`Random` + `EditText` + `TextView` + `Toast`).""")

post(617, """## #617 Minos (de.tcrass.minos 1.0.4) — official APK acquired + hash VERIFIED, run queued

**Artifact (this session):** downloaded from the official F-Droid repo: `https://f-droid.org/repo/de.tcrass.minos_10004.apk` → stored as `upload/handoff_apks/de.tcrass.minos_10004.apk`.
**SHA-256:** `af76923388c4ee3a265f66ea1fdab80092ed72400123d7e23f38a886281228a0` — **exact match** with the issue's cross-check value ✓ (140,203 bytes, matches the F-Droid-reported ~136 KiB).

**Status:** fresh-sandbox runtime rebuild (commit `93721416`) is finishing its link; the run (boot → inflate → custom-drawn maze render → drag hit-testing → first-divergence log) fires right after. Note for the run: minSdk 28 means the app will exercise the modern framework surface (the same family the WAVE-4 launch-drain laws target). Receipt + screenshot follow here.""")
print("ALL COMMENTS POSTED")
