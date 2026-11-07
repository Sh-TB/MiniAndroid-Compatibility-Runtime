#!/usr/bin/env python3
"""W15 recon #6: pfdicer ViewPager/FragmentPagerAdapter decode.
Goal: the setAdapter -> populate -> instantiateItem contract the engine must run.
"""
import logging
logging.disable(logging.DEBUG)
from androguard.core.apk import APK
from androguard.core.dex import DEX

APK_PATH = "/home/z/my-project/apk_cache/org.secuso.privacyfriendlydicer_101.apk"
a = APK(APK_PATH)
print("package:", a.get_package())
dexes = [DEX(b) for b in a.get_all_dex()]

def disasm_pc(m, limit=300):
    out = []
    if not m.get_code(): return out
    pc = 0
    for ins in m.get_code().get_bc().get_instructions():
        out.append(f"pc=0x{pc//2:03x} " + ins.get_name() + " " + str(ins.get_output())[:105])
        pc += ins.get_length()
        if len(out) >= limit: break
    return out

# 1. find ViewPager + FragmentPagerAdapter + FragmentStatePagerAdapter classes
found = {}
for d in dexes:
    for c in d.get_classes():
        cn = c.get_name()
        s = str(c.get_superclassname())
        if ("ViewPager" in cn or "ViewPager" in s or
            "FragmentPagerAdapter" in cn or "FragmentPagerAdapter" in s or
            "FragmentStatePagerAdapter" in cn or "FragmentStatePagerAdapter" in s or
            "PagerAdapter" in cn):
            found.setdefault(cn, s)

for cn, s in sorted(found.items()):
    print(f"  {cn}  extends {s}")

# 2. dump ViewPager.populate + setAdapter + FragmentPagerAdapter methods
DUMP = {
    "Landroidx/viewpager/widget/ViewPager;": ("populate", "setAdapter", "onMeasure", "onAttachedToWindow", "initViewPager", "<init>"),
}
for d in dexes:
    for c in d.get_classes():
        cn = c.get_name()
        if cn in DUMP:
            for m in c.get_methods():
                if m.get_name() in DUMP[cn]:
                    print(f"\n### {cn} {m.get_name()} {m.get_descriptor()}")
                    for l in disasm_pc(m, 90): print("   ", l)

# 3. app's adapter class
for d in dexes:
    for c in d.get_classes():
        s = str(c.get_superclassname())
        if "PagerAdapter" in s:
            print(f"\n### APP ADAPTER {c.get_name()} extends {s}")
            for m in c.get_methods():
                print(f"    {m.get_name()} {m.get_descriptor()}")
