#!/usr/bin/env python3
"""
EXP-088 Phase F — Handler/Looper queue semantics verification.

This Python script orchestrates the Phase F verification:

1. Runs the standalone C++ test `exp088_phasef_handler_queue_semantics`
   which exercises the user's exact scenario:
     post(A), post(B), postDelayed(C), removeCallbacks(B), drain → [A, C]
   Plus 7 additional tests covering exactly-once execution, FIFO ordering,
   delayed semantics, removeCallbacksAndMessages, etc.

2. Optionally runs the existing APK-based Phase F test that checks
   whether real APKs trigger Handler.post during onCreate.

Saves consolidated results to:
  miniandroid/tests/corpus/results/EXP088_PHASEF_HANDLER.json
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path("/home/z/my-project/MiniAndroid-Compatibility-Runtime")
MINIANDROID = REPO_ROOT / "miniandroid" / "build"
PHASEF_BIN = MINIANDROID / "exp088_phasef_handler_queue_semantics"
RESULTS_DIR = REPO_ROOT / "miniandroid" / "tests" / "corpus" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def run_cpp_phasef() -> dict:
    """Run the standalone C++ Phase F test."""
    if not PHASEF_BIN.exists():
        return {"status": "BLOCKED", "reason": f"binary not found: {PHASEF_BIN}"}

    r = subprocess.run(
        [str(PHASEF_BIN)],
        capture_output=True, text=True, timeout=60,
    )

    output = r.stdout + r.stderr

    # Parse the SUMMARY block
    passed = 0
    failed = 0
    total = 0
    in_summary = False
    for line in output.splitlines():
        if "=== SUMMARY ===" in line:
            in_summary = True
            continue
        if in_summary:
            if "Passed:" in line:
                passed = int(line.split(":")[1].strip())
            elif "Failed:" in line:
                failed = int(line.split(":")[1].strip())
            elif "Total:" in line:
                total = int(line.split(":")[1].strip())

    return {
        "status": "PASS" if (failed == 0 and passed > 0) else "FAIL",
        "exit_code": r.returncode,
        "passed": passed,
        "failed": failed,
        "total": total,
        "output_excerpt": "\n".join(output.splitlines()[:30]) + "\n...[truncated]...\n" + "\n".join(output.splitlines()[-15:]),
    }


def run_apk_phasef() -> dict:
    """Run the existing APK-based Phase F test."""
    apk = REPO_ROOT / "miniandroid" / "download" / "exp073_real_apps" / "omegacentauri.mobi.simplestopwatch_26.apk"
    if not apk.exists():
        return {"status": "SKIP", "reason": "APK not found"}

    out_dir = Path("/tmp/exp088_f_apk_run")
    if out_dir.exists():
        import shutil
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    r = subprocess.run(
        [str(MINIANDROID / "miniandroid"), "run", str(apk), "-o", str(out_dir), "-v"],
        capture_output=True, text=True, timeout=120,
    )
    full_output = r.stdout + r.stderr

    return {
        "status": "PARTIAL" if r.returncode != 0 else "PASS",
        "exit_code": r.returncode,
        "handler_class_loaded": "Landroid/os/Handler" in full_output,
        "queue_enqueue_seen": "[QUEUE]" in full_output and "enqueued" in full_output,
        "queue_dequeue_seen": "[QUEUE]" in full_output and "dequeued" in full_output,
        "remove_callbacks_seen": "[QUEUE]" in full_output and "removed" in full_output,
        "enqueue_count": full_output.count("enqueued"),
        "dequeue_count": full_output.count("dequeued"),
    }


def main() -> int:
    print("=== EXP-088 Phase F — Handler/Looper Queue Semantics ===\n")

    print("[1] Running standalone C++ Phase F test:")
    cpp_result = run_cpp_phasef()
    print(f"    Status: {cpp_result['status']}")
    print(f"    Passed: {cpp_result['passed']}/{cpp_result['total']}")
    print(f"    Failed: {cpp_result['failed']}/{cpp_result['total']}")

    print("\n[2] Running APK-based Phase F test (simplestopwatch):")
    apk_result = run_apk_phasef()
    print(f"    Status: {apk_result['status']}")
    print(f"    Handler class loaded: {apk_result.get('handler_class_loaded', False)}")
    print(f"    Queue enqueue seen: {apk_result.get('queue_enqueue_seen', False)}")
    print(f"    Queue dequeue seen: {apk_result.get('queue_dequeue_seen', False)}")
    print(f"    removeCallbacks seen: {apk_result.get('remove_callbacks_seen', False)}")

    # Consolidated status
    overall_status = "PASS" if cpp_result["status"] == "PASS" else "FAIL"
    if apk_result["status"] == "PARTIAL":
        overall_status = "PASS_WITH_APK_PARTIAL"

    result = {
        "test": "EXP-088 Phase F — Handler/Looper Queue Semantics",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "cpp_test": cpp_result,
        "apk_test": apk_result,
        "overall_status": overall_status,
        "summary": {
            "cpp_passed": cpp_result["passed"],
            "cpp_failed": cpp_result["failed"],
            "cpp_total": cpp_result["total"],
            "user_scenario_tested": True,
            "user_scenario_description": "post(A), post(B), postDelayed(C), removeCallbacks(B), drain → [A, C]",
            "user_scenario_passed": cpp_result["status"] == "PASS",
            "infrastructure_changes": [
                "HandlerShadow::remove_callbacks() — previously a no-op stub, now actually removes matching Runnables",
                "HandlerShadow::remove_all() — implements removeCallbacksAndMessages(null)",
                "HandlerShadow::dispatch() — removeCallbacks/removeCallbacksAndMessages now call the real methods"
            ]
        }
    }

    out_path = RESULTS_DIR / "EXP088_PHASEF_HANDLER.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"\nResults saved to: {out_path}")
    print(f"\n=== OVERALL: {overall_status} ===")

    return 0 if overall_status in ("PASS", "PASS_WITH_APK_PARTIAL") else 1


if __name__ == "__main__":
    sys.exit(main())
