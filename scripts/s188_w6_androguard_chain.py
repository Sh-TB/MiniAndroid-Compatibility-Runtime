#!/usr/bin/env python3
"""S188 W6-2b: callers of o0/i1.k() + g0/c.c; layout XML via zipfile."""
import zipfile, re
from loguru import logger
logger.remove()

from androguard.core.apk import APK
from androguard.core.dex import DEX

APK_PATH = '/home/z/my-project/upload/stuck_apks/tibarj.tranquilstopwatch.apk'
a = APK(APK_PATH)
d = DEX(a.get_dex())
classes = {c.get_name(): c for c in d.get_classes()}

targets = {
    'i1.k': 'Lo0/i1;->k()Lg0/c;',
    'g0c.c': 'Lg0/c;->c(Landroid/graphics/Insets;)Lg0/c;',
}
callers = {k: [] for k in targets}
for cn, c in classes.items():
    for m in c.get_methods():
        code = m.get_code()
        if not code:
            continue
        try:
            for ins in code.get_bc().get_instructions():
                if ins.get_name().startswith('invoke'):
                    s = str(ins.get_operands())
                    for k, t in targets.items():
                        if t.replace(';->', ';->') in s:
                            callers[k].append(f"{cn}->{m.get_name()}")
        except Exception:
            continue
for k, v in callers.items():
    uniq = sorted(set(v))
    print(f"\n## callers of {k}: {len(uniq)}")
    for u in uniq[:16]:
        print('  ', u)

# DrawerLayout chain: dump DrawerLayout methods mentioning InsetsCompat / onApplyWindowInsets
dl = classes.get('Landroidx/drawerlayout/widget/DrawerLayout;')
if dl:
    print('\n## DrawerLayout methods:')
    for m in dl.get_methods():
        print('  ', m.get_name(), m.get_descriptor())

# layouts via zipfile
z = zipfile.ZipFile(APK_PATH)
layouts = [n for n in z.namelist() if n.startswith('res/layout')]
print('\n## layouts:', layouts[:24])
from androguard.core.axml import AXMLPrinter
for ln in layouts:
    try:
        s = AXMLPrinter(z.read(ln)).get_xml().decode('utf-8', 'ignore')
    except Exception:
        continue
    if 'layout_anchor' in s or 'DrawerLayout' in s or 'NavigationView' in s:
        print(f'\n## ==== {ln} ==== (first 60 lines)')
        for line in s.splitlines()[:60]:
            print(line)
