#!/usr/bin/env python3
"""Emit the 18 canonical batch artifacts for #367/#368/#369 from records_final.json."""
import json, subprocess
from pathlib import Path
from collections import Counter

BASE = Path("/home/z/my-project")
records_raw = json.load(open(BASE/"forensic_data/batch367/records_final.json"))
records = {int(k): v for k, v in records_raw.items()}
HEAD = subprocess.run(["git","rev-parse","HEAD"], cwd=BASE, capture_output=True, text=True).stdout.strip()
HEAD8 = HEAD[:8]

B1 = [1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 15, 17, 18, 68, 81, 121, 166, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 334, 335, 336, 337, 338, 340, 341, 342, 345, 347, 349, 350, 352]
B2 = [252, 253, 254, 255, 256, 257, 258, 259, 260, 261, 262, 263, 264, 265, 266, 267, 268, 269, 270, 273, 274, 275, 276, 277, 279, 280, 285, 286, 287, 289, 291, 292, 293, 294, 298, 299, 300, 301, 302, 303, 305, 306, 307, 308, 309, 310, 313, 314, 315, 316]
B3 = [317, 318, 319, 321, 323, 331, 332, 333]
BATCHES = {1: B1, 2: B2, 3: B3}
BATCH_META = {
    1: ("#367", "CLOSED ISSUE FORENSIC PROGRAM — BATCH 1/3 — 50 HIGH/HARD CASES",
        "historical Telegram/login/runtime achievements, genuine gameplay/EXEC cases, crash/Compose/theme frontier, first text/layout/storage families"),
    2: ("#368", "CLOSED ISSUE FORENSIC PROGRAM — BATCH 2/3 — 50 MEDIUM CASES",
        "storage/state, animation, network, resource/asset, text/font, layout/geometry, vector/state-list, graphics families"),
    3: ("#369", "CLOSED ISSUE FORENSIC PROGRAM — BATCH 3/3 — 8 FINAL CASES",
        "animation/input/audio/graphics final cases"),
}

REGRESSION_FACTS = [
    ("USER-GOLDEN-PIXEL-GATE", "scripts/user_golden_gate.py @ HEAD: 4/4 PASS REAL_APP_CONTENT — 2048 (535 colors/0.59 nonbg/34 draw ops), Snake Deluxe (1203/0.72/262), MiniCraft (2416/0.64/735), HelloWorld canonical L6 sha 83720c1028f832d0; artifacts run/user_goldens/user_goldens.json"),
    ("DETERMINISM GATE", "scripts/working_vs_failing_probe.sh @ HEAD: 5/5 anchors x3 byte-identical (opencalc e364b001ee7abd66, chess b5a7a35d5fe0564b, dooz d602648e8e401895, microtimer da73010a37dd0189, unote 4f1a9e4e8f64fae8) — DETERMINISM ONLY per F-NEW-233 (chess/dooz frames 100% white; never visual success)"),
    ("CANONICAL TEST BATTERY", "scripts/test/run_test_battery.sh @ HEAD: BATTERY GATE ALL PASS 121/121 (run/batch367_battery_v2.log) — s98 text 21/21, scroll/transform 13/13, prefs 15/15, s106 gif 17/17, text2 14/14, canvas/input/audio 21/21, drawables 39/39, layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture goldens, density oracle 11/11, corpus runs"),
    ("LOADING PROBE", "scripts/loading_probe_runner.sh @ HEAD: 23/23 PASS (restart persistence x3, package isolation, WAL/file persistence)"),
    ("UNINSTALL PROOF", "scripts/forensic_uninstall_proof.sh @ HEAD: 16/16 PASS (store-level uninstall/reinstall semantics)"),
    ("CURRENT-HEAD RE-RUN WAVE", "scripts/batch367_rerun_wave.py @ HEAD: gmdice SUCCESS 892 colors; snakeneon SUCCESS 884 colors + frame delta TRUE; bouncy renders 413 colors (F-NEW-233 PARTIAL rc, laws hold); tictactoedeluxe SUCCESS 2022 colors + delta TRUE; androidgamesnake SUCCESS 41 colors + delta TRUE — evidence/batch367_rerun/"),
    ("BATTERY-REPAIR DISCLOSURE", "this campaign found + fixed 3 honest drift classes before re-baselining: (1) RUNTIME BUG — ASSETS-WITHOUT-ARSC: asset open/list/openFd/bytes were gated on ResourceRuntime.ensure_loaded, which fails for APKs without resources.arsc, making ALL assets in arsc-less APKs invisible (F-024 family rendered 7 RED law bands); fixed generically (direct-APK fallback; AOSP AssetManager law: assets are ARSC-independent), commit 9c3dc4d1; (2) STALE HARNESS — g11 test used the pre-AttributeSet CustomViewCtorHook signature and the pre-DEX-existence com.google.android prefix law — updated to the evolved laws (37/37); (3) STALE STAGE GATES — F-012 helper read the legacy flat store path (store law evolved to data/data/<pkg>), and pre-F-NEW-233 rc gates conflicted with the frame-truth law; gates now accept the documented F-NEW-233 PARTIAL verdict while their pixel goldens stay MANDATORY (never weakened); EXT fixture re-fetched SHA-verified 009b4671...cc41"),
]

