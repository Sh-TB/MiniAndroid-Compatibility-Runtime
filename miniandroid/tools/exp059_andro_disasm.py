#!/usr/bin/env python3
"""Use androguard to disassemble a specific method - lightweight."""
import sys, zipfile, io
from androguard.core.dex import DEX

APK = '/home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid/download/exp038_telegram/Telegram.apk'
TARGET_CLASS = sys.argv[1] if len(sys.argv) > 1 else 'Lorg/telegram/ui/ActionBar/ActionBarLayout;'
TARGET_METHOD = sys.argv[2] if len(sys.argv) > 2 else 'addFragmentToStack'
TARGET_DESC = sys.argv[3] if len(sys.argv) > 3 else None  # e.g. '(Lorg/telegram/ui/ActionBar/BaseFragment;I)Z'

with zipfile.ZipFile(APK) as z:
    for dex_name in sorted(n for n in z.namelist() if n.endswith('.dex')):
        data = z.read(dex_name)
        d = DEX(data)
        for cls in d.get_classes():
            if cls.get_name() != TARGET_CLASS: continue
            print(f'Found class in {dex_name}')
            for m in cls.get_methods():
                if m.get_name() != TARGET_METHOD: continue
                desc = m.get_descriptor()
                if TARGET_DESC and desc != TARGET_DESC: continue
                print(f'\n=== Method: {TARGET_METHOD}{desc} ===')
                code = m.get_code()
                if code is None:
                    print('  no code')
                    continue
                print(f'  registers: {code.get_registers_size()} ins: {code.get_ins_size()} outs: {code.get_outs_size()}')
                print(f'  --- bytecode ---')
                for ins in code.get_bc().get_instructions():
                    print(f'  PC={ins.get_off():4d}  {ins.get_name():25s}  {ins.get_output()}')
            break
