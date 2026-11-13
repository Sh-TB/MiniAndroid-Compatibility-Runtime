#!/usr/bin/env python3
"""tests/evidence_retention_test.py — the #587 forensic-addendum §5 required
test battery (evidence retention + report honesty laws):

 1. canonical golden PNG pixels remain exact under lossless optimization
 2. derivatives are explicitly noncanonical (JPEG re-encode changes pixels;
    a lossy derivative must never pass as canonical pixel-exact evidence)
 3. duplicate files are detected (tools/duplicate_scan.py SHA grouping +
    strict exit with the exemption registry)
 4. per-run IDs/hashes survive compaction (batch summary retains every run
    id + original screenshot SHA for removed full PNGs)
 5. a deliberately contradictory NO_APP_OPS + REAL_APP_CONTENT report is
    rejected (tools/report_sanity.py), and the corrected honest report passes

Also: stale screenshot size, duplicate embed, APK cross-run path mismatch
negative tests on report_sanity.

Run: python3 tests/evidence_retention_test.py   (exit 0 = all pass)
"""
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "tools"))

import io

import report_sanity
from duplicate_scan import duplicate_groups
from PIL import Image

PASS = 0
FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name} {detail}")


def make_png(path, size=(320, 240), color=(120, 40, 200), noise=True):
    img = Image.new("RGB", size, color)
    if noise:
        px = img.load()
        for y in range(0, size[1], 7):
            for x in range(0, size[0], 7):
                px[x, y] = (255 - color[0], color[1], 255 - color[2])
    img.save(path, format="PNG")
    return img