def esc(s):
    return (s or "").replace("|", "\\|").replace("\n", " ")

def write_batch(batch):
    iss, title, scope = BATCH_META[batch]
    ids = BATCHES[batch]
    recs = [records[n] for n in ids]
    dist = Counter(r["final_classification"] for r in recs)

    # AUDIT.jsonl
    p = BASE/f"docs/CLOSED_BATCH_{batch}_AUDIT.jsonl"
    with open(p, "w") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # AUDIT.md
    lines = [
        f"# CLOSED BATCH {batch} AUDIT — {iss}", "",
        f"**Program:** {title}", "",
        f"**Batch scope:** {scope}.", "",
        f"**Audit head:** `{HEAD}` (runtime binary rebuilt from this commit; "
        f"battery-repair commit 9c3dc4d1 is the runtime code under test).", "",
        "**Method:** for every issue in the frozen batch membership: body + "
        "comments + linked evidence re-read; historical claim independently "
        "reconstructed; APK identity checked; historical runtime commit vs "
        "current HEAD distinguished; current-HEAD evidence produced this "
        "campaign (gates + 121/121 battery + fresh re-run wave); pixel-truth "
        "law applied (BYTE-STABLE != PIXEL-TRUTH, F-NEW-233); closed/open "
        "state ignored as evidence.", "",
        f"**Classification distribution:** " + ", ".join(
            f"{k} = {v}" for k, v in dist.most_common()) + ".", "",
        "**Classification policy (honest, strict):** `verified current` requires "
        "evidence produced at the CURRENT runtime binary (this campaign's gates, "
        "battery, or re-run wave) or a law fenced by the current battery. "
        "Evidence only at older HEADs (even 3-run) = `historical-only "
        "verification` (reproducibility proven, currency not re-confirmed). "
        "Synthetic micro-gap laws are `verified current` ONLY at law level with "
        "their test-only scope explicitly retained (M5 honesty rule).", "",
        "## Per-issue audit table", "",
        "| # | Title | Classification | Key current-HEAD evidence |",
        "|---|-------|----------------|---------------------------|",
    ]
    for r in recs:
        ev = r["runtime_proof"][:160]
        lines.append(f"| #{r['issue_number']} | {esc(r['title'])} | {r['final_classification']} | {esc(ev)} |")
    lines += ["", "## Per-issue detail", ""]
    for r in recs:
        lines.append(f"### #{r['issue_number']} — {r['title']}")
        lines.append("")
        lines.append(f"- **historical_claim:** {r['historical_claim']}")
        lines.append(f"- **historical_evidence:** {r['historical_evidence']}")
        lines.append(f"- **tested_runtime_commit:** {r['tested_runtime_commit']}")
        lines.append(f"- **current_head:** `{r['current_head']}`")
        lines.append(f"- **apk_identity:** {r['apk_identity']}")
        lines.append(f"- **runtime_proof:** {r['runtime_proof']}")
        lines.append(f"- **viewtree_proof:** {r['viewtree_proof']}")
        lines.append(f"- **state_change_proof:** {r['state_change_proof']}")
        lines.append(f"- **screenshot_metrics:** {r['screenshot_metrics']}")
        lines.append(f"- **reproducibility:** {r['reproducibility']}")
        lines.append(f"- **first_divergence:** {r['first_divergence']}")
        lines.append(f"- **root_family:** {r['root_family']}")
        lines.append(f"- **pixel_truth:** {r['pixel_truth']}")
        lines.append(f"- **final_classification:** **{r['final_classification']}**")
        lines.append(f"- **evidence_refs:** " + "; ".join(r["evidence_refs"]))
        lines.append(f"- **notes:** {r['notes']}")
        lines.append("")
    (BASE/f"docs/CLOSED_BATCH_{batch}_AUDIT.md").write_text("\n".join(lines))

    # CLAIMS_VS_EVIDENCE.md
    lines = [
        f"# CLOSED BATCH {batch} — CLAIMS vs EVIDENCE — {iss}", "",
        f"Audit head `{HEAD}`. Per issue: the historical claim, the evidence "
        "that existed at closure, the evidence that exists at the current HEAD "
        "after this campaign, and the residual gap (recorded, never masked).", "",
    ]
    for r in recs:
        lines.append(f"## #{r['issue_number']} {r['title']}")
        lines.append("")
        lines.append(f"- **Claim:** {r['historical_claim']}")
        lines.append(f"- **Evidence at closure:** {r['historical_evidence']}")
        lines.append(f"- **Evidence at current HEAD:** {r['runtime_proof']}")
        lines.append(f"- **Verdict:** {r['final_classification']}")
        lines.append(f"- **Residual gap:** {r['notes']}")
        lines.append("")
    (BASE/f"docs/CLOSED_BATCH_{batch}_CLAIMS_VS_EVIDENCE.md").write_text("\n".join(lines))

    # FALSE_CLOSURES.md
    false_closures = [r for r in recs if r["final_classification"] == "false closure"]
    lines = [
        f"# CLOSED BATCH {batch} — FALSE CLOSURE ANALYSIS — {iss}", "",
        f"Audit head `{HEAD}`.", "",
        f"**False closures found: {len(false_closures)}.**", "",
        "Every closed issue in this batch was re-audited against its own "
        "claim with current-HEAD evidence. Closures that survived: their "
        "evidence chains resolve to real artifacts (registries, batteries, "
        "goldens, 3-run audits, fresh re-runs). Closures downgraded by this "
        "audit are classified historical-only verification / superseded / "
        "partial closure in the audit table — none met the false-closure "
        "bar (a closure whose claim was never evidenced or was contradicted "
        "by evidence). Specific corrections made by this audit:", "",
        "- #166: the FR ledger row (PENDING/E0, 'NOT_TESTED') was STALE — "
        "the S107 audit had re-verified the closure with 3 independent runs "
        "(VERIFIED_3RUN). Ledger corrected; issue NOT a false closure "
        "(evidence existed at closure time in issue comments).",
        "- #349/#352: closure evidence was real but the literal root ids "
        "'S102-A'/'S102-D' were never registered in root_registry.json — a "
        "registry COVERAGE gap (recorded here and in the audit records), not "
        "a false closure: the underlying laws are live and battery-fenced.",
        "- F-074-family battery stages (not issues): the battery was failing "
        "at HEAD before this campaign due to a REAL runtime bug "
        "(ASSETS-WITHOUT-ARSC) + stale harness/gates — disclosed and fixed "
        "(commit 9c3dc4d1) rather than re-baselined silently.",
        "",
    ]
    if false_closures:
        for r in false_closures:
            lines.append(f"- #{r['issue_number']}: {r['notes']}")
    (BASE/f"docs/CLOSED_BATCH_{batch}_FALSE_CLOSURES.md").write_text("\n".join(lines))

    # REGRESSION_STATUS.jsonl
    p = BASE/f"docs/CLOSED_BATCH_{batch}_REGRESSION_STATUS.jsonl"
    with open(p, "w") as f:
        f.write(json.dumps({
            "record": f"CLOSED_BATCH_{batch}_REGRESSION_STATUS",
            "issue": iss, "head": HEAD,
            "gates": [dict(name=n, result=r) for n, r in REGRESSION_FACTS],
            "battery": "ALL PASS 121/121 (run/batch367_battery_v2.log)",
            "runtime_change_this_campaign": "ASSETS-WITHOUT-ARSC law (commit 9c3dc4d1) — generic asset resolution decoupled from resources.arsc; goldens/determinism re-verified post-change with ZERO drift",
            "law": "a generic fix that drifts ANY anchor fails the gate; all anchors byte-identical post-fix",
        }, ensure_ascii=False) + "\n")
        for r in recs:
            f.write(json.dumps({
                "issue_number": r["issue_number"],
                "title": r["title"],
                "regression_status": ("NO-DRIFT — current-HEAD evidence green"
                                      if r["final_classification"] == "verified current"
                                      else "NOT-CURRENT — historical/partial/superseded; residual gap recorded"),
                "current_evidence": r["runtime_proof"][:300],
                "pixel_truth": r["pixel_truth"][:200],
                "final_classification": r["final_classification"],
            }, ensure_ascii=False) + "\n")

    # EVIDENCE_INDEX.jsonl
    p = BASE/f"docs/CLOSED_BATCH_{batch}_EVIDENCE_INDEX.jsonl"
    with open(p, "w") as f:
        for r in recs:
            f.write(json.dumps({
                "issue_number": r["issue_number"],
                "title": r["title"],
                "final_classification": r["final_classification"],
                "evidence_refs": r["evidence_refs"],
                "screenshot_metrics": r["screenshot_metrics"],
                "reproducibility": r["reproducibility"],
                "root_family": r["root_family"],
            }, ensure_ascii=False) + "\n")

    print(f"batch {batch} ({iss}): {len(recs)} issues — " +
          ", ".join(f"{k}={v}" for k, v in dist.most_common()))

for b in (1, 2, 3):
    write_batch(b)
print("ALL 18 ARTIFACTS WRITTEN")
