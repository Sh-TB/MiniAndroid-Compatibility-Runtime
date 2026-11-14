#!/usr/bin/env python3
"""#596 §1.4: OpenSudoku real UI chain with harness v2 — raw logs retained."""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "/tmp/s236_audit/scripts")
from s236_deep_verify import SU, OUT, run, run_app, install, census, markers_from_raw

store = Path(tempfile.mkdtemp(prefix="s236_sudoku_596_root_"))
out = Path(tempfile.mkdtemp(prefix="s236_sudoku_596_out_"))
pkg = install(SU, store)
rec = run_app(store, pkg, out, "sudoku_596_40f", 40)
raw = (OUT / "sudoku_596_40f.stdout.log").read_text(errors="replace")
serr = (OUT / "sudoku_596_40f.stderr.log").read_text(errors="replace")
res = {
    "pkg": pkg, "rc": rec["rc"], "duration_s": rec["duration_s"],
    "stdout_bytes": rec["stdout_bytes"], "stderr_bytes": rec["stderr_bytes"],
    "stdout_markers": markers_from_raw(rec),
    "stderr_markers": {m: serr.count(m) for m in (
        "SQLITE-SHADOW] rawQuery", "SQLITE-SHADOW] query", "SimpleCursorAdapter",
        "getView", "S191", "C013-ONDRAW", "ListView", "measure", "onLayout",
        "uncaught", "NotFoundException", "folder", "provider")},
    "census": census(store),
}
(OUT / "sudoku_596_result.json").write_text(json.dumps(res, indent=1) + "\n")
print(json.dumps(res["stderr_markers"]))
print("census:", res["census"])
print("rc:", res["rc"], "stderr_bytes:", res["stderr_bytes"])
