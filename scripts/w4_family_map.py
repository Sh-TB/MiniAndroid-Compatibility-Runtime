#!/usr/bin/env python3
"""W4 family map: top-level definitions in dalvik_engine.cpp with namespace
context, sizes, and name-prefix clustering to identify semantic families."""
import re, json
from collections import Counter

SRC = "src/dex/dalvik_engine.cpp"
raw = open(SRC).read()

# Strip comments and string/char literals (state machine) so brace counting is
# reliable; replace stripped chars with spaces to preserve line numbers.
def strip_code(text):
    out = []
    i, n = 0, len(text)
    state = "code"  # code | line_comment | block_comment | string | char
    while i < n:
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        if state == "code":
            if c == "/" and nxt == "/":
                state = "line_comment"; out.append("  "); i += 2; continue
            if c == "/" and nxt == "*":
                state = "block_comment"; out.append("  "); i += 2; continue
            if c == '"':
                state = "string"; out.append(" "); i += 1; continue
            if c == "'":
                state = "char"; out.append(" "); i += 1; continue
            out.append(c); i += 1; continue
        if state == "line_comment":
            if c == "\n":
                state = "code"; out.append("\n")
            else:
                out.append(" ")
            i += 1; continue
        if state == "block_comment":
            if c == "*" and nxt == "/":
                state = "code"; out.append("  "); i += 2; continue
            out.append("\n" if c == "\n" else " "); i += 1; continue
        if state == "string":
            if c == "\\":
                out.append("  "); i += 2; continue
            if c == '"':
                state = "code"; out.append(" "); i += 1; continue
            out.append("\n" if c == "\n" else " "); i += 1; continue
        if state == "char":
            if c == "\\":
                out.append("  "); i += 2; continue
            if c == "'":
                state = "code"; out.append(" "); i += 1; continue
            out.append(" "); i += 1; continue
    return "".join(out)

lines = strip_code(raw).split("\n")

sig_re = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_:<>,\*& \t]*[ \*&]([A-Za-z_][A-Za-z0-9_:<>~]*)\s*\(")
ns_re = re.compile(r"^namespace(?:\s+([A-Za-z_][A-Za-z0-9_:]*)\s*)?\{")
tmpl_re = re.compile(r"^template\s*<")
class_re = re.compile(r"^(class|struct)\s+[A-Za-z_]")

defns = []          # (start, end, name, ns_path, size)
ns_path = []        # namespace names ('' for anonymous)
depth = 0           # total open braces
ns_depth = 0        # braces contributed by namespace scopes only

i = 0
while i < len(lines):
    line = lines[i]
    st = line.strip()
    dm = ns_re.match(st)
    if dm and depth == ns_depth:
        ns_path.append(dm.group(1) or "ANON")
        ns_depth += line.count("{") - line.count("}")
        depth += line.count("{") - line.count("}")
        i += 1
        continue
    at_ns_body = depth == ns_depth
    if at_ns_body and st.startswith("}") and ns_path:
        ns_path.pop()
        ns_depth += line.count("{") - line.count("}")
        depth += line.count("{") - line.count("}")
        i += 1
        continue
    if at_ns_body and st and not st.startswith(("//", "#", "using ", "template <",
                                                "extern ", "friend ")):
        m = sig_re.match(line)
        if (m and not tmpl_re.match(line)
                and not line.rstrip().endswith(";")
                and not class_re.match(st)
                and not st.endswith("}")
                and not st.endswith(")")):
            name = m.group(1)
            d = 0
            seen = False
            end = i
            for j in range(i, min(i + 100000, len(lines))):
                d += lines[j].count("{") - lines[j].count("}")
                if "{" in lines[j]:
                    seen = True
                if seen and d <= 0:
                    end = j
                    break
            ns = "::".join(ns_path) or "(global)"
            defns.append((i + 1, end + 1, name, ns, end + 1 - (i + 1) + 1))
            depth += sum(l.count("{") - l.count("}")
                         for l in lines[i:end + 1])
            i = end + 1
            continue
        if class_re.match(st):
            d = 0
            seen = False
            end = i
            for j in range(i, min(i + 20000, len(lines))):
                d += lines[j].count("{") - lines[j].count("}")
                if "{" in lines[j]:
                    seen = True
                if seen and d <= 0:
                    end = j
                    break
            depth += sum(l.count("{") - l.count("}")
                         for l in lines[i:end + 1])
            i = end + 1
            continue
    depth += line.count("{") - line.count("}")
    i += 1

total = len(lines)
anon = sum(s for _, _, _, ns, s in defns if "ANON" in ns.split("::"))
with open("evidence/issue612_audit/wave4_family_map.json", "w") as f:
    json.dump({"total_lines": total, "n_top_defns": len(defns),
               "lines_in_anon_ns": anon, "defns": defns}, f, indent=1)

top = sorted(defns, key=lambda x: -x[4])[:40]
print(f"total {total} lines, {len(defns)} top-level defns, "
      f"{anon} lines in anonymous NS")
print("TOP 40 (start-end, size, ns, name):")
for s, e, n, ns, sz in top:
    print(f"  {s:6d}-{e:6d} {sz:6d}  {ns.split('::')[-1][:16]:16s} {n[:56]}")

clusters = Counter()
for s, e, n, ns, sz in defns:
    if "ANON" not in ns.split("::"):
        continue
    pref = re.match(r"^[A-Za-z]+(?:_[A-Za-z0-9]+)?", n)
    clusters[pref.group(0) if pref else n[:8]] += sz
print("TOP 25 anon-ns name-prefix clusters by lines:")
for k, v in clusters.most_common(25):
    print(f"  {v:7d}  {k}*")
