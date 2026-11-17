#!/usr/bin/env python3
"""W6 Phase 2: source-level family map for dalvik_bridge.cpp and
dalvik_interpreter.cpp — function defs with exact line ranges at current
HEAD, brace-depth verified. Output: evidence/wave6/w6_family_map.json
"""
import json, os, re, sys

os.chdir("/home/z/my-project/miniandroid")
EV = "evidence/wave6"

def strip_code(text):
    out = []; i = 0; n = len(text); state = 'code'
    while i < n:
        c = text[i]; nxt = text[i+1] if i + 1 < n else ''
        if state == 'code':
            if c == '/' and nxt == '/': state = 'lc'; out.append('  '); i += 2; continue
            if c == '/' and nxt == '*': state = 'bc'; out.append('  '); i += 2; continue
            if c == '"': state = 'str'; out.append(' '); i += 1; continue
            if c == "'": state = 'chr'; out.append(' '); i += 1; continue
            out.append(c); i += 1; continue
        if state == 'lc':
            out.append('\n' if c == '\n' else ' ')
            if c == '\n': state = 'code'
            i += 1; continue
        if state == 'bc':
            if c == '*' and nxt == '/': state = 'code'; out.append('  '); i += 2; continue
            out.append('\n' if c == '\n' else ' '); i += 1; continue
        if state == 'str':
            if c == '\\': out.append('  '); i += 2; continue
            if c == '"': state = 'code'; out.append(' '); i += 1; continue
            out.append('\n' if c == '\n' else ' '); i += 1; continue
        if state == 'chr':
            if c == '\\': out.append('  '); i += 2; continue
            if c == "'": state = 'code'; out.append(' '); i += 1; continue
            out.append(' '); i += 1; continue
    return ''.join(out)

NAME = re.compile(r'([A-Za-z_][A-Za-z0-9_:]*)\s*\(')

def map_file(path):
    text = open(path, errors='replace').read()
    stripped = strip_code(text).split('\n')
    depth = 0
    defns = []
    BASE = {1, 2}  # anonymous namespace (1) or miniandroid::dalvik (2)
    for i, l in enumerate(stripped, 1):
        opens = depth in BASE and '{' in l
        if opens:
            # walk back over the contiguous signature block
            j = i - 1
            block = [l.split('{')[0]]
            while j > 0:
                cand = stripped[j - 1].rstrip()
                if not cand or cand.startswith('#') or cand.endswith(';') \
                        or cand.endswith('}') or cand.endswith(':') \
                        or cand.lstrip().startswith('//'):
                    break
                block.insert(0, cand)
                j -= 1
            joined = ' '.join(block)
            if '(' in joined and ')' in joined and '=' not in joined.split('(')[0]:
                m = NAME.search(joined)
                if m and m.group(1).split('::')[-1] not in (
                        'if', 'for', 'while', 'switch', 'return', 'catch',
                        'sizeof', 'else', 'do', 'namespace', 'class',
                        'struct', 'enum'):
                    defns.append({"start": j, "brace": i, "name": m.group(1),
                                  "linkage": "internal" if depth == 1 else "external",
                                  "sig": joined.strip()[:110]})
        if defns and defns[-1].get("end") is None and depth > 1 \
                and (depth - l.count('}') + l.count('{')) in BASE \
                and l.rstrip().endswith('}'):
            defns[-1]["end"] = i
            defns[-1]["lines"] = i - defns[-1]["start"] + 1
        depth += l.count('{') - l.count('}')
    return [d for d in defns if "end" in d]

out = {}
for path in sys.argv[1:] or ["src/dex/dalvik_bridge.cpp", "src/dex/dalvik_interpreter.cpp"]:
    defns = map_file(path)
    total = sum(d["lines"] for d in defns)
    out[os.path.basename(path)] = {
        "path": path, "defns": defns, "defn_count": len(defns),
        "lines_covered": total,
        "top15": sorted(defns, key=lambda d: -d["lines"])[:15]}
    print(f"{path}: {len(defns)} defs, {total} lines in functions")
    for d in sorted(defns, key=lambda d: -d["lines"])[:12]:
        print(f"   {d['start']:6d}-{d['end']:6d} ({d['lines']:6d} ln) {d['name'][:60]}")
json.dump(out, open(f"{EV}/w6_family_map.json", "w"), indent=1)
print("map written")
