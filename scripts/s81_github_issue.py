#!/usr/bin/env python3
"""s81_github_issue.py — S81 §28/§29: ONE consolidated tracking issue with the
required evidence chain format (source links, APK provenance, reference,
MiniAndroid screenshot pointers, runtime result, visual comparison, missing
capabilities, evidence, current status). GH_TOKEN from .secrets (never echoed)."""
import json
import urllib.request

TOKEN = open("/home/z/my-project/.secrets/gh_token").read().strip()
REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
API = f"https://api.github.com/repos/{REPO}"

TITLE = ("S81 — REAL APP VISUAL COMPATIBILITY: audit ladder, VF fixes, "
         "200-item F-Droid corpus + BATCH-01")

BODY = """## S81 wave — visual compatibility campaign (status: CORPUS_READY, EXECUTION_PARTIAL)

New law this wave (S81 §1/§52): **EXECUTED ≠ VISUALLY COMPATIBLE**. Status ladder L0 LOADED_ONLY → L1 NONBLANK → L2 GRAPHICALLY_NONTRIVIAL → L3 STRUCT_CANDIDATE → L4 SEMANTICALLY_CORRELATED → L5 VISUALLY_VERIFIED (L5 requires human review, never self-granted). Methodology + thresholds: `scripts/s81_visual_audit.py` (no single fake overall score, §36).

### Visual audit of the existing ladder (18 APKs at HEAD)

| Result | Detail |
|---|---|
| Only S80's own games reach L3 | Snake Deluxe, Mini Tetris (82/70 uniq colors, ICON_PRESENT) |
| Zero curated third-party apps reach L3 | gmdice dom=0.91 MONOCHROME_LIKE, Notes uniq=6, Simple Keyboard uniq=2, Dooz uniq=2 |
| 7 apps flag `IMAGE_DECODED_VS_RENDERED_GAP` | APK ships 24–32 rasters, screen shows 0 image/icon pixels |
| 7 prior HUMAN_VISIBLE statuses DOWNGRADED per §39 | honest re-classification, recorded in `docs/audit/APP_MATRIX.md` |

Report: `run/s81_audit/s81_visual_report.json` + evidence JPGs in `docs/evidence/s81/`.

### Root-caused + FIXED (visual failure registry VF-*, §42/§43 workflow)

**VF-NEW-001 / VF-DIALOG-ITEMS** — `AlertDialog$Builder.setItems` dropped the item array (probe-proven: dialog painted title+message, `items=0`).
- Root cause: DialogShadow recorded only the listener; array never materialized.
- Fix (AOSP law): heap array elements materialized into the builder window in BOTH dispatch layers (`try_shadow_dispatch` + `bridge_to_api`, same dual-view shape as R-NEW-339).
- Observed: `materialized 3/3 items`, dialog 920x144→920x408, ITEM-A/B/C rows painted with dividers.
- Evidence: `probe_dialog_items_BEFORE_fix.jpg` / `probe_dialog_items_AFTER_fix.jpg`.

**VF-NEW-002 / VF-PLACEHOLDER-GARBLE** — C013-CUSTOMVIEW placeholder painted the raw class descriptor (`Lorg.billthefarmer.markdown.MarkdownView`) over full-screen regions — this WAS the user-visible garbled text in Notes + Simple Stopwatch screenshots.
- Fix: neutral small `custom view (not rendered)` marker at bottom-left; class name kept in stderr trace only.
- Evidence: `notes_garble_BEFORE_fix_crop.jpg` vs `notes_AFTER_fix.jpg`, `stopwatch_AFTER_fix.jpg`.

### Regression (final binary)

battery 26/26 rc=0 · fidelity BYTE-IDENTICAL 90/90 · f152 6/6 · f153 3/3 · spot pixel-golden verifier 4/4. Zero golden deltas from VF fixes.

### 200-item F-Droid corpus (§4–§15, §31)

`docs/corpus/s81/corpus_index.json` (+CSV): CORPUS_SEED recorded, deterministic selection.
- **Mandatory §7 with full provenance**: P9 `se.tube42.p9.android` v0.1.1 (vc11), source https://github.com/tube42/9p ; TimeLimit `io.timelimit.android.aosp.direct` v7.7.1 (vc231), source https://codeberg.org/timelimit/timelimit-android — both with F-Droid reference-screenshot URLs (REFERENCE provenance recorded). Status: DISCOVERED (not yet executed — honest).
- Stopwatch inventory: 16 packages (§8). Platformer inventory: 10 packages (§9).
- **100 GAMES + 100 APPS** selected from live F-Droid category slugs (puzzle/board/card/action/casual/platformer/shooter/educational-game; calculator/clock/file-manager/gallery/multimedia/weather/connectivity/reading/internet/security/development/navigation/stopwatch).
- Batch plan: 4 × 25 mixed batches (§13/§14).

### BATCH-01 (25 fresh F-Droid APKs, mixed subset — §13/§14/§32)

- 20/25 RENDERED, 1 RENDERED_PARTIAL, 4 loaded-only, 1 download-fail. Disk before 5.8G avail → after 5.1G (guard respected, §32/§34).
- **Key honest finding (F-NEW-156)**: the dominant fresh-corpus frontier is the **onCreate APP BOUNDARY unwind family** — a first NPE inside app `onCreate` (e.g. solitaire `GameSelector.onCreate` invoke#3, heading-calculator `MainActivity.onCreate` invoke#6) unwinds the process → blank two-color screen. 19/25 fresh apps hit this family. These are NEW frontiers, individually queued for the §43 chain (reproduce → producer trace → root cause → law → fix).
- Report: `run/s81_batch01/batch01_report.json` (per-APK SHA256, sizes, statuses, visual metrics).

### Missing capabilities / next wave

1. F-NEW-156 onCreate-unwind family: per-app first-NPE disasm (`scripts/s81_disasm_probe.py`).
2. IMAGE_DECODED_VS_RENDERED_GAP: programmatic `setImageResource` → pixels proven at EXP-067, but XML-src/complex chains still drop (7 flagged apps).
3. P9 + TimeLimit: build/run + reference-vs-MiniAndroid comparison (L4/L5 needs reference screenshots side-by-side, §16-§19).
4. BATCH-02..04.

### Evidence

`docs/evidence/s81/` (SHA256SUMS): 12 JPGs ≤100KB (before/after both fixes, audit flagships, batch samples), corpus index+CSV, batch report, visual report. Scripts: `s81_visual_audit.py`, `s81_run_and_audit.py`, `s81_fdroid_corpus.py`, `s81_batch01.py`, `s81_disasm_probe.py`, fixture `fixtures/s81_visual_probe/`.

### Current status

CORPUS_READY · EXECUTION_PARTIAL (not "200_APPS_VERIFIED" — §51). Visual fixes regression-proven. No claim of VISUALLY_VERIFIED anywhere: L5 awaits human review with reference+MiniAndroid side by side (§48).
"""


def main():
    body = {"title": TITLE, "body": BODY, "labels": ["wave-report", "visual-compatibility"]}
    req = urllib.request.Request(f"{API}/issues", method="POST",
                                 data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {TOKEN}",
                                          "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req) as r:
        res = json.loads(r.read().decode())
        print("issue created:", res.get("number"), res.get("html_url"))


if __name__ == "__main__":
    main()
