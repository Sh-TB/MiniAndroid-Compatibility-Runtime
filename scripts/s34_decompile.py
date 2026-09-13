#!/usr/bin/env python3
"""S34 R-NEW-333 analysis: decompile the compose-view pairing methods from the
dooz APK with androguard (battle-tested DEX disassembly)."""
import sys, zipfile
from androguard.core.dex import DEX

APK = '/tmp/my-project/apk_cache/io.github.yamin8000.dooz_18.apk'

def get_dex():
    z = zipfile.ZipFile(APK)
    return DEX(z.read('classes.dex'))

def find_method(d, cls, name=None, desc_contains=None, list_all=False):
    for c in d.get_classes():
        if c.get_name() == cls:
            for m in c.get_methods():
                if name and m.get_name() != name:
                    continue
                if desc_contains and desc_contains not in m.get_descriptor():
                    continue
                yield m
            return

def show(m, max_ins=200):
    print(f"=== {m.get_class_name()}.{m.get_name()}{m.get_descriptor()}"
          f" access={m.get_access_flags()}")
    n = 0
    for ins in m.get_instructions():
        out = ins.get_output()
        if len(out) > 150: out = out[:150] + '...'
        print(f"  {ins.get_name():26s} {out}")
        n += 1
        if n >= max_ins:
            print("  ... (truncated)")
            break

if __name__ == '__main__':
    d = get_dex()
    mode = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if mode in ('all', 'setcontent'):
        for m in find_method(d, 'Landroidx/compose/ui/platform/ComposeView;', 'setContent'):
            show(m)
    if mode in ('all', 'ctors'):
        for m in find_method(d, 'Landroidx/compose/ui/platform/ComposeView;', '<init>'):
            show(m, max_ins=60)
    if mode in ('all', 'bc'):
        # b() and c() on AbstractComposeView — candidates for
        # ensureCompositionCreated / disposeComposition
        for m in find_method(d, 'Landroidx/compose/ui/platform/AbstractComposeView;', 'b', '()->V'):
            show(m)
        for m in find_method(d, 'Landroidx/compose/ui/platform/AbstractComposeView;', 'c', '()->V'):
            show(m)
    if mode in ('all', 'attach'):
        for m in find_method(d, 'Landroidx/compose/ui/platform/AbstractComposeView;', 'onAttachedToWindow'):
            show(m)
    if mode in ('all', 'listcv'):
        for m in find_method(d, 'Landroidx/compose/ui/platform/ComposeView;'):
            print(f"  {m.get_name()}{m.get_descriptor()} access=0x{m.get_access_flags_value():x}")
