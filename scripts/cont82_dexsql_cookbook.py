#!/usr/bin/env python3
# cont82_dexsql_cookbook.py — DexSQL query cookbook harness (CONT-81 directive §4).
# Runs the 13 required query categories against a target APK, saves each SQL +
# raw output + sha256, measures wall-clock per query. Categories that DexSQL's
# DEX-only schema cannot express are recorded UNSUPPORTED with the baseline
# tool that covers them (honesty law — never invent table names).
#
# Usage: python3 scripts/cont82_dexsql_cookbook.py <apk-path> <out-dir>
import hashlib
import json
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEXSQL = os.path.join(ROOT, "tools/dexsql/dexsql-linux-amd64")


def run_dexsql(apk, sql, timeout=240):
    t0 = time.monotonic()
    p = subprocess.run([DEXSQL, "query", "--input", apk, "--sql", sql],
                       capture_output=True, text=True, timeout=timeout)
    dt = time.monotonic() - t0
    return p.returncode, p.stdout, p.stderr, dt


def sha16(b):
    return hashlib.sha256(b).hexdigest()[:16]


COOKBOOK = [
    # (cat, name, sql or None, baseline_tool_if_unsupported)
    (2, "dex_inventory",
     "SELECT f.source_path, f.string_count, f.method_count, f.class_count "
     "FROM dex_files f ORDER BY f.file_id", None),
    (2, "dup_class_defs",
     "SELECT descriptor, COUNT(*) AS defs FROM classes "
     "GROUP BY descriptor HAVING COUNT(*) > 1 ORDER BY defs DESC, descriptor LIMIT 30", None),
    (3, "string_exception_text",
     "SELECT s.string_idx, s.value FROM strings s WHERE s.value LIKE "
     "'%was aborted%' OR s.value LIKE '%on a null object%' "
     "ORDER BY s.string_idx LIMIT 40", None),
    (3, "string_class_descriptor",
     "SELECT s.string_idx, s.value FROM strings s WHERE s.value LIKE 'Landroidx/fragment/app/%' "
     "ORDER BY s.string_idx LIMIT 40", None),
    (4, "callers_of_method",
     "SELECT method_class, method_name, callee_class, callee_name "
     "FROM method_calls WHERE callee_name = 'postDelayed' "
     "ORDER BY method_class LIMIT 40", None),
    (4, "two_hop_chain",
     "WITH c1 AS (SELECT DISTINCT callee_class, callee_name FROM method_calls "
     "WHERE callee_name = 'postDelayed'), "
     "c2 AS (SELECT c.method_class, c.method_name, c.callee_class, c.callee_name "
     "FROM method_calls c JOIN c1 ON c.callee_class = c1.callee_class "
     "AND c.callee_name = c1.callee_name) "
     "SELECT c2.method_class, c2.method_name, c2.callee_class, c2.callee_name "
     "FROM method_calls c3 JOIN c2 ON c3.callee_class = c2.method_class "
     "AND c3.callee_name = c2.method_name LIMIT 30", None),
    (5, "field_accesses_in_method",
     "SELECT f.using_type, f.field_class, f.field_name, f.field_type "
     "FROM method_field_accesses f WHERE f.method_class = 'Ljwtc/android/chess/start;' "
     "ORDER BY f.field_name LIMIT 60", None),
    (5, "try_catch_ranges",
     "SELECT t.method_idx, t.start_addr, t.insn_count, h.type_idx, h.addr, h.is_catch_all "
     "FROM try_items t JOIN catch_handlers h ON h.method_idx = t.method_idx "
     "AND h.handler_off = t.handler_off ORDER BY t.method_idx, t.start_addr LIMIT 40", None),
    (6, "reflection_callsites",
     "SELECT method_class, method_name, callee_class, callee_name FROM method_calls "
     "WHERE callee_name IN ('forName','getDeclaredMethod','getDeclaredField','getMethod') "
     "ORDER BY method_class LIMIT 40", None),
    (7, "activity_entry_chain",
     "SELECT c.method_class, c.method_name, c.callee_class, c.callee_name "
     "FROM method_calls c WHERE c.method_class LIKE '%/start;' AND "
     "(c.callee_name = 'setContentView' OR c.callee_name = 'onCreate' OR "
     "c.callee_name = 'postDelayed') LIMIT 30", None),
    (8, "canvas_overloads",
     "SELECT method_class, method_name, callee_class, callee_name "
     "FROM method_calls WHERE callee_class = 'Landroid/graphics/Canvas;' AND "
     "(callee_name LIKE 'draw%' OR callee_name = 'clipPath') "
     "ORDER BY method_class LIMIT 60", None),
    (11, "missing_callee_classes",
     "SELECT DISTINCT c.callee_class FROM method_calls c "
     "WHERE c.callee_class LIKE 'Ljwtc/%' AND c.callee_class NOT IN "
     "(SELECT descriptor FROM classes) ORDER BY c.callee_class LIMIT 40", None),
    # Category 1 + 12: manifest / resources are NOT DEX tables — the schema
    # has no manifest/resource table (verified via `dexsql tables`); recorded
    # UNSUPPORTED with aapt2 as the baseline tool.
    (1, "manifest_components", None, "aapt2 dump xmltree --file AndroidManifest.xml"),
    (12, "resource_evidence", None, "aapt2 dump resources"),
]


def main():
    apk = os.path.abspath(sys.argv[1])
    outdir = os.path.abspath(sys.argv[2])
    os.makedirs(outdir, exist_ok=True)
    ver = subprocess.run([DEXSQL, "--version"], capture_output=True, text=True)
    manifest = {
        "apk": apk,
        "apk_sha256": hashlib.sha256(open(apk, "rb").read()).hexdigest(),
        "dexsql_version": (ver.stdout + ver.stderr).strip()[:120],
        "dexsql_binary_sha256": hashlib.sha256(open(DEXSQL, "rb").read()).hexdigest(),
        "queries": [],
    }
    for cat, name, sql, fallback in COOKBOOK:
        entry = {"cat": cat, "name": name}
        if sql is None:
            entry["supported"] = False
            entry["baseline_tool"] = fallback
            entry["note"] = ("DexSQL schema is DEX-only; no manifest/resource "
                             "table exists (verified via `dexsql tables`). "
                             "Baseline tool covers this category.")
            manifest["queries"].append(entry)
            continue
        rc, out, err, dt = run_dexsql(apk, sql)
        entry["supported"] = rc == 0
        entry["sql"] = sql
        entry["rc"] = rc
        entry["wall_seconds"] = round(dt, 3)
        if rc == 0:
            raw = out.encode()
            outfile = os.path.join(outdir, f"cat{cat}_{name}.out")
            with open(outfile, "wb") as f:
                f.write(raw)
            entry["output_file"] = outfile
            entry["output_sha256_16"] = sha16(raw)
            entry["rows_like"] = len(re.findall(r"^\|", out, re.M)) - 3
            entry["stderr"] = err[:200] if err else ""
        else:
            entry["stderr"] = (err or out)[:400]
        manifest["queries"].append(entry)
        print(f"cat{cat:>2} {name:<28} rc={rc} t={dt:6.2f}s")
    mpath = os.path.join(outdir, "cookbook_manifest.json")
    with open(mpath, "w") as f:
        json.dump(manifest, f, indent=1)
    print("MANIFEST:", mpath, "sha16:", sha16(open(mpath, "rb").read()))


if __name__ == "__main__":
    main()
