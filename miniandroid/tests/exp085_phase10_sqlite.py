#!/usr/bin/env python3
"""
EXP-085 Phase 10 — SQLite Smoke Test.

Tests SQLite persistence across two launches.

Strategy:
  - The 'notes' APK (org.billthefarmer.notes_139) is a real SQLite app.
  - Run it twice with the same output dir.
  - Check if any SQLite file is created in the data sandbox.
  - If SQLite is unavailable, identify the exact first missing API.

The runtime has a file_sandbox (miniandroid/src/storage/file_sandbox.cpp).
We check if /data/data/<package>/databases/*.db files are created.
"""

from __future__ import annotations

import json
import subprocess
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path("/home/z/my-project/MiniAndroid-Compatibility-Runtime")
MINIANDROID = REPO_ROOT / "miniandroid" / "build" / "miniandroid"
RESULTS_DIR = REPO_ROOT / "miniandroid" / "tests" / "corpus" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def run_sqlite_test(apk_path: Path, package_name: str) -> dict:
    """Run APK twice, check for SQLite database files."""
    print(f"\n  Testing SQLite persistence for {package_name}...")

    # Run 1
    out_dir1 = Path(f"/tmp/exp085_phase10_run1")
    if out_dir1.exists():
        import shutil
        shutil.rmtree(out_dir1)
    out_dir1.mkdir(parents=True)

    r1 = subprocess.run(
        [str(MINIANDROID), "run", str(apk_path), "-o", str(out_dir1), "-v"],
        capture_output=True, text=True, timeout=60,
    )
    full1 = r1.stdout + r1.stderr

    # Run 2 (same output dir to test persistence)
    out_dir2 = out_dir1  # reuse
    r2 = subprocess.run(
        [str(MINIANDROID), "run", str(apk_path), "-o", str(out_dir2), "-v"],
        capture_output=True, text=True, timeout=60,
    )
    full2 = r2.stdout + r2.stderr

    # Look for SQLite-related evidence in stdout
    sqlite_evidence = {
        "sqlite_open_called": "openDatabase" in full1 or "SQLiteOpenHelper" in full1 or "sqlite" in full1.lower(),
        "create_table_called": "CREATE TABLE" in full1,
        "insert_called": "INSERT" in full1,
        "select_called": "SELECT" in full1,
        "sql_native_lib_loaded": "libdatabase_sqlcipher" in full1 or "libsqlite" in full1,
        "sqlite_java_class_loaded": "Landroid/database/sqlite" in full1,
        "sql_exception": "SQLiteException" in full1 or "SQLException" in full1,
    }

    # Check if runtime has a file_sandbox that simulates /data/data
    sandbox_paths = list(out_dir1.rglob("*.db")) + list(out_dir1.rglob("*.sqlite"))
    sandbox_evidence = {
        "sandbox_db_files": [str(p.relative_to(out_dir1)) for p in sandbox_paths],
        "sandbox_databases_dir_exists": (out_dir1 / "databases").exists(),
    }

    # Look at runtime data dir
    runtime_data_dir = REPO_ROOT / "miniandroid" / "runtime" / "data" / package_name
    runtime_data_evidence = {
        "runtime_data_dir_exists": runtime_data_dir.exists(),
        "shared_prefs_files": [],
        "database_files": [],
    }
    if runtime_data_dir.exists():
        runtime_data_evidence["shared_prefs_files"] = [
            str(p.relative_to(runtime_data_dir)) for p in runtime_data_dir.rglob("*.xml")
        ]
        runtime_data_evidence["database_files"] = [
            str(p.relative_to(runtime_data_dir)) for p in runtime_data_dir.rglob("*.db")
        ]

    # Classify
    if sqlite_evidence["sqlite_open_called"] and (
        sqlite_evidence["create_table_called"] or sqlite_evidence["insert_called"]
    ):
        if sandbox_evidence["sandbox_db_files"]:
            classification = "SQLITE_BRIDGE"
        else:
            classification = "SQLITE_STUB"
    elif sqlite_evidence["sql_exception"]:
        classification = "SQLITE_BLOCKED_EXCEPTION"
    elif sqlite_evidence["sqlite_java_class_loaded"]:
        classification = "SQLITE_BLOCKED_NO_NATIVE"
    else:
        classification = "SQLITE_BLOCKED_NO_STARTUP"

    # Check if notes APK uses SQLCipher (native lib)
    import zipfile
    has_sqlcipher = False
    try:
        with zipfile.ZipFile(apk_path) as z:
            for n in z.namelist():
                if "libsqlite" in n or "sqlcipher" in n:
                    has_sqlcipher = True
                    break
    except Exception:
        pass

    return {
        "apk": str(apk_path),
        "package": package_name,
        "run1_exit_code": r1.returncode,
        "run2_exit_code": r2.returncode,
        "sqlite_evidence": sqlite_evidence,
        "sandbox_evidence": sandbox_evidence,
        "runtime_data_evidence": runtime_data_evidence,
        "has_native_sqlite": has_sqlcipher,
        "classification": classification,
        "run1_stdout_tail": full1[-500:],
        "run2_stdout_tail": full2[-500:],
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


def main():
    print("=== Phase 10: SQLite Smoke Test ===")
    # Test notes (uses SQLite via Android framework)
    notes_apk = REPO_ROOT / "miniandroid" / "download" / "exp073_real_apps" / "org.billthefarmer.notes_139.apk"
    if not notes_apk.exists():
        print(f"SKIP — notes APK not found: {notes_apk}")
        return

    result = run_sqlite_test(notes_apk, "org.billthefarmer.notes")

    print(f"\n  Classification: {result['classification']}")
    print(f"  Has native SQLite lib: {result['has_native_sqlite']}")
    print(f"  SQLite evidence:")
    for k, v in result["sqlite_evidence"].items():
        marker = "✓" if v else "✗"
        print(f"    {marker} {k}: {v}")
    print(f"  Sandbox DB files: {result['sandbox_evidence']['sandbox_db_files']}")

    out_path = RESULTS_DIR / "EXP085_PHASE10_SQLITE.json"
    out_path.write_text(json.dumps({
        "test": "EXP085 Phase 10 — SQLite smoke test",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "results": [result],
    }, indent=2, default=str), encoding="utf-8")
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    main()
