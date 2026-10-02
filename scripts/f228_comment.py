#!/usr/bin/env python3
"""F-NEW-228 wave — post compact report to issue #354."""
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

BODY = """## F-NEW-228 wave — "228 رو کامل بکن" + master-list merge (commit bf1ecfd3)

### Compact root table (mandated format)

| ROOT ID | FILE | FUNCTION | SYMPTOM | FIRST DIVERGENCE | ROOT CAUSE | GENERIC FIX | TEST | 3-RUN RESULT | STATUS |
|---|---|---|---|---|---|---|---|---|---|
| F-NEW-228 | resources/layout_inflater.cpp | measure_node weight block + first-pass spec | opencalc numpad rows 0/0/1057/1056/1056, last row off-screen y=2274; NO numpad pixels (91.3% display-blue) | VSTACK: row 731 content=126 but h=0; row 743 match-inflated 1888 | (1) weight pass EXCLUDED TableLayout/TableRow though AOSP TableLayout.java L470-476 calls super.measureVertical; (2) no findLargestCells row-WRAP law (L527-529); (3) weight block misrouted TableLayout to WIDTH axis (orientation never set → default-horizontal); (4) total_length used measured_WIDTH for vertical weighted rows; (5) raw spec-size excess (AOSP resolves min(content,spec) under AT_MOST) | 5-law port: LEG-A row-wrap force; LEG-B exclusion removal; LEG-B2 vertical force; LEG-C resolved-excess; mTotalLength vertical-axis fix | laws130 51/51; dooz/microtimer/unote goldens ×3 MATCH; ssw/headingcalc/secuso/whatsapp baseline-equal ×3 | opencalc ×3 e364b001ee7abd66 — rows 126+352×5 EQUAL, last row ends exactly y=1920, 64.7% button field, glyphs draw | IMPLEMENTED+TESTED |
| F-NEW-229 | resources/layout_inflater.cpp (CL branch) | CL child spec fallback | opencalc rows 462 wide (buttons 115px pitch, right 45% of each row = background) | [U007-SPEC] view 612 SlidingUpPanelLayout spec=1080/**AT_MOST** (lp=-1, only vertical constraints); AOSP CL gives EXACTLY | CL MATCH_PARENT children without anchors fall back to AT_MOST → subtree shrink-wraps (612→579, 646→504, 711→504) | attempted EXACTLY(avail) fallback — NO effect at the edited branch (routing differs) → **REVERTED** per no-unproven-change gate; needs branch-attribution trace first | after-fix: rows 1038, buttons 259px pitch + goldens byte-identical | — | OBSERVED |
| F-NEW-230 | evidence process | golden banking | 4 banked goldens unreproducible at HEAD default config (ssw f48ae6→0297e27f, headingcalc be1cea9c→4d462461, secuso eb5ebd55→31ddd(100% WHITE), whatsapp gate 31ddd IS a white frame); muellerma-vs-omegacentauri ssw APK mapping error | battery matrix: drifts IDENTICAL on baseline and patched binaries (patch-neutral) | goldens banked without recorded repro block (WxH/flags/flow/frame index) | re-bank with registry `golden_repro` blocks; blank-golden reject gate | every golden reproduces ×3 from its repro block | — | OBSERVED |

### opencalc BEFORE → AFTER (pixel truth, not SHA-truth)

- BEFORE `ae07c6804b5071d0`: rows h = 126 / **0** / **0** / 1057 / 1056 / 1056; last row at y=2274 (off-screen, 1920 screen); frame = 91.3% #6fa8dc display + 8.2% #303030; **numpad invisible**.
- AFTER `e364b001ee7abd66`: rows h = 126 / 351 / 352 / 352 / 352 / 352 (AOSP equal shares); last row ends **exactly at y=1920**; frame = 64.7% #303030 button field + 34.5% display; glyphs draw (250 unique colors). ×3 deterministic, rc=0.
- Residual: rows 462 wide → F-NEW-229 (full width needs the CL MATCH_PARENT spec law at its real production site).

### Master merged checklist

CAMPAIGN_STATE.md now carries the merged master list (previous leftovers F-NEW-217/221/192/204-207 + §A–§P + new Families A–W audit + Platform/README/Release audit Phases 0–21). Next: F-NEW-229 → F-NEW-230 → Families I/J law tests → platform audit (installed-APK filesystem proof) → README/release audit.
"""

tok = token()
url = f"https://api.github.com/repos/{REPO}/issues/354/comments"
r = subprocess.run(
    ["curl", "-s", "-X", "POST", url,
     "-H", f"Authorization: token {tok}",
     "-H", "Accept: application/vnd.github+json",
     "-d", json.dumps({"body": BODY})],
    capture_output=True, text=True)
resp = json.loads(r.stdout)
print("comment id:", resp.get("id"), "| url:", resp.get("html_url", resp.get("message")))
