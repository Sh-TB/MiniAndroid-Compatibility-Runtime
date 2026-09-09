#!/usr/bin/env python3
"""F-023c: raw 16-bit code-unit dump of a method (no decode, ground truth)."""
import zipfile, sys, struct
sys.path.insert(0, '/home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid/tools')
import exp059_disasm as d

APK = '/home/z/my-project/apk_cache/corpus/dooz.apk'
target_class = sys.argv[1]
target_method = sys.argv[2]

with zipfile.ZipFile(APK) as z:
    data = z.read('classes.dex')
dex = d.load_dex(data)
result = d.find_method(dex, target_class, target_method)
if not result:
    print('NOT FOUND'); sys.exit(1)
code_off, regs, ins, outs, tries, insns_size = result
raw = dex['data']
print(f'=== {target_class}.{target_method} code_off=0x{code_off:x} insns={insns_size} ===')
# code_item: registers(2) ins(2) outs(2) tries(2) debug(4) insns_size(4)
insns_off = code_off + 16
for i in range(insns_size):
    cu = struct.unpack_from('<H', raw, insns_off + i*2)[0]
    op = cu & 0xFF
    print(f'  [{i:4d}] 0x{cu:04x}  op=0x{op:02x}')
