#!/usr/bin/env python3
"""CONT-32 CowStr migration fixer — wrap CowStr member reads inside the
std::string-vs-CowStr ternary sites reported by g++ so the conditional
operator finds a common type (std::string). Only READ shapes are wrapped;
assignment-LHS occurrences are skipped. Idempotent (skips already-wrapped)."""
import re, sys, collections

BASE = "/home/z/my-project/miniandroid/"
ERRLOG = "/home/z/my-project/run/cont32_build2.log"

# member-access expression: identifier chain with [] blocks and . / -> hops
# ending in .string_val / .class_desc (final hop may be '.' or '->')
ACCESS = re.compile(
    r"(?P<expr>\w+\s*(?:\[[^\]\[]*\])?\s*(?:[.>]\s*[\w~]+\s*(?:\[[^\]\[]*\])?\s*)*"
    r"(?:\.|->)\s*(?:string_val|class_desc))\b")

def wrap_line(line):
    out = []
    pos = 0
    changed = False
    for m in ACCESS.finditer(line):
        s, e = m.span()
        out.append(line[pos:s])
        expr = m.group("expr")
        # skip assignment LHS: followed by optional space + '=' (not '==')
        tail = line[e:]
        if re.match(r"\s*=[^=]", tail) or re.match(r"\s*=", tail) and "==":  # LHS guard
            out.append(expr)
        elif "std::string(" in line[max(0, s-12):s]:
            out.append(expr)  # already wrapped
        else:
            out.append(f"std::string({expr})")
            changed = True
        pos = e
    out.append(line[pos:])
    return "".join(out), changed

def main():
    sites = collections.defaultdict(set)
    for line in open(ERRLOG, errors="replace"):
        if "error:" not in line or "operands to" not in line:
            continue
        m = re.match(r"([^:]+):(\d+):", line)
        if m:
            f, ln = m.group(1), int(m.group(2))
            for d in (-1, 0, 1):
                sites[f].add(ln + d)
    total = 0
    for f, lns in sites.items():
        path = BASE + f
        lines = open(path).read().splitlines(keepends=True)
        n = 0
        for ln in sorted(lns):
            if 1 <= ln <= len(lines):
                new, changed = wrap_line(lines[ln - 1])
                if changed:
                    lines[ln - 1] = new
                    n += 1
        if n:
            open(path, "w").write("".join(lines))
            print(f"{f}: wrapped {n} lines")
            total += n
    print(f"TOTAL wrapped lines: {total}")

if __name__ == "__main__":
    main()