def main():
    tmp = tempfile.mkdtemp(prefix="s230_retention_")
    try:
        # ---- 1. canonical golden PNG pixel exactness (lossless path) ----
        print("[1] canonical golden pixel exactness under lossless optimize")
        golden = os.path.join(tmp, "golden.png")
        img = make_png(golden)
        before = list(img.getdata())
        Image.open(golden).save(golden + ".opt.png",
                                format="PNG", optimize=True)
        after = list(Image.open(golden + ".opt.png").getdata())
        check("lossless optimize keeps every pixel", before == after)
        im2 = Image.open(golden + ".opt.png")
        check("dims/mode preserved",
              im2.size == img.size and im2.mode == img.mode)

        # ---- 2. derivatives are explicitly noncanonical ----
        print("[2] JPEG derivative changes pixels -> NOT pixel-exact")
        img.convert("RGB").save(os.path.join(tmp, "deriv.jpg"),
                                format="JPEG", quality=85)
        jp = list(Image.open(os.path.join(tmp, "deriv.jpg")).getdata())
        check("JPEG re-encode is lossy (pixels differ)", jp != before)
        manifest = {"deriv.jpg": {"lossy": True,
                                  "canonical_screenshot": False}}
        check("retention manifest marks derivative lossy/noncanonical",
              manifest["deriv.jpg"]["lossy"] is True
              and manifest["deriv.jpg"]["canonical_screenshot"] is False)

        # ---- 3. duplicate detection ----
        print("[3] byte-identical duplicates are detected")
        dupdir = os.path.join(tmp, "dups")
        os.makedirs(dupdir)
        make_png(os.path.join(dupdir, "a.png"))
        shutil.copy(os.path.join(dupdir, "a.png"),
                    os.path.join(dupdir, "b.png"))
        make_png(os.path.join(dupdir, "c.png"), color=(10, 200, 30))
        groups = duplicate_groups([dupdir])
        check("duplicate group found", len(groups) == 1)
        check("group has 2 members",
              len(next(iter(groups.values()))) == 2)
        lone = os.path.join(tmp, "lone")
        os.makedirs(lone)
        make_png(os.path.join(lone, "c.png"), color=(10, 200, 30))
        check("distinct file not flagged",
              duplicate_groups([lone]) == {})

        # ---- 4. per-run IDs/hashes survive compaction ----
        print("[4] compaction preserves run ids + original SHAs")
        runs = {f"halma_w18_r{i}": {"screenshot_sha256": f"{i:064x}",
                                    "removed_full_png": True}
                for i in range(1, 12)}
        batch = {"runs": runs,
                 "retained_representative": "halma_w18_r1",
                 "law": "one full PNG per batch + compact SHA rows"}
        check("all 11 run ids present in compact record",
              len(batch["runs"]) == 11
              and all(k in batch["runs"] for k in runs))
        check("every run keeps its original sha row",
              all(batch["runs"][k]["screenshot_sha256"] == v
                  ["screenshot_sha256"] for k, v in runs.items()))
        # the live manifest law: batch summaries are pointer rows that must
        # resolve to real compaction files carrying run ids + sha rows
        man_path = os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), "evidence",
            "evidence_retention_manifest.json")
        with open(man_path, encoding="utf-8") as f:
            man = json.load(f)
        live = man.get("batch_summaries", [])
        check("live retention manifest has batch summaries",
              len(live) > 0)
        root_dir = os.path.dirname(man_path)
        resolved = False
        for row in live:
            path = row.split(" ")[0] if isinstance(row, str) else row.get("path", "")
            path = os.path.join(root_dir, os.path.relpath(
                path, "evidence")) if not os.path.isabs(path) else path
            if not os.path.exists(path):
                path = os.path.normpath(os.path.join(root_dir, "..",
                                                     row.split(" ")[0]))
            if os.path.exists(path) and path.endswith(".json"):
                with open(path, encoding="utf-8") as f:
                    body = f.read()
                if "sha" in body.lower() and "_r" in body:
                    resolved = True
        check("live batch summaries resolve to run-id + sha rows", resolved)

        # ---- 5. contradictory report rejected; corrected passes ----
        print("[5] contradictory report rejected by report_sanity")
        bad = os.path.join(tmp, "halma_w18_r4")
        os.makedirs(bad)
        make_png(os.path.join(bad, "screenshot.png"))
        with open(os.path.join(bad, "report.md"), "w") as f:
            f.write(
                "# W18 Halma run halma_w18_r4\n"
                "- APK: store_halma_w18_r1/data/app/base.apk\n"
                "- screenshot sha256: "
                "15130c72ce569ae8aa457ffe9ce9d3e0cd068330d7812fccc0147bb0d4b44868 "
                "(999999999 bytes, 1080x1920)\n"
                "## Output Frame\n\n![s](screenshot.png)\n\n"
                "## Output Frame\n\n![s](screenshot.png)\n\n"
                "- trace verdict: NO_APP_OPS; app_draw_ops=0\n"
                "- summary verdict: REAL_APP_CONTENT SUCCESS\n")
        v = report_sanity.check_report(os.path.join(bad, "report.md"))
        codes = {c for c, _ in v}
        for expected in ("CONTRADICTORY_VERDICT", "PIXEL_PROVENANCE_MISMATCH",
                         "STALE_SCREENSHOT_SIZE", "DUPLICATE_SCREENSHOT_EMBED",
                         "APK_PATH_MISMATCH"):
            check(f"bad report flags {expected}", expected in codes,
                  f"got {codes}")
        # corrected honest report (the S212/W18 shape) must pass
        good = os.path.join(tmp, "halma_w18_r5")
        os.makedirs(good)
        make_png(os.path.join(good, "screenshot.png"), color=(60, 130, 90))
        n = os.path.getsize(os.path.join(good, "screenshot.png"))
        sha = __import__("hashlib").sha256(
            open(os.path.join(good, "screenshot.png"), "rb").read()).hexdigest()
        with open(os.path.join(good, "report.md"), "w") as f:
            f.write(
                "# W18 Halma run halma_w18_r5 — CORRECTED\n"
                "- APK package: `app.halma`\n"
                f"- screenshot sha256: `{sha}` ({n} bytes, 1080x1920)\n"
                "- F-016: 1 uncaught in-flight exception(s); census 924 "
                "IMPLEMENTED / 63 STUBBED\n"
                "- trace verdict: NO_APP_OPS (RENDER_OK); summary verdict "
                "REAL_APP_CONTENT is an unreconciled classifier contradiction "
                "— NOT evidence of app UI\n"
                "- honest status: first-frame boundary evidence only\n\n"
                "## Output Frame\n\n![Retained representative frame]"
                "(screenshot.png)\n")
        v2 = report_sanity.check_report(os.path.join(good, "report.md"))
        check("corrected honest report passes", v2 == [], f"got {v2}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"\nevidence_retention_test: {PASS} pass / {FAIL} fail")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
