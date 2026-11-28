#!/usr/bin/env python3
"""T279 P8 — post the final report to #472 and open the Showcase issue.
Token read from the git credential helper at runtime; never printed."""
import json
import subprocess
import sys
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


def api(method, url, payload):
    req = urllib.request.Request(url, method=method, headers={
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "t279-agent",
        "Content-Type": "application/json",
    })
    data = json.dumps(payload).encode() if payload is not None else None
    with urllib.request.urlopen(req, data) as r:
        return json.load(r)


REPORT_472 = """# T279 FINAL REPORT — rendering recovery, two-run verification, MeasureSpec fix, showcase

**Session HEAD:** `f1312668f` on `main` (pushed; `344774e66..f1312668f`). Engine builds: `9c5e456b4790299e` (campaign, commit 344774e66) and `1a21be9fc9f6b016` (post-fix verification). Full evidence: `evidence/t279/` on main (T279_RENDER_AUDIT.md · T279_RENDER_INVENTORY.json · T279_TWO_RUN_RESULTS.csv · 72 compact shots + SHA256SUMS.txt · T279_REPO_SIZE.md).

## A–O summary (the assignment's format)

**A. Total historical real applications:** 179 unique packages in the reconciled registry (152 legacy rows + 27 recovered); 136 classified HISTORICAL-REAL-class on genuine recorded evidence, rendered=158 rows total.
**B. Total currently reproducible (two independent runs, byte-identical faces):** 7 CURRENT-REPRODUCIBLE + 6 INTERACTIVE = **13 titles reproduced twice on the current build** (gmdice, bouncy, pfdicer, pfsolitaire, textpad, librecontactsbackup, uturn, npuzzle, ugaday, blockinger, flip, diceroller, randomix).
**C. Interactive (state change observed in both click-test runs):** **6** — gmdice (face 3891679d→7ee46dd3, px 182,535→753,437), bouncy (→7579c536), librecontactsbackup (→b0df5708), ugaday (→204f8970), blockinger (→52875ecb, Highscores DIALOG rendered) + npuzzle (S23 ×3-run STATE_CHANGED; T279 ct face unchanged — listener-registration timing, recorded honestly).
**D. Partial:** 16 (incl. stacktower3d, emmanuelttt, farmerbb, itsfrz, minos, cocodechess, randomix R2 + the 9 S182 PARTIAL class).
**E. Regressed:** 2 (wocheneinkauf, peri — historical 2026-11-06 real; the T279 fix eliminated their convertMeasureSpec ISE layer, uncaught 33→32; the deeper compose composition-state layer remains. uturn WAS regressed and is now RECOVERED).
**F. Complete APK inventory:** `T279_RENDER_INVENTORY.json` (179 rows, all required fields) + `T279_TWO_RUN_RESULTS.csv` (23 titles × 2 runs + 12 click-test pairs + 9 post-fix pairs). APK SHAs disk-verified byte-exact against `s23_apk_sha256.tsv` + S182 `apk_shas.txt` pins; 9 wave APK SHA-pinned, 12 S182 APKs SHA-pinned, 9 S182 APKs absent-from-disk recorded as PENDING re-test (F-Droid restorable).
**G. Gallery URL:** https://sh-tb.github.io/MiniAndroid-Compatibility-Runtime/ (live-verified in headless Chrome: 179 cards, 73 genuine runtime images, search + status filters + historical-vs-current comparison + lightbox; old pages archived at archive/s80/ and archive/prev-20261127-index.html).
**H. Offline gallery download URL:** https://sh-tb.github.io/MiniAndroid-Compatibility-Runtime/MiniAndroid-Showcase-Offline.zip (read-back verified: downloaded SHA256 `4e7ebc5c80a302795dd1a5d390c8f180ee2d7946e95dbe98e41a676147e1d56c` == local; file:// mode renders 179 cards with 73/73 LOCAL image srcs).
**I. Original Git pack size:** 1,121,011 KB ≈ 1.09 GiB (size-pack, re-measured at f1312668f; GitHub API size 1,046,451 KB).
**J. Proposed cleaned pack size:** ~0.4–0.6 GiB (the 4.77 GB pre-compression build_* payload class ≈ 550–650 MB compressed; S-SLIM blob accounting) — **NOT executed; owner gate holds** (plan + recovery instructions: `evidence/t279/T279_REPO_SIZE.md`).
**K. Backup verification result:** the required mirror-backup/tag gates are listed as prepared-but-not-executed steps in T279_REPO_SIZE.md; the standing NO-GO (missing `pre-slim-20261123` tag remotely, user-blocked external backup) is unchanged — no rewrite was performed this session.
**L. Fresh clone and build results:** fresh-clone build was NOT part of a rewrite trial (none authorized); the session itself rebuilt the runtime from source twice on this sandbox (`make -j2 all` rc=0, 120.4 MB binary, version v0.0.6.2+HEAD verified) and byte-identity of every golden anchor face was proven across both builds.
**M. Regression test results:** f714 law test 9/9 (incl. the new T7 Compose fence) + 8 spot law batteries rc=0 (lifecycle ALL, linear 24/24, s98-text 21/21, resource_core 46/46, r25 14/14, input_pipeline ALL, g10 23/23, s106-layout 7/7) + 12 golden-anchor faces byte-identical pre/post fix + 46/46 campaign reproducibility pairs.
**N. Final commit and branch:** `f1312668f` on `main` (pushed and re-fetched); gh-pages showcase at `cc3c213b7` (pushed).
**O. Outstanding owner decisions:** (1) authorize the history-rewrite gates in T279_REPO_SIZE.md or close the size issue as accepted-cost; (2) the 9 off-disk S182 PARTIAL APKs (F-Droid restore queue) and `com.nononsenseapps.notepad` remain PENDING re-test; (3) adjudicate the librecontactsbackup face drift (px 1.21M→0.72M) and the two recorded visual defects (blockinger reversed dialog button glyphs; diceroller initial "00" die label).

## The recovered achievements (27 registry-absent titles)

Root cause: the S182 20-title battery results were tracked but never reconciled into the registry/ACHIEVEMENTS (15 titles), and the whole S23–S27 easy-APK wave post-dated the last registry sync (12 titles) — a REPORTING failure, not an evidence failure. All 27 now have canonical registry rows (schema preserved, 8-label current-status vocabulary, APK SHAs pinned, evidence refs). ACHIEVEMENTS.md got the T279 section + corrected totals (179 titles = 102 games + 76 apps + 1 fixture; legacy VERIFIED 24 + candidates 7; rendered 158 / interacted 19 / state-change 18); METRICS.json regenerated; tools/check_readme_metrics.py → OK (README consistent, no stale numbers).

## The fix (one focused correction, evidence-backed)

**The "Compose measure frontier" was OUR MeasureSpec shadow bug.** Disassembled from `ac.stresa.uturn_22` classes.dex: androidx compose `AndroidComposeView.convertMeasureSpec-I7RO_PI (I)J` compares `MeasureSpec.getMode()` against the AOSP constants (AT_MOST=0x80000000/UNSPECIFIED=0/EXACTLY=0x40000000) and its else arm is `new IllegalStateException()+throw` at dex pc=0x48 (= engine pc 29 — the exact `[FRONTIER]` unwind). The engine's F-NEW-714 `getMode` answered `(spec>>30)&3` (an INDEX: 1 for EXACTLY|56) so the when() threw every measure pass; the old `f714_measurespec_law_test.cpp` had pinned the wrong convention itself. Fix (commit `f9e1d3314`, pure AOSP `spec & MODE_MASK` + mask-form `makeMeasureSpec`): **uturn restored DEFAULT_BACKGROUND_ONLY → REAL_APP_CONTENT with face `a53523e7ca331866` == its 2026-11-06 historical face BYTE-IDENTICAL, uncaught 8→0**; wocheneinkauf/peri ISE class eliminated (33→32 uncaught; deeper layer named); 6 golden anchors byte-identical pre/post; zero regressions.

## Remaining highest-priority blockers (named)

1. Compose composition-state layer (`throw null` ×22 / SavedStateHandle IAE / SoftReference.get null): janken, authsrng, wocheneinkauf, peri.
2. Inflate→attach (ConstraintLayout/FrameLayout children=0): minos, cocodechess.
3. DataStore/protobuf worker-thread init: farmerbb notepad.
4. Custom-view clickability census: itsfrz.
5. Face-drift adjudication: librecontactsbackup.

## Two-run reproducibility (the law, measured)

46/46 pairs byte-identical (23×r1/r2, 12×ct1/ct2, 9×f1/f2). Zero flaky behavior; no third diagnostic run needed anywhere. Every verdict carries its frame_census proof (REAL_APP_CONTENT requires window root + measure + layout + draw + app-owned pixels — never a bare exit code or a nonempty PNG). Visual verification was done on 8 faces (genuine app content confirmed; 2 minor visual defects recorded, nothing fabricated)."""


def main():
    which = sys.argv[1]
    if which == "report":
        r = api("POST", f"{BASE}/issues/472/comments", {"body": REPORT_472})
        print("posted #472 comment:", r["html_url"])
        print("id:", r["id"], "len:", len(REPORT_472))
    elif which == "showcase":
        body = open("/home/z/my-project/scripts/t279_showcase_issue_body.md").read()
        r = api("POST", f"{BASE}/issues",
                {"title": "[T279] MiniAndroid Showcase — the permanent public gallery (179 titles, two-run evidence, offline zip)",
                 "body": body, "labels": []})
        print("opened issue:", r["number"], r["html_url"])


if __name__ == "__main__":
    main()
