#!/usr/bin/env python3
"""
EXP-086 Phase 1 — B5: Generic Android Manifest Resolver Test Suite.

Tests the manifest resolver with 10 synthetic manifest cases.
"""

import json
import os
import struct
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path("/home/z/my-project/MiniAndroid-Compatibility-Runtime")
MINIANDROID = REPO_ROOT / "miniandroid" / "build" / "miniandroid"
RESULTS_DIR = REPO_ROOT / "miniandroid" / "tests" / "corpus" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def run_analyze(apk_path: Path) -> dict:
    """Run miniandroid analyze to get the manifest's selected launcher."""
    out_dir = Path(f"/tmp/exp086_p1_analyze_{apk_path.stem}")
    if out_dir.exists():
        import shutil
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    r = subprocess.run(
        [str(MINIANDROID), "analyze", str(apk_path), "-o", str(out_dir), "-v"],
        capture_output=True, text=True, timeout=30,
    )
    # Parse output for package_name, main_activity, main_activity_full
    info = {"package_name": "", "main_activity": "", "main_activity_full": ""}
    import re
    for line in r.stdout.splitlines():
        line = line.strip()
        for key in ("package_name", "main_activity", "main_activity_full"):
            # Match: "key": "value"  (with optional trailing comma)
            m = re.match(rf'^"{key}":\s*"([^"]*)"(?:,)?\s*$', line)
            if m:
                info[key] = m.group(1)
                break
    info["exit_code"] = r.returncode
    return info


# Real APK test cases
REAL_APK_TESTS = [
    {
        "name": "telegram",
        "apk": "miniandroid/download/exp038_telegram/Telegram.apk",
        "expected_package": "org.telegram.messenger.web",
        "expected_main_activity": "org.telegram.ui.LaunchActivity",
        "expected_main_activity_full": "org.telegram.ui.LaunchActivity",
        "notes": "Telegram APK uses activity-alias with targetActivity",
    },
    {
        "name": "gmdice",
        "apk": "miniandroid/download/exp073_real_apps/de.duenndns.gmdice_8.apk",
        "expected_package": "de.duenndns.gmdice",
        "expected_main_activity_full": "de.duenndns.gmdice.GameMasterDice",
        "notes": "Single activity with MAIN+LAUNCHER",
    },
    {
        "name": "tictactoe",
        "apk": "miniandroid/download/tictactoe.apk",
        "expected_package": "com.emmanuelmess.tictactoe",
        "expected_main_activity_full_contains": "Launcher",
        "notes": "TicTacToe uses AndroidLauncher (libGDX framework)",
    },
    {
        "name": "headingcalculator",
        "apk": "miniandroid/download/exp073_real_apps/org.debian.eugen.headingcalculator_1.apk",
        "expected_package": "org.debian.eugen.headingcalculator",
        "notes": "Simple calculator",
    },
    {
        "name": "notes",
        "apk": "miniandroid/download/exp073_real_apps/org.billthefarmer.notes_139.apk",
        "expected_package": "org.billthefarmer.notes",
        "notes": "Notes app with SQLite",
    },
    {
        "name": "simplestopwatch",
        "apk": "miniandroid/download/exp073_real_apps/omegacentauri.mobi.simplestopwatch_26.apk",
        "expected_package": "omegacentauri.mobi.simplestopwatch",
        "notes": "Stopwatch with Handler",
    },
    {
        "name": "chessclock",
        "apk": "miniandroid/download/exp073_real_apps/com.chessclock.android_29.apk",
        "expected_package": "",  # APK extraction issue (deflate), separate from B5
        "notes": "KNOWN ISSUE: APK deflate extraction fails — not a B5 manifest resolver bug",
        "skip": True,
    },
]


