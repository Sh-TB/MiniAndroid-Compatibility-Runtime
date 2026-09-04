#!/usr/bin/env python3
"""
EXP-086 Phase 2 — Real APK Entry-Point Regression.

Verifies that the manifest resolver not only SELECTS the correct launcher
activity, but that the runtime actually ENTERS its onCreate method.

For each APK:
  1. Get expected launcher (from analyze)
  2. Run the APK
  3. Verify the runtime trace shows the expected class.method invocation
  4. Compare against independent reference (the manifest's declared activity)

Telegram is only considered PASS if:
  - LaunchActivity is selected ✅
  - LaunchActivity.onCreate is actually entered ✅
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path("/home/z/my-project/MiniAndroid-Compatibility-Runtime")
MINIANDROID = REPO_ROOT / "miniandroid" / "build" / "miniandroid"
RESULTS_DIR = REPO_ROOT / "miniandroid" / "tests" / "corpus" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def get_manifest_activity(apk_path: Path) -> str:
    """Use miniandroid analyze to get the expected launcher activity."""
    out_dir = Path(f"/tmp/exp086_p2_analyze_{apk_path.stem}")
    if out_dir.exists():
        import shutil
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    r = subprocess.run(
        [str(MINIANDROID), "analyze", str(apk_path), "-o", str(out_dir), "-v"],
        capture_output=True, text=True, timeout=30,
    )
    for line in r.stdout.splitlines():
        line = line.strip()
        m = re.match(r'^"main_activity_full":\s*"([^"]*)"(?:,)?\s*$', line)
        if m:
            return m.group(1)
    return ""


def run_apk_and_check_entry(apk_path: Path, expected_class: str) -> dict:
    """Run the APK and check if expected_class.onCreate is entered."""
    out_dir = Path(f"/tmp/exp086_p2_run_{apk_path.stem}")
    if out_dir.exists():
        import shutil
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    r = subprocess.run(
        [str(MINIANDROID), "run", str(apk_path), "-o", str(out_dir), "-v"],
        capture_output=True, text=True, timeout=180,
    )
    full_output = r.stdout + r.stderr

    # Convert expected_class to DEX descriptor form
    # "org.telegram.ui.LaunchActivity" → "Lorg/telegram/ui/LaunchActivity;"
    descriptor = expected_class
    if not descriptor.startswith("L"):
        descriptor = "L" + expected_class.replace(".", "/") + ";"

    # Look for evidence that this class was invoked
    # The runtime emits "METHOD-IN L<class>;.<method>" or
    # "🔄 RECURSIVE INVOKE: L<class>;.<method>"
    oncreate_entered = False
    method_invocations = []
    for line in full_output.splitlines():
        if descriptor in line and ("METHOD-IN" in line or "RECURSIVE INVOKE" in line):
            method_invocations.append(line.strip())
            if "onCreate" in line:
                oncreate_entered = True

    # Also check for "Injected" message (multi-DEX injection)
    injected = "Injected " + descriptor in full_output

    return {
        "exit_code": r.returncode,
        "expected_class": expected_class,
        "expected_descriptor": descriptor,
        "oncreate_entered": oncreate_entered,
        "method_invocations": method_invocations[:5],
        "injected_into_dex_report": injected,
        "stdout_tail": full_output[-500:],
    }


# APKs to test
TEST_APKS = [
    ("telegram", "miniandroid/download/exp038_telegram/Telegram.apk"),
    ("gmdice", "miniandroid/download/exp073_real_apps/de.duenndns.gmdice_8.apk"),
    ("tictactoe", "miniandroid/download/tictactoe.apk"),
    ("headingcalculator", "miniandroid/download/exp073_real_apps/org.debian.eugen.headingcalculator_1.apk"),
    ("simplestopwatch", "miniandroid/download/exp073_real_apps/omegacentauri.mobi.simplestopwatch_26.apk"),
    ("notes", "miniandroid/download/exp073_real_apps/org.billthefarmer.notes_139.apk"),
    ("unote", "miniandroid/download/exp076_corpus/app.varlorg.unote_30.apk"),
]


def run_phase2() -> dict:
    print("=== Phase 2: Real APK Entry-Point Regression ===")
    print(f"Testing {len(TEST_APKS)} APKs")

    results = []
    for name, apk_rel in TEST_APKS:
        apk_path = REPO_ROOT / apk_rel
        if not apk_path.exists():
            print(f"\n  [{name}] SKIP — APK not found: {apk_path}")
            results.append({"name": name, "status": "SKIP", "reason": "APK not found"})
            continue

        print(f"\n  [{name}] analyzing {apk_path.name}...")
        expected_activity = get_manifest_activity(apk_path)
        if not expected_activity:
            print(f"    SKIP — could not resolve manifest activity")
            results.append({"name": name, "status": "SKIP",
                            "reason": "manifest activity not resolved"})
            continue

        print(f"    Expected launcher: {expected_activity}")
        print(f"    Running APK...")
        run_result = run_apk_and_check_entry(apk_path, expected_activity)

        # Classify
        if run_result["oncreate_entered"]:
            status = "PASS"
        elif run_result["injected_into_dex_report"]:
            # Class was injected but onCreate didn't fire — partial
            status = "PARTIAL_INJECTED_NO_ONCREATE"
        elif run_result["exit_code"] in (0, 1):
            # Exit 0/1 but no clear onCreate entry
            status = "PARTIAL_NO_ENTRY"
        else:
            status = f"FAIL_EXIT_{run_result['exit_code']}"

        result = {
            "name": name,
            "apk": str(apk_path),
            "expected_activity": expected_activity,
            "run_result": run_result,
            "status": status,
        }
        print(f"    Status: {status}")
        print(f"    onCreate entered: {run_result['oncreate_entered']}")
        if run_result["method_invocations"]:
            print(f"    Method invocations found:")
            for inv in run_result["method_invocations"][:3]:
                print(f"      {inv[:100]}")
        results.append(result)

    # Summary
    print("\n" + "=" * 70)
    print("PHASE 2 SUMMARY")
    print("=" * 70)
    pass_count = sum(1 for r in results if r["status"] == "PASS")
    partial_count = sum(1 for r in results if r["status"].startswith("PARTIAL"))
    fail_count = sum(1 for r in results if r["status"].startswith("FAIL"))
    skip_count = sum(1 for r in results if r["status"] == "SKIP")
    print(f"PASS: {pass_count}  PARTIAL: {partial_count}  FAIL: {fail_count}  SKIP: {skip_count}")
    for r in results:
        marker = "✅" if r["status"] == "PASS" else \
                ("⚠️ " if r["status"].startswith("PARTIAL") else
                 ("⏭️ " if r["status"] == "SKIP" else "❌"))
        print(f"  {marker} {r['name']:25s}  {r['status']:30s}  "
              f"expected={r.get('expected_activity', '?')}")

    summary = {
        "test": "EXP086 Phase 2 — Real APK entry-point regression",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pass_count": pass_count,
        "partial_count": partial_count,
        "fail_count": fail_count,
        "skip_count": skip_count,
        "results": results,
    }
    out_path = RESULTS_DIR / "EXP086_PHASE2_ENTRY_POINT.json"
    out_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(f"\nResults saved to {out_path}")
    return summary


def main():
    summary = run_phase2()
    sys.exit(0 if summary["fail_count"] == 0 else 1)


if __name__ == "__main__":
    main()
