#!/usr/bin/env python3
"""Find UiApplier-like classes: methods with signature containing (I Lel0;)V
and classes holding Lel0; fields with list-of-children semantics."""
import sys, zipfile, re
sys.path.insert(0, '/home/z/my-project/tmp/w4venv/lib/python3.12/site-packages')
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

APK = '/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk'
with zipfile.ZipFile(APK) as z:
    d = DEX(z.read('classes.dex'))

hits = []
for c in d.get_classes():
    for m in c.get_methods():
        desc = m.get_descriptor()
        # insertTopDown / insertBottomUp / remove patterns over LayoutNode
        if re.search(r'\(I Lel0;\)V', desc) or re.search(r'\(Lel0;\)V', desc):
            hits.append((c.get_name(), m.get_name(), desc))

from collections import defaultdict
bycls = defaultdict(list)
for cn, mn, ds in hits:
    bycls[cn].append((mn, ds))

for cn in sorted(bycls):
    methods = bycls[cn]
    # applier-like: has BOTH index+node and node-only removes
    idx_nodes = [x for x in methods if '(I Lel0;)V' in x[1]]
    if idx_nodes:
        print(f"{cn}: {methods[:10]}")
