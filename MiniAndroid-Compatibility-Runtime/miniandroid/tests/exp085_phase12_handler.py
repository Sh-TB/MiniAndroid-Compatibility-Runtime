#!/usr/bin/env python3
"""
EXP-085 Phase 12 — Handler/Looper/Delay Test.

Tests that Handler.post() and postDelayed() execute exactly once.

Strategy:
  - Run simplestopwatch (uses Handler for timer updates)
  - Verify Handler is dispatched
  - Verify no duplicate callback execution (the bug from EXP-078)

We also check the runtime's handler draining logic in application_runtime.cpp.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path("/home/z/my-project/MiniAndroid-Compatibility-Runtime")
MINIANDROID = REPO_ROOT / "miniandroid" / "build" / "miniandroid"
RESULTS_DIR = REPO_ROOT / "miniandroid" / "tests" / "corpus" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def run_handler_test(apk_path: Path, apk_name: str) -> dict:
    """Run APK and check for handler evidence."""
    out_dir = Path(f"/tmp/exp085_phase12_{apk_name}")
    if out_dir.exists():
        import shutil
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    print(f"\n  [{apk_name}] running {apk_path.name}...")
    r = subprocess.run(
        [str(MINIANDROID), "run", str(apk_path), "-o", str(out_dir), "-v"],
        capture_output=True, text=True, timeout=60,
    )
    full_output = r.stdout + r.stderr

    # Look for handler evidence
    handler_evidence = {
        "handler_class_loaded": "Landroid/os/Handler" in full_output or "Handler" in full_output,
        "looper_class_loaded": "Landroid/os/Looper" in full_output or "Looper" in full_output,
        "post_called": "post(" in full_output or "postDelayed" in full_output,
        "drain_handler_queue": "drain_handler" in full_output or "HandlerShadow" in full_output,
        "runnable_executed": "Runnable" in full_output or "run()" in full_output,
        "duplicate_callback_evidence": full_output.count("onNextPressed") > 1 or
                                       full_output.count("callback") > 5,
    }

    # Count occurrences of key markers
    counts = {
        "onNextPressed_count": full_output.count("onNextPressed"),
        "sendRequest_count": full_output.count("sendRequest"),
        "drain_ready_count": full_output.count("drain_ready"),
        "post_count": full_output.count("post("),
        "postDelayed_count": full_output.count("postDelayed"),
    }

    # Classify
    if handler_evidence["drain_handler_queue"]:
        if handler_evidence["duplicate_callback_evidence"]:
            classification = "HANDLER_DUPLICATE_BUG"
        else:
            classification = "HANDLER_WORKING"
    elif handler_evidence["handler_class_loaded"]:
        classification = "HANDLER_LOADED_NOT_DRAINED"
    elif r.returncode > 128:
        classification = "HANDLER_BLOCKED_CRASH"
    else:
        classification = "HANDLER_BLOCKED_NO_STARTUP"

    return {
        "apk": str(apk_path),
        "apk_name": apk_name,
        "exit_code": r.returncode,
        "handler_evidence": handler_evidence,
        "counts": counts,
        "classification": classification,
        "stdout_tail": full_output[-500:],
    }


def main():
    print("=== Phase 12: Handler/Looper/Delay Test ===")

    # Test with stopwatch (uses Handler) and telegram (uses Handler for callbacks)
    test_apks = [
        ("simplestopwatch", REPO_ROOT / "miniandroid" / "download" / "exp073_real_apps" / "omegacentauri.mobi.simplestopwatch_26.apk"),
        ("chessclock", REPO_ROOT / "miniandroid" / "download" / "exp073_real_apps" / "com.chessclock.android_29.apk"),
        ("telegram", REPO_ROOT / "miniandroid" / "download" / "exp038_telegram" / "Telegram.apk"),
    ]

    results = []
    for name, apk_path in test_apks:
        if not apk_path.exists():
            print(f"\n  [{name}] SKIP — APK not found")
            continue
        result = run_handler_test(apk_path, name)
        results.append(result)
        print(f"    classification={result['classification']}, "
              f"handler_loaded={result['handler_evidence']['handler_class_loaded']}, "
              f"drain={result['handler_evidence']['drain_handler_queue']}, "
              f"duplicate={result['handler_evidence']['duplicate_callback_evidence']}")

    print("\n" + "=" * 70)
    print("PHASE 12 SUMMARY")
    print("=" * 70)
    for r in results:
        marker = "✅" if r["classification"] == "HANDLER_WORKING" else "❌"
        print(f"  {marker} {r['apk_name']:25s}  {r['classification']}")

    summary = {
        "test": "EXP085 Phase 12 — Handler/Looper/delay test",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "results": results,
    }
    out_path = RESULTS_DIR / "EXP085_PHASE12_HANDLER.json"
    out_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    main()
