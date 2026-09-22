#!/usr/bin/env python3
"""s83_disasm_appcompat.py — disassemble the androidx methods that unwind
in the blank-game family (blackjack/queens/no.thanks/solitaire/...):
  * Landroidx/fragment/app/FragmentActivity;.onCreate  (NPE @ invoke_pc=0xc)
  * Landroidx/appcompat/app/AppCompatDelegateImpl;.ensureSubDecor (ISE)
  * Landroidx/appcompat/app/AppCompatDelegateImpl;.setContentView
Print bytecode with pc so the throw-site can be matched to invoke_pc.
"""
import sys
from loguru import logger
logger.remove()
from androguard.misc import AnalyzeDex

apk_dex = sys.argv[1]          # path to classes.dex extracted from APK
targets = [
    ("Landroidx/fragment/app/FragmentActivity;", "onCreate"),
    ("Landroidx/appcompat/app/AppCompatDelegateImpl;", "ensureSubDecor"),
    ("Landroidx/appcompat/app/AppCompatDelegateImpl;", "setContentView"),
    ("Landroidx/appcompat/app/AppCompatActivity;", "setContentView"),
    ("Landroidx/appcompat/app/AppCompatActivity;", "onCreate"),
]

a, d, dx = AnalyzeDex(apk_dex)
for cls_def in d.get_classes():
    cls = cls_def.get_name()
    for m in cls_def.get_methods():
        name = m.get_name()
        if not any(cls == tc and name == tn for tc, tn in targets):
            continue
        code = m.get_code()
        if code is None:
            print(f"### {cls}.{name} (abstract/native)")
            continue
        print(f"### {cls}.{name}{m.get_descriptor()}")
        bc = code.get_bc()
        idx = 0
        for ins in bc.get_instructions():
            op = ins.get_name()
            out = ins.get_output()
            print(f"  {idx:#06x}: {op:<28} {out}")
            idx += ins.get_length()
        print()
