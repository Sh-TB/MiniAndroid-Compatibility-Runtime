#!/usr/bin/env python3
"""
EXP-085 Phase 4 — Exception / Try-Catch Smoke Test.

Tests that the runtime correctly distinguishes:
  - HANDLED_LOCALLY: try { throw } catch { continue }
  - PROPAGATED: A → B throws, A catches
  - UNHANDLED: throw with no catch

Strategy:
  - Use the existing exp052 case1-case4 fixtures:
    * case1_no_catch: throw with no catch → UNHANDLED
    * case2_local_catch: try { throw } catch → HANDLED_LOCALLY
    * case3_nested_catch: nested try/catch → HANDLED_LOCALLY (inner)
    * case4_catch_all: catch-all → HANDLED_LOCALLY
  - Run each via miniandroid
  - Verify api_trace + stdout show the correct exception flow path
  - Distinguish HANDLED vs PROPAGATED vs UNHANDLED via runtime stdout
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path("/home/z/my-project/MiniAndroid-Compatibility-Runtime")
MINIANDROID = REPO_ROOT / "miniandroid" / "build" / "miniandroid"
RESULTS_DIR = REPO_ROOT / "miniandroid" / "tests" / "corpus" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


TEST_CASES = [
    {
        "name": "case1_no_catch_UNHANDLED",
        "apk": "miniandroid/test_apks/exp052/case1_no_catch.apk",
        "expected_flow": "UNHANDLED",
        "verifies": "throw with no catch → exception propagates out",
    },
    {
        "name": "case2_local_catch_HANDLED_LOCALLY",
        "apk": "miniandroid/test_apks/exp052/case2_local_catch.apk",
        "expected_flow": "HANDLED_LOCALLY",
        "verifies": "try { throw } catch { continue }",
    },
    {
        "name": "case3_nested_catch_HANDLED_LOCALLY",
        "apk": "miniandroid/test_apks/exp052/case3_nested_catch.apk",
        "expected_flow": "HANDLED_LOCALLY",
        "verifies": "nested try/catch with inner handler",
    },
    {
        "name": "case4_catch_all_HANDLED_LOCALLY",
        "apk": "miniandroid/test_apks/exp052/case4_catch_all.apk",
        "expected_flow": "HANDLED_LOCALLY",
        "verifies": "catch-all handler",
    },
]


def run_exception_test(apk_path: Path, fixture_name: str, expected_flow: str) -> dict:
    """Run an exception test fixture and classify the observed exception flow."""
    out_dir = Path(f"/tmp/exp085_phase4_{fixture_name}")
    if out_dir.exists():
        import shutil
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    print(f"\n  [{fixture_name}] running {apk_path.name}...")
    r = subprocess.run(
        [str(MINIANDROID), "run", str(apk_path), "-o", str(out_dir), "-v"],
        capture_output=True, text=True, timeout=60,
    )
    full_output = r.stdout + r.stderr

    # Look for exception flow markers in stdout
    # The runtime should emit markers like:
    #   "TRY-ENTRY" — entering try block
    #   "CATCH-HIT" — caught exception
    #   "THROWING exception" — runtime detected a throw
    #   "UNCAUGHT-EXCEPTION" — propagated out
    observed_flow = "UNKNOWN"
    flow_evidence = []

    if "TRY-ENTRY" in full_output:
        flow_evidence.append("TRY-ENTRY marker found")
    if "THROWING exception" in full_output or "throw" in full_output.lower():
        # A throw was detected
        flow_evidence.append("THROW marker found")
    if "CATCH" in full_output or "catch" in full_output.lower():
        # Look for evidence of catch handler execution
        if "API BRIDGE" in full_output or "Method returned" in full_output:
            observed_flow = "HANDLED_LOCALLY"
            flow_evidence.append("Catch handler executed (method returned)")
        else:
            flow_evidence.append("Catch reference found but no handler execution")
    # If a THROW was detected but no CATCH marker, it's UNHANDLED
    if observed_flow == "UNKNOWN":
        if "THROWING exception" in full_output and "CATCH" not in full_output:
            observed_flow = "UNHANDLED"
            flow_evidence.append("Throw with no catch — UNHANDLED")
        elif "TRY-ENTRY" in full_output:
            # If onCreate returned successfully despite a try block, likely handled
            if "Method returned successfully" in full_output:
                observed_flow = "HANDLED_LOCALLY"
                flow_evidence.append("onCreate returned successfully after try")
            else:
                observed_flow = "PROPAGATED"
                flow_evidence.append("Try entered but no clear handler")

    # Look for exception_table / tries_size info from DEX parser
    has_tries_size = "tries_size:" in full_output
    if has_tries_size:
        flow_evidence.append("DEX exception table present")

    # Check if onCreate was actually executed
    oncreate_executed = "execute_method_internal" in full_output or "METHOD-IN" in full_output

    # Match against expected
    status = "PASS" if observed_flow == expected_flow else "MISMATCH"

    result = {
        "fixture": fixture_name,
        "apk": str(apk_path),
        "exit_code": r.returncode,
        "expected_flow": expected_flow,
        "observed_flow": observed_flow,
        "status": status,
        "oncreate_executed": oncreate_executed,
        "flow_evidence": flow_evidence,
        "stdout_excerpt": full_output[-1000:],
    }
    print(f"    expected={expected_flow}, observed={observed_flow}, status={status}")
    return result


def run_phase4(verbose: bool = False) -> dict:
    """Run all Phase 4 exception tests."""
    print("=== Phase 4: Exception / Try-Catch Smoke Test ===")
    print(f"Testing {len(TEST_CASES)} fixtures")

    results = []
    for tc in TEST_CASES:
        apk_path = REPO_ROOT / tc["apk"]
        if not apk_path.exists():
            print(f"  [{tc['name']}] SKIP — APK not found")
            results.append({
                "fixture": tc["name"], "status": "SKIP",
                "reason": "APK not found", "verifies": tc["verifies"],
            })
            continue
        r = run_exception_test(apk_path, tc["name"], tc["expected_flow"])
        r["verifies"] = tc["verifies"]
        results.append(r)

    # Summary
    print("\n" + "=" * 70)
    print("PHASE 4 SUMMARY")
    print("=" * 70)
    pass_count = sum(1 for r in results if r["status"] == "PASS")
    mismatch_count = sum(1 for r in results if r["status"] == "MISMATCH")
    skip_count = sum(1 for r in results if r["status"] == "SKIP")
    print(f"PASS: {pass_count}  MISMATCH: {mismatch_count}  SKIP: {skip_count}")
    for r in results:
        marker = "✅" if r["status"] == "PASS" else \
                ("⏭️ " if r["status"] == "SKIP" else "⚠️ ")
        print(f"  {marker} {r['fixture']:45s}  expected={r.get('expected_flow', '?'):18s}  "
              f"observed={r.get('observed_flow', '?')}")

    summary = {
        "test": "EXP085 Phase 4 — Exception / try-catch smoke test",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pass_count": pass_count,
        "mismatch_count": mismatch_count,
        "skip_count": skip_count,
        "results": results,
    }
    out_path = RESULTS_DIR / "EXP085_PHASE4_EXCEPTIONS.json"
    out_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(f"\nResults saved to {out_path}")
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()
    summary = run_phase4(verbose=args.verbose)
    sys.exit(0 if summary["mismatch_count"] == 0 else 1)


if __name__ == "__main__":
    main()
