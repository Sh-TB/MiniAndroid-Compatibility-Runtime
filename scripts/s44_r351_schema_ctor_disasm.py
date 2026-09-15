#!/usr/bin/env python3
"""S44 Attack-1 (R-NEW-351 frontier): full disassembly of the protobuf-javalite
MessageSchema ctor Llt0;.w in dooz_23 ground truth.

S43 established (evidence run s44_dooz_baseline reproduced byte-exact):
  [R337-REFLECT] Class(Ly81;).getDeclaredField("preferences_") -> Field obj#971
  [R337-UNSAFE]  objectFieldOffset Ly81;.preferences_ -> 280 caller=Llt0;.w
  [SYNTH-EXC]    aput-oob AIOOBE (length=1; index=1) method=Llt0;.w pc=953
                 -> uncaught -> MainActivity.onCreate dead -> blank frame.

S44 questions this script answers from pure bytecode:
  Q1: What is the instruction at pc=953 (array register, index register, value)?
  Q2: Where does the array register come from (backward dataflow: new-array /
      filled-new-array / aget / iget / move)?
  Q3: Where does the SIZE register of that new-array come from (computation)?
  Q4: What other arrays does Llt0;.w build (full new-array/filled-new-array census)?
  Q5: The method's overall shape (number of instructions, key branches) so the
      engine-side law can be placed at the exact failing opcode family.
"""
import zipfile, sys
import logging
logging.disable(logging.CRITICAL)
try:
    from loguru import logger
    logger.remove()
except Exception:
    pass
from androguard.core.dex import DEX

APK = '/tmp/my-project/apk_cache/s36new/io.github.yamin8000.dooz_23.apk'
TARGET_CLASS = 'Llt0;'   # androguard get_name() keeps the L...; form
TARGET_KEY = 'lt0'       # stripped key used in the methods map
TARGET_METH = 'w'

z = zipfile.ZipFile(APK)
dex_names = [n for n in z.namelist() if n.endswith('.dex')]
print(f"APK dex files: {dex_names}")

methods = {}
classes = {}
for dn in dex_names:
    d = DEX(z.read(dn))
    for c in d.get_classes():
        cname = c.get_name()
        if cname == TARGET_CLASS:
            classes[cname] = c
        for m in c.get_methods():
            methods[(cname, m.get_name(), m.get_descriptor())] = m

print(f"\n=== class {TARGET_CLASS} lookup: {'FOUND' if TARGET_CLASS in classes else 'NOT FOUND'} ===")
cls_key = TARGET_KEY
if cls_key in classes:
    c = classes[cls_key]
    print(f"super: {c.get_superclassname()}")
    for m in c.get_methods():
        print(f"  method {m.get_name()}{m.get_descriptor()}  access={m.get_access_flags_string()}")

# find all 'w' methods on Llt0; and dump the biggest (the 1009B ctor per S43)
cands = [(k, m) for k, m in methods.items() if k[0] == TARGET_CLASS and k[1] == TARGET_METH]
print(f"\n=== {TARGET_CLASS};.{TARGET_METH} candidates: {len(cands)} ===")
for k, m in cands:
    code = m.get_code()
    sz = code.get_bc().get_length() if code else 0
    print(f"  {k[2]}  code_bytes={sz}  regs={code.get_registers_size() if code else '-'} ins={code.get_ins_size() if code else '-'} outs={code.get_outs_size() if code else '-'}")

# dump the largest one with full pc-annotated bytecode
best_key, best_m = max(cands, key=lambda km: km[1].get_code().get_bc().get_length())
print(f"\n=== FULL BYTECODE {best_key[0]};.{best_key[1]}{best_key[2]} ===")
insns = []
code = best_m.get_code()
pc = 0
for ins in code.get_bc().get_instructions():
    op = ins.get_name()
    out = ins.get_output()
    length = ins.get_length()
    insns.append((pc, op, out))
    print(f"  {pc:5d} (0x{pc:04x}) {op:28s} {out}")
    pc += length
print(f"\ntotal instructions: {len(insns)}")

# census of array ops
print("\n=== ARRAY-OP CENSUS in Llt0;.w ===")
for pc, op, out in insns:
    if 'new-array' in op or 'filled-new-array' in op or op.startswith('aput') or op.startswith('aget') or op == 'array-length':
        print(f"  {pc:5d} {op:28s} {out}")
