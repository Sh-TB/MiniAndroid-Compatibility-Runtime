#!/usr/bin/env python3
"""P0 census v2 — correct line-comment reset; extracts the top-level block
structure of DalvikExecutionEngine::bridge_to_api (dalvik_bridge.cpp) and
classifies shared locals + sequential dependencies.
"""
import json
import re

SRC = 'src/dex/dalvik_bridge.cpp'


def scan():
    lines = open(SRC, encoding='utf-8').read().splitlines()
    depth = 0
    in_bc = in_lc = in_s = in_c = False
    events = []
    for n, raw in enumerate(lines, 1):
        i = 0
        while i < len(raw):
            c = raw[i]
            nxt = raw[i + 1] if i + 1 < len(raw) else ''
            if in_bc:
                if c == '*' and nxt == '/':
                    in_bc = False
                    i += 2
                    continue
                i += 1
                continue
            if in_lc:
                break
            if in_s:
                if c == '\\':
                    i += 2
                    continue
                if c == '"':
                    in_s = False
                i += 1
                continue
            if in_c:
                if c == '\\':
                    i += 2
                    continue
                if c == "'":
                    in_c = False
                i += 1
                continue
            if c == '/' and nxt == '/':
                in_lc = True
                i += 2
                continue
            if c == '/' and nxt == '*':
                in_bc = True
                i += 2
                continue
            if c == '"':
                in_s = True
                i += 1
                continue
            if c == "'":
                in_c = True
                i += 1
                continue
            if c == '{':
                depth += 1
                events.append((n, depth, 'open'))
            elif c == '}':
                events.append((n, depth, 'close'))
                depth -= 1
            i += 1
        in_lc = False  # line comments end at EOL
    return lines, events


def main():
    lines, events = scan()
    # find body_open: the '{' at depth 2 on/after line 197 whose enclosing
    # open (depth 1) is the namespace; signature at 197
    sig = next(n for n, ln in enumerate(lines, 1)
               if ln.startswith('bool DalvikExecutionEngine::bridge_to_api('))
    body_open = next(n for n, d, k in events
                     if k == 'open' and n >= sig and
                     'method_idx_hint) {' in lines[n - 1])
    body_depth = next(d for n, d, k in events if k == 'open' and n == body_open)
    # function end: matching close at the same depth
    func_end = next(n for n, d, k in events
                    if k == 'close' and n > body_open and d == body_depth)
    # top-level blocks: opens at depth body_depth+1 with their matching close
    blocks = []
    cur = None
    for n, d, k in events:
        if n <= body_open or n > func_end:
            continue
        if k == 'open' and d == body_depth + 1:
            cur = n
        elif k == 'close' and d == body_depth + 1 and cur is not None:
            blocks.append((cur, n))
            cur = None
    body_first = body_open + 1
    body_last = func_end - 1
    print(f'sig={sig} body_open={body_open} func_end={func_end} '
          f'({func_end - body_open + 1} lines) file={len(lines)}')
    print(f'top-level blocks: {len(blocks)}')
    body_text = '\n'.join(lines[body_open - 1:func_end])
    mc = len(re.findall(r'\bmethod\s*==\s*"', body_text))
    print(f'method== comparisons in body: {mc}')

    # shared locals: declarations at brace depth 3-line-start BEFORE first
    # depth-3 open, i.e., between body_open+1 and blocks[0][0]
    shared = []
    if blocks:
        for ln in range(body_first, blocks[0][0]):
            t = lines[ln - 1]
            m = re.match(
                r'^(?:static\s+|const\s+|constexpr\s+)*(?:auto|bool|int'
                r'|int32_t|uint32_t|int64_t|uint64_t|size_t|float|double'
                r'|std::string|DalvikValue|ApiCallTrace|unsigned [a-z0-9_]+'
                r'|[A-Za-z_][A-Za-z0-9_:<>]*)\s+&?([A-Za-z_][A-Za-z0-9_]*)'
                r'\s*(?:=|;|\()', t)
            if m and not t.strip().startswith('//'):
                shared.append((ln, m.group(1), t.strip()[:84]))
    print(f'shared locals before first block: {len(shared)}')
    for ln, nm, txt in shared:
        print(f'  :{ln} {nm} | {txt}')

    names = [nm for _, nm, _ in shared]
    lam = len(re.findall(r'\]\s*\(', body_text))
    print(f'lambda-ish call sites: {lam}')

    rec = []
    for (a, b) in blocks:
        blk = '\n'.join(lines[a - 1:b])
        writes = sorted({nm for nm in names
                         if re.search(rf'(?<![\w.]){nm}\s*(?:=[^=]|\+=|\+\+|--)', blk)})
        reads = sorted({nm for nm in names
                        if nm not in writes and re.search(rf'\b{nm}\b', blk)})
        lab = ''
        for ln in range(a, min(a + 14, b)):
            t = lines[ln - 1].strip()
            if t.startswith('//'):
                lab = t[2:78].strip()
                break
            m = re.match(r'(?:if|else if)\s*\((.{0,70})', t)
            if m:
                lab = 'IF: ' + re.sub(r'\s+', ' ', m.group(1))[:66]
                break
        rec.append({'a': a, 'b': b, 'w': writes, 'r': reads, 'lab': lab})
    json.dump({'sig': sig, 'body_open': body_open, 'func_end': func_end,
               'shared': shared, 'blocks': rec},
              open('scripts/p0_census.json', 'w'), indent=1)
    risky = [d for d in rec if d['w']]
    print(f'blocks writing shared locals: {len(risky)}')
    for d in risky[:15]:
        print(f"  {d['a']}-{d['b']} w={','.join(d['w'][:5])} | {d['lab'][:48]}")
    print('json -> scripts/p0_census.json')


if __name__ == '__main__':
    main()
