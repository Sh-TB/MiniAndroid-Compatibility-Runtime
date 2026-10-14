#!/usr/bin/env python3
# cont40_decode.py — CONT-40 Phase-1: static decode of dooz v23's
# AbstractComposeView attach chain. Questions:
#  (1) Does ANY class in the APK call View.getWindowToken() — and from
#      which class/method? (the friend's claimed composition-creation gate)
#  (2) Where is the AbstractComposeView subclass (the onAttachedToWindow
#      override that drives ensureCompositionCreated) and what does its
#      attach chain ACTUALLY check (isAttachedToWindow? windowRecomposer?
#      ViewTreeLifecycleOwner? getWindowToken?)
#  (3) withFrameNanos / MonotonicFrameClock call shape (the friend's
#      parked-coroutine claim) — which class implements it.
# Field-ref-exact against the real (R8-renamed) DEX. No guessing.
import zipfile, sys
from androguard.core.dex import DEX

APK = '/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk'
z = zipfile.ZipFile(APK)
d = DEX(z.read('classes.dex'))

classes = list(d.get_classes())
print(f"classes: {len(classes)}")

# ── (1) getWindowToken census ────────────────────────────────────────────
targets = {
    'getWindowToken': 'Landroid/os/IBinder;',
    'getWindowId': 'Landroid/view/WindowId;',
    'isAttachedToWindow': 'Z',
    'getDisplay': 'Landroid/view/Display;',
    'getWindowSystemUiVisibility': 'I',
}
census = {k: [] for k in targets}
wtoken_callers = []
for c in classes:
    cn = c.get_name()
    for m in c.get_methods():
        code = m.get_code()
        if not code:
            continue
        for i in code.get_bc().get_instructions():
            op = i.get_name()
            if not op.startswith('invoke'):
                continue
            out = i.get_output()
            for name, desc in targets.items():
                if f";->{name}(" in out:
                    census[name].append((cn, m.get_name(), out.split('->')[0].strip()))
for k, v in census.items():
    print(f"\n== {k}: {len(v)} call sites")
    for cn, mn, recv in v[:12]:
        print(f"   {cn}->{mn}  recv={recv}")

# ── (2) find AbstractComposeView subclass: extends ViewGroup, has
#      onAttachedToWindow override, and a setContent ────────────────────
print("\n== onAttachedToWindow overrides:")
for c in classes:
    cn = c.get_name()
    sf = c.get_superclassname()
    for m in c.get_methods():
        if m.get_name() == 'onAttachedToWindow' and m.get_code():
            print(f"   {cn} extends {sf} -> onAttachedToWindow")

# ── (3) withFrameNanos implementers ─────────────────────────────────────
print("\n== withFrameNanos implementations:")
for c in classes:
    for m in c.get_methods():
        if m.get_name() == 'withFrameNanos' and m.get_code():
            print(f"   {c.get_name()}->withFrameNanos{m.get_descriptor()}")
