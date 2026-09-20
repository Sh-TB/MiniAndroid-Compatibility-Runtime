#!/usr/bin/env python3
"""engine_extractor.py — static extraction of MiniAndroid's live engine structure.

S70 UPGRADE (RUNTIME UNDERSTANDING campaign):
  S69 BUG #1  FUNC_RE could not parse `Class::method(...) {` definitions (the
              dominant style in dalvik_engine.cpp) -> 19 of ~hundreds of
              functions parsed from a 30k-line TU.
  S69 BUG #2  GUARD_RE only knew 7 variable names; this codebase dispatches on
              cls/cd/act/op/current_class_/... -> served_api came out EMPTY
              (0 pairs) and api_matrix mislabeled implemented APIs as UNSERVED
              (verified: Color.rgb dalvik_engine.cpp:18290, Canvas.clipRect
              canvas_shadow.cpp:1347 both live in the engine but UNSERVED in
              the S69 matrix).
  S70 FIX     brace-style-agnostic function parser + variable-agnostic string
              guard extraction + nearest-preceding-class pairing for served
              pairs + full function-node dump (functions.json) that feeds the
              ACTIVE runtime knowledge graph.

Outputs (docs/foundation/graph/):
  served_api.json    (class,method) pairs the engine dispatches on
                     — extraction law recorded per pair (honest over-approx)
  functions.json     every parsed dispatch function: guards, calls, lines
                     — backbone for DISPATCHES_TO / IMPLEMENTED_BY edges
  class_graph.json   C++ class/struct inheritance + defining header
  subsystem_graphs.json  render/lifecycle/input/resource/runtime stage chains

Parse law: functions are detected line-wise; a column-0 line ending in `{`
whose paren group closes before the brace opens a balanced-brace body.
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

# S70: function-definition header — brace on the header line, ANY return type
# (namespaces/templates/pointers/references), free OR scoped `Class::name`.
#   group(1) = possibly-qualified name (we keep the last ::-segment)
FUNC_RE = re.compile(
    r"^(?P<ret>[A-Za-z_][\w:<>,&*\s\-\[\]~]*?)?\b(?P<name>[A-Za-z_][A-Za-z0-9_]*"
    r"(?:::[A-Za-z_][A-Za-z0-9_]*)*)\s*\((?P<params>[^;{}()]*)\)\s*"
    r"(?:const\s*)?(?:noexcept\s*)?(?:->\s*[\w:<>,&*\s]+)?\{\s*$")

# S70: ANY string-literal equality guard, variable-agnostic. Values that look
# like DEX descriptors ("L...;") are class guards; everything else is a
# method/op/field guard. Variable naming is NOT trusted (S69 BUG #2).
GUARD_ANY_RE = re.compile(r'==\s*"([^"]+)"')
# S70: substring class-guards — the engine dispatches some families via
# class_name.find("X") != npos (e.g. Context/Activity/Resources families,
# F-033 getSystemService). These are class CANDIDATES (over-approx).
SUBSTR_GUARD_RE = re.compile(
    r'(?:class_name|declaring_class|current_class_|cls)\.find\("([^"]+)"\)')

CALL_RE = re.compile(r'\b([A-Za-z_][A-Za-z0-9_]*)\s*\(')

CONTROL = {"if", "for", "while", "switch", "return", "sizeof", "catch", "else",
           "namespace", "struct", "class", "enum", "do"}


def strip_comments_strings(text: str) -> str:
    """Comments AND string contents removed (brace-accurate body capture)."""
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
            j = j + 2 if j != -1 else n
            # S70: preserve every newline the comment spanned so that line
            # numbers stay aligned with the raw file (bodies are re-sliced
            # from the string-keeping text using the parsed line numbers).
            out.append("\n" * text.count("\n", i, j))
            i = j
        else:
            out.append(c)
            i += 1
    return "".join(out)


def strip_comments_keep_strings(text: str) -> str:
    """S70: comments removed, STRING LITERALS PRESERVED — guard extraction
    must see `method == "rgb"`. (S69 stripped strings first, so its guard
    pass was structurally incapable of finding any pair.)"""
    out = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c == '"':
            j = i + 1
            while j < n and text[j] != '"':
                j += 2 if text[j] == "\\" else 1
            j = min(j + 1, n)
            out.append(text[i:j])
            i = j
        elif c == "'":
            j = min(i + 2, n)
            out.append(text[i:j])
            i = j
        elif c == '/' and i + 1 < n and text[i + 1] == '/':
            j = text.find("\n", i)
            i = j if j != -1 else n
        elif c == '/' and i + 1 < n and text[i + 1] == '*':
            j = text.find("*/", i)
            j = j + 2 if j != -1 else n
            # S70: preserve every newline the comment spanned so that line
            # numbers stay aligned with the raw file (bodies are re-sliced
            # from the string-keeping text using the parsed line numbers).
            out.append("\n" * text.count("\n", i, j))
            i = j
        else:
            out.append(c)
            i += 1
    return "".join(out)


HDR_CLOSE_RE = re.compile(
    r"\)\s*(?:const\s*)?(?:noexcept\s*)?(?:->\s*[\w:<>,&*\s]+)?\{\s*$")


def parse_functions(path: Path) -> list[dict]:
    """Line-wise function detection + balanced-brace body capture.

    S70: accepts `Class::name(...)` and any return type; single-line AND
    MULTI-LINE signatures (e.g. bridge_to_api — the engine's central
    dispatch — wraps its parameter list across lines; the S69 parser missed
    every one of them). A column-0 line that opens a paren but does not
    close it is joined with continuation lines (max 12) until the signature
    closes with `... { `.
    """
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
        if "(" not in line or line.rstrip().startswith("//"):
            i += 1
            continue
        # ── assemble the logical header line (join continuations) ────────
        header = line
        hdr_line_end = i
        ok = HDR_CLOSE_RE.search(header)
        joined = 0
        while not ok and joined < 12 and hdr_line_end + 1 < n:
            hdr_line_end += 1
            joined += 1
            header += " " + lines[hdr_line_end].strip()
            ok = HDR_CLOSE_RE.search(header)
        if not ok:
            i += 1
            continue
        m = FUNC_RE.match(header)
        if not m:
            i += 1
            continue
        qual = m.group("name")
        name = qual.split("::")[-1] if "::" in qual else qual
        if name in CONTROL or qual in CONTROL:
            i = hdr_line_end + 1
            continue
        # balanced brace walk from the line carrying the opening brace
        depth = lines[hdr_line_end].count("{") - lines[hdr_line_end].count("}")
        j = hdr_line_end + 1
        while depth > 0 and j < n:
            depth += lines[j].count("{") - lines[j].count("}")
            j += 1
        body = "\n".join(lines[hdr_line_end + 1:j])
        guards = GUARD_ANY_RE.findall(body)
        class_guards = sorted({g for g in guards
                               if g.startswith("L") and g.endswith(";")})
        plain_guards = sorted({g for g in guards
                               if not (g.startswith("L") and g.endswith(";"))})
        calls = sorted({c for c in CALL_RE.findall(body)
                        if c not in CONTROL and c != name})
        funcs.append({"name": name, "qualified": qual,
                      "start_line": i + 1, "end_line": j,
                      "class_guards": class_guards,
                      "plain_guards": plain_guards,
                      "calls": calls, "bytes": len(body)})
        i = j
    return funcs


def extract_shadow_bindings() -> dict:
    """S70 law: shadow→class bindings live in `handles_class()` overrides in
    the shadow HEADERS; the methods each shadow serves are dispatched in the
    shadow's .cpp via `m == "<name>"` guards. Returns {ShadowClass: [desc...]}.
    """
    bindings = {}
    cls_open = re.compile(r"\bclass\s+(\w+)\s*(?::[^{]*)?\{")
    hdrs = sorted((SRC / "framework").glob("*.h")) + sorted((SRC / "api").glob("*.h"))
    for h in hdrs:
        text = strip_comments_keep_strings(h.read_text(errors="replace"))
        for m in cls_open.finditer(text):
            cname = m.group(1)
            # balanced walk of the class body
            depth, j = 1, m.end()
            while depth > 0 and j < len(text):
                if text[j] == "{":
                    depth += 1
                elif text[j] == "}":
                    depth -= 1
                j += 1
            body = text[m.end():j - 1]
            hm = re.search(r"handles_class\s*\([^)]*\)\s*(?:const\s*)?(?:override\s*)?\{",
                           body)
            if not hm:
                continue
            hd, k = 1, hm.end()
            while hd > 0 and k < len(body):
                if body[k] == "{":
                    hd += 1
                elif body[k] == "}":
                    hd -= 1
                k += 1
            descs = [d for d in GUARD_ANY_RE.findall(body[hm.end():k - 1])
                     if d.startswith("L") and d.endswith(";")]
            for d in descs:
                bindings.setdefault(cname, [])
                if d not in bindings[cname]:
                    bindings[cname].append(d)
    return bindings


def served_pairs_from_functions(funcs_by_tu: dict, bindings: dict) -> list[dict]:
    """(class,method) served-surface extraction with TWO honest laws:

    ordered (primary): inside a dispatch body, a plain guard is attributed to
        the NEAREST PRECEDING class guard — dispatch chains here are written
        class-then-method. Tight pairing, still static over-approx.
    crossproduct (fallback): within one function, class guards x plain guards,
        emitted only for functions with <=6 class guards to bound explosion;
        flagged extraction="function-guard (over-approx)".
    """
    ordered, cross = [], []
    seen = set()
    for tu, funcs in funcs_by_tu.items():
        for f in funcs:
            if not f["class_guards"] or not f["plain_guards"]:
                continue
            # --- ordered law: walk guards in body order -------------------
            body_guards = []  # (kind, value) in textual order
            for m in GUARD_ANY_RE.finditer(f.get("_body", "")):
                v = m.group(1)
                kind = "class" if (v.startswith("L") and v.endswith(";")) else "plain"
                body_guards.append((kind, v))
            cur_class = None
            for kind, v in body_guards:
                if kind == "class":
                    cur_class = v
                elif cur_class is not None:
                    key = (cur_class, v, tu, f["name"])
                    if key not in seen:
                        seen.add(key)
                        ordered.append({"class": cur_class, "method": v, "tu": tu,
                                        "function": f["name"],
                                        "line": f["start_line"],
                                        "extraction": "ordered-guards (over-approx)"})
            # --- shadow-binding law: functions of a Shadow subclass serve
            # the classes claimed by that shadow's handles_class() — pair
            # binding classes x in-body plain guards (m == "...").
            for shadow_cls, descs in bindings.items():
                if not (f["qualified"] == shadow_cls
                        or f["qualified"].startswith(shadow_cls + "::")):
                    continue
                for c in descs:
                    for mth in f["plain_guards"]:
                        key = (c, mth, tu, f["name"], "b")
                        if key not in seen:
                            seen.add(key)
                            cross.append({"class": c, "method": mth, "tu": tu,
                                          "function": f["name"],
                                          "line": f["start_line"],
                                          "extraction": "shadow-binding (over-approx)"})
            # --- substring-class law (line-proximity): class_name.find("X")
            # dispatch families (F-033 getSystemService etc.). A plain guard is
            # paired with the NEAREST substring guard within 3 preceding lines
            # — mega-function cross-products are noise, proximity is precise.
            body_lines = f.get("_body", "").splitlines()
            for li, ln in enumerate(body_lines):
                pm = re.search(r'==\s*"([^"]+)"', ln)
                if not pm:
                    continue
                pv = pm.group(1)
                if pv.startswith("L") and pv.endswith(";"):
                    continue
                cands = []
                for back in (-2, -1, 0, 1, 2, 3, 4):
                    k = li + back
                    if k < 0 or k >= len(body_lines):
                        continue
                    sm = SUBSTR_GUARD_RE.search(body_lines[k])
                    if sm and sm.group(1) not in cands:
                        # OR-chains list several families; each is a candidate
                        cands.append(sm.group(1))
                for sub in cands:
                    mth = pv
                    key = (sub, mth, tu, f["name"], "s")
                    if key not in seen:
                        seen.add(key)
                        cross.append({"class": sub, "method": mth,
                                      "tu": tu, "function": f["name"],
                                      "line": f["start_line"] + li,
                                      "extraction": "substring-class (over-approx)"})
            # --- bounded cross-product fallback ---------------------------
            if len(f["class_guards"]) <= 6:
                for c in f["class_guards"]:
                    for mth in f["plain_guards"]:
                        key = (c, mth, tu, f["name"], "x")
                        if key not in seen:
                            seen.add(key)
                            cross.append({"class": c, "method": mth, "tu": tu,
                                          "function": f["name"],
                                          "line": f["start_line"],
                                          "extraction": "function-guard (over-approx)"})
    return ordered, cross


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    all_funcs = {}
    tus = sorted(set(DISPATCH_TUS) | {t for ts in STAGE_TUS.values() for t in ts})
    for tu in tus:
        all_funcs[tu] = parse_functions(ROOT / "miniandroid" / tu)

    # re-attach comment-stripped STRING-KEEPING bodies for guard extraction
    # (S70: guard values must survive; S69 fed stripped bodies -> 0 pairs)
    for tu in tus:
        p = ROOT / "miniandroid" / tu
        if not p.exists():
            continue
        text = strip_comments_keep_strings(p.read_text(errors="replace"))
        lines = text.splitlines()
        for f in all_funcs[tu]:
            f["_body"] = "\n".join(lines[f["start_line"] - 1:f["end_line"]])
            # S70: guards MUST be extracted from the string-keeping body —
            # parse_functions sees string-blanked text (brace accuracy), so
            # its guard lists are empty by construction.
            g = GUARD_ANY_RE.findall(f["_body"])
            f["class_guards"] = sorted({x for x in g
                                        if x.startswith("L") and x.endswith(";")})
            f["plain_guards"] = sorted({x for x in g
                                        if not (x.startswith("L") and x.endswith(";"))})

    # ── served API surface ────────────────────────────────────────────────
    bindings = extract_shadow_bindings()
    ordered, cross = served_pairs_from_functions(all_funcs, bindings)
    served = ordered + cross
    (OUT / "served_api.json").write_text(json.dumps({
        "note": "Static extraction of (class,method) dispatch pairs. "
                "ordered-guards = plain guard attributed to nearest preceding "
                "class guard in body order; function-guard = bounded cross "
                "product. Both are static over-approximations; live run "
                "traces remain ground truth. S70 fixed the S69 empty-pairs "
                "parser bug (Class:: style + variable-agnostic guards).",
        "count": len(served),
        "ordered_count": len(ordered),
        "cross_count": len(cross),
        "pairs": served}, indent=1))

    # ── function-node dump (knowledge-graph backbone) ─────────────────────
    funcs_out = []
    for tu in tus:
        for f in all_funcs[tu]:
            funcs_out.append({k: f[k] for k in
                              ("name", "qualified", "start_line", "end_line",
                               "class_guards", "plain_guards", "calls", "bytes")}
                             | {"tu": tu})
    (OUT / "functions.json").write_text(json.dumps({
        "note": "Every parsed LIVE-TU dispatch function with its string guards "
                "and intra-TU call names. Node source for the ACTIVE runtime "
                "knowledge graph (DISPATCHES_TO / IMPLEMENTED_BY edges).",
        "tus": {t: len(all_funcs[t]) for t in tus},
        "count": len(funcs_out), "functions": funcs_out}, indent=1))

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
                                               "guards": (f["class_guards"]
                                                          + f["plain_guards"])[:8]}
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

    print(f"served_api: {len(served)} pairs (ordered {len(ordered)} / cross "
          f"{len(cross)}) | functions: {len(funcs_out)} | classes: "
          f"{len(classes)} | stages: " + str({k: v['node_count']
                                              for k, v in graphs.items()}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
