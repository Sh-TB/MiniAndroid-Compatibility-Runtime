#!/usr/bin/env python3
"""w23_fanout_from_d.py — ground-truth header fan-out from gcc -MMD dep files.

Reads every build/**/*.d (or a given build dir), extracts each linked TU's
full transitive header closure as recorded by the compiler, and prints the
reverse fan-out table: for each project header, how many linked TUs depend on
it and the estimated cascade seconds (W22 per-TU slot weights).

Usage: python3 scripts/w23_fanout_from_d.py [build_dir] [--json OUT]
"""
import collections
import glob
import json
import os
import sys

REPO = os.environ.get("MINIANDROID_REPO", "/home/z/my-project/miniandroid")
W22 = {
    "src/runtime/execution_engine.cpp": 38.01,
    "src/dex/dalvik_bridge_domain_ui_graphics.cpp": 32.45,
    "src/dex/dalvik_bridge_domain_app_runtime.cpp": 29.78,
    "src/dex/dalvik_bridge_domain_io_lang.cpp": 28.12,
    "src/dex/dalvik_bridge_domain_android_core.cpp": 25.08,
    "src/dex/dalvik_engine_core.cpp": 22.04,
    "src/dex/dalvik_engine_invoke.cpp": 21.39,
    "src/dex/dalvik_bridge_domain_jdk.cpp": 21.28,
    "src/runtime/application_runtime.cpp": 20.64,
    "src/dex/dalvik_interpreter.cpp": 20.43,
}
DEF = 3.9


def main():
    bdir = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "build"
    deps = collections.defaultdict(set)
    for d in glob.glob(os.path.join(REPO, bdir, "**", "*.d"), recursive=True):
        txt = open(d).read().replace("\\\n", " ")
        body = txt.split(":", 1)[1].split()
        cpps = [p for p in body if p.endswith(".cpp")]
        if not cpps:
            continue
        cpp = os.path.relpath(cpps[0], REPO) if cpps[0].startswith("/") else cpps[0]
        for p in body:
            rp = os.path.relpath(p, REPO) if p.startswith("/") else p
            if rp.endswith((".h", ".hpp")) and (rp.startswith("src/") or rp.startswith("third_party/")):
                deps[rp].add(cpp)
    rows = []
    for h, ts in deps.items():
        rows.append({"header": h, "fanout": len(ts),
                     "cascade_s": round(sum(W22.get(t, DEF) for t in ts), 1),
                     "tus": sorted(ts)})
    rows.sort(key=lambda r: (-r["cascade_s"], -r["fanout"]))
    if "--json" in sys.argv:
        out = sys.argv[sys.argv.index("--json") + 1]
        with open(out, "w") as f:
            json.dump(rows, f, indent=1)
        print("wrote", out)
    print("%-50s %7s %9s" % ("header", "fanout", "cascade_s"))
    for r in rows[:20]:
        print("%-50s %7d %9.1f" % (r["header"], r["fanout"], r["cascade_s"]))


if __name__ == "__main__":
    main()
