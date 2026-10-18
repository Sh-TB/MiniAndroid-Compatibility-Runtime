#!/usr/bin/env python3
# cont98_registry_update.py — register the CONT-98 T6 outcome (F-NEW-401,
# the Cursor/database contract laws) in root_registry.json and mirror it to
# canonical/root_cause_registry.json.
import json

PATH = "root_registry.json"
MIRROR = "canonical/root_cause_registry.json"

with open(PATH) as f:
    reg = json.load(f)
roots = reg["roots"] if isinstance(reg, dict) and "roots" in reg else reg
if isinstance(roots, dict):
    root_list = list(roots.values())
    dict_mode = True
else:
    root_list = roots
    dict_mode = False

n0 = len(root_list)
ids = {r.get("id") for r in root_list}
assert "F-NEW-401" not in ids, "F-NEW-401 already registered"

entry = {
    "id": "F-NEW-401",
    "status": "ROOT-CAUSED-FIXED",
    "priority": "P0",
    "title": "CONT-98 T6 Cursor contract: SQLiteCursor shadow violated the AOSP AbstractCursor/CursorWindow dynamic-typing and bounds laws (REAL cells collapsed to int64; out-of-row access returned silent engine defaults; 14 cursor methods missing)",
    "layer": "storage/cursor-shadow",
    "directive": "#364 CONT-98 T6 (comment 6248212134) — Cursor and database contract beyond file existence",
    "root_cause": "raw_query_common materialized SQLITE_FLOAT into an int64 Cell (2.5 -> 2 — silent data corruption) and had no DOUBLE kind; cursor_dispatch had no position predicates (getPosition/isBeforeFirst/isAfterLast/isFirst/isLast/isClosed), no moveToLast/moveToPrevious, no getType/getDouble/getFloat/getShort/getColumnName/getColumnIndexOrThrow; getString answered non-STRING cells with \"\" (INTEGER 1 -> \"\"; NULL -> \"\" instead of null); getInt answered TEXT with 0 (no sqlite3Atoi64 leading-prefix law: '42abc' -> 0, '  -7xyz' -> 0); moveToPosition clamped negative positions to count (AOSP parks at -1/beforeFirst); and every out-of-row getter fell through to the engine default (silent 0/\"\") instead of the AbstractCursor.checkPosition CursorIndexOutOfBoundsException law.",
    "fix": "src/storage/sqlite_shadow.{h,cpp}: (1) Cell gains DOUBLE kind; raw_query_common keeps SQLITE_FLOAT exact via sqlite3_column_double. (2) Conversion laws: getString TEXT->as-is / INTEGER->decimal / REAL->SQLite %.15g text (integral reals keep '.0') / NULL->handled_null; getInt/getLong/getShort TEXT->strtoll leading prefix, REAL->truncate toward zero, NULL->0; getDouble/getFloat TEXT->strtod prefix. (3) getType FIELD_TYPE_{NULL=0,INTEGER=1,FLOAT=2,TEXT=3}. (4) Position laws: moveToPosition(<0) parks -1, (>=count) parks count; moveToLast/moveToPrevious AOSP parking; getPosition/isBeforeFirst/isAfterLast/isFirst/isLast/isClosed (empty-cursor law: before/after predicates false). (5) getColumnIndexOrThrow throws IllegalArgumentException(\"Unknown column 'x'\"); getColumnName bounds-checked with the ART AIOOBE message format. (6) AbstractCursor.checkPosition law: accessors at pos==-1 throw CursorIndexOutOfBoundsException(\"Before first row.\"), at pos==count throw (\"After last row.\") via the F-NEW-259g-a shadow exception channel; bad column indexes guarded the same way (was an unchecked host read). Loud [SQLITE-SHADOW] provenance lines accompany each throw. Honest scope notes: BLOB kind (FIELD_TYPE 4) not materialized yet; requery deliberately NOT faked (cursor is a materialized set).",
    "evidence": {
        "wave": "CONT-98",
        "fixture": "fixtures/cont98_cursor_probe (real aapt2/ECJ/D8; apk run/cont98/c98cur.apk sha16 5898381c801cf187, V2-C98)",
        "paired_ab": "PRE binary d90541058611608c (frozen CONT-97 baseline, stash-rebuilt byte-identical): 6/18 rows PASS; POST binary e51d7a643e6817ba: 18/18 PASS. Same probe, same harness command.",
        "rows_fixed": "STR-INT getInt-cell->'1'; NULLSTR null not ''; GETTYPE [1,3,2,0]; DOUBLE 2.5 exact (was 0/2); INT-TEXT '42abc'->42 '  -7xyz'->-7 (was 0,0); POSITIONS moveToLast/Previous/predicates; MOVEPOS pos(-1)->beforeFirst (was parked afterLast); OOB-BEFORE/AFTER CursorIndexOutOfBoundsException exact AOSP messages (was silent defaults); IDXORTHROW IAE (was silent); CLOSE isClosed=true",
        "determinism_proof": "stash-rebuild reproduced d90541058611608c byte-identically; pop-rebuild reproduced e51d7a643e6817ba byte-identically (x2 each across the perf1 A/B)",
        "regression": "wall 12/12 MATCH byte-identical (dooz 31ddd4d5b8e6d18e, opencalc f25b754c4565c38b, unote 90a67cc1ddda57b7, microtimer bbd350b6c14fbd52, x3); goldens 4/4; negatives 19/19; reinstall 8/8; MG-310 7/7; MG-150 3/3; selftests 13/13; F-NEW-376 70/70 (c72 probes rebuilt in-container: c72priv_v1 1e212250c1a8b1ad, v2 89af054a64041371); anchors sax1 PASS events=6/6, clock1 4/4, clinit1 law-correct, c74esc containment OK, perf1 checksums byte-identical A/B (3688000/31744000/14534196240/14569628240 both binaries)",
        "honest_notes": "negatives needed a container-fresh sequence repair: run/gatea/gate_a_probe.apk was rebuilt (cont9 script, sha c5dd91e799f2b3f9) and the probe RUN step that produces gate_a_results.jsonl was missing in this container — the interim 9/19 was a sequence artifact, not a runtime regression; 19/19 after the canonical install+run. POST harness runs exit rc=1 identical to PRE (paired, non-behavioral).",
    },
}

if dict_mode:
    reg["roots"]["F-NEW-401"] = entry
    out = reg
else:
    root_list.append(entry)
    out = root_list

# Top-level LIST file (1-space indent, ensure_ascii=False) — keep the
# committed shape so the diff is exactly the one appended entry.
with open(PATH, "w") as f:
    json.dump(out, f, indent=1, ensure_ascii=False)
    f.write("\n")

with open(MIRROR, "w") as f:
    json.dump(out, f, indent=1, ensure_ascii=False)
    f.write("\n")

final = out["roots"] if isinstance(out, dict) and "roots" in out else out
print(f"registry {n0} -> {len(final)} roots; F-NEW-401 registered")
