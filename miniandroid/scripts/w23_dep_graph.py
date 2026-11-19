#!/usr/bin/env python3
"""w23_dep_graph.py — MiniAndroid include-graph & header fan-out analyzer (W23-02).

Parses every project header/source for quoted #include directives, resolves them
the same way the compiler does (includer's dir first, then the Makefile -I list),
builds the transitive include DAG, and reports for every header:
  - fan-out: how many linked translation units transitively depend on it
  - cascade cost: sum of those TUs' measured W22 compile seconds (the seconds a
    one-line edit to this header costs in a -j1 production rebuild)
  - max single-TU cost, list of affected TUs

Also emits, per TU, its own direct-include count and transitive include weight
(lines of header text pulled in), to locate expensive transitive chains.

Output: JSON to --out (default evidence/w23/dep_graph.json) and a Markdown
summary to --md (default evidence/w23/dep_graph_summary.md).

Usage: python3 scripts/w23_dep_graph.py [--srcdir src] [--out PATH] [--md PATH]
"""
import argparse
import collections
import json
import os
import re
import sys

REPO = os.environ.get("MINIANDROID_REPO", "/home/z/my-project/miniandroid")

# W22 measured per-TU compile seconds (evidence/w22/W22_BUILD_BASELINE.md +
# tu-slot profile of prod_build_fresh.log). 0 = unknown/default small TU.
# These are compile-slot seconds at -j1 production profile on this host.
W22_TU_SECONDS = {
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
DEFAULT_TU_SECONDS = 3.9  # measured average of the 78-slot long tail

INCLUDE_RE = re.compile(r'^\s*#\s*include\s*"([^"]+)"')
ANGLE_RE = re.compile(r'^\s*#\s*include\s*<([^>]+)>')

# -I order from the Makefile (base INCLUDES)
IDIRS = ["src", "src/webview", "src/apk", "src/dex", "src/runtime", "src/api",
         "src/graphics", "src/diagnostics", "src/resources", "src/renderer",
         "src/framework", "src/storage", "src/fonts", "src/gles", "src/jni",
         "src/audio", "third_party/portablegl", "/usr/include/freetype2",
         "third_party/nlohmann_json/include"]


def resolve(inc, includer_dir):
    """Resolve a quoted include exactly like the compiler search order."""
    cand = os.path.normpath(os.path.join(includer_dir, inc))
    if os.path.isfile(os.path.join(REPO, cand)):
        return cand
    for d in IDIRS:
        cand = os.path.normpath(os.path.join(REPO, d, inc))
        if os.path.isfile(cand):
            return os.path.relpath(cand, REPO)
    return None  # not a project file (system/third_party with own -I)


def parse():
    headers = {}     # relpath -> line count
    deps = {}        # relpath -> set of direct project includes (relpaths)
    srcs = []
    for root, dirs, files in os.walk(os.path.join(REPO, "src")):
        for f in files:
            p = os.path.join(root, f)
            rel = os.path.relpath(p, REPO)
            if f.endswith((".h", ".hpp")):
                headers[rel] = sum(1 for _ in open(p, encoding="utf-8", errors="replace"))
            if f.endswith(".cpp"):
                srcs.append(rel)
    for rel in sorted(headers) + sorted(srcs):
        d = set()
        ddir = os.path.dirname(os.path.join(REPO, rel))
        for i, line in enumerate(open(os.path.join(REPO, rel),
                                      encoding="utf-8", errors="replace")):
            m = INCLUDE_RE.match(line)
            if m:
                r = resolve(m.group(1), ddir)
                if r:
                    d.add(r)
        deps[rel] = d
    return headers, deps, srcs


def transitive_closure(deps, start):
    seen = set()
    stack = list(deps[start])
    while stack:
        h = stack.pop()
        if h in seen:
            continue
        seen.add(h)
        stack.extend(deps.get(h, ()))
    return seen


def reverse_closure(deps, targets):
    """For each target file, which .cpps transitively include it."""
    consumers = collections.defaultdict(set)
    for cpp in [k for k in deps if k.endswith(".cpp")]:
        for h in transitive_closure(deps, cpp):
            consumers[h].add(cpp)
    return consumers


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="evidence/w23/dep_graph.json")
    ap.add_argument("--md", default="evidence/w23/dep_graph_summary.md")
    ap.add_argument("--linked-only", action="store_true",
                    help="only count TUs that are linked (core_sources.manifest)")
    args = ap.parse_args()

    headers, deps, srcs = parse()

    # linked TU set: manifest (single source of truth)
    manifest = []
    mf = os.path.join(REPO, "core_sources.manifest")
    for line in open(mf):
        line = line.strip()
        if line and not line.startswith("#"):
            manifest.append(line)
    linked = set(manifest)

    consumers = reverse_closure(deps, None)

    # per-header cascade cost over LINKED TUs only
    rows = []
    for h, hl in headers.items():
        tus = sorted(c for c in consumers.get(h, set()) if c in linked)
        cost = sum(W22_TU_SECONDS.get(t, DEFAULT_TU_SECONDS) for t in tus)
        maxt = max((W22_TU_SECONDS.get(t, DEFAULT_TU_SECONDS) for t in tus), default=0.0)
        rows.append({
            "header": h, "lines": hl, "fanout": len(tus),
            "cascade_s": round(cost, 1), "max_tu_s": maxt,
            "tus": tus,
        })
    rows.sort(key=lambda r: (-r["cascade_s"], -r["fanout"]))

    # per-TU include weight
    tu_rows = []
    for cpp in sorted(linked):
        cl = transitive_closure(deps, cpp)
        hdrs = [h for h in cl if h in headers]
        w = sum(headers[h] for h in hdrs)
        tu_rows.append({"tu": cpp, "direct": len(deps[cpp]),
                        "transitive_headers": len(hdrs),
                        "header_lines": w,
                        "own_seconds": W22_TU_SECONDS.get(cpp, DEFAULT_TU_SECONDS)})
    tu_rows.sort(key=lambda r: -r["header_lines"])

    os.makedirs(os.path.dirname(os.path.join(REPO, args.out)), exist_ok=True)
    with open(os.path.join(REPO, args.out), "w") as f:
        json.dump({"headers": rows, "tus": tu_rows,
                   "n_headers": len(headers), "n_linked_tus": len(linked)}, f, indent=1)

    with open(os.path.join(REPO, args.md), "w") as f:
        f.write("# W23 include-graph summary (auto: scripts/w23_dep_graph.py)\n\n")
        f.write("## Header cascade cost ranking (linked TUs, W22 seconds)\n\n")
        f.write("| header | lines | fan-out | cascade s | max TU s |\n|---|---:|---:|---:|---:|\n")
        for r in rows[:35]:
            f.write("| %s | %d | %d | %.1f | %.1f |\n" % (
                r["header"], r["lines"], r["fanout"], r["cascade_s"], r["max_tu_s"]))
        f.write("\n## TU header weight ranking\n\n")
        f.write("| TU | direct includes | transitive headers | header lines | own s |\n|---|---:|---:|---:|---:|\n")
        for r in tu_rows[:25]:
            f.write("| %s | %d | %d | %d | %.1f |\n" % (
                r["tu"], r["direct"], r["transitive_headers"], r["header_lines"], r["own_seconds"]))

    # console short report
    print("headers=%d linked_tus=%d" % (len(headers), len(linked)))
    print("top-12 cascade headers:")
    for r in rows[:12]:
        print("  %-55s lines=%-5d fanout=%-2d cascade=%6.1fs max_tu=%.1f" % (
            r["header"], r["lines"], r["fanout"], r["cascade_s"], r["max_tu_s"]))
    print("\ndalvik_engine.h consumers (%d):" % len(
        next(r for r in rows if r["header"] == "src/dex/dalvik_engine.h")["tus"]))
    for t in next(r for r in rows if r["header"] == "src/dex/dalvik_engine.h")["tus"]:
        print("  ", t, "%.1fs" % W22_TU_SECONDS.get(t, DEFAULT_TU_SECONDS))


if __name__ == "__main__":
    main()
