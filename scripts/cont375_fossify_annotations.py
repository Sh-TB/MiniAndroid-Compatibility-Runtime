#!/usr/bin/env python3
"""cont375 — inspect @Subscribe runtime-visible annotations on the
fossifyclock App class + subscriber classes (R-NEW-464 real-APK leg).

Checks annotations_directory_item / method_annotations presence for
LOrg/fossify/clock/App; and prints each method's access flags — verifies
whether EventBus's reflection scan can ever find @Subscribe methods with
the current minting (which includes <init>/<clinit>).
"""
import logging, zipfile, sys
logging.disable(logging.CRITICAL)
try:
    from loguru import logger
    logger.remove()
except Exception:
    pass
from androguard.core.bytecodes.dvm import DalvikVMFormat

APK = '/home/z/my-project/tmp/diff366_apks/org.fossify.clock_10.apk'
CLASSES = ['Lorg/fossify/clock/App;', 'Ls5/a;']

def main():
    z = zipfile.ZipFile(APK)
    for dn in [n for n in z.namelist() if n.endswith('.dex')]:
        raw = z.read(dn)
        d = DalvikVMFormat(raw)
        for c in d.get_classes():
            if c.get_name() not in CLASSES:
                continue
            print(f"### {c.get_name()} extends {c.get_superclassname()}")
            # annotations_directory_item
            ann_off = getattr(c, 'annotations_off', 0)
            print(f"  annotations_off=0x{ann_off:x}" if ann_off else
                  "  annotations_off=0 (none)")
            for m in c.get_methods():
                mf = m.get_access_flags()
                mods = []
                for bit, nm in [(0x1,'PUBLIC'),(0x2,'PRIVATE'),(0x4,'PROTECTED'),
                                (0x8,'STATIC'),(0x10,'FINAL'),(0x100,'NATIVE'),
                                (0x400,'ABSTRACT'),(0x10000,'CONSTRUCTOR'),
                                (0x40,'BRIDGE'),(0x1000,'SYNTHETIC')]:
                    if mf & bit: mods.append(nm)
                anns = m.get_annotations() if hasattr(m, 'get_annotations') else None
                print(f"    {m.get_name()} flags=0x{mf:x} [{' '.join(mods)}]"
                      f" anns={anns if anns else '-'}")

if __name__ == '__main__':
    main()
