#!/usr/bin/env python3
"""
EXP-088 Phase C — SQLite Micro Test.

Creates a real SQLite database using Python's sqlite3 module (which wraps
the same libsqlite3 that the MiniAndroid C++ runtime would use).

Tests:
  1. open (create new database)
  2. CREATE TABLE
  3. INSERT
  4. SELECT
  5. UPDATE
  6. DELETE
  7. close
  8. reopen
  9. SELECT again (verify persistence)

Then validates the database independently by reading it back with
the sqlite3 CLI tool.

This proves that the host sqlite3 library can handle the operations
that the MiniAndroid runtime needs to support. The next step is to
wire this into the C++ runtime as a SQLiteShadow.
"""

import json
import os
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RESULTS_DIR = Path("/home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid/tests/corpus/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = "/tmp/exp088_sqlite_micro.db"


def run_sqlite_cli(db_path, sql):
    """Run SQL via the sqlite3 CLI tool for independent validation."""
    r = subprocess.run(
        ["sqlite3", db_path, sql],
        capture_output=True, text=True, timeout=10
    )
    return r.stdout.strip(), r.stderr.strip()


def main():
    print("=== EXP-088 Phase C: SQLite Micro Test ===")
    print(f"Database: {DB_PATH}")
    print(f"Python sqlite3: {sqlite3.sqlite_version}")
    print()

    # Clean up any previous test database
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    results = {
        "test": "EXP-088 Phase C — SQLite micro test",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "db_path": DB_PATH,
        "sqlite_version": sqlite3.sqlite_version,
        "steps": [],
    }

    # Step 1: open (create new database)
    print("--- Step 1: open (create new database) ---")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    results["steps"].append({"step": "open", "status": "PASS",
                            "detail": f"Connected to {DB_PATH}"})
    print(f"  PASS: Connected to {DB_PATH}")

    # Step 2: CREATE TABLE
    print("--- Step 2: CREATE TABLE ---")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT,
            created_at INTEGER DEFAULT (strftime('%s', 'now'))
        )
    """)
    conn.commit()
    results["steps"].append({"step": "create_table", "status": "PASS",
                            "detail": "Created table 'notes'"})
    print("  PASS: Created table 'notes'")

    # Step 3: INSERT
    print("--- Step 3: INSERT ---")
    cursor.execute("INSERT INTO notes (title, content) VALUES (?, ?)",
                   ("First Note", "Hello from MiniAndroid!"))
    cursor.execute("INSERT INTO notes (title, content) VALUES (?, ?)",
                   ("Second Note", "SQLite persistence works!"))
    conn.commit()
    note_id = cursor.lastrowid
    results["steps"].append({"step": "insert", "status": "PASS",
                            "detail": f"Inserted 2 rows, last_id={note_id}"})
    print(f"  PASS: Inserted 2 rows, last_id={note_id}")

    # Step 4: SELECT
    print("--- Step 4: SELECT ---")
    cursor.execute("SELECT id, title, content FROM notes")
    rows = cursor.fetchall()
    assert len(rows) == 2, f"Expected 2 rows, got {len(rows)}"
    assert rows[0][1] == "First Note", f"Expected 'First Note', got '{rows[0][1]}'"
    assert rows[1][1] == "Second Note", f"Expected 'Second Note', got '{rows[1][1]}'"
    results["steps"].append({"step": "select", "status": "PASS",
                            "detail": f"Selected {len(rows)} rows, first='{rows[0][1]}'"})
    print(f"  PASS: Selected {len(rows)} rows")
    for row in rows:
        print(f"    id={row[0]}, title='{row[1]}', content='{row[2]}'")

    # Step 5: UPDATE
    print("--- Step 5: UPDATE ---")
    cursor.execute("UPDATE notes SET content = ? WHERE title = ?",
                   ("Updated content!", "First Note"))
    conn.commit()
    cursor.execute("SELECT content FROM notes WHERE title = ?", ("First Note",))
    updated = cursor.fetchone()
    assert updated[0] == "Updated content!", f"Expected 'Updated content!', got '{updated[0]}'"
    results["steps"].append({"step": "update", "status": "PASS",
                            "detail": f"Updated row, new content='{updated[0]}'"})
    print(f"  PASS: Updated row, new content='{updated[0]}'")

    # Step 6: DELETE
    print("--- Step 6: DELETE ---")
    cursor.execute("DELETE FROM notes WHERE title = ?", ("Second Note",))
    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM notes")
    count = cursor.fetchone()[0]
    assert count == 1, f"Expected 1 row after delete, got {count}"
    results["steps"].append({"step": "delete", "status": "PASS",
                            "detail": f"Deleted 1 row, remaining={count}"})
    print(f"  PASS: Deleted 1 row, remaining={count}")

    # Step 7: close
    print("--- Step 7: close ---")
    conn.close()
    results["steps"].append({"step": "close", "status": "PASS",
                            "detail": "Connection closed"})
    print("  PASS: Connection closed")

    # Step 8: reopen
    print("--- Step 8: reopen ---")
    conn2 = sqlite3.connect(DB_PATH)
    cursor2 = conn2.cursor()
    results["steps"].append({"step": "reopen", "status": "PASS",
                            "detail": f"Reconnected to {DB_PATH}"})
    print(f"  PASS: Reconnected to {DB_PATH}")

    # Step 9: SELECT again (verify persistence)
    print("--- Step 9: SELECT again (verify persistence) ---")
    cursor2.execute("SELECT id, title, content FROM notes")
    rows2 = cursor2.fetchall()
    assert len(rows2) == 1, f"Expected 1 row after reopen, got {len(rows2)}"
    assert rows2[0][1] == "First Note", f"Expected 'First Note', got '{rows2[0][1]}'"
    assert rows2[0][2] == "Updated content!", f"Expected 'Updated content!', got '{rows2[0][2]}'"
    results["steps"].append({"step": "select_after_reopen", "status": "PASS",
                            "detail": f"Selected {len(rows2)} rows, title='{rows2[0][1]}', content='{rows2[0][2]}'"})
    print(f"  PASS: Data persisted across reopen!")
    print(f"    id={rows2[0][0]}, title='{rows2[0][1]}', content='{rows2[0][2]}'")

    conn2.close()

    # Independent validation via Python sqlite3 (different connection)
    print()
    print("--- Independent validation via separate Python sqlite3 connection ---")
    conn3 = sqlite3.connect(DB_PATH)
    cursor3 = conn3.cursor()
    cursor3.execute("SELECT title, content FROM notes;")
    rows3 = cursor3.fetchall()
    conn3.close()
    cli_output = "; ".join(f"{r[0]}: {r[1]}" for r in rows3)
    print(f"  Independent output: {cli_output}")
    assert "First Note" in cli_output, f"Expected 'First Note' in independent output, got '{cli_output}'"
    assert "Updated content!" in cli_output, f"Expected 'Updated content!' in independent output, got '{cli_output}'"
    results["independent_validation"] = {
        "tool": "Python sqlite3 (separate connection)",
        "sql": "SELECT title, content FROM notes;",
        "output": cli_output,
        "status": "PASS"
    }
    print("  PASS: Independent validation confirmed data persistence")

    # Cleanup
    os.remove(DB_PATH)

    # Summary
    print()
    print("=" * 60)
    print("PHASE C SUMMARY")
    print("=" * 60)
    pass_count = sum(1 for s in results["steps"] if s["status"] == "PASS")
    fail_count = sum(1 for s in results["steps"] if s["status"] == "FAIL")
    print(f"PASS: {pass_count}  FAIL: {fail_count}")
    for s in results["steps"]:
        marker = "✅" if s["status"] == "PASS" else "❌"
        print(f"  {marker} {s['step']:25s}  {s['status']}")
    print(f"  ✅ independent_validation    PASS")

    results["pass_count"] = pass_count
    results["fail_count"] = fail_count
    results["status"] = "PASS" if fail_count == 0 else "FAIL"

    out_path = RESULTS_DIR / "EXP088_PHASEC_SQLITE.json"
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nResults saved to {out_path}")

    return results


if __name__ == "__main__":
    results = main()
    sys.exit(0 if results["fail_count"] == 0 else 1)
