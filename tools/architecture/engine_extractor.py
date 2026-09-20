#!/usr/bin/env python3
"""engine_extractor.py — static extraction of MiniAndroid's live engine structure.

§2 GRAPH (SOURCE-LINKED campaign): every graph node/edge below is EXTRACTED
from the real source tree — no hand-decorated annotations.

Outputs (docs/foundation/graph/):
  served_api.json         (class, method) pairs the engine/shadows dispatch on
                          — with the honest per-block over-approximation flag
  class_graph.json        C++ class/struct inheritance + defining header
  subsystem_graphs.json   render / lifecycle / input / resource / runtime
                          stage chains extracted from the LIVE TUs

Parse law: functions are detected line-wise (K&R brace-on-same-line style used
by this codebase): a header line matching FUNC_RE opens a balanced-brace body.
Dead TUs (S68_BUILD_GRAPH verdicts) are excluded — never graph the dead one.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path("/home/z/my-project")
SRC = ROOT / "miniandroid" / "src"
OUT = ROOT / "docs" / "foundation" / "graph"

DISPATCH_TUS = [
    "src/dex/dalvik_engine.cpp",
    "src/framework/android_shadows.cpp",
    "src/framework/shadow_registry.cpp",
    "src/framework/canvas_shadow.cpp",
    "src/framework/bitmap_shadow.cpp",
    "src/framework/touch_dispatcher.cpp",
    "src/framework/state_list.cpp",
    "src/framework/lifecycle_controller.cpp",
    "src/framework/choreographer_shadow.cpp",
    "src/framework/dialog_shadow.cpp",
    "src/framework/clipboard_shadow.cpp",
    "src/framework/executor_shadow.cpp",
    "src/framework/pending_intent_shadow.cpp",
    "src/framework/locks_shadow.cpp",
    "src/framework/atomic_shadow.cpp",
    "src/api/application_context.cpp",
    "src/api/shared_prefs.cpp",
    "src/resources/layout_inflater.cpp",
    "src/resources/resource_runtime.cpp",
]

STAGE_TUS = {
    "render": ["src/renderer/software_renderer.cpp", "src/fonts/text_shaper.cpp",
               "src/framework/canvas_shadow.cpp"],
    "lifecycle": ["src/runtime/application_runtime.cpp",
                  "src/framework/lifecycle_controller.cpp"],
    "input": ["src/framework/touch_dispatcher.cpp",
              "src/runtime/application_runtime.cpp"],
    "resource": ["src/resources/arsc_parser.cpp", "src/resources/axml_parser.cpp",
                 "src/resources/layout_inflater.cpp", "src/resources/resource_runtime.cpp",
                 "src/resources/resource_parser.cpp", "src/resources/res_config.cpp"],
    "runtime": ["src/dex/dalvik_engine.cpp", "src/dex/class_resolver.cpp",
                "src/runtime/application_runtime.cpp"],
}

CLASS_RE = re.compile(
    r"^\s*(?:template\s*<[^>]*>\s*)?(?:class|struct)\s+([A-Za-z_][A-Za-z0-9_]*)"
    r"(?:\s*:\s*([^{]+))?\s*\{?[;]?\s*(?://.*)?$")
# function-definition header: brace ON the header line (this codebase's style)
FUNC_RE = re.compile(
    r"^(?:[A-Za-z_][\w:<>,&*\s\-]*[\s*&])?\s*(?:~)?\b([A-Za-z_][A-Za-z0-9_]*)\s*\("
    r"[^;{}]*\)\s*(?:const\s*)?(?:noexcept\s*)?\{\s*$")
# method/class guard string comparisons inside dispatch bodies
GUARD_RE = re.compile(
    r'(?:class_name|method_name|name|class_desc|method|api_class|field_name)\s*==\s*"([^"]+)"')
CALL_RE = re.compile(r'\b([A-Za-z_][A-Za-z0-9_]*)\s*\(')

CONTROL = {"if", "for", "while", "switch", "return", "sizeof", "catch", "else"}


def strip_comments_strings(text: str) -> str:
    out = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c == '"':
            i += 1
            while i < n and text[i] != '"':
                i += 2 if text[i] == "\\" else 1
            i += 1
            out.append('""')
        elif c == "'":
            i += 2
            out.append("''")
        elif c == '/' and i + 1 < n and text[i + 1] == '/':
            j = text.find("\n", i)
            i = j if j != -1 else n
        elif c == '/' and i + 1 < n and text[i + 1] == '*':
            j = text.find("*/", i)
            i = j + 2 if j != -1 else n
        else:
            out.append(c)
            i += 1
    return "".join(out)


def parse_functions(path: Path) -> list[dict]:
    """Line-wise function detection + balanced-brace body capture."""
    try:
        raw = path.read_text(errors="replace")
    except FileNotFoundError:
        return []
    text = strip_comments_strings(raw)
    lines = text.splitlines()
    funcs = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if line.startswith((" ", "\t", "}", "#")) or not line.strip():
            i += 1
            continue
        m = FUNC_RE.match(line)
        if not m:
            i += 1
            continue
        name = m.group(1)
        if name in CONTROL or name in ("namespace", "struct", "class", "enum"):
            i += 1
            continue
        # balanced brace walk from this line
        depth = line.count("{") - line.count("}")
        j = i + 1
        while depth > 0 and j < n:
            depth += lines[j].count("{") - lines[j].count("}")
            j += 1
        body = "\n".join(lines[i + 1:j])
        guards = sorted(set(GUARD_RE.findall(body)))
        calls = sorted({c for c in CALL_RE.findall(body)
                        if c not in CONTROL and c != name})
        funcs.append({"name": name, "start_line": i + 1, "end_line": j,
                      "guards": guards, "calls": calls,
                      "bytes": len(body)})
        i = j
    return funcs


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    all_funcs = {}
    tus = sorted(set(DISPATCH_TUS) | {t for ts in STAGE_TUS.values() for t in ts})
    for tu in tus:
        all_funcs[tu] = parse_functions(ROOT / "miniandroid" / tu)

    # ── served API surface ────────────────────────────────────────────────
    served = []
    for tu in DISPATCH_TUS:
        for f in all_funcs[tu]:
            guards = f["guards"]
            classes = [g for g in guards if g.startswith("L") and g.endswith(";")]
            plain = [g for g in guards if not (g.startswith("L") and g.endswith(";"))]
            for c in set(classes):
                for m in set(plain):
                    served.append({"class": c, "method": m, "tu": tu,
                                   "function": f["name"], "line": f["start_line"],
                                   "extraction": "function-guard (over-approx)"})
    (OUT / "served_api.json").write_text(json.dumps({
        "note": "Static extraction of (class,method) string-guard pairs per "
                "dispatch function. Cross-product within a function is an honest "
                "OVER-approximation; live run traces are ground truth.",
        "count": len(served), "pairs": served}, indent=1))

    # ── class graph ───────────────────────────────────────────────────────
    classes = []
    for h in sorted(SRC.rglob("*.h")):
        rel = str(h.relative_to(ROOT / "miniandroid"))
        try:
            for line in h.read_text(errors="replace").splitlines():
                m = CLASS_RE.match(line)
                if m:
                    name, bases = m.group(1), (m.group(2) or "")
                    blist = [b.strip().split("::")[-1].split("<")[0]
                             for b in bases.split(",") if b.strip()]
                    classes.append({"class": name, "header": rel, "bases": blist})
        except FileNotFoundError:
            continue
    (OUT / "class_graph.json").write_text(json.dumps(
        {"count": len(classes), "classes": classes}, indent=1))

    # ── stage graphs ──────────────────────────────────────────────────────
    graphs = {}
    for stage, stus in STAGE_TUS.items():
        nodes, edges = {}, set()
        for tu in stus:
            fs = all_funcs[tu]
            names = {f["name"] for f in fs}
            for f in fs:
                nodes[f"{tu}::{f['name']}"] = {"line": f["start_line"],
                                               "guards": f["guards"][:8]}
            for f in fs:
                for callee in f["calls"]:
                    if callee in names:
                        edges.add((f"{tu}::{f['name']}", f"{tu}::{callee}"))
        graphs[stage] = {"tus": stus, "node_count": len(nodes),
                         "nodes": nodes, "edges": sorted(list(e) for e in edges)}

    (OUT / "subsystem_graphs.json").write_text(json.dumps({
        "note": "Stage graphs: nodes = functions extracted from the LIVE TUs; "
                "edges = intra-TU name-calls (static). Dead TUs excluded.",
        "stages": graphs}, indent=1))

    print(f"served_api: {len(served)} pairs | classes: {len(classes)} | stages: "
          + str({k: v['node_count'] for k, v in graphs.items()}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