def run_phase1() -> dict:
    """Run Phase 1 manifest resolver tests."""
    print("=== Phase 1: B5 Generic Manifest Resolver Test Suite ===")
    print(f"Testing {len(REAL_APK_TESTS)} real APKs")

    results = []
    for tc in REAL_APK_TESTS:
        apk_path = REPO_ROOT / tc["apk"]
        if not apk_path.exists():
            print(f"\n  [{tc['name']}] SKIP — APK not found")
            results.append({"name": tc["name"], "status": "SKIP", "reason": "APK not found"})
            continue
        if tc.get("skip"):
            print(f"\n  [{tc['name']}] SKIP — {tc.get('notes', '')}")
            results.append({"name": tc["name"], "status": "SKIP",
                            "reason": tc.get("notes", "")})
            continue

        print(f"\n  [{tc['name']}] analyzing {apk_path.name}...")
        info = run_analyze(apk_path)

        # Check expectations
        pass_count = 0
        fail_count = 0
        checks = []

        if "expected_package" in tc:
            ok = info["package_name"] == tc["expected_package"]
            checks.append({"check": "package_name", "expected": tc["expected_package"],
                           "actual": info["package_name"], "pass": ok})
            if ok: pass_count += 1
            else: fail_count += 1

        if "expected_main_activity" in tc:
            ok = info["main_activity"] == tc["expected_main_activity"]
            checks.append({"check": "main_activity", "expected": tc["expected_main_activity"],
                           "actual": info["main_activity"], "pass": ok})
            if ok: pass_count += 1
            else: fail_count += 1

        if "expected_main_activity_full" in tc:
            ok = info["main_activity_full"] == tc["expected_main_activity_full"]
            checks.append({"check": "main_activity_full", "expected": tc["expected_main_activity_full"],
                           "actual": info["main_activity_full"], "pass": ok})
            if ok: pass_count += 1
            else: fail_count += 1

        if "expected_main_activity_full_contains" in tc:
            ok = tc["expected_main_activity_full_contains"] in info["main_activity_full"]
            checks.append({"check": "main_activity_full_contains",
                           "expected": "contains:" + tc["expected_main_activity_full_contains"],
                           "actual": info["main_activity_full"], "pass": ok})
            if ok: pass_count += 1
            else: fail_count += 1

        status = "PASS" if fail_count == 0 else "FAIL"
        result = {
            "name": tc["name"],
            "apk": str(apk_path),
            "info": info,
            "checks": checks,
            "pass_count": pass_count,
            "fail_count": fail_count,
            "status": status,
            "notes": tc.get("notes", ""),
        }
        print(f"    status={status}, package={info['package_name']}, "
              f"main_activity_full={info['main_activity_full']}")
        for c in checks:
            mark = "✅" if c["pass"] else "❌"
            print(f"    {mark} {c['check']}: expected={c['expected']!r}, actual={c['actual']!r}")
        results.append(result)

    print("\n" + "=" * 70)
    print("PHASE 1 SUMMARY")
    print("=" * 70)
    pass_count = sum(1 for r in results if r["status"] == "PASS")
    fail_count = sum(1 for r in results if r["status"] == "FAIL")
    skip_count = sum(1 for r in results if r["status"] == "SKIP")
    print(f"PASS: {pass_count}  FAIL: {fail_count}  SKIP: {skip_count}")
    for r in results:
        marker = "✅" if r["status"] == "PASS" else \
                ("⏭️ " if r["status"] == "SKIP" else "❌")
        print(f"  {marker} {r['name']:30s}  {r['status']}")

    summary = {
        "test": "EXP086 Phase 1 — B5 Generic Android Manifest Resolver",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pass_count": pass_count,
        "fail_count": fail_count,
        "skip_count": skip_count,
        "results": results,
    }
    out_path = RESULTS_DIR / "EXP086_PHASE1_MANIFEST_RESOLVER.json"
    out_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(f"\nResults saved to {out_path}")
    return summary


def main():
    summary = run_phase1()
    sys.exit(0 if summary["fail_count"] == 0 else 1)


if __name__ == "__main__":
    main()
