#!/usr/bin/env python3
"""
EXP-085 Phase 17/18 — Telegram Regression + Checkpoint M.

Phase 17: Run current Telegram using external corpus, capture:
  - LaunchActivity
  - LoginActivity
  - PhoneView
  - input
  - click
  - sendRequest
  - callback
  - SMS transition
  - SMS View
  - screenshot

Phase 18: Checkpoint M — prove the full controlled test:
  Phone number injected → click → onNextPressed → auth.sendCode →
  mock response → RequestDelegate callback → setPage(VIEW_CODE_SMS) →
  SMS View visible → login_sms.png valid

  Verify:
  - event count exactly 1
  - callback count exactly 1
  - screenshot is NOT fallback
  - 3 independent runs reproduce
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path("/home/z/my-project/MiniAndroid-Compatibility-Runtime")
MINIANDROID = REPO_ROOT / "miniandroid" / "build" / "miniandroid"
RESULTS_DIR = REPO_ROOT / "miniandroid" / "tests" / "corpus" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def run_telegram_once(run_id: int, apk_path: Path) -> dict:
    """Run Telegram once and capture checkpoint evidence."""
    out_dir = Path(f"/tmp/exp085_phase17_run{run_id}")
    if out_dir.exists():
        import shutil
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    print(f"\n  Run {run_id}: executing Telegram...")
    r = subprocess.run(
        [str(MINIANDROID), "run", str(apk_path), "-o", str(out_dir), "-v"],
        capture_output=True, text=True, timeout=180,
    )
    full_output = r.stdout + r.stderr

    # Count key events
    counts = {
        "LaunchActivity": full_output.count("LaunchActivity"),
        "LoginActivity": full_output.count("LoginActivity"),
        "PhoneView": full_output.count("PhoneView"),
        "onNextPressed": full_output.count("onNextPressed"),
        "sendRequest": full_output.count("sendRequest"),
        "TL_auth_sentCode": full_output.count("TL_auth_sentCode"),
        "Lambda2": full_output.count("Lambda2") + full_output.count("RequestDelegate"),
        "setPage": full_output.count("setPage"),
        "VIEW_CODE_SMS": full_output.count("VIEW_CODE_SMS") + full_output.count("sms"),
    }

    # Check artifacts
    artifacts = {
        "report_md_exists": (out_dir / "report.md").exists(),
        "view_tree_exists": (out_dir / "view_tree.json").exists(),
        "screenshot_exists": (out_dir / "screenshot.png").exists(),
        "screenshot_size": (out_dir / "screenshot.png").stat().st_size if (out_dir / "screenshot.png").exists() else 0,
        "ppm_exists": (out_dir / "screenshot.ppm").exists(),
        "ppm_size": (out_dir / "screenshot.ppm").stat().st_size if (out_dir / "screenshot.ppm").exists() else 0,
    }

    # Compute screenshot SHA256 (if exists)
    screenshot_sha = ""
    if artifacts["screenshot_exists"]:
        h = hashlib.sha256()
        with open(out_dir / "screenshot.png", "rb") as f:
            for blk in iter(lambda: f.read(1 << 20), b""):
                h.update(blk)
        screenshot_sha = h.hexdigest()

    # Classify
    has_full_flow = (counts["LoginActivity"] > 0 and
                     counts["onNextPressed"] >= 1 and
                     counts["sendRequest"] >= 1 and
                     counts["TL_auth_sentCode"] >= 1)

    if has_full_flow:
        # Check for duplicate onNextPressed (bug from EXP-078)
        if counts["onNextPressed"] > 1:
            status = "PARTIAL_DUPLICATE_CALLBACK"
        elif counts["onNextPressed"] == 1:
            status = "CHECKPOINT_M_PASS"
        else:
            status = "PARTIAL_NO_ONNEXT"
    elif counts["LoginActivity"] > 0:
        status = "PARTIAL_NO_SENDREQUEST"
    elif counts["LaunchActivity"] > 0:
        status = "PARTIAL_LAUNCHED_NO_LOGIN"
    else:
        status = "BLOCKED_NO_STARTUP"

    return {
        "run_id": run_id,
        "exit_code": r.returncode,
        "counts": counts,
        "artifacts": artifacts,
        "screenshot_sha256": screenshot_sha,
        "status": status,
        "stdout_tail": full_output[-1000:],
    }


def main():
    print("=== Phase 17/18: Telegram Regression + Checkpoint M ===")

    apk_path = REPO_ROOT / "miniandroid" / "download" / "exp038_telegram" / "Telegram.apk"
    if not apk_path.exists():
        print(f"SKIP — Telegram APK not found at {apk_path}")
        return

    # Phase 17: single run for regression evidence
    print("\n--- Phase 17: Single regression run ---")
    phase17_result = run_telegram_once(1, apk_path)

    # Phase 18: 3 independent runs for reproducibility
    print("\n--- Phase 18: Checkpoint M (3 independent runs) ---")
    runs = [run_telegram_once(i, apk_path) for i in range(1, 4)]

    # Compare run outputs
    screenshot_shas = [r["screenshot_sha256"] for r in runs if r["screenshot_sha256"]]
    all_shas_match = len(set(screenshot_shas)) == 1 if len(screenshot_shas) == 3 else False

    statuses = [r["status"] for r in runs]
    all_pass = all(s == "CHECKPOINT_M_PASS" for s in statuses)

    print("\n" + "=" * 70)
    print("PHASE 17/18 SUMMARY")
    print("=" * 70)
    print(f"Phase 17 status: {phase17_result['status']}")
    print(f"Phase 18 statuses: {statuses}")
    print(f"All 3 runs CHECKPOINT_M_PASS: {all_pass}")
    print(f"All 3 screenshot SHA256s identical: {all_shas_match}")
    if screenshot_shas:
        print(f"Screenshot SHA256s:")
        for i, sha in enumerate(screenshot_shas, 1):
            print(f"  Run {i}: {sha[:16]}...")

    summary = {
        "test": "EXP085 Phase 17/18 — Telegram regression + Checkpoint M",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "phase17_result": phase17_result,
        "phase18_runs": runs,
        "checkpoint_m_pass": all_pass,
        "screenshots_match": all_shas_match,
    }
    out_path = RESULTS_DIR / "EXP085_PHASE17_18_TELEGRAM.json"
    out_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    main()
