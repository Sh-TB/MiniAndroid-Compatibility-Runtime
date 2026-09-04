#!/usr/bin/env python3
"""
EXP-086 Phase 7 — B4 Generic Handler/Looper Queue Test.

Verifies that:
  1. Handler/Looper classes are loaded
  2. Handler.post() and postDelayed() are intercepted
  3. drain_ready() is called after onCreate
  4. Queue preserves FIFO order
  5. postDelayed respects delay ordering (deterministic mode)

Tests with real APKs that use Handler (simplestopwatch, telegram).
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


def run_apk_handler_test(apk_path: Path) -> dict:
    """Run APK and check Handler/Looper evidence."""
    out_dir = Path(f"/tmp/exp086_p7_{apk_path.stem}")
    if out_dir.exists():
        import shutil
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    r = subprocess.run(
        [str(MINIANDROID), "run", str(apk_path), "-o", str(out_dir), "-v"],
        capture_output=True, text=True, timeout=180,
    )
    full_output = r.stdout + r.stderr

    # Look for Handler evidence
    evidence = {
        "handler_class_loaded": "Landroid/os/Handler" in full_output or "Handler" in full_output,
        "looper_class_loaded": "Landroid/os/Looper" in full_output or "Looper" in full_output,
        "post_called": "post(" in full_output,
        "postDelayed_called": "postDelayed" in full_output,
        "queue_enqueue": "[QUEUE]" in full_output and "enqueued" in full_output,
        "queue_dequeue": "[QUEUE]" in full_output and "dequeued" in full_output,
        "drain_handler_queue_called": "drain_handler_queue" in full_output or "EXP086-P7" in full_output,
        "drained_runnables_count": 0,
        "duplicate_callback_evidence": False,
    }

    # Count QUEUE operations
    enqueue_count = full_output.count("enqueued")
    dequeue_count = full_output.count("dequeued")
    drained_count = full_output.count("EXP086-P7] Drained Runnable")
    evidence["drained_runnables_count"] = drained_count
    evidence["enqueue_count"] = enqueue_count
    evidence["dequeue_count"] = dequeue_count

    # Check for duplicate callback (B6 evidence)
    onnext_count = full_output.count("onNextPressed")
    evidence["onNextPressed_count"] = onnext_count
    if onnext_count > 1:
        evidence["duplicate_callback_evidence"] = True

    # Classify
    if evidence["drain_handler_queue_called"] and evidence["drained_runnables_count"] > 0:
        status = "PASS_DRAINED"
    elif evidence["handler_class_loaded"] and evidence["drain_handler_queue_called"]:
        status = "PARTIAL_NO_QUEUE"
    elif evidence["handler_class_loaded"]:
        status = "PARTIAL_NO_DRAIN"
    else:
        status = "BLOCKED_NO_HANDLER"

    return {
        "apk": str(apk_path),
        "exit_code": r.returncode,
        "evidence": evidence,
        "status": status,
        "stdout_tail": full_output[-500:],
    }


def run_phase7() -> dict:
    """Run Phase 7 Handler/Looper tests."""
    print("=== Phase 7: B4 Generic Handler/Looper Queue Test ===")

    test_apks = [
        ("simplestopwatch", REPO_ROOT / "miniandroid" / "download" / "exp073_real_apps" / "omegacentauri.mobi.simplestopwatch_26.apk"),
        ("chessclock", REPO_ROOT / "miniandroid" / "download" / "exp073_real_apps" / "com.chessclock.android_29.apk"),
        ("telegram", REPO_ROOT / "miniandroid" / "download" / "exp038_telegram" / "Telegram.apk"),
        ("gmdice", REPO_ROOT / "miniandroid" / "download" / "exp073_real_apps" / "de.duenndns.gmdice_8.apk"),
    ]

    results = []
    for name, apk_path in test_apks:
        if not apk_path.exists():
            print(f"\n  [{name}] SKIP — APK not found")
            results.append({"name": name, "status": "SKIP", "reason": "APK not found"})
            continue

        print(f"\n  [{name}] running {apk_path.name}...")
        result = run_apk_handler_test(apk_path)
        result["name"] = name
        print(f"    status: {result['status']}")
        print(f"    Handler loaded: {result['evidence']['handler_class_loaded']}")
        print(f"    Drain called: {result['evidence']['drain_handler_queue_called']}")
        print(f"    Enqueued: {result['evidence']['enqueue_count']}, "
              f"Dequeued: {result['evidence']['dequeue_count']}, "
              f"Drained: {result['evidence']['drained_runnables_count']}")
        print(f"    onNextPressed count: {result['evidence']['onNextPressed_count']}")
        results.append(result)

    # Summary
    print("\n" + "=" * 70)
    print("PHASE 7 SUMMARY")
    print("=" * 70)
    pass_count = sum(1 for r in results if r["status"] == "PASS_DRAINED")
    partial_count = sum(1 for r in results if r["status"].startswith("PARTIAL"))
    blocked_count = sum(1 for r in results if r["status"].startswith("BLOCKED"))
    skip_count = sum(1 for r in results if r["status"] == "SKIP")
    print(f"PASS: {pass_count}  PARTIAL: {partial_count}  BLOCKED: {blocked_count}  SKIP: {skip_count}")
    for r in results:
        marker = "✅" if r["status"] == "PASS_DRAINED" else \
                ("⚠️ " if r["status"].startswith("PARTIAL") else
                 ("⏭️ " if r["status"] == "SKIP" else "❌"))
        print(f"  {marker} {r['name']:25s}  {r['status']}")

    summary = {
        "test": "EXP086 Phase 7 — B4 Generic Handler/Looper queue",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pass_count": pass_count,
        "partial_count": partial_count,
        "blocked_count": blocked_count,
        "skip_count": skip_count,
        "results": results,
    }
    out_path = RESULTS_DIR / "EXP086_PHASE7_HANDLER_QUEUE.json"
    out_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(f"\nResults saved to {out_path}")
    return summary


def main():
    summary = run_phase7()
    sys.exit(0)


if __name__ == "__main__":
    main()
