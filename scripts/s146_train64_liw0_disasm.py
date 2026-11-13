#!/usr/bin/env python3
"""s146_train64_liw0_disasm.py — TRAIN-64: the coroutine-pump gap.

The S145 tap run shows the UP reaches Liw0; (SuspendingPointerInputModifierNodeImpl,
compose-ui 1.6.7) but the app lambda never runs post-UP ([QUEUE] zero enqueues,
zero io.github.yamin8000.dooz methods in the tap window).

The 1.6.7 VERBATIM source (docs/upstream/androidx/compose/1.6.7/commonMain/.../
SuspendingPointerInputFilter.kt) pins the law:
  onPointerEvent -> (first event) coroutineScope.launch(UNDISPATCHED){pointerInputHandler()}
                 -> dispatchPointerEvent -> forEachCurrentPointerHandler{ it.offerPointerEvent }
  awaitPointerEventScope = suspendCancellableCoroutine -> PointerEventHandlerCoroutine
  offerPointerEvent: if (pass == awaitPass) { pointerAwaiter = null; resume(event) }

This tool disassembles EVERY Liw0; method from the dooz dex so the minified
methods (.k/.b/.c/.g/...) can be mapped onto those source roles by signature,
size and call targets.
Usage: s146_train64_liw0_disasm.py <apk> [class_desc]
"""
import sys, zipfile, importlib.util

spec = importlib.util.spec_from_file_location(
    'cd', '/home/z/my-project/scripts/cont9_dexdump.py')
cd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cd)

APK = sys.argv[1]
DESC = sys.argv[2] if len(sys.argv) > 2 else 'Liw0;'

z = zipfile.ZipFile(APK)
dex = cd.Dex(z.read('classes.dex'))

cls_off = dex.find_class(DESC)
if cls_off is None:
    print('CLASS NOT FOUND', DESC)
    sys.exit(1)
info = dex.class_methods(cls_off)

print('=' * 78)
print(f'CLASS {DESC}  super={info["super"]}')
print('  ifaces:', info['ifaces'])
for kind, ftype, fname in info['fields']:
    print(f'  {kind:6s} {fname} : {ftype}')
print('=' * 78)

for kind in ('direct', 'virtual'):
    for mname, mdesc, acc, sz, code in info[kind]:
        print(f'{kind:7s} {mname}{mdesc}  acc={acc:#x} size={sz} code_off={code:#x}')

print('=' * 78)
for kind in ('direct', 'virtual'):
    for mname, mdesc, acc, sz, code in info[kind]:
        if not code:
            print(f'### {mname}{mdesc}  (abstract/native)')
            continue
        print(f'### {kind} {mname}{mdesc}  size={sz}')
        try:
            lines = dex.disasm(code)
            print(lines if isinstance(lines, str) else '\n'.join(str(x) for x in lines))
        except Exception as e:
            print('  <disasm error:', e, '>')
        print()
