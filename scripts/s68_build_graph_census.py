#!/usr/bin/env python3
"""S68 FINAL BASE CLOSURE — R4 BUILD GRAPH AUDIT.
Classifies every source file under miniandroid/src:
  LIVE-COMPILED   : in Makefile CORE_SOURCES/MAIN_SOURCE object list
  LIVE-INCLUDED   : transitively #included by a LIVE-COMPILED TU
  DEAD            : neither compiled nor transitively included
  EXPERIMENTAL    : exp*_main.cpp targets (not part of the engine binary)
Output: docs/foundation/S68_BUILD_GRAPH.md + JSON.
"""
import os, re, json, subprocess
from collections import defaultdict

ROOT = "/home/z/my-project/miniandroid"
SRC = os.path.join(ROOT, "src")
OUT_MD = "/home/z/my-project/docs/foundation/S68_BUILD_GRAPH.md"
OUT_JSON = "/home/z/my-project/docs/foundation/S68_BUILD_GRAPH.json"

mk = open(os.path.join(ROOT, "Makefile")).read()

# --- parse Makefile compiled sources ---
var_blocks = {}
# gather all VAR = ... lines (may span with backslash continuations)
mk_flat = mk.replace("\\\n", " ")
for m in re.finditer(r"^([A-Z_0-9]+)\s*[:+]?=\s*(.+)$", mk_flat, re.M):
    var_blocks[m.group(1)] = m.group(2)

def expand(var, seen=None):
    seen = seen or set()
    if var in seen: return []
    seen.add(var)
    out = []
    for tok in var_blocks.get(var, "").split():
        if tok.startswith("$(") and tok.endswith(")"):
            inner = tok[2:-1]
            if inner.startswith("wildcard "):
                pat = inner[len("wildcard "):].strip()
                base = os.path.dirname(os.path.join(ROOT, pat))
                out.extend(sorted(glob_dir(base)))
            else:
                out.extend(expand(inner, seen))
        elif tok.endswith(".cpp"):
            out.append(os.path.normpath(os.path.join(SRC, tok.replace("$(SRCDIR)/", "")) if not tok.startswith("$(SRCDIR)") else tok))
    return out

def glob_dir(d):
    res = []
    for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        if f.endswith(".cpp"):
            res.append(os.path.join(d, f))
    return res

compiled = set()
for var in ["APK_SOURCES","DEX_SOURCES","RUNTIME_SOURCES","DIAGNOSTICS_SOURCES",
            "RESOURCES_SOURCES","RENDERER_SOURCES","FONTS_SOURCES","FRAMEWORK_SOURCES",
            "API_SOURCES","STORAGE_SOURCES"]:
    for p in expand(var):
        p2 = p.replace("$(SRCDIR)", SRC)
        compiled.add(os.path.normpath(p2))
compiled.add(os.path.normpath(os.path.join(SRC, "main.cpp")))
# test executable
test_src = os.path.normpath(os.path.join(ROOT, "tests/simple_test.cpp"))

# --- resolve wildcard storage ---
st = var_blocks.get("STORAGE_SOURCES","")
m = re.search(r"wildcard\s+(.*)\)\s*$", st.strip())
if m:
    pat = m.group(1).strip().replace("$(SRCDIR)", SRC)
    d = os.path.dirname(pat)
    if os.path.isdir(d):
        for f in sorted(os.listdir(d)):
            if f.endswith(".cpp"):
                compiled.add(os.path.join(d, f))

# --- transitive include closure from compiled TUs ---
inc_re = re.compile(r'#include\s*["<]([^">]+)[">]')
def includes_of(path):
    try: txt = open(path, encoding="utf-8", errors="replace").read()
    except: return []
    return [m.group(1) for m in inc_re.finditer(txt)]

# map basename -> actual files
all_files = {}
for dirpath, _, files in os.walk(SRC):
    for f in files:
        if f.endswith((".cpp",".h")):
            all_files.setdefault(f, []).append(os.path.join(dirpath, f))
for dirpath, _, files in os.walk(os.path.join(ROOT,"tests")):
    for f in files:
        if f.endswith((".cpp",".h")):
            all_files.setdefault(f, []).append(os.path.join(dirpath, f))

live = set(compiled)
queue = list(compiled)
while queue:
    tu = queue.pop()
    for inc in includes_of(tu):
        base = os.path.basename(inc)
        for cand in all_files.get(base, []):
            if cand not in live:
                live.add(cand); queue.append(cand)

# --- classify everything ---
rows = []
for dirpath, _, files in os.walk(SRC):
    for f in sorted(files):
        if not f.endswith((".cpp",".h")): continue
        p = os.path.join(dirpath, f)
        rel = os.path.relpath(p, ROOT)
        if p in compiled: status = "LIVE-COMPILED"
        elif p in live:   status = "LIVE-INCLUDED"
        else:             status = "DEAD"
        rows.append((rel, status, os.path.getsize(p)))

# engine binary symbol check for a few key classes
def nm_grep(pattern):
    try:
        out = subprocess.run(["nm","-C","--defined-only",os.path.join(ROOT,"build/miniandroid")],
                             capture_output=True, text=True, timeout=60).stdout
        return len([l for l in out.splitlines() if pattern in l])
    except Exception as e:
        return -1

sym_checks = {p: nm_grep(p) for p in ["SoftwareRenderer","ViewRenderer","RealLayout",
                                       "ExceptionSystem","ApiDispatcher","LayoutInflater",
                                       "TouchDispatcher","CanvasShadow"]}

# report
dead = [r for r in rows if r[1]=="DEAD"]
livec = [r for r in rows if r[1]=="LIVE-COMPILED"]
livei = [r for r in rows if r[1]=="LIVE-INCLUDED"]
json.dump({"rows":rows,"symbols":sym_checks}, open(OUT_JSON,"w"), indent=1)

with open(OUT_MD,"w") as f:
    f.write("# S68 BUILD GRAPH AUDIT (FINAL BASE CLOSURE)\n\n")
    f.write("Method: Makefile `CORE_SOURCES` + `main.cpp` = LIVE-COMPILED roots; "
            "transitive `#include` closure = LIVE-INCLUDED; rest = DEAD.\n\n")
    f.write("## Engine binary symbol presence (nm -C)\n\n| symbol | defs |\n|---|---|\n")
    for k,v in sym_checks.items(): f.write(f"| {k} | {v} |\n")
    f.write(f"\n## Counts\n\n- LIVE-COMPILED: {len(livec)}\n- LIVE-INCLUDED: {len(livei)}\n- DEAD: {len(dead)}\n\n")
    f.write("## DEAD files (not compiled by Makefile, not transitively included)\n\n")
    f.write("| file | bytes |\n|---|---|\n")
    for rel,_,sz in sorted(dead): f.write(f"| {rel} | {sz} |\n")
    f.write("\n## LIVE-COMPILED (Makefile)\n\n")
    for rel,_,sz in sorted(livec): f.write(f"- {rel}\n")
    f.write("\n## LIVE-INCLUDED (headers pulled in transitively)\n\n")
    for rel,_,sz in sorted(livei): f.write(f"- {rel}\n")
print("DEAD:", len(dead), "LIVE-COMPILED:", len(livec), "LIVE-INCLUDED:", len(livei))
print("symbols:", sym_checks)
for rel,_,_ in sorted(dead): print("  DEAD:", rel)
