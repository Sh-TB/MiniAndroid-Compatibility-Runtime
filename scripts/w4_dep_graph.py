#!/usr/bin/env python3
"""W4 dependency graph of dalvik_engine.cpp top-level definitions.
Answers: (a) which defns are static/internal-linkage, (b) which are declared
in dalvik_engine.h, (c) call-graph components -> candidate TU partitions."""
import json, re
from collections import defaultdict

mapj = json.load(open("evidence/issue612_audit/wave4_family_map.json"))
defns = mapj["defns"]
src = open("src/dex/dalvik_engine.cpp").read().split("\n")
hdr = open("src/dex/dalvik_engine.h").read()

names = [d[2] for d in defns]
nameset = set(names)
static_set = set()
for s, e, n, ns, sz in defns:
    if re.match(r"^static\b", src[s - 1]):
        static_set.add(n)

# header declarations: name followed by ( in header text
hdr_decl = {n for n in names if re.search(r"\b" + re.escape(n.split("::")[-1]) + r"\s*\(", hdr)}

# call edges: for each defn body, which OTHER defn names appear
body_of = {}
for s, e, n, ns, sz in defns:
    body_of[n] = "\n".join(src[s - 1:e])
edges = defaultdict(set)
for n, body in body_of.items():
    for m in nameset:
        if m != n and m.split("::")[-1] in body:
            edges[n].add(m)
rev_edges = defaultdict(set)
for n, ts in edges.items():
    for t in ts:
        rev_edges[t].add(n)

# connected components (undirected)
seen = set()
comps = []
for n in names:
    if n in seen:
        continue
    stack, comp = [n], set()
    while stack:
        x = stack.pop()
        if x in comp:
            continue
        comp.add(x)
        stack.extend(edges[x] | rev_edges.get(x, set()))
    seen |= comp
    comps.append(comp)
comps.sort(key=len, reverse=True)

freefns = [n for n in names if "::" not in n]
methods = [n for n in names if "::" in n]
print(f"defns={len(names)} methods={len(methods)} free={len(freefns)} "
      f"static={len(static_set)} declared_in_hdr={len(hdr_decl)}")
free_static = [n for n in freefns if n in static_set]
print(f"free&static: {len(free_static)} -> {free_static[:8]}")
free_not_in_hdr = [n for n in freefns if n not in hdr_decl]
print(f"free fns NOT declared in header: {len(free_not_in_hdr)}")
print("components:", [(len(c), sum(dict((d[2], d[4]) for d in defns)[n] for n in c))
                      for c in comps[:8]])
lines_of = {d[2]: d[4] for d in defns}
print("Largest components with member lists (top 6):")
for c in comps[:6]:
    tot = sum(lines_of[n] for n in c)
    print(f"  comp size={len(c)} lines={tot}: {sorted(c, key=lambda x: -lines_of[x])[:6]}")
out = {"static": sorted(static_set), "hdr_decl": sorted(hdr_decl),
       "free_fns": freefns, "edges": {k: sorted(v) for k, v in edges.items()},
       "components": [sorted(c) for c in comps]}
json.dump(out, open("evidence/issue612_audit/wave4_dep_graph.json", "w"), indent=1)
