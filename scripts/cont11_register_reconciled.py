#!/usr/bin/env python3
"""cont11_register_reconciled.py — register the genuinely-NEW faces found by
the CONT-11 loading census on the RECONCILED (remote W9) registry.
The three fixes the census wave made independently (interface exactness /
Thread UEH / WindowMetrics) are ALREADY in this lineage as F-NEW-281c /
F-NEW-272 / F-NEW-486 — duplicates are NOT re-registered. The next faces
are new: F-NEW-514/515/516."""
import json

REG = "/home/z/my-project/root_registry.json"
d = json.load(open(REG))
roots = d["roots"] if isinstance(d, dict) else d
have = {r.get("id") for r in roots}

NEW = [
    {
        "id": "F-NEW-514",
        "title": "NEXT FACE (loading census, issue #387): WindowInsetsCompat.toWindowInsetsCompat(View,WindowInsets) NPE — Object.getClass on null at the class-identity dispatch (census 16-title Object.getClass umbrella survivors: nononsenseapps.notepad, app.simple.peri, eu.faircode.netguard + cluster). CL-TRACE (peri): the crashing static call arrives with a truncated arg window (a0=i0 only; the WindowInsets arg absent) from ThemeKt.PeristyleTheme after GapComposer.consume(LocalView) — the compose composition-locals chain (LocalView.current) and/or the static invoke arg extraction at that call site. Upstream body: new-instance → insets.getClass() (Impl-table dispatch) → Impl34 ctor; the NULL is the WindowInsets slot. Probe-first next wave: disassemble PeristyleTheme register flow at 0x01bc-0x01f0, prove which register is UNSET, then fix the compose-locals law (LocalView provisioning) or the static arg window.",
        "status": "REGISTERED",
        "priority": "P0",
        "layer": "compose/composition-locals",
    },
    {
        "id": "F-NEW-515",
        "title": "NEXT FACE (loading census, issue #387): org.fossify.* 7-title family — ContentResolver.query('content://org.fossify.android.provider/fonts') throws the AOSP-faithful IAE 'Unknown authority' (N-18 law), the app's finally-close path (catch-all handler closes cursor, `throw v0` rethrow) re-raises it, and the unwind dies at SplashActivity/MainActivity.onCreate WITHOUT consulting the registered deferred handler (type=Exception) — the coroutine-boundary frame-collapse face (kotlinx BaseContinuationImpl/AbstractCoroutine resumeWith Result.failure law; kin of F-NEW-217). Faces: fossify calendar/clock/math/messages/musicplayer/notes/phone (7 titles) + opennotescanner service-intent IAE. Fix surface: exception unwind across collapsed direct-dispatch frames must consult the logical chain's deferred handlers.",
        "status": "REGISTERED",
        "priority": "P0",
        "layer": "runtime/exception-unwind",
    },
    {
        "id": "F-NEW-516",
        "title": "NEXT FACE (loading census, issue #387): List.size-on-null family (5 titles: bouncy ScoreView F-138 kin ×2, org.dmfs.tasks TabConfig.visible, surgeengine liballeg Sensors.unlisten, +1) — a shadow/list-returning API answers null where upstream answers an empty/non-null collection, then List.size NPEs; plus the recurring backlog: ViewDragHelper.continueSettling NPE (2 drawer-layout titles), libGDX AndroidInput.onResume NPE (2 surge-family titles — kin of F-NEW-157 EGL), NSM singles (guandan LocalLifecycleOwner, tictactoe GLSurfaceView20.setPreserveEGLContextOnPause, lrceditor CoordinatorLayout.<init>). Each needs its own first-dive (probe-first).",
        "status": "REGISTERED",
        "priority": "P1",
        "layer": "framework/collections-nullability",
    },
]

for e in NEW:
    if e["id"] not in have:
        roots.append(e)

if isinstance(d, dict):
    d["roots"] = roots
json.dump(d, open(REG, "w"), indent=1, ensure_ascii=False)
print("registry now", len(roots), "roots")
