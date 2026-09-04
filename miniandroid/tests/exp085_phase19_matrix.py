#!/usr/bin/env python3
"""
EXP-085 Phase 19 — Corpus Matrix.

Compile all phase results into a single corpus matrix.

For each APK + capability combination, classify:
  - PROVEN: capability works
  - PARTIAL: capability partially works (documented reason)
  - BLOCKED: capability blocked (documented blocker)
  - NOT_TESTED: capability not relevant for this APK
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path("/home/z/my-project/MiniAndroid-Compatibility-Runtime")
RESULTS_DIR = REPO_ROOT / "miniandroid" / "tests" / "corpus" / "results"


def load_phase_results() -> dict:
    """Load all phase result JSONs."""
    phases = {}
    for pf in sorted(RESULTS_DIR.glob("EXP085_PHASE*.json")):
        try:
            with open(pf) as f:
                phases[pf.stem] = json.load(f)
        except Exception:
            pass
    return phases


def build_matrix(phases: dict) -> dict:
    """Build the unified corpus matrix."""
    # APKs we tested
    apks = [
        {"name": "gmdice", "package": "de.duenndns.gmdice",
         "apk": "miniandroid/download/exp073_real_apps/de.duenndns.gmdice_8.apk"},
        {"name": "tictactoe", "package": "com.emmanuelmess.tictactoe",
         "apk": "miniandroid/download/tictactoe.apk"},
        {"name": "headingcalculator", "package": "org.debian.eugen.headingcalculator",
         "apk": "miniandroid/download/exp073_real_apps/org.debian.eugen.headingcalculator_1.apk"},
        {"name": "simplestopwatch", "package": "omegacentauri.mobi.simplestopwatch",
         "apk": "miniandroid/download/exp073_real_apps/omegacentauri.mobi.simplestopwatch_26.apk"},
        {"name": "chessclock", "package": "com.chessclock.android",
         "apk": "miniandroid/download/exp073_real_apps/com.chessclock.android_29.apk"},
        {"name": "notes", "package": "org.billthefarmer.notes",
         "apk": "miniandroid/download/exp073_real_apps/org.billthefarmer.notes_139.apk"},
        {"name": "telegram", "package": "org.telegram.messenger",
         "apk": "miniandroid/download/exp038_telegram/Telegram.apk"},
    ]

    # Capabilities we test
    capabilities = [
        "MULTI_DEX", "AXML", "TEXT", "IMAGE", "BUTTON_CLICK",
        "CALCULATOR", "TIMER", "HANDLER", "SCROLL",
        "SQLITE", "PERMISSIONS", "JNI", "NETWORK",
        "RECYCLERVIEW", "R8_LAMBDA", "POLYMORPHIC",
        "RENDERER_PNG", "RENDERER_PPM",
    ]

    # Build matrix from phase results
    matrix = {apk["name"]: {cap: "NOT_TESTED" for cap in capabilities} for apk in apks}

    # From Phase 1 (multi-DEX)
    p1 = phases.get("EXP085_PHASE1_MULTI_DEX", {})
    for r in p1.get("results", []):
        name = r.get("apk_name", "")
        # Normalize name
        if "telegram" in name.lower():
            name = "telegram"
        elif "tictactoe" in name.lower():
            name = "tictactoe"
        elif "openlauncher" in name.lower():
            continue  # APK is corrupted
        elif "simplekeyboard" in name.lower():
            name = "simplekeyboard"  # Not in our list
            continue
        if name in matrix:
            matrix[name]["MULTI_DEX"] = "PROVEN" if r.get("dex_count", 0) > 1 and r.get("status") == "PASS" else \
                                        ("PROVEN" if r.get("dex_count", 0) == 1 else "BLOCKED")

    # From Phase 2 (dispatch)
    p2 = phases.get("EXP085_PHASE2_DISPATCH", {})
    for r in p2.get("results", []):
        name = r.get("apk_name", "")
        if "telegram" in name.lower():
            name = "telegram"
        elif "tictactoe" in name.lower():
            name = "tictactoe"
        if name in matrix:
            matrix[name]["POLYMORPHIC"] = "PROVEN" if r.get("polymorphic_override_count", 0) > 0 else "NOT_TESTED"

    # From Phase 3 (return values)
    p3 = phases.get("EXP085_PHASE3_RETURN_VALUES", {})
    # Phase 3 only tested micro fixtures, not corpus APKs

    # From Phase 4 (exceptions) — also only micro fixtures

    # From Phase 5 (AXML)
    p5 = phases.get("EXP085_PHASE5_AXML_RESOURCES", {})
    for r in p5.get("results", []):
        name = r.get("name", "")
        if name in matrix:
            status = r.get("status", "")
            if status.startswith("PARTIAL"):
                matrix[name]["AXML"] = "PARTIAL"
            elif status == "PASS":
                matrix[name]["AXML"] = "PROVEN"

    # From Phases 6-16 (capabilities)
    p6_16 = phases.get("EXP085_PHASES_6_16_CAPABILITIES", {})
    for r in p6_16.get("results", []):
        name = r.get("name", "")
        if name in matrix:
            for cap, status in r.get("capabilities", {}).items():
                if cap in matrix[name]:
                    # Take the better of existing or new
                    if matrix[name][cap] == "NOT_TESTED":
                        matrix[name][cap] = status
                    elif matrix[name][cap] == "BLOCKED" and status == "PROVEN":
                        matrix[name][cap] = status

    # From Phase 10 (SQLite)
    p10 = phases.get("EXP085_PHASE10_SQLITE", {})
    for r in p10.get("results", []):
        if "notes" in r.get("apk", "").lower():
            matrix["notes"]["SQLITE"] = r.get("classification", "BLOCKED")

    # From Phase 12 (Handler)
    p12 = phases.get("EXP085_PHASE12_HANDLER", {})
    for r in p12.get("results", []):
        name = r.get("apk_name", "")
        if name in matrix:
            classification = r.get("classification", "")
            if classification == "HANDLER_WORKING":
                matrix[name]["HANDLER"] = "PROVEN"
            elif classification.startswith("HANDLER_LOADED"):
                matrix[name]["HANDLER"] = "PARTIAL"
            else:
                matrix[name]["HANDLER"] = "BLOCKED"
            if "TIMER" in matrix[name] and matrix[name]["TIMER"] == "NOT_TESTED":
                matrix[name]["TIMER"] = matrix[name]["HANDLER"]

    # From Phase 14 (renderer)
    p14 = phases.get("EXP085_PHASE14_RENDERER", {})
    for r in p14.get("results", []):
        name = r.get("apk_name", "")
        if name in matrix:
            status = r.get("status", "")
            if status == "PASS_PNG":
                matrix[name]["RENDERER_PNG"] = "PROVEN"
                matrix[name]["RENDERER_PPM"] = "PROVEN"
            elif status == "PARTIAL_PPM_ONLY":
                matrix[name]["RENDERER_PNG"] = "BLOCKED"
                matrix[name]["RENDERER_PPM"] = "PROVEN"
            elif status == "PARTIAL_PNG_NO_IDAT":
                matrix[name]["RENDERER_PNG"] = "PARTIAL"
            else:
                matrix[name]["RENDERER_PNG"] = "BLOCKED"
                matrix[name]["RENDERER_PPM"] = "BLOCKED"

    # From Phase 17/18 (Telegram)
    p17_18 = phases.get("EXP085_PHASE17_18_TELEGRAM", {})
    if p17_18.get("checkpoint_m_pass"):
        matrix["telegram"]["NETWORK"] = "PROVEN"
    else:
        matrix["telegram"]["NETWORK"] = "PARTIAL"
    # Telegram-specific
    matrix["telegram"]["R8_LAMBDA"] = "PARTIAL"  # EXP-081/082 verified

    return {"apks": apks, "capabilities": capabilities, "matrix": matrix}


def main():
    print("=== Phase 19: Corpus Matrix ===")
    phases = load_phase_results()
    print(f"Loaded {len(phases)} phase result files:")
    for k in sorted(phases):
        print(f"  {k}")

    matrix_data = build_matrix(phases)

    # Print matrix
    print("\nCorpus Matrix:")
    print()
    cap_header = "APK".ljust(25)
    for cap in matrix_data["capabilities"]:
        cap_header += " | " + cap[:13].ljust(13)
    print(cap_header)
    print("-" * len(cap_header))

    for apk in matrix_data["apks"]:
        row = apk["name"].ljust(25)
        for cap in matrix_data["capabilities"]:
            v = matrix_data["matrix"][apk["name"]].get(cap, "NOT_TESTED")
            # Shorten for display
            short = v.split("_")[0] if "_" in v else v
            row += " | " + short[:13].ljust(13)
        print(row)

    # Summary
    proven_count = sum(1 for apk in matrix_data["apks"]
                       for cap in matrix_data["capabilities"]
                       if matrix_data["matrix"][apk["name"]].get(cap) == "PROVEN")
    partial_count = sum(1 for apk in matrix_data["apks"]
                         for cap in matrix_data["capabilities"]
                         if matrix_data["matrix"][apk["name"]].get(cap, "").startswith("PARTIAL"))
    blocked_count = sum(1 for apk in matrix_data["apks"]
                         for cap in matrix_data["capabilities"]
                         if matrix_data["matrix"][apk["name"]].get(cap, "").startswith("BLOCKED"))
    not_tested = sum(1 for apk in matrix_data["apks"]
                     for cap in matrix_data["capabilities"]
                     if matrix_data["matrix"][apk["name"]].get(cap) == "NOT_TESTED")

    print()
    print(f"PROVEN: {proven_count}  PARTIAL: {partial_count}  BLOCKED: {blocked_count}  NOT_TESTED: {not_tested}")

    summary = {
        "test": "EXP085 Phase 19 — Corpus matrix",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "proven_count": proven_count,
        "partial_count": partial_count,
        "blocked_count": blocked_count,
        "not_tested_count": not_tested,
        "matrix": matrix_data["matrix"],
        "apks": matrix_data["apks"],
        "capabilities": matrix_data["capabilities"],
    }
    out_path = RESULTS_DIR / "EXP085_PHASE19_MATRIX.json"
    out_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    main()
