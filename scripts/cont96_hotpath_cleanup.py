#!/usr/bin/env python3
"""cont96_hotpath_cleanup.py — CONT-96 W1/W2 hot-path hygiene transform.

W1 (diag_env law): diagnostic env presence-checks in per-instruction /
per-invocation paths call std::getenv() every execution — an environ walk
per opcode / per method call (F-074 throughput violation; measured share of
the 30s Telegram gate budget). diag_env() caches by string-literal pointer
identity (all diagnostic sites pass literals; literals are stable) and
answers in ~tens of ns. Identical answers, env read at first use.

W2 (diag-find gating): ALWAYS-ON debug stderr prints whose guard is a
string::find per invocation are gated behind cached diag_env flags
(S58-hygiene precedent: "was ALWAYS-ON stderr — env-gated, bounded, same
format").

Targeted line-level edits with exact-text verification: the script fails
loudly on any mismatch instead of guessing.
"""
import re
import sys

PATH = 'miniandroid/src/dex/dalvik_engine.cpp'

# (1-based line number, substring that MUST appear on that line, rewrite fn)
edits = []


def getenv_true(line, flag):
    """std::getenv("F") != nullptr  /  if (std::getenv("F"))  -> diag_env("F")"""
    a = f'std::getenv("{flag}") != nullptr'
    b = f'getenv("{flag}") != nullptr'
    c = f'std::getenv("{flag}")'
    d = f'getenv("{flag}")'
    if a in line:
        return line.replace(a, f'diag_env("{flag}")'), True
    if b in line:
        return line.replace(b, f'diag_env("{flag}")'), True
    if c in line and line.rstrip().endswith('&& current_registers_)'):
        pass  # fallthrough below
    if c in line:
        return line.replace(c, f'diag_env("{flag}")'), True
    if d in line:
        return line.replace(d, f'diag_env("{flag}")'), True
    return line, False


def gate_with(line, flag):
    """Insert diag_env("F") && as the outermost condition prefix."""
    m = re.match(r'^(\s*)if \((.*)\)\s*\{\s*$', line)
    if m:
        return f'{m.group(1)}if (diag_env("{flag}") && {m.group(2)}) {{', True
    return line, False


HOT_GETENV = []  # populated below from inventory

regions = [
    ('execute_method_internal', 2991, 6756),
    ('try_recursive_invoke', 6756, 7600),
    ('invoke_virtual', 21694, 22309),
    ('invoke_direct', 22521, 22802),
    ('invoke_static', 22802, 23515),
    ('invoke_interface', 23515, 24129),
    ('try_shadow_dispatch', 25937, 26800),
    ('main_switch_invoke_static_case', 15525, 15545),
    ('post_switch_f040', 17820, 17840),
    ('s44_iget_site', 14765, 14775),
]

lines = open(PATH).read().split('\n')

plan = []
for name, s, e in regions:
    for i in range(s - 1, min(e, len(lines))):
        l = lines[i]
        m = re.search(r'(?:std::)?getenv\("([A-Z0-9_]+)"\)', l)
        if m:
            plan.append((i + 1, m.group(1), name, l.strip()[:90]))

print("=== getenv sites in hot regions ===")
for p in plan:
    print(p[0], p[1], p[2], '|', p[3])
print("total:", len(plan))
