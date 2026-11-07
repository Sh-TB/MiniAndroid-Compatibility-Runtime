#!/usr/bin/env python3
"""S188 W5-1: androguard dissection of the FragmentManager host-wiring gap.

Target: tibarj.tranquilstopwatch (VIEW route, FragmentContainerView wall).
Obfuscated androidx names (from W4 live evidence):
  b1/t0 = androidx.fragment.app.FragmentManager
  b0/k  = androidx.fragment.app.FragmentHostCallback
  b0/n? = FragmentContainerView chain
Questions the law needs answered from REAL DEX:
  1. All <init> descriptors of b1/t0 — does a ()V ctor really exist?
  2. Who instantiates b1/t0 (new-instance sites) and in which class/method?
  3. Who iput-object's field b1/t0.a (Lb0/k;) — the host — anywhere?
  4. What does androidx FragmentController / FragmentActivity attachHost
     chain look like in THIS apk (obfuscated class names)?
  5. Field layout of b0/k (FragmentHostCallback) — which fields hold
     Activity/Context/handler (needed to fabricate a real host).
"""
import sys, json
from pathlib import Path
from androguard.core.apk import APK
from androguard.core.dex import DEX

APK_PATH = '/home/z/my-project/upload/stuck_apks/tibarj.tranquilstopwatch.apk'
OUT = Path('/home/z/my-project/evidence/s188_w5/w5_androguard_fragments.json')

a = APK(APK_PATH)
dex_data = a.get_dex()
d = DEX(dex_data)

FM = 'Lb1/t0;'      # FragmentManager (W4 evidence)
HOST = 'Lb0/k;'     # FragmentHostCallback (W4 evidence)

classes = {c.get_name(): c for c in d.get_classes()}

def desc_str(m):
    return f"{m.get_name()}{m.get_descriptor()}"

report = {}

# 1) b1/t0 class: fields + ctors + key methods
if FM in classes:
    c = classes[FM]
    fm = {
        'fields': [(f.get_name(), f.get_descriptor()) for f in c.get_fields()],
        'ctors': [desc_str(m) for m in c.get_methods() if m.get_name() == '<init>'],
        'method_count': len(list(c.get_methods())),
    }
    report['fragment_manager'] = fm

# 2) who news b1/t0
new_sites = []
for c in d.get_classes():
    for m in c.get_methods():
        code = m.get_code()
        if not code:
            continue
        try:
            for ins in code.get_bc().get_instructions():
                op = ins.get_name()
                if op.startswith('new-instance'):
                    t = ins.get_operands()
                    if t and len(t) >= 1:
                        # operand format: (register), (type_index, type)
                        for _, _, val in t:
                            if str(val) == FM:
                                new_sites.append({'class': c.get_name(),
                                                  'method': desc_str(m)})
        except Exception:
            pass
report['fm_new_instance_sites'] = new_sites

# 3) who writes FM.<field Lb0/k;> (iput-object on FM host field)
host_field_names = set()
if FM in classes:
    for f in classes[FM].get_fields():
        if f.get_descriptor() == HOST:
            host_field_names.add(f.get_name())
report['fm_host_field_names'] = sorted(host_field_names)

iput_sites = []
if host_field_names:
    for c in d.get_classes():
        for m in c.get_methods():
            code = m.get_code()
            if not code:
                continue
            try:
                for ins in code.get_bc().get_instructions():
                    op = ins.get_name()
                    if op in ('iput-object', 'iput-object-volatile'):
                        ops = ins.get_operands()
                        if len(ops) >= 3:
                            fld = str(ops[2][2])
                            cls, name = fld.split('->')
                            if cls == FM and name in host_field_names:
                                iput_sites.append({'class': c.get_name(),
                                                   'method': desc_str(m),
                                                   'field': name})
            except Exception:
                pass
report['fm_host_iput_sites'] = iput_sites

# 4) FragmentController-ish classes: find classes that call attachHost or
#    hold fields of type HOST
host_holders = []
for c in d.get_classes():
    flds = [(f.get_name(), f.get_descriptor()) for f in c.get_fields()]
    if any(fd == HOST for _, fd in flds):
        host_holders.append({'class': c.get_name(),
                             'fields': flds})
report['host_field_holders'] = host_holders

# methods named attachHost anywhere
attach = []
for c in d.get_classes():
    for m in c.get_methods():
        if m.get_name() in ('attachHost', 'attachController', 'm'):
            attach.append({'class': c.get_name(), 'method': desc_str(m)})
report['attach_named_methods'] = attach

# 5) b0/k fields + ctor chain (to fabricate the host)
if HOST in classes:
    hc = classes[HOST]
    host_info = {'fields': [(f.get_name(), f.get_descriptor()) for f in hc.get_fields()],
                 'ctors': [desc_str(m) for m in hc.get_methods() if m.get_name() == '<init>']}
    # superclass chain
    sup = hc.get_superclassname()
    chain = [sup]
    cur = sup
    for _ in range(6):
        if cur in classes:
            cur = classes[cur].get_superclassname()
            chain.append(cur)
        else:
            break
    host_info['super_chain'] = chain
    report['fragment_host_callback'] = host_info

# bonus: FragmentContainerView class name (context tag) + its loader/ctor path
fcv = []
for c in d.get_classes():
    s = c.get_superclassname()
    if s and 'FrameLayout' in s:
        fcv.append(c.get_name())
report['framelayout_subclasses'] = fcv

OUT.write_text(json.dumps(report, indent=1))
print(json.dumps({k: (v if k in ('fragment_manager', 'fm_new_instance_sites',
                                 'fm_host_iput_sites', 'attach_named_methods',
                                 'fragment_host_callback', 'framelayout_subclasses')
                       else v)
                  for k, v in report.items()}, indent=1))
