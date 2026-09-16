#!/usr/bin/env python3
"""S49 — R-NEW-361 forensics: disassemble the failing v18 sites.

Sites (S45 record + S49 baseline reproduction):
  - Lh/r;.c  — HALT-LOOP at PC=0x1c, 50001 visits, bytecode_size=264
  - LP/v$a;.c — aput-oob length=7 index=613985991 at pc=28
Also Lh/r;.b and LP/v$a;.a (S45 failing methods) for context.
Prints full bytecode with operands so the index computation and loop
structure can be mapped against androidx.collection semantics.
"""
import sys
from androguard.core.bytecodes.dvm import DalvikVMFormat as DEX

APK = "/tmp/my-project/apk_cache/dooz.apk"
TARGETS = [
    ("Lh/r;", "c"),
    ("Lh/r;", "b"),
    ("LP/v$a;", "c"),
    ("LP/v$a;", "a"),
]

import zipfile
z = zipfile.ZipFile(APK)
dex_data = z.read("classes.dex")
d = DEX(dex_data)

for cls in d.get_classes():
    cname = cls.get_name()
    for want_cls, want_m in TARGETS:
        if cname != want_cls.replace("/", "/"):
            continue
        for m in cls.get_methods():
            if m.get_name() != want_m:
                continue
            code = m.get_code()
            print(f"=== {cname} -> {m.get_name()}{m.get_descriptor()} "
                  f"(registers={code.get_registers_size() if code else 0}) ===")
            if not code:
                print("  (no code)")
                continue
            bc = code.get_bc()
            off = 0
            for ins in bc.get_instructions():
                op = ins.get_name()
                ins_off = off
                off += ins.get_length()
                if op in ("nop",):
                    continue
                operands = ins.get_operands()
                ops = []
                for o in operands:
                    if o[0] == 0:      # register
                        ops.append(f"v{o[1]}")
                    elif o[0] == 1:    # literal
                        v = o[1]
                        ops.append(f"#{v:#x}" if isinstance(v, int) and abs(v) > 9 else f"#{v}")
                    elif o[0] == 2:    # string/reference index
                        ops.append(f"@{o[1]}")
                    elif o[0] == 3:    # field/method ref handled via get_string below
                        ops.append(str(o[1]))
                print(f"  {ins_off:06x}: {op:28s} {', '.join(ops)}")
            print()
