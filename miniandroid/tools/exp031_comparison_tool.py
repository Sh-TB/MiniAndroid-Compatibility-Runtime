#!/usr/bin/env python3
"""
EXP-031: Legacy vs Real-Dalvik Comparison Tool
Runs each APK in both modes and generates comparison report
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List

def run_apk_in_mode(apk_path: str, mode: str, output_base: str) -> Dict:
    """Run single APK in specified mode and capture results"""
    apk_name = Path(apk_path).stem
    output_dir = f"{output_base}/{mode}/{apk_name}"
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Build command
    cmd = [
        "./build/miniandroid",
        "run",
        f"--execution-mode={mode}",
        f"--output={output_dir}",
        apk_path
    ]
    
    result = {
        "apk_name": apk_name + ".apk",
        "mode": mode,
        "exit_code": None,
        "stdout": "",
        "stderr": "",
        "status": "UNKNOWN",
        "source": "HOST_SHORTCUT" if mode == "legacy" else "REAL_DALVIK_INTERPRETER"
    }
    
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd="/home/z/my-project/miniandroid"
        )
        
        result["exit_code"] = proc.returncode
        result["stdout"] = proc.stdout
        result["stderr"] = proc.stderr
        
        # Parse status from output
        if "Status: SUCCESS" in proc.stdout:
            result["status"] = "SUCCESS"
        elif "Status: FAILURE" in proc.stdout:
            result["status"] = "FAILURE"
        elif "Status: PARTIAL" in proc.stdout:
            result["status"] = "PARTIAL_SUCCESS"
            
    except subprocess.TimeoutExpired:
        result["status"] = "TIMEOUT"
    except Exception as e:
        result["status"] = "ERROR"
        result["error"] = str(e)
    
    return def generate_comparison_report(legacy_results: List[Dict], real_results: List[Dict]) -> Dict:
    """Generate comparison report between legacy and real-dalvik modes"""
    report = {
        "experiment": "EXP-031",
        "report_type": "LEGACY_VS_REAL_COMPARISON",
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_apks": len(legacy_results),
            "legacy_success": sum(1 for r in legacy_results if r["status"] == "SUCCESS"),
            "real_dalvik_success": sum(1 for r in real_results if r["status"] == "SUCCESS"),
            "legacy_all_shortcut": True,  # Legacy always uses shortcuts
            "real_has_evidence": False
        },
        "comparisons": []
    }
    
    # Match results by APK name
    legacy_by_apk = {r["apk_name"]: r for r in legacy_results}
    real_by_apk = {r["apk_name"]: r for r in real_results}
    
    all_apks = set(legacy_by_apk.keys()) | set(real_by_apk.keys())
    
    for apk_name in sorted(all_apks):
        legacy = legacy_by_apk.get(apk_name, {})
        real = real_by_apk.get(apk_name, {})
        
        comparison = {
            "apk": apk_name,
            "legacy": {
                "status": legacy.get("status", "NOT_RUN"),
                "source": legacy.get("source", "UNKNOWN"),
                "exit_code": legacy.get("exit_code")
            },
            "real_dalvik": {
                "status": real.get("status", "NOT_RUN"),
                "source": real.get("source", "UNKNOWN"),
                "exit_code": real.get("exit_code")
            },
            "analysis": {}
        }
        
        # Analyze differences
        l_status = legacy.get("status")
        r_status = real.get("status")
        
        if l_status == "SUCCESS" and r_status == "SUCCESS":
            comparison["analysis"]["verdict"] = "BOTH_SUCCEED"
            comparison["analysis"]["note"] = "Both modes succeed - check evidence for real execution proof"
        elif l_status == "SUCCESS" and r_status != "SUCCESS":
            comparison["analysis"]["verdict"] = "LEGACY_ONLY"
            comparison["analysis"]["note"] = "Legacy shortcut works but real execution failed - expected during transition"
        elif l_status != "SUCCESS" and r_status == "SUCCESS":
            comparison["analysis"]["verdict"] = "REAL_ONLY"
            comparison["analysis"]["note"] = "Real execution succeeds where legacy fails - investigate"
        else:
            comparison["analysis"]["verdict"] = "BOTH_FAIL"
            comparison["analysis"]["note"] = "Both modes failed"
        
        report["comparisons"].append(comparison)
    
    return report


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="EXP-031: Legacy vs Real Comparison")
    parser.add_argument("--apk-dir", required=True, help="Directory with APKs")
    parser.add_argument("--output", default="run/exp031/comparison_report.json", help="Output path")
    parser.add_argument("--sample", type=int, default=5, help="Number of APKs to test (default: 5)")
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("EXP-031: LEGACY VS REAL-DALVIK COMPARISON TOOL")
    print("=" * 70)
    print(f"APK Directory: {args.apk_dir}")
    print(f"Sample Size: {args.sample}")
    print(f"Output: {args.output}")
    print()
    
    # Find APKs
    apk_dir = Path(args.apk_dir)
    apks = sorted(apk_dir.glob("*.apk"))[:args.sample]
    
    if not apks:
        print("[ERROR] No APKs found")
        sys.exit(1)
    
    print(f"Found {len(apks)} APKs to test\n")
    
    legacy_results = []
    real_results = []
    
    for i, apk in enumerate(apks, 1):
        print(f"[{i}/{len(apks)}] Testing {apk.name}...")
        
        # Test LEGACY mode
        print(f"  → Running in LEGACY mode...")
        legacy_result = run_apk_in_mode(str(apk), "legacy", "run/exp031/comparison")
        legacy_results.append(legacy_result)
        print(f"    Status: {legacy_result['status']}")
        
        # Test REAL_DALVIK mode
        print(f"  → Running in REAL_DALVIK mode...")
        real_result = run_apk_in_mode(str(apk), "real-dalvik", "run/exp031/comparison")
        real_results.append(real_result)
        print(f"    Status: {real_result['status']}")
        print()
    
    # Generate report
    print("Generating comparison report...")
    report = generate_comparison_report(legacy_results, real_results)
    
    # Save report
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print("=" * 70)
    print("COMPARISON SUMMARY")
    print("=" * 70)
    print(f"APKs Tested:       {report['summary']['total_apks']}")
    print(f"Legacy Success:    {report['summary']['legacy_success']} (all via HOST_SHORTCUT)")
    print(f"Real-Dalvik Success: {report['summary']['real_dalvik_success']}")
    print()
    
    print("DETAILED COMPARISONS:")
    print("-" * 70)
    for comp in report["comparisons"]:
        apk = comp["apk"]
        verdict = comp["analysis"]["verdict"]
        l_s = comp["legacy"]["status"]
        r_s = comp["real_dalvik"]["status"]
        icon = "✅" if "SUCCEED" in verdict else "⚠️" if "FAIL" in verdict else "ℹ️"
        print(f"{icon} {apk}: LEGACY={l_s} | REAL={r_s} [{verdict}]")
    
    print()
    print(f"[+] Report saved to: {output_path}")


if __name__ == "__main__":
    main()
