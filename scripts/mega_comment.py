#!/usr/bin/env python3
"""MEGA-CAMPAIGN wave (F-NEW-231/232/233) — post compact report to issue #354."""
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

BODY = """## FINAL MEGA-CAMPAIGN wave — installed-APK access + random corpus loop + frame-truth laws (commits b865a27d, e9ce717b)

### Wave result (§25 format — numbers, not adjectives)

```text
WAVE RESULT (HEAD e9ce717b, 2026-10-02)

Random APKs tested (seed 20261002): 2
  sudoku_secuso_101 (app): WHITE/rc=0-false-SUCCESS → PARTIAL + real layout
                           + 2 buttons ×3 (text gap registered)
  fishrings_v1.23_vc6 (game): flat #303030 → REAL GAME BOARD ×3
Previously failing → working: 1 (fishrings)
New REAL_APP_CONTENT: 1 (fishrings, a341e3ad9092f640 ×3)
New interactive: 0 (no tap-proof run this wave)

Telegram: real settings face only (NOT main UI) — not marked success
Safir: BLOCKED-BY-IDENTITY (zero project records — APK needed)
Black: BLOCKED-BY-IDENTITY (zero project records — APK needed)

Installed-APK inspection: PASS (10/10 platform claims, 2 APKs, source-hidden)
Golden validity: dooz/microtimer/unote/opencalc VALID ×3 (repro blocks banked);
  whatsapp white golden REJECTED; ssw/headingcalc/secuso/forkgram STALE (recorded)
Regression: NONE (all goldens byte-identical ×3)
```

### Roots landed this wave

| ROOT | FILE | SYMPTOM | ROOT CAUSE | GENERIC FIX | PROOF | STATUS |
|---|---|---|---|---|---|---|
| F-NEW-231 | src/main.cpp | NO install mechanism existed; only raw APK path; sourceDir = sideload path | platform gap (AOSP PMS /data/app + PackageInfo + /data/data law unimplemented) | `install` (SHA-256 + integrity re-hash + package.json + app dirs), `list-packages`, `run --package` (identity-only, deterministic-mapping deviation documented) | opencalc ×3 rc=0 e364b001ee7abd66 (= golden!) + bouncy ×3 real content, source APKs physically hidden during runs, provenance = installed codePath; 10/10 claims | IMPLEMENTED+TESTED |
| F-NEW-232 | runtime/execution_engine.{cpp,h} | deferred-UI apps classified by a PROVISIONAL launch face (fishrings flat #303030; census silent) | F-NEW-197/F-115b law: plain run freezes at Looper t≈0; splash Timer(5000)→startActivity never observable; census did not record pending work | census fields deferred_ui_pending/queue_size/earliest_ready_ms at quiescence + capture-time pending-intent snapshot + message annotation; launch-frame law unchanged | fishrings --frames 14 --frame-delay 500: a341e3ad9092f640 ×3 REAL GAME BOARD (6673 colors); sudoku ×3 real layout+2 buttons | IMPLEMENTED+TESTED |
| F-NEW-233 | runtime/execution_engine.{cpp,h} | plain runs (no --trace) reported SUCCESS on 100%-blank frames (sudoku live: white, rc=0, "SUCCESS") | 21-P0 census/verdict/downgrade block was boot-trace-gated | census/verdict/downgrade UNconditional; verdict+first_missing persisted; post-final-status annotation | sudoku plain now PARTIAL + "[F-NEW-233 frame truth: verdict=NO_ROOT, first_missing_stage=WINDOW_ROOT]"; goldens byte-identical ×3 | IMPLEMENTED+TESTED |

### First-divergence chain (fishrings, evidence not guesswork)

1. SplashActivity.onCreate → WebView.loadUrl(file:///android_asset/banner.html)
2. APK has ZERO assets/ entries — banner.html genuinely absent (F085 honest placeholder; app-side)
3. onResume → java.util.Timer.schedule(task, 5000) → startActivity(GameActivity)  ([F115-TIMER] live)
4. Plain run quiesces at Looper t≈0 with the task queued → launch-frame face = flat #303030
5. Time-driven capture advances the clock: Timer fires → GameActivity → REAL GAME BOARD ×3

### Telegram honest state

telegram_official + forkgram both land on the same REAL settings face
("LowPowerEnabledTitle" doubled-text + "Disable") — real app content, wrong
screen, title-overlap layout bug. REAL_APP_CONTENT on the MAIN UI NOT
demonstrated; first missing laws = intro/auth navigation chain + overlap bug.
Not marked tested/success.

### F-NEW-230 progress

- VALID ×3 with repro blocks banked in the registry: dooz d602648e8e401895,
  microtimer da73010a37dd0189, unote 4f1a9e4e8f64fae8, opencalc e364b001ee7abd66
  (also reproduced FROM THE INSTALLED PACKAGE).
- whatsapp 31ddd4d5b8e6d18e = 100% white → REJECTED as a gate.
- ssw/headingcalc/secuso/forkgram = STALE (current SHAs recorded; re-bank pending).

### Sentinel note

"Safir"/"Black": exhaustive search (registry/worklog/docs/evidence/issues) found
ZERO records. Not fabricated, not closed — APKs needed from the requester to
become sentinels. Working sentinels SAFE: all 4 reproducible goldens ×3.

Registry 525→528. Master checklist: docs/FINAL_COMPATIBILITY_CAMPAIGN.md.
"""


def main():
    t = token()
    payload = json.dumps({"body": BODY}).encode()
    out = subprocess.run(
        ["curl", "-s", "-X", "POST",
         "-H", f"Authorization: token {t}",
         "-H", "Accept: application/vnd.github+json",
         "-d", "@-",
         f"https://api.github.com/repos/{REPO}/issues/354/comments"],
        input=payload, capture_output=True)
    r = json.loads(out.stdout)
    print("comment id:", r.get("id"), "url:", r.get("html_url",
          r.get("errors", r.get("message"))))


if __name__ == "__main__":
    main()
