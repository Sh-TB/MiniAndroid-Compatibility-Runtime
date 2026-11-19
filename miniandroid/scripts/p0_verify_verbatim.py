#!/usr/bin/env python3
"""P0 verification: prove the extraction is verbatim and complete.

1. Every domain TU's body (between the alias block and the trailing
   `return false;`) must equal the corresponding byte range of the
   pre-split file (scripts/p0_before_bridge.cpp.bak).
2. The coordinator's kept pieces (sig, preamble 203..300, void tail,
   arms) must equal their backup ranges.
3. Concatenating coordinator-body + domain bodies in order must equal
   backup lines 203..55442 exactly (no line lost, none reordered).
Prints a byte-exact PASS/FAIL table.
"""
BAK = 'scripts/p0_before_bridge.cpp.bak'
DOMAINS = [('jdk', 301, 8158), ('android_core', 8159, 16614),
           ('ui_graphics', 16615, 31136), ('app_runtime', 31137, 45288),
           ('io_lang', 45289, 55440)]

import os
import subprocess
if not os.path.exists(BAK):
    # fall back to the committed pre-split blob (the W18-laws commit)
    sha = subprocess.run(['git', 'rev-parse', 'HEAD~1'],
                         capture_output=True, text=True).stdout.strip()
    blob = subprocess.run(['git', 'show', f'{sha}:src/dex/dalvik_bridge.cpp'],
                          capture_output=True)
    open(BAK, 'wb').write(blob.stdout)
    print(f'restored pre-split bytes from {sha[:12]}:src/dex/dalvik_bridge.cpp')

bak = open(BAK, encoding='utf-8').read().splitlines(keepends=True)
ok = True
pieces = []
for nm, s, e in DOMAINS:
    gen = open(f'src/dex/dalvik_bridge_domain_{nm}.cpp',
               encoding='utf-8').read().splitlines(keepends=True)
    # body = between the alias end and the final `    return false;\n`
    ai = next(i for i, ln in enumerate(gen)
              if ln.startswith('    uint32_t method_idx_hint = fr.method_idx_hint;'))
    ri = len(gen) - 1
    while not gen[ri].startswith('    return false;'):
        ri -= 1
    body = gen[ai + 1:ri]
    want = bak[s - 1:e]
    match = body == want
    ok &= match
    pieces.extend(body)
    print(f'{nm:13s} backup[{s},{e}] = {len(want)} lines | '
          f'extracted = {len(body)} | byte-identical = {match}')

# coordinator pieces
new = open('src/dex/dalvik_bridge.cpp', encoding='utf-8').read() \
    .splitlines(keepends=True)
si = next(i for i, ln in enumerate(new)
          if ln.startswith('bool DalvikExecutionEngine::bridge_to_api('))
ti = next(i for i, ln in enumerate(new)
          if ln.startswith('    DalvikBridgeFrame fr{'))
coord_pre = new[si:ti]
want_pre = bak[196:300]
m1 = coord_pre == want_pre
ok &= m1
print(f'coordinator sig+preamble: backup[197,300] = {len(want_pre)} | '
      f'kept = {len(coord_pre)} | byte-identical = {m1}')

ti_end = next(i for i, ln in enumerate(new)
              if ln.startswith('    if (bridge_domain_jdk(fr)) return true;'))
tail_i = next(i for i, ln in enumerate(new)
              if ln.startswith('    result = DalvikValue::make_void();'))
m2 = new[tail_i:tail_i + 2] == bak[55440:55442]
ok &= m2
print(f'coordinator void-tail byte-identical = {m2}')

arms_i = next(i for i, ln in enumerate(new)
              if ln.startswith('namespace miniandroid { namespace dalvik {'))
arms = new[arms_i:]
m3 = arms == bak[55446:55995]
ok &= m3
print(f'bridge_arm_* block byte-identical = {m3} ({len(arms)} lines)')

# full-body reconstruction: coordinator pre + domain bodies + tail
recon = coord_pre + pieces + bak[55440:55442]
want_full = bak[196:55442]
print(f'full reconstruction: {len(recon)} lines vs original '
      f'{len(want_full)} | identical = {recon == want_full}')
ok &= recon == want_full
print('P0 VERBATIM PROOF:', 'PASS' if ok else 'FAIL')
