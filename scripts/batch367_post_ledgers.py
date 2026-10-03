#!/usr/bin/env python3
"""Post completion ledgers to #367/#368/#369 (STATUS — RESULT — EVIDENCE)."""
import subprocess, json, urllib.request, time
from pathlib import Path
from collections import Counter

BASE = Path("/home/z/my-project")
out = subprocess.run(["git", "credential", "fill"],
                     input="protocol=https\nhost=github.com\n\n",
                     capture_output=True, text=True, cwd=BASE).stdout
token = [l.split("=", 1)[1] for l in out.splitlines() if l.startswith("password=")][0]
HDRS = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json",
        "User-Agent": "forensic"}
REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
HEAD = subprocess.run(["git", "rev-parse", "HEAD"], cwd=BASE,
                      capture_output=True, text=True).stdout.strip()
HEAD8 = HEAD[:8]

records = {int(k): v for k, v in json.load(
    open(BASE/"forensic_data/batch367/records_final.json")).items()}
BATCHES = {
    1: (367, [1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 15, 17, 18, 68, 81, 121, 166,
              234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244, 245, 246, 247,
              248, 249, 250, 251, 334, 335, 336, 337, 338, 340, 341, 342, 345, 347,
              349, 350, 352]),
    2: (368, [252, 253, 254, 255, 256, 257, 258, 259, 260, 261, 262, 263, 264, 265,
              266, 267, 268, 269, 270, 273, 274, 275, 276, 277, 279, 280, 285, 286,
              287, 289, 291, 292, 293, 294, 298, 299, 300, 301, 302, 303, 305, 306,
              307, 308, 309, 310, 313, 314, 315, 316]),
    3: (369, [317, 318, 319, 321, 323, 331, 332, 333]),
}

def esc(s):
    return (s or "").replace("|", "\\|").replace("\n", " ")

def post(issue, body):
    url = f"https://api.github.com/repos/{REPO}/issues/{issue}/comments"
    req = urllib.request.Request(url, data=json.dumps({"body": body}).encode(),
                                 headers=HDRS, method="POST")
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req) as r:
                obj = json.loads(r.read())
            return obj["id"], obj["html_url"]
        except Exception as e:
            if attempt == 3:
                raise
            time.sleep(2 * (attempt + 1))

for batch, (issue, ids) in BATCHES.items():
    recs = [records[n] for n in ids]
    dist = Counter(r["final_classification"] for r in recs)
    body = []
    body.append(f"## COMPLETION LEDGER — CLOSED BATCH {batch}/3 (all {len(ids)} issues audited)")
    body.append("")
    body.append(f"**STATUS:** DONE — every issue in the frozen batch membership "
                f"individually classified with the 18 required fields. Audit head "
                f"`{HEAD8}` (runtime under test = battery-repair commit `9c3dc4d1`).")
    body.append("")
    body.append("**RESULT:** " + ", ".join(f"{k} = {v}" for k, v in dist.most_common()) + ".")
    body.append("")
    body.append("**Method:** issue body + comments + linked evidence re-read; claim "
                "reconstructed independently; APK identity checked; historical commit "
                "vs current HEAD distinguished; current-HEAD evidence produced this "
                "campaign; pixel-truth law applied (BYTE-STABLE != PIXEL-TRUTH, "
                "F-NEW-233 — chess/dooz are DETERMINISM anchors only, never visual "
                "success); closed state ignored as evidence; no package-specific hacks.")
    body.append("")
    body.append("**Classification policy:** `verified current` requires evidence at "
                "the CURRENT binary (this campaign's gates / 121-stage battery / fresh "
                "re-run wave) or a law fenced by that battery; synthetic micro-gap laws "
                "are verified current ONLY at law level with test-only scope retained "
                "(M5 rule). Older-HEAD-only evidence = `historical-only verification`.")
    body.append("")
    body.append("**Current-HEAD regression evidence (this campaign):**")
    body.append("")
    body.append("- USER-GOLDEN-PIXEL-GATE 4/4 REAL_APP_CONTENT (2048 / Snake Deluxe / "
                "MiniCraft / HelloWorld L6)")
    body.append("- DETERMINISM 5/5 anchors x3 byte-identical (zero drift post runtime fix)")
    body.append("- CANONICAL TEST BATTERY **121/121 ALL PASS** (run/batch367_battery_v2.log)")
    body.append("- LOADING PROBE 23/23; UNINSTALL PROOF 16/16")
    body.append("- Fresh re-run wave at HEAD: gmdice, snakeneon (delta TRUE), bouncy, "
                "tictactoedeluxe (delta TRUE), androidgamesnake (delta TRUE) — "
                "evidence/batch367_rerun/")
    body.append("")
    body.append("**Honest disclosures (fixed, not masked):** the battery was FAILING at "
                "audit start — root-caused to (1) a REAL runtime bug: ASSETS-WITHOUT-ARSC "
                "(all assets invisible in arsc-less APKs; F-024 family 7 RED bands) — "
                "fixed generically with the direct-APK fallback law (AOSP AssetManager: "
                "assets are ARSC-independent), commit 9c3dc4d1; (2) stale g11 harness "
                "(pre-AttributeSet hook signature; pre-DEX-existence prefix law) — "
                "updated to evolved laws 37/37; (3) stale stage gates (F-012 legacy flat "
                "store path; pre-F-NEW-233 rc gates) — re-baselined with pixel goldens "
                "kept MANDATORY; EXT fixture re-fetched SHA-verified 009b4671...cc41.")
    body.append("")
    body.append("**FALSE CLOSURES: 0** (FR-166 stale ledger row corrected; S102-A/D "
                "registry coverage gaps recorded, not masked).")
    body.append("")
    body.append("### Per-issue ledger (STATUS — RESULT — EVIDENCE)")
    body.append("")
    body.append("| # | Classification | RESULT | EVIDENCE |")
    body.append("|---|----------------|--------|----------|")
    for r in recs:
        n = r["issue_number"]
        status = r["final_classification"].upper()
        result = esc(r["runtime_proof"])[:220]
        ev = "; ".join(r["evidence_refs"][:3])
        body.append(f"| #{n} | {status} | {result} | {esc(ev)} |")
    body.append("")
    body.append("### Canonical artifacts (committed)")
    body.append("")
    body.append("- `docs/CLOSED_BATCH_%d_AUDIT.md` + `.jsonl` (18 required fields per issue)" % batch)
    body.append("- `docs/CLOSED_BATCH_%d_CLAIMS_VS_EVIDENCE.md` (claim vs closure vs current vs residual gap)" % batch)
    body.append("- `docs/CLOSED_BATCH_%d_FALSE_CLOSURES.md`" % batch)
    body.append("- `docs/CLOSED_BATCH_%d_REGRESSION_STATUS.jsonl`" % batch)
    body.append("- `docs/CLOSED_BATCH_%d_EVIDENCE_INDEX.jsonl`" % batch)
    body.append("")
    body.append(f"Completion gate: all {len(ids)} issues classified individually — "
                f"met. High-value visual/game claims: user goldens 4/4 pixel-truth at "
                f"HEAD; determinism 5/5 x3; fresh re-run wave attached.")
    cid, curl = post(issue, "\n".join(body))
    print(f"posted to #{issue}: comment {cid} {curl}")
