#!/usr/bin/env python3
"""cont96_decode_benchvirtual.py — disassemble com.probe.perf1MainActivity.benchVirtual
and .ident from the perf1 APK to determine whether the F084 halt (50001 visits,
frozen branch signature) reflects a REAL frozen loop counter (engine semantic bug)
or a false positive."""
import sys, zipfile

try:
    from androguard.core.bytecodes.dvm import DalvikVMFormat
except ImportError:
    sys.path.insert(0, '/home/z/.local/lib/python3.12/site-packages')
    from androguard.core.bytecodes.dvm import DalvikVMFormat

apk = 'run/cont96/perf1.apk'
zf = zipfile.ZipFile(apk)
dex_bytes = zf.read('classes.dex')
dvm = DalvikVMFormat(dex_bytes)

for m in dvm.get_methods():
    name = m.get_name()
    cls = m.get_class_name()
    if 'bench' in name or name == 'ident':
        print(f"\n=== {cls}->{name} {m.get_descriptor()} ===")
        try:
            code = m.get_code()
            if code is None:
                print("  (no code)")
                continue
            bc = code.get_bc()
            off = code.get_offsets() if hasattr(code, 'get_offsets') else None
            pc = code.registers_size  # not used; walk with get_length instead
            addr = 0
            for ins in bc.get_instructions():
                ln = ins.get_length()
                try:
                    out = ins.get_output()
                except Exception:
                    out = '?'
                print(f"  {addr:4d}: {ins.get_name():22s} {out}")
                addr += ln // 2 if ln >= 2 else 1  # length in bytes; code units = /2
        except Exception as e:
            print("  decode error:", e)
