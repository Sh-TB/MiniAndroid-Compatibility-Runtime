#!/usr/bin/env python3
"""S44 Attack-2 (R-NEW-351): ground-truth extraction of the protobuf
rawMessageInfo string for Ly81; (the Dooz settings proto message class).

The S44 probe caught: Llt0;.w pc=377 sees numEntries v12=0 because the
MessageInfo string decode yields nothing. This script answers:
  Q1: What produces the string that flows into Llt0;.w? (Ly81;.<clinit>
      const-string / RawMessageInfo construction — full bytecode)
  Q2: What is the EXACT const-string content (codepoints!)?
  Q3: Hand-simulation of the Llt0;.w 13-bit decode over that string:
      expected numEntries (v12 at code-unit pc 377) and the
      checkInitialized size (v2/v24 at byte 706).
"""
import zipfile, logging
logging.disable(logging.CRITICAL)
try:
    from loguru import logger
    logger.remove()
except Exception:
    pass
from androguard.core.dex import DEX

APK = '/tmp/my-project/apk_cache/s36new/io.github.yamin8000.dooz_23.apk'
z = zipfile.ZipFile(APK)
d = DEX(z.read('classes.dex'))

cls = None
for c in d.get_classes():
    if c.get_name() == 'Ly81;':
        cls = c
        break
assert cls, "Ly81; not found"
print(f"=== Ly81; super={cls.get_superclassname()} ===")
for f in cls.get_fields():
    print(f"  field {f.get_name()} : {f.get_descriptor()}  [{f.get_access_flags_string()}]")

for m in cls.get_methods():
    name = m.get_name()
    if name in ('<clinit>', '<init>') or 'o' == name:
        code = m.get_code()
        print(f"\n=== Ly81;.{name}{m.get_descriptor()} ===")
        if code is None:
            print("  (abstract)")
            continue
        pc = 0
        for ins in code.get_bc().get_instructions():
            op = ins.get_name()
            out = ins.get_output()
            if op.startswith('const-string') or op.startswith('sput') or op.startswith('new-instance') or op.startswith('invoke'):
                print(f"  {pc:5d} {op:26s} {out}")
            pc += ins.get_length()

# extract ALL const-string in <clinit> fully with codepoints
print("\n=== FULL const-string dump of <clinit> ===")
for m in cls.get_methods():
    if m.get_name() == '<clinit>':
        pc = 0
        for ins in m.get_code().get_bc().get_instructions():
            if ins.get_name().startswith('const-string'):
                out = ins.get_output()
                # output format: vN, "string"
                try:
                    sval = out.split(', ', 1)[1]
                except Exception:
                    sval = out
                cps = ' '.join(f"U+{ord(ch):04X}({ord(ch)})" if ord(ch) < 0x20 or ord(ch) > 0x7e else repr(ch) for ch in eval(sval))
                print(f"  pc={pc} reg={out.split(',')[0]} len={len(eval(sval))}")
                print(f"    codepoints: {cps[:2000]}")
            pc += ins.get_length()
