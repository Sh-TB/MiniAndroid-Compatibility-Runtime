#!/usr/bin/env python3
"""cont11_comment.py — post the reconciliation report to issue #387."""
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
BODY = """## CONT-11 reconciliation report — deduplication + completions + census numbers

The 121-APK loading census ran on this workspace while the parallel W7–W9 lineage advanced the main tree. Honest reconciliation at the W9 head:

### Deduplication (no double-landing)

| census-wave root | parallel-lineage root that already fixed it | action |
|---|---|---|
| interface-resolution exactness gate (compose Lookahead `$placementBlock` UNSET) | **F-NEW-281c** (JVMS 5.4.3.4 exact (name,proto) gate, same fall-through order) | not re-landed |
| Thread UncaughtExceptionHandler law | **F-NEW-272** (per-thread map + KillApplicationHandler default) | not re-landed |
| WindowMetrics family | **F-NEW-486** (singleton metrics + mBounds Rect) | not re-landed |

### Completions landed (probe-proven gaps in the F-NEW-272 dispatch coverage)

1. **ThreadShadow void no-op family** still answered `get/setUncaughtExceptionHandler` with `handled_void` BEFORE the engine F-NEW-272 law (the registry-level dispatch precedes `try_shadow_dispatch`) — pair removed (same precedent as the F-150 `sleep` removal). Probe rows F273-A1 (`getDefault → null`) and F273-A3 (`set-then-get`) failed before, PASS after.
2. **The STATIC arm was unreachable**: `execute_invoke_static → bridge_to_api` never reaches `try_shadow_dispatch` on this lineage — the same law added to `bridge_to_api` (the R-NEW-339 two-view pattern), reusing `default_uncaught_handler_` / `thread_uncaught_handlers_`. Static `getDefaultUncaughtExceptionHandler()` now answers the never-null process default (AOSP RuntimeInit boot law).

### New registrations (genuinely missing from the 828-root registry)

- **F-NEW-514** — WindowInsetsCompat.toWindowInsetsCompat(View,WindowInsets) / LocalView compose-locals cluster (the surviving `Object.getClass` umbrella: notepad, peri, netguard, aurora, …).
- **F-NEW-515** — org.fossify.* 7-title family: AOSP-faithful `Unknown authority` IAE rethrown through the finally-close path dies at `XxxActivity.onCreate` without consulting the registered deferred handler (coroutine-boundary frame collapse; kin of F-NEW-217).
- **F-NEW-516** — List.size-on-null family (5 titles) + ViewDragHelper (2) + libGDX AndroidInput.onResume (2) + NSM singles backlog.

### Census numbers (121 titles, APP-BOUNDARY crash titles)

| stage | crash titles |
|---|---|
| baseline (pre-W7 lineage) | 93 |
| + first census fixes | 90 |
| **reconciled W9 head + completions** | **81** |

The 4 nominal regressions are `verdict=NO_ROOT` white-screens → deeper SPECIFIC faces (cordova `AllowList` NumberFormatException; `Future.get` NPE) — success-path progress, not drift. uturn → **SUCCESS**; librecontactsbackup → **SUCCESS**; floatdeck → past its crash.

### Regression battery (reconciled binary)

- anchors ×3 byte-identical, matching the rebased records exactly: opencalc `63020bc7` · chess `a0319686` · dooz `851cc176` (recorded fresh-store first-run face) · microtimer `bbd350b6` · unote `7481e9b4` — ZERO drift from the completions.
- negatives **19/19** · reinstall-identity **5/5** · cont11 probe **12/12** (real aapt2/ECJ/D8).

Task stays OPEN: next waves own F-NEW-514 → F-NEW-515 → F-NEW-516 (probe-first, generic fixes only).
"""

tok = token()
r = subprocess.run(
    ["curl", "-s", "-X", "POST",
     f"https://api.github.com/repos/{REPO}/issues/387/comments",
     "-H", f"Authorization: token {tok}",
     "-H", "Accept: application/vnd.github+json",
     "-d", json.dumps({"body": BODY})],
    capture_output=True, text=True)
resp = json.loads(r.stdout)
print("comment id", resp.get("id"), resp.get("html_url", resp.get("message")))
