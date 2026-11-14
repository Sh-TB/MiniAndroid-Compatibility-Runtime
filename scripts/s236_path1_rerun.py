#!/usr/bin/env python3
"""#596 path-1: post-fix re-runs. Chess full flow (menu -> Practice ->
list row -> board) + OpenSudoku fresh run, with harness v2 raw capture."""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "/tmp/s236_audit/scripts")
from s236_deep_verify import BIN, CH, SU, OUT, run_app, install, census

res = {}

# --- Chess: two-tap flow, longer budget ---
store = Path(tempfile.mkdtemp(prefix="s236_chessfix_root_"))
out = Path(tempfile.mkdtemp(prefix="s236_chessfix_out_"))
pkg = install(CH, store)
rec = run_app(store, pkg, out, "chessfix_flow", 48,
              taps=["540,110@8", "540,210@24"])
raw = (OUT / "chessfix_flow.stdout.log").read_text(errors="replace")
serr = (OUT / "chessfix_flow.stderr.log").read_text(errors="replace")
res["chess"] = {
    "rc": rec["rc"], "duration_s": rec["duration_s"],
    "stdout_markers": {m: raw.count(m) for m in (
        "loadPGN", "FEN", "board", "practice", "rawQuery rows=1",
        "SQLITE-INSERT", "PRAGMA table_info(games)")},
    "stderr_markers": {m: serr.count(m) for m in (
        "F596-P1", "371-GETXML-NOTFOUND", "uncaught", "C013-ONDRAW",
        "practice.pgn", "AssetManager", "IllegalStateException",
        "loadPGNHead", "FEN", "onDraw")},
    "census": census(store),
}
# screenshot copy for the receipt
src_shot = out / "screenshot.png"
if src_shot.exists():
    (OUT / "chessfix_flow.screenshot.png").write_bytes(src_shot.read_bytes())

# --- OpenSudoku: longer run with the Instant fix ---
store2 = Path(tempfile.mkdtemp(prefix="s236_sudokufix_root_"))
out2 = Path(tempfile.mkdtemp(prefix="s236_sudokufix_out_"))
pkg2 = install(SU, store2)
rec2 = run_app(store2, pkg2, out2, "sudokufix_80f", 80)
raw2 = (OUT / "sudokufix_80f.stdout.log").read_text(errors="replace")
serr2 = (OUT / "sudokufix_80f.stderr.log").read_text(errors="replace")
res["sudoku"] = {
    "rc": rec2["rc"], "duration_s": rec2["duration_s"],
    "stdout_markers": {m: raw2.count(m) for m in (
        "ListView", "folder", "getView", "SQLITE-INSERT")},
    "stderr_markers": {m: serr2.count(m) for m in (
        "F596-P1", "f141-null-recv", "uncaught", "Instant.now",
        "toEpochMilli", "rawQuery", "SQLITE-LIFECYCLE", "SimpleCursorAdapter",
        "getView", "C013-ONDRAW", "onLayout", "NotFoundException")},
    "census": census(store2),
}
src2 = out2 / "screenshot.png"
if src2.exists():
    (OUT / "sudokufix_80f.screenshot.png").write_bytes(src2.read_bytes())

(OUT / "path1_rerun_results.json").write_text(json.dumps(res, indent=1) + "\n")
print(json.dumps(res, indent=1))
