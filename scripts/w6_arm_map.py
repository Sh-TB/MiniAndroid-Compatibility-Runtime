#!/usr/bin/env python3
"""W6 Phase 2: internal structure map of the two oversized functions:
- bridge_to_api (dalvik_bridge.cpp 187-55382): top-level dispatch arms
  (if/else-if blocks at function-body depth), terminal returns, fallback tail.
- fetch_decode_execute (dalvik_interpreter.cpp 184-5619): switch case clusters
  grouped by opcode family.
Output: evidence/wave6/w6_arm_map.json
"""
import json, os, re

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

def fn_span(path, fname):
    stripped = strip_code(open(path, errors='replace').read()).split('\n')
    depth = 0; cur = None
    for i, l in enumerate(stripped, 1):
        if cur is None and fname in l and '(' in l and depth == 2:
            cur = {"start": i}
        elif cur is not None and depth > 2 and (depth - l.count('}') + l.count('{')) == 2 \
                and l.rstrip().endswith('}'):
            cur["end"] = i
            return stripped, cur
        depth += l.count('{') - l.count('}')
    return stripped, None

def map_arms(stripped, span):
    arms = []; depth = 0; cur = None
    for i, l in enumerate(stripped, 1):
        if i < span["start"]:
            depth += l.count('{') - l.count('}'); continue
        if i > span["end"]: break
        if cur is None and depth == 3 and ('if' in l or l.lstrip().startswith('else')) \
                and '{' in l:
            cond = stripped[i-1].strip()
            k = i - 2
            while k >= span["start"] and not stripped[k].strip().endswith((';', '}', '{')):
                cond = stripped[k].strip() + ' ' + cond; k -= 1
            cur = {"start": i, "cond": cond[:120]}
        elif cur is not None and depth > 3 and (depth - l.count('}') + l.count('{')) == 3 \
                and l.rstrip().endswith('}'):
            cur["end"] = i; cur["lines"] = i - cur["start"] + 1
            body = stripped[cur["start"]:i]
            cur["terminal_return"] = bool(re.search(r'\breturn\b', ' '.join(body[-12:])))
            arms.append(cur); cur = None
        depth += l.count('{') - l.count('}')
    # top-level returns after the last arm (fallback region)
    if arms:
        tail_start = arms[-1]["end"]
        tail_returns = [stripped[t-1].strip()[:80] for t in range(tail_start, span["end"])
                        if depth == 3]  # approximate; filled below
        return arms, {"tail_start": tail_start}
    return arms, {}

def map_cases(stripped, span):
    cases = []
    depth = 0
    for i, l in enumerate(stripped, 1):
        if i < span["start"] or i > span["end"]:
            depth += l.count('{') - l.count('}'); continue
        m = re.match(r'\s*case (0x[0-9a-fA-F]+|\d+):', l)
        if m:
            cases.append({"line": i, "opcode": m.group(1)})
        depth += l.count('{') - l.count('}')
    return cases

res = {}
# bridge arms
stripped, span = fn_span("src/dex/dalvik_bridge.cpp", "bridge_to_api")
arms, tail = map_arms(stripped, span)
res["bridge_to_api"] = {
    "span": span, "arm_count": len(arms), "arms": arms,
    "arm_lines_total": sum(a["lines"] for a in arms),
    "biggest_arms": sorted([a for a in arms], key=lambda a: -a["lines"])[:12],
    "tail": tail}
print(f"bridge_to_api: {len(arms)} top-level arms, "
      f"{sum(a['lines'] for a in arms)} of {span['end']-span['start']+1} lines")
for a in sorted(arms, key=lambda a: -a["lines"])[:10]:
    print(f"   {a['start']:6d}-{a['end']:6d} ({a['lines']:6d} ln) ret={a['terminal_return']} "
          f"{a['cond'][:80]}")

# interpreter case clusters
stripped2, span2 = fn_span("src/dex/dalvik_interpreter.cpp", "fetch_decode_execute")
cases = map_cases(stripped2, span2)
res["fetch_decode_execute"] = {"span": span2, "case_count": len(cases), "cases": cases}
print(f"fetch_decode_execute: {len(cases)} case labels over "
      f"{span2['end']-span2['start']+1} lines")
json.dump(res, open(f"{EV}/w6_arm_map.json", "w"), indent=1)
print("arm map written")
