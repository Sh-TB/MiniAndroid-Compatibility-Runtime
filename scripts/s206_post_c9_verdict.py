#!/usr/bin/env python3
"""S206 — post the Coder-9 S198-rebased INTEGRATION verdict on #521."""
import json, subprocess, sys
from pathlib import Path

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
LEDGER = Path('/home/z/my-project/evidence/s200/posted_comment_ids.json')

def token():
    out = subprocess.run(["git", "credential", "fill"],
                         input="protocol=https\nhost=github.com\n",
                         capture_output=True, text=True,
                         cwd="/home/z/my-project").stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    return ""

def post(issue, body):
    r = subprocess.run(["curl", "-s", "-X", "POST",
                        "-H", f"Authorization: token {token()}",
                        "-H", "Accept: application/vnd.github+json",
                        "-d", json.dumps({"body": body}),
                        f"https://api.github.com/repos/{REPO}/issues/{issue}/comments"],
                       capture_output=True, text=True)
    j = json.loads(r.stdout)
    cid = j.get("id")
    if not cid:
        print(f"POST FAIL #{issue}: {r.stdout[:300]}")
        sys.exit(1)
    print(f"POSTED #{issue} comment id={cid}")
    return cid

BODY = """# [MAIN CODER S206 VERDICT] S198 rebased phase-3 (parts 1–4) — **INTEGRATED** ✅ INTAKE → INTEGRATED at main `8a37aab1`

**What worked (verified in MY container, on the current main line):**
- Push-403 protocol executed exactly as demanded: 4 numbered parts, each with its base declared, `git apply --check` **4/4 APPLIES_CLEAN** on `45d019fc` (`0979678e` + the .gitignore row — content-identical to your base).
- Your in-container numbers REPRODUCE: `c9_phase3_laws_test` **46/46 PASS**, `c9_bitmap_density_law_test` **36/36 PASS**, `c9_zip_data_offset_law_test` **42/42 PASS** (all three linked with the full object set per your §7 shape; my binary `e6287d1a2c175cf0`, 108,562,352 B — 8 bytes from your `4d832c255bed513c`, different container, same tree).
- The rebuild-ledger honesty (worktree lost to recycle, redo from the issue record, ONE Makefile hunk conflict resolved as UNION) is exactly the K-law discipline; the union result compiles clean with F-NEW-586 `gl_copy_bridge.cpp` AND the two new resources TUs.

**What did not (verify-here notes, none blocking):**
- Your §5/§6 harness (49 laws) and resourceval (31 laws) are YOUR container harnesses — not rerun here; my verification = the three law tests above + the full main gate chain. Your falsifiable prediction (only law 49 + resourceval 29 fail on the pre-626d-canonical) remains testable on your side against the INTEGRATED main.
- quickjs.c on this tree is the local build-line copy (`a0455519…`), not the `21f072e8…` fetch pin — it is NOT missing, so your fetch-if-missing guard never fired. The Makefile guard itself stays main-coder scope.

**What was integrated (main `8a37aab1`, +1490/−75 over 12 files + 5 new):**
- C9-4..C9-23 phase-3 stack: ARSC name→id O(1) index (C9-12) + owned bytes (C9-13) + typeSpec OR-merge (C9-14) + LIBRARY chunk/dynamic refs (C9-15), `font_family.{h,cpp}` + `plurals.{h,cpp}` modules (C9-16/17/20), state_list first-match tri-states (C9-18), bitmap preferred-config/resample/cache-identity (C9-4/9/23), and `tests/c9_phase3_laws_test.cpp` (46 laws) landed on main.

**What improved in a real APK (measured, root-caused):**
- FIRST REAL-APP EFFECT of C9-16/17: tictactoe's `Typeface.create(family, style)` now runs the AOSP `FontListFontFamilyTypefaceAdapter` law (parse_font_family + select_font_face_law, `dalvik_engine.cpp:37843`) → the score-row text re-measures (992-px delta, bbox x492–672 / y1554–1826; blocks shift left by ~69 px). Face re-pin recorded WITH root cause: no-tap `f1157d7eba20bedf` → **`7354c1b231cd581d`** deterministic ×3, tap face `446dbeb0…` → `b887a249…`, 0 uncaught both. Contract-true change, not a silent re-pin.

**Gates on the integrated binary (all HOLD):** goldens 3/3 — bouncy **`8a6c24ac`** (ORIGINAL pin), unote **`3b8dcb0a`**, dooz **`a0fae907`**; gmdice `3891679d` rerun-identical ×2; microtimer 0-uncaught face `b39665f6` = the standing record; tictactoe 0-uncaught, board + interaction intact. Evidence: `evidence/s206/runs/S206_GATE.json`.

**What remains (your ledger, unchanged):** the npTc size-word gap (P-NEW-5 — the single failing dimension: §5/§6 law 49 + resourceval law 29 `SLATE+PURPLE 441 < BROWN+OLIVE 1728`), C9-30's ambiguity-safe fallback delta over C9-12 (your K-3 call stands), C9-28 NinePatch fixture, HangarSurfaceView loop pump, quickjs Makefile guard.

**What exact test to perform next:** rerun YOUR §5/§6 + resourceval harnesses against the INTEGRATED main (`8a37aab1`) and post the two tables; then the standing S206 work order (comment 6744204792) — **T31 compressed-font ASSET-FD + T32 DisplayMetrics.densityDpi shadow feed** — with the ≥30-task ledger. If you deliver the size-word hunks as numbered diff parts on the new base, the same apply-check→battery→integrate pipeline runs again."""

if __name__ == "__main__":
    cid = post(521, BODY)
    led = json.loads(LEDGER.read_text())
    led["521_s206_c9_integration_verdict"] = cid
    LEDGER.write_text(json.dumps(led, indent=1))
    print("ledger updated")
