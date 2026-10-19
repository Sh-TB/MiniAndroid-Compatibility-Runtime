#!/usr/bin/env python3
#!/usr/bin/env python3.13
"""CONT-111: chess (jwtc 298) appcompat Toolbar constructor decode —
verify setMinimumHeight/setMinimumWidth callsites + theme-attr reads
(F-NEW-448 lever: content/min-height chain, layer=theme dimension resolution)."""
from androguard.core.apk import APK
from androguard.core.dex import DEX

APK_PATH = 'upload/chess_jwtc_298.apk'

import zipfile, io
z = zipfile.ZipFile(APK_PATH)
dex_bytes = z.read('classes.dex')
d = DEX(dex_bytes)

targets = {}
for c in d.get_classes():
    cn = c.get_name()
    if cn in ('Landroidx/appcompat/widget/Toolbar;',
              'Landroidx/appcompat/widget/ActionBarOverlayLayout;'):
        targets[cn] = c

print('classes found:', list(targets))
for cn, c in targets.items():
    for m in c.get_methods():
        mn = m.get_name()
        if mn in ('<init>', 'setMinimumHeight', 'setMinimumWidth', 'getSuggestedMinimumHeight'):
            code = m.get_code()
            if code is None:
                continue
            bc = m.get_instructions()
            lines = []
            hit = False
            for ins in bc:
                op = ins.get_name()
                out = ins.get_output()
                if any(k in out for k in ('setMinimumHeight', 'setMinimumWidth',
                                          'obtainStyledAttributes', 'getDimensionPixelSize',
                                          'minHeight', 'minWidth')):
                    hit = True
                    lines.append(f'  {op} {out}')
            if hit:
                print(f'\n== {cn} {mn}{m.get_descriptor()} ==')
                for l in lines[:40]:
                    print(l)
