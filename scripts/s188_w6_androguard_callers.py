#!/usr/bin/env python3
"""S188 W6-2/3: h0.a/h0.c callers + layout XML anchor attrs via androguard."""
import re
from pathlib import Path
from loguru import logger
logger.remove()

from androguard.core.apk import APK
from androguard.core.dex import DEX

APK_PATH = '/home/z/my-project/upload/stuck_apks/tibarj.tranquilstopwatch.apk'

a = APK(APK_PATH)
d = DEX(a.get_dex())
classes = {c.get_name(): c for c in d.get_classes()}

# 1) find callers of h0.a(Insets)I, h0.c(WindowInsets)Insets
targets = {
    'a': 'Landroidx/lifecycle/h0;->a(Landroid/graphics/Insets;)I',
    'c': 'Landroidx/lifecycle/h0;->c(Landroid/view/WindowInsets;)Landroid/graphics/Insets;',
    'm': 'Landroidx/lifecycle/h0;->m(Landroid/view/WindowInsets;)Landroid/view/WindowInsets$Builder;',
    'u': 'Landroidx/lifecycle/h0;->u(Landroidx/coordinatorlayout/widget/CoordinatorLayout; Landroid/content/Context; [I Landroid/util/AttributeSet; Landroid/content/res/TypedArray;)V',
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
                    for o in ins.get_operands():
                        nm = getattr(o, 'name', None) or str(o)
                        s = str(o)
                        for k, t in targets.items():
                            if t.split('->')[0] in s and f'->{k}(' in s:
                                callers[k].append(f"{cn}->{m.get_name()}{m.get_descriptor()}")
        except Exception:
            continue
for k, v in callers.items():
    uniq = sorted(set(v))
    print(f"\n## callers of h0.{k}: {len(uniq)}")
    for u in uniq[:12]:
        print('  ', u)

# 2) DrawerLayout class: who calls getRootWindowInsets (platform shadow) or
#    ViewCompat c(...)? find DrawerLayout obfuscated class first
dl = None
for cn in classes:
    if 'DrawerLayout' in cn:
        print('DrawerLayout class:', cn)

# 3) layouts: list res/layout names, dump the main drawer layout's anchor attrs
print('\n## layouts:', [n for n in a.get_files() if n.startswith('res/layout')][:20])
for ln in a.get_files():
    if ln.startswith('res/layout') and ln.endswith('.xml'):
        xml = a.get_file(ln)
        try:
            from androguard.core.axml import AXMLPrinter
            s = AXMLPrinter(xml).get_xml().decode('utf-8', 'ignore')
        except Exception as e:
            continue
        if 'layout_anchor' in s:
            print(f"\n## {ln} HAS layout_anchor:")
            # print only elements with anchor
            for el in s.split('<'):
                if 'layout_anchor' in el:
                    print('  <' + el[:220])
