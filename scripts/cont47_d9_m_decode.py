#!/usr/bin/env python3
"""CONT-47 D9b: decode Lzs0;.m()V + .k()V + .r/.s/.q/.c bytecode from the
dooz v23 APK (ALL dex shards) to name the exact callee/guard that kills the
measureAndLayout -> performMeasureAndLayout hop."""
import warnings, logging, zipfile
warnings.filterwarnings("ignore")
logging.disable(logging.CRITICAL)

from androguard.core.bytecodes.dvm import DalvikVMFormat as DEX

APK = "upload/canonical_apks/io.github.yamin8000.dooz_23.apk"

WANT = {
    ("Lzs0;", "m"), ("Lzs0;", "k"), ("Lzs0;", "r"),
    ("Lzs0;", "s"), ("Lzs0;", "q"), ("Lzs0;", "c"),
}

zf = zipfile.ZipFile(APK)
dex_names = [n for n in zf.namelist() if n.startswith("classes") and n.endswith(".dex")]
for dex_name in dex_names:
    d = DEX(zf.read(dex_name))
    for m in d.get_methods():
        cls, name = m.get_class_name(), m.get_name()
        if (cls, name) not in WANT:
            continue
        desc = m.get_descriptor()
        code = m.get_code()
        regs = (code.registers_size if code else "-")
        ins_n = (code.ins_size if code else "-")
        csize = code.get_length() if code else 0
        print(f"=== [{dex_name}] {cls}->{name}{desc} regs={regs} ins={ins_n} code={csize}")
        if not code:
            print("    <no code — abstract/native>")
            continue
        for ins in code.get_bc().get_instructions():
            op = ins.get_name()
            pieces = []
            for opr in ins.get_operands():
                kind, val = opr[0], opr[1]
                if kind == 0:
                    pieces.append(f"v{val}")
                elif kind == 1:
                    pieces.append(f"#{val}")
                elif kind == 2:
                    pieces.append(f'str@"{val}"')
                elif kind == 3:
                    pieces.append(f"ty@{val}")
                elif kind == 4:
                    pieces.append(f"fld@{val}")
                elif kind == 5:
                    pieces.append(f"mth@{val}")
                else:
                    pieces.append(f"?{val}")
            line = "    " + op + ((" " + ", ".join(pieces[:6])) if pieces else "")
            print(line[:220])
        print()
    print(f"--- scanned {dex_name} ---")
