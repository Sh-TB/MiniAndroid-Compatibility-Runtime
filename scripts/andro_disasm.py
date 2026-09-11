from loguru import logger
logger.remove()
from androguard.core.apk import APK
from androguard.core.dex import DEX
import sys
a = APK('/home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid/download/dooz_18.apk')
d = DEX(a.get_file('classes.dex'))
cls_want = sys.argv[1]
meth_want = sys.argv[2] if len(sys.argv) > 2 else None
for c in d.get_classes():
    if c.get_name() == cls_want:
        print('=== fields:', [(f.get_name(), f.get_descriptor()) for f in c.get_fields()])
        for m in c.get_methods():
            if meth_want and m.get_name() != meth_want:
                continue
            print(f'--- {m.get_name()} {m.get_descriptor()}')
            off = 0
            try:
                for ins in m.get_instructions():
                    sz = ins.get_length() // 2
                    print(f'  {off:#06x}: {ins.get_name():26s} {ins.get_output()}')
                    off += sz
            except Exception as e:
                print('  [decode error]', e)
