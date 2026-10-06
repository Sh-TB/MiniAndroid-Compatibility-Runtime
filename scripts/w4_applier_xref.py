#!/usr/bin/env python3
"""Find xrefs to Lqc; applier interface methods (c/f = insertTop/BottomUp)
to locate the Change-executor / ComposerImpl classes."""
import sys, zipfile, re
sys.path.insert(0, '/home/z/my-project/tmp/w4venv/lib/python3.12/site-packages')
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

APK = '/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk'
with zipfile.ZipFile(APK) as z:
    d = DEX(z.read('classes.dex'))

# Build class/method index and scan instruction refs to Lqc;->c / Lqc;->f / Lqc;->d / Lqc;->j
targets = {}
for c in d.get_classes():
    for m in c.get_methods():
        code = m.get_code()
        if not code: continue
        for ins in code.get_bc().get_instructions():
            op = ins.get_name()
            if not op.startswith('invoke-'): continue
            try:
                out = ins.get_output()
            except Exception:
                continue
            if re.search(r'Lqc;->(c|f|d|j|h)\(.*Lel0;|Lqc;->(c|f|d|j|h)\(', out):
                targets.setdefault(c.get_name(), []).append((m.get_name(), out.strip()[:120]))

for cn in sorted(targets):
    uniq = sorted(set(x[1] for x in targets[cn]))
    print(f"{cn} ({len(targets[cn])} refs)")
    for u in uniq[:6]:
        print(f"    {u}")
