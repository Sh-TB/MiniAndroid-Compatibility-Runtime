#!/usr/bin/env python3
"""#596 §1.2: the causality pair at a 240-frame budget, independent fresh
roots, same binary, same APK, same env except the probe flag. Persists raw
logs + censuses + run metadata via harness v2. Greps the thread-pump
lifecycle markers (R-NEW-345 consume_pending_start / run_thread_start_body)
and the seed INSERTs from the retained raw stdout.
"""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "/tmp/s236_audit/scripts")
from s236_deep_verify import (BIN, CH, OUT, run, run_app, install,
                              census, markers_from_raw)

results = {}
for tag, env in (("pairA_240_probeOFF", None),
                 ("pairB_240_probeON",
                  {"MINIANDROID_S236_PROBE_DEFER_DRAW": "1"})):
    store = Path(tempfile.mkdtemp(prefix=f"s236_{tag}_root_"))
    out = Path(tempfile.mkdtemp(prefix=f"s236_{tag}_out_"))
    pkg = install(CH, store)
    rec = run_app(store, pkg, out, tag, 240, env=env)
    raw = (OUT / f"{tag}.stdout.log").read_text(errors="replace")
    thread_marks = {m: raw.count(m) for m in (
        "R-NEW-345", "consume_pending_start", "run_thread_start_body",
        "THREAD", "run() body", "PRAGMA table_info(games)",
        "PRAGMA user_version", "SQLITE-SHADOW] rawQuery",
        "SQLITE-SHADOW] insert", "SQLITE-INSERT", "CV-PUT",
        "C013-ONDRAW")}
    results[tag] = {"pkg": pkg, "rc": rec["rc"],
                    "duration_s": rec["duration_s"],
                    "timed_out": rec["timed_out"],
                    "stdout_bytes": rec["stdout_bytes"],
                    "census": census(store), "markers": thread_marks}
    print(tag, "rc", rec["rc"], "dur", rec["duration_s"],
          "census", results[tag]["census"], "marks", thread_marks)

(OUT / "causality_pair_240.json").write_text(json.dumps(results, indent=1) + "\n")
print("PAIR DONE")
