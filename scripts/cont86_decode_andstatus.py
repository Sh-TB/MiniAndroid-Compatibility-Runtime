#!/usr/bin/env python3
"""cont86_decode_andstatus.py — decode Ll90;.u + Lt60 (the CONT-84 T5
AndStatus2048 NPE anchor: 'getClass/Map.size on null at Ll90;.u pc=160')
from org.andstatus.game2048_47 via androguard. Names the app-level root.
"""
import sys, zipfile
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

APK = "/home/z/my-project/upload/cont73_apks/org.andstatus.game2048_47.apk"
z = zipfile.ZipFile(APK)
d = DEX(z.read("classes.dex"))

WANT = {"Ll90;", "Lt60;", "Ld80;", "Lur;"}
for m in d.get_methods():
    cls = m.get_class_name()
    if cls not in WANT:
        continue
    name = m.get_name()
    if cls == "Ll90;" and name != "u":
        continue
    if cls in ("Lt60;", "Ld80;", "Lur;") and name not in (
            "getValue", "<init>", "<clinit>") and not name.startswith("get"):
        continue
    print(f"\n===== {cls} -> {name} {m.get_descriptor()} =====")
    code = m.get_code()
    if code is None:
        print("  (abstract/native)")
        continue
    for ins in code.get_bc().get_instructions():
        op = ins.get_name()
        out = f"  {ins.get_offset():#06x}: {op}"
        try:
            if op.startswith(("invoke",)):
                out += " " + ins.get_translated_kind()[:110]
            elif op.startswith(("iget", "iput", "sget", "sput")):
                out += " " + str(ins.get_operands())[:110]
            elif op in ("const/16", "const/4", "const", "const-wide",
                        "const/high16"):
                out += " " + str(ins.get_operands())[:60]
        except Exception as e:
            out += f" <{e}>"
        print(out)
