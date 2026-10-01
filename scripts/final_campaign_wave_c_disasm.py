#!/usr/bin/env python3
"""WAVE C (F-NEW-181): disassemble the app-bundled guava
RegularImmutableMap.get + Hashing.smearedHash from the WhatsApp APK.
Decisive for the get() probe-loop spin: exact slot stride (2x key/value
interleave?), mask law, the loop exit condition, and the smear chain the
lookup key passes through."""
import logging, zipfile, sys
logging.disable(logging.CRITICAL)
try:
    from loguru import logger
    logger.remove()
except Exception:
    pass
from androguard.core.dex import DEX

APK = '/tmp/my-project/apk_cache/WhatsApp_real.apk'
TARGETS = {
    'Lcom/google/common/collect/RegularImmutableMap;': ['get'],
    'Lcom/google/common/collect/Hashing;': ['smearedHash'],
    'Lcom/google/common/collect/RegularImmutableMap;': ['get', 'createHashTable'],
}

def main():
    z = zipfile.ZipFile(APK)
    dexnames = [n for n in z.namelist() if n.endswith('.dex')]
    print(f"dex files: {len(dexnames)}")
    for dn in dexnames:
        data = z.read(dn)
        try:
            d = DEX(data)
        except Exception as e:
            print(f"  {dn}: parse fail {e}")
            continue
        for cls in d.get_classes():
            name = cls.get_name()
            if name not in TARGETS:
                continue
            for m in cls.get_methods():
                mname = m.get_name()
                if mname not in TARGETS[name]:
                    continue
                print(f"\n=== [{dn}] {name}.{mname} {m.get_descriptor()} ===")
                code = m.get_code()
                if code is None:
                    print("  (abstract/native)")
                    continue
                bc = m.get_instructions()
                off = 0
                for ins in bc:
                    print(f"  {off:04x}: {ins.get_name():28s} {ins.get_output()}")
                    off += ins.get_length()

if __name__ == '__main__':
    main()
