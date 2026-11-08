#!/usr/bin/env python3
# S188-W18 contract audit — evidence BEFORE code (W8 law):
#  1. androguard: Gdx2DPixmap native-method face from p9 classes.dex
#     (which natives exist, which the <init> chain calls)
#  2. objdump: libgdx.so JNI slot demand — enumerate `call *0xNN(%rax)`
#     offsets in the pixmap/Matrix4 JNI functions and map NN/8 -> spec slot.
# Output: evidence/s188_w18/W18_JNI_DEMAND_AUDIT.json
import json, re, subprocess, sys, os

OUT = {}
os.makedirs('/home/z/my-project/evidence/s188_w18', exist_ok=True)

# ── part 1: DEX audit (androguard — primary DEX oracle) ─────────────────
APK = '/home/z/my-project/upload/stuck_apks/se.tube42.p9.android.apk'
from androguard.misc import AnalyzeAPK
import logging
logging.disable(logging.DEBUG)
a, dlist, dx = AnalyzeAPK(APK)
gdx_classes = {}
for d in dlist:
    for cls in d.get_classes():
        name = cls.get_name() or ''
        if 'Gdx2DPixmap' not in name and not name.endswith('Lcom/badlogic/gdx/math/Matrix4;'):
            continue
        methods = []
        for m in cls.get_methods():
            info = {
                'name': m.get_name() or '',
                'desc': m.get_descriptor() or '',
                'access': m.get_access_flags_string(),
            }
            code = m.get_code()
            if info['name'] == '<init>' and code:
                calls = []
                for ins in code.get_bc().get_instructions():
                    t = str(ins.get_output())
                    mo = re.search(r'L\S+?;->\S+', t)
                    if mo:
                        calls.append(mo.group(0))
                info['init_calls'] = calls
            methods.append(info)
        gdx_classes[name] = methods
OUT['dex'] = gdx_classes

# ── part 2: libgdx.so JNI call-face audit ───────────────────────────────
LIB = '/tmp/p9w17_store/data/app/se.tube42.p9.android/lib/x86_64/libgdx.so'
JNI_FN_OFFS = {  # spec slot -> function (subset we care about)
    4: 'GetVersion', 6: 'FindClass', 13: 'Throw', 14: 'ThrowNew',
    15: 'ExceptionOccurred', 17: 'ExceptionClear', 21: 'NewGlobalRef',
    23: 'DeleteLocalRef', 31: 'GetObjectClass', 33: 'GetMethodID',
    94: 'GetFieldID', 113: 'GetStaticMethodID', 144: 'GetStaticFieldID',
    146: 'GetStaticBooleanField', 150: 'GetStaticIntField',
    151: 'GetStaticLongField', 152: 'GetStaticFloatField',
    163: 'NewString', 165: 'GetStringChars', 167: 'NewStringUTF',
    169: 'GetStringUTFChars', 171: 'GetArrayLength', 172: 'NewObjectArray',
    173: 'GetObjectArrayElement', 174: 'SetObjectArrayElement',
    176: 'NewByteArray', 177: 'NewCharArray', 179: 'NewIntArray',
    180: 'NewLongArray', 181: 'NewFloatArray',
    184: 'GetByteArrayElements', 187: 'GetIntArrayElements',
    188: 'GetLongArrayElements', 189: 'GetFloatArrayElements',
    192: 'ReleaseByteArrayElements', 195: 'ReleaseIntArrayElements',
    196: 'ReleaseLongArrayElements', 197: 'ReleaseFloatArrayElements',
    200: 'GetByteArrayRegion', 203: 'GetIntArrayRegion',
    204: 'GetLongArrayRegion', 205: 'GetFloatArrayRegion',
    208: 'SetByteArrayRegion', 211: 'SetIntArrayRegion',
    212: 'SetLongArrayRegion', 213: 'SetFloatArrayRegion',
    215: 'RegisterNatives', 217: 'MonitorEnter', 218: 'MonitorExit',
    222: 'GetPrimitiveArrayCritical', 223: 'ReleasePrimitiveArrayCritical',
    226: 'NewWeakGlobalRef', 229: 'NewDirectByteBuffer',
    230: 'GetDirectBufferAddress', 231: 'GetDirectBufferCapacity',
    95: 'GetObjectField', 96: 'GetBooleanField', 100: 'GetIntField',
    101: 'GetLongField', 102: 'GetFloatField', 104: 'SetObjectField',
    109: 'SetIntField', 110: 'SetLongField',
}

def audit_fn(fn_name):
    """objdump -d one function; collect `call *0xNN(%rax)` env-table calls."""
    r = subprocess.run(['objdump', '-d', '--no-show-raw-insn', LIB,
                        '--start-address', '0', '0'], capture_output=True)
    return r

# Use objdump disassembly of the whole .text once; slice per function.
r = subprocess.run(['objdump', '-d', '--no-show-raw-insn', LIB],
                   capture_output=True, text=True)
if r.returncode != 0:
    OUT['objdump_error'] = r.stderr[:500]
else:
    lines = r.stdout.splitlines()
    fns = {}  # fn_name -> list of (offset, slot)
    cur = None
    call_re = re.compile(r'^\s*([0-9a-f]+):\s+call\s+\*0x([0-9a-f]+)\(%rax\)')
    for ln in lines:
        mo = re.match(r'^[0-9a-f]+ <(.+)>:', ln)
        if mo:
            cur = mo.group(1)
            continue
        if cur is None:
            continue
        m = call_re.match(ln)
        if m:
            off = int(m.group(2), 16)
            slot = off // 8 if off % 8 == 0 else None
            fns.setdefault(cur, []).append((m.group(1), slot, off))
    # audit the Gdx2DPixmap + Matrix4 + relevant JNI functions
    targets = {}
    for fn, calls in fns.items():
        if ('Gdx2DPixmap' in fn or 'Matrix4' in fn or 'Pixmap' in fn or
            'gdx2d_load' in fn or 'GL20' in fn and False):
            slots = [s for _, s, _ in calls if s]
            names = sorted({JNI_FN_OFFS.get(s, f'?slot{s}') for s in slots})
            targets[fn] = {
                'env_calls': len(slots),
                'slot_names': names,
                'detail': [(o, s, JNI_FN_OFFS.get(s, '?')) for o, s, _ in calls],
            }
    OUT['so'] = targets
    OUT['so_fn_count'] = len(fns)

with open('/home/z/my-project/evidence/s188_w18/W18_JNI_DEMAND_AUDIT.json', 'w') as f:
    json.dump(OUT, f, indent=1)
print('dex classes:', list(gdx_classes.keys()))
print('so audited fns:', len(targets))
for fn, info in sorted(targets.items()):
    print(f"  {fn}: {info['env_calls']} env calls -> {info['slot_names']}")
