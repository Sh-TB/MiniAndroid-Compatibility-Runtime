#!/usr/bin/env python3
"""T279 CONT close-out comment on #472."""
import json
import subprocess
import urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
BASE = "https://api.github.com/repos/" + REPO


def get_token():
    p = subprocess.run(["git", "credential", "fill"],
                       input="protocol=https\nhost=github.com\n\n",
                       capture_output=True, text=True)
    for line in p.stdout.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    raise RuntimeError("no token")


TOKEN = get_token()


def comment(body):
    req = urllib.request.Request(f"{BASE}/issues/472/comments", method="POST",
        headers={"Authorization": f"Bearer {TOKEN}",
                 "Accept": "application/vnd.github+json",
                 "User-Agent": "t279-agent", "Content-Type": "application/json"})
    data = json.dumps({"body": body}).encode()
    with urllib.request.urlopen(req, data) as r:
        return json.load(r)


BODY = """# T279 CONT close-out — corpus complete, honest R-scale, LLO law

Follow-up to the T279 final report (issuecomment-7234223463). Commit `5c8343e94` on `main` (pushed); the sandbox recycle between sessions was survived — all work re-synced from origin and re-verified.

## 1. The S182 corpus is now 100% two-run measured

The 9 off-disk APKs were restored from F-Droid byte-pinned (`scripts/t279c_restore_receipt.txt`) and measured on the rebuilt binary `c3006bf71e02b3ae` (same source as `1a21be9f`): **all 9 pairs face-identical, 0 INSTALL_FAILs**. Two further recoveries: **pfludo** (REAL_APP_CONTENT, px 58,212 — SECUSO Skip/Next intro) and **lrceditor** (REAL, px 2,194). The S182 PARTIAL class keeps improving with each engine wave, exactly like flip/diceroller did.

## 2. Honest R-scale corrections (every claim now visually verified)

Visual inspection of every previously-unverified claim corrected five levels — recorded in the registry notes, nothing deleted:
- **uturn** = "UTurn Installed…" notice screen (face == its S182 historical face byte-identical; the recovery stands — honestly R2, not R3)
- **pfdicer** = blue welcome dialog (gate) · **pfsolitaire** = SECUSO SKIP/NEXT intro (same 58,212-px template as pfludo) · **textpad** = editor chrome bar only · **npuzzle** = picture-selection prompt

Final census across 32 two-run titles: **7 R3 / 8 R2 / 17 R1**; statuses: 5 INTERACTIVE / 10 CURRENT-REPRODUCIBLE / 18 PARTIAL / 2 REGRESSED / 4 BLOCKED. Every R3 claim is visually verified genuine app content (gmdice dice UI, bouncy table, librecontactsbackup full backup UI + dialog, ugaday guess UI, blockinger menu+dialog, flip coin, diceroller die).

## 3. Second focused fix: T279-LLO-PROVIDE law

Fresh stacks named the compose composition-state frontier exactly: janken dies at `ISE "CompositionLocal LocalLifecycleOwner not present"`. The new law (dalvik_interpreter.cpp, the S22-LC-PROVIDE family, exact AOSP error-string key, app-agnostic) returns the current Activity as the owner — the AOSP ComponentActivity-IS-the-LifecycleOwner semantic; the app's own bundled `getLifecycle()` DEX answers its real LifecycleRegistry. **Result: janken uncaught 33→32, deterministic; the next frontier is NAMED, not guessed:** androidx Navigation `"You cannot access the Navigator's state until the Navigator is attached"` (boot-order class — recorded, not chased). authsrng's remaining blocker = kotlin-reflect `SynchronizedLazyImpl` NPE (different class).

**Regression gate (binary c3006bf7):** f714 9/9 · lifecycle ALL · linear 24/24 · input_pipeline ALL · gmdice/bouncy/pfdicer faces byte-identical (3891679d/37326cb2/31ffa499) — zero regressions.

## 4. Records + per-app trackers

Registry: 9 rows measured + 5 R2 corrections + layer notes (179 titles, rendered 151). ACHIEVEMENTS totals updated; METRICS regenerated (README checker OK); audit doc §6 written; showcase regenerated and republished (gh-pages `ab33d08e6`). Per-app trackers updated: #473 gmdice INTERACTIVE (3-build byte-identical faces), #475 emmanuelttt honest PARTIAL correction, #487 pfdicer CURRENT-REPRODUCIBLE, #489 itsfrz listener gap.

## 5. Remaining queue (evidence-ranked)

1. androidx Navigator-attach boot-order law (janken + the compose nav family).
2. kotlin-reflect internals for authsrng.
3. Inflate→attach (minos, cocodechess); DataStore worker-thread (farmerbb); custom-cell listener census (itsfrz).
4. Owner decisions: history-rewrite gates (T279_REPO_SIZE.md), librecontactsbackup face-drift adjudication.
"""


def main():
    r = comment(BODY)
    print("posted:", r["html_url"])


if __name__ == "__main__":
    main()
