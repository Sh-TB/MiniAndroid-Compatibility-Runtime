#!/usr/bin/env python3
"""cont86_registry_update.py — CONT-86 registry update.

New roots: F-NEW-390 (gesture callback receiver-contract fix),
F-NEW-391 (System.getenv law), F-NEW-392 (PackageManager
.getSystemAvailableFeatures law), F-NEW-393 (ByteBuffer statics family:
wrap/duplicate + ByteOrder constants), F-NEW-394 (Class.forName framework
bridge: java.lang.Thread), F-NEW-395 (CONFIRMED_OPEN_GAP: deferred
exception raised inside <clinit> does not match the in-frame catch-all).

Re-grades (fresh evidence this wave): F-NEW-156, F-NEW-157, F-144,
F-NEW-169, R-NEW-047/048/049/050/064/114/115/116/117/118/119/120/121,
R-NEW-164/165/166.
"""
import json, shutil

REG = "/home/z/my-project/canonical/root_cause_registry.json"
MIRROR = "/home/z/my-project/root_registry.json"

with open(REG) as f:
    reg = json.load(f)
roots = reg["roots"]
before = len(roots)
by_id = {r["id"]: r for r in roots}

NEW = [
{
 "id": "F-NEW-390",
 "status": "ROOT-CAUSED-FIXED",
 "priority": "P1",
 "title": "GestureDetector callback DEX marshaling: args[0]=receiver contract (onScroll/onFling/onDown param shift)",
 "layer": "framework/input",
 "root_cause": "dispatch_gesture_cb passed ONLY the callback params [e1, e2, f3, f4] to try_recursive_invoke, whose binder contract is args[0]=receiver(this) — the touch-listener path passes [view, ev] correctly, the gesture path did not. Every declared param shifted one slot: e1-param read e2's object, e2-param read f3's float BITS as an object id (getX/getY -> 0), distanceX/vx read f4, distanceY/vy read OUT OF BOUNDS -> NaN (Float.toString '' and float-to-int 0). Fixture proof com.probe.swipe1: [SWIPE1-SCROLL] dx=25.0 (the y-delta) dy='' e2=0,0; [SWIPE1-FLING] vx=-1562.487427 (the vy value) vy=''. The C++ boundary diag [C86-GCB] proved the tracker CORRECT (f3=+1055.77=real x-velocity, f4=-1562.49=real y-velocity) — one receiver-contract bug, not two.",
 "evidence": "fixtures/cont86_swipe_probe (com.probe.swipe1, apk run/cont86/swipe1.apk) + harness --swipe 100,400,300,100@2 (S129 law): pre-fix rows vs post-fix rows; run/cont86/swipe_run*.log. Post-fix: onDown x=100,y=400 (real event object); onScroll dx=-16/-17 dy=+25 (AOSP distanceX=last-curr law); onFling vx=+1055.77 vy=-1562.49 (axes + signs correct). e2 carries down-coords (the 4-float emit payload has no current-coords slot) — NAMED RESIDUAL: e2-current-coords needs the emit payload widened to 6 floats; deltas/velocities are the load-bearing consumer values.",
 "test": "Post-fix swipe probe rows x3 + full regression on the fixed binary (wall 12/12, goldens 4/4, negatives 19/19, reinstall 8/8, MG-310 7/7, MG-150 3/3, c72priv 12OK/0BAD, selftests 13/13) — zero drift; the shared callback path regressed nothing.",
 "fix": "dispatch_gesture_cb prepends the listener object as args[0] (receiver), matching the touch-listener/key-listener contract.",
},
{
 "id": "F-NEW-391",
 "status": "ROOT-CAUSED-FIXED",
 "priority": "P1",
 "title": "System.getenv() law — AOSP never-null unmodifiable Map (was REC-MISS null)",
 "layer": "java/system",
 "root_cause": "Ljava/lang/System;.getenv() fell through to the generic null default. org.andstatus.game2048's Lmb;.<clinit> pc=136 does System.getenv()!.getClass() (R8 os-detection idiom) — the null receiver threw a deferred NPE, the clinit state still recorded result=OK (the F-NEW-215 honesty gap observed live: [CLASS_INIT] result=OK AFTER [SYNTH-EXC] uncaught — registered separately), the Lmb statics then answered null, and the null statics NPE'd getClass/Map.size at Ll90;.u pc=160 + Lt60;.getValue pc=33 on EVERY run (reproduced on two binaries). AOSP law (System.java): getenv() answers the process environment as an UNMODIFIABLE, NEVER-NULL String->String map.",
 "evidence": "run/cont86/as2048*.log: NPE census 22 (pre) -> 5 (post-F-NEW-391) -> 0 (post full chain); androguard decode scripts/cont86_decode_andstatus.py (Lmb;.<clinit> pc=128-142 getenv->getClass chain decoded from org.andstatus.game2048_47). Deterministic sandbox law: EMPTY map with __array_length__=0 (byte-stable across runs).",
 "test": "andstatus2048_47 full-boot run with 0 NPE / 0 uncaught + the full regression battery on the final binary (all gates green, zero drift).",
 "fix": "bridge_to_api: getenv() materializes an empty LinkedHashMap heap object (never null).",
},
{
 "id": "F-NEW-392",
 "status": "ROOT-CAUSED-FIXED",
 "priority": "P2",
 "title": "PackageManager.getSystemAvailableFeatures law — FeatureInfo[] never-null (was REC-MISS null)",
 "layer": "framework/pm",
 "root_cause": "getSystemAvailableFeatures REC-MISSed to null. org.andstatus.game2048's Lr30;.d (R8 feature classifier) does context.getPackageManager().getSystemAvailableFeatures().getClass() — getClass on the null array threw the deferred NPE one link past F-NEW-391, propagating through Lt60;.getValue into MyMainActivity.onCreate (APP BOUNDARY unwind). AOSP law: answers FeatureInfo[], never null (empty when none declared).",
 "evidence": "run/cont86/as2048_post*.log: NPE census 5 -> 2 after this law; decode shows Lr30;.d pc=16 getClass on the array + the size==0 early-exit guard that consumes an empty array AOSP-honestly.",
 "test": "andstatus2048_47 chain: 0 NPE end-to-end; regression battery green on final binary.",
 "fix": "bridge_to_api: materialize a zero-length [Landroid/content/pm/FeatureInfo; heap array (__array_length__=0).",
},
{
 "id": "F-NEW-393",
 "status": "ROOT-CAUSED-FIXED",
 "priority": "P2",
 "title": "ByteBuffer statics family: wrap([B)/wrap([BII) + duplicate() laws + ByteOrder constant materialization",
 "layer": "java/nio",
 "root_cause": "Three gaps in the nio surface: (a) ByteBuffer.wrap was absent — Lb8;.<init>'s endian-view ctor (wrap([B).order(BO)) got null and NPE'd order-on-null (the chain's third link); (b) ByteBuffer.duplicate() was absent — the same ctor's big-endian view NPE'd (fourth link); (c) ByteOrder.LITTLE_ENDIAN/BIG_ENDIAN statics answered null (obj_id=0). OpenJDK law: wrap/duplicate answer non-null buffers (duplicate = a view; shadow model returns this, separate-cursor divergence = named residual), ByteOrder constants are non-null singletons.",
 "evidence": "run/cont86/as2048_post*.log NPE census 2 -> 0; [C86-BRIDGE] rows prove the statics reach bridge_to_api (wrap argc=1, nativeOrder argc=0, duplicate argc=1); decode of Lb8;.<init> (I Z)V + (Ljava/nio/ByteBuffer;)V.",
 "test": "andstatus2048_47: 0 NPE, 0 uncaught, boot to frame pump; regression battery green on final binary.",
 "fix": "ByteBuffer block: wrap law (cap from __array_length__, off+len for the 3-arg form) + duplicate law (returns receiver); SGET static chain: ByteOrder constants materialize with ordinal 0/1.",
},
{
 "id": "F-NEW-394",
 "status": "ROOT-CAUSED-FIXED",
 "priority": "P2",
 "title": "Class.forName framework bridge widened: java.lang.Thread (engine-modeled class)",
 "layer": "java/lang/reflect",
 "root_cause": "R350-FORNAME resolved only the Build-family whitelist; forName(\"java.lang.Thread\") CNFE'd although Thread is engine-modeled (ThreadShadow: THREAD-START/SLEEP-YIELD laws). org.andstatus.game2048's Luu;.<clinit> probes Thread.onSpinWait availability via forName(...).getMethod(\"onSpinWait\") inside a catch-all — on device forName NEVER throws for a shipped framework class. The CNFE answer tripped the deferred-exception handler-match gap (F-NEW-395); the bridge makes the app-visible outcome match the device truth (getMethod miss -> caught -> fallback).",
 "evidence": "run/cont86/as2048_post*.log: [R350-FORNAME] java.lang.Thread -> ClassNotFoundException -> uncaught -> APP BOUNDARY; post-fix: 0 uncaught. S84 A/B law respected (Thread is modeled, not a stub-artifact Class-object recursion storm source).",
 "test": "andstatus2048_47 clean boot; wall 12/12 + full battery green on the final binary (Thread consumers in the wall corpus unaffected).",
 "fix": "r350_fw_classes whitelist + \"Ljava/lang/Thread;\".",
},
{
 "id": "F-NEW-395",
 "status": "CONFIRMED_OPEN_GAP",
 "priority": "P2",
 "title": "Deferred exception raised INSIDE <clinit> does not match the clinit frame's own catch-all handler",
 "layer": "dex/exceptions",
 "root_cause": "Luu;.<clinit> wraps forName(\"java.lang.Thread\").getMethod(\"onSpinWait\") in a catch-all (move-exception at pc=28, try covering the probe region — decoded from org.andstatus.game2048_47). The engine's deferred CNFE from R350-FORNAME reported 'uncaught (deferred frame unwind + propagate)' instead of dispatching to that in-frame handler, killing the clinit and propagating to MyMainActivity.onCreate. The same CNFE shape DID dispatch to the app-level handler in Lk00;.<clinit> ('deferred handler @0x0xe') — the handler search covers CALLER frames but misses the CURRENT clinit frame's own try ranges. Related honesty defect observed live: a clinit that throws records [CLASS_INIT] result=OK (F-NEW-215's erroneous-class state was NOT set for deferred raises) — the getenv fix (F-NEW-391) removed the throw so result=OK became true, but the state-machine defect remains.",
 "evidence": "run/cont86/as2048_post*.log rows: '[SYNTH-EXC] R350-FORNAME (deferred): CNFE method=Luu;.<clinit> pc=2 -> uncaught' vs the dex decode (catch-all present at pc=28); contrast row 'deferred handler @0x0xe' for Lk00. androguard decode of both clinits.",
 "test": "Negative evidence: the gap is REPRODUCIBLE from the log rows + decode; fix requires the clinit-frame deferred-raise path to consult the current frame's handler table before unwinding.",
},
]
for r in NEW:
    assert r["id"] not in by_id, r["id"]
    roots.append(r)
    by_id[r["id"]] = r

def regrade(rid, status, evidence_add, note):
    r = by_id[rid]
    r["status"] = status
    r["evidence"] = (r.get("evidence", "") + " | " + evidence_add).strip(" |")
    r["cont86_note"] = note

regrade("F-NEW-156",
        "ALREADY_FIXED_AND_TESTED",
        "[CONT-86 fresh run] chessclock_29 on the final binary: the registered root (Settings$System.DEFAULT_RINGTONE_URI SGET-MISS -> NPE unwind at onCreate) no longer reproduces — the static materializes (obj_id=11) and the run reaches the frame pump with zero APP-BOUNDARY rows; face fe3ae1167c9e968c (static post-boot face).",
        "Root non-reproducing on the current binary; the static-face content is a separate unnamed frontier, not this root.")
regrade("F-NEW-157",
        "SUPERSEDED-BY-EVIDENCE",
        "[CONT-86 fresh run] tictactoe_emmanuel on the final binary: NO createGLSurfaceView NPE; the libGDX chain runs, SharedLibraryLoader's native probe throws GdxRuntimeException which libGDX's OWN catch-all handles (non-fatal by design), app reaches the frame pump; face b5a7a35d5fe0564b BYTE-IDENTICAL to the recorded CONT-17 anchor. Superseded by the F-NEW-387/388/389 native+GLES+display law family (tower3d, a deeper libGDX app, is the family reference).",
        "Family closed by the CONT-83 law stack; this row's specific NPE no longer exists.")
regrade("F-144",
        "SUPERSEDED-BY-EVIDENCE",
        "[CONT-86] The GL/EGL surface family is now covered by F-NEW-387 (native deps), F-NEW-388 (GLES20 dispatch, GLSL frontier NAMED), F-NEW-389 (DisplayManager) + the EGL shadow/frame pump; residual = the GLSL-compile frontier, tracked in the F-NEW-388 row.",
        "Row closed as superseded; keep the GLSL residual pointer.")
regrade("F-NEW-169",
        "NOT-APPLICABLE",
        "[CONT-86 re-grade] The registered artifact (upload/whatsapp.apk) fails ZIP magic — an invalid APK file, not a runtime defect; no lattice advance is possible from a corrupt input. The runtime's install path correctly REJECTS invalid archives (loud negative family).",
        "Input artifact is invalid; the runtime behavior (reject) is correct.")
for rid in ["R-NEW-047", "R-NEW-048", "R-NEW-049", "R-NEW-050", "R-NEW-064",
            "R-NEW-114", "R-NEW-115", "R-NEW-116", "R-NEW-117", "R-NEW-118",
            "R-NEW-119", "R-NEW-120", "R-NEW-121"]:
    regrade(rid,
            "SUPERSEDED-BY-EVIDENCE",
            f"[CONT-86 bulk re-grade] {rid}'s researched-not-implemented classification (jni_bridge/.so/ELF boundary) is IMPLEMENTED by F-NEW-387 (CONT-83): in-process ELF64 DT_NEEDED parse + host-native/app-bundled/first-party-anchor/missing classification + @LIBC versym strip, proven on stack.tower3d's real libgdx.so (dlopen ok) + probe negatives.",
            "Research row superseded by the landed law.")
regrade("R-NEW-164",
        "SUPERSEDED-BY-EVIDENCE",
        "[CONT-86] The planned tooling class G is delivered as INFRA-GFXTRACE-1 (MINIANDrodid_GFX_TRACE op-level JSONL + first-missing auto-derivation, zero-drift A/B).",
        "Tooling row superseded by the landed observability subsystem.")
for rid in ["R-NEW-165", "R-NEW-166"]:
    regrade(rid,
            "SUPERSEDED-BY-EVIDENCE",
            "[CONT-86] The planned differential harness exists: the wall/goldens/negatives/reinstall gate family + zero-drift A/B byte-identical proofs (CONT-83/86 evidence) + the harness result contract (CONT-84 T10 CONFIRMED_ADVANCED).",
            "Harness row superseded by the landed gate family.")

reg["roots"] = roots
with open(REG, "w") as f:
    json.dump(reg, f, indent=1, ensure_ascii=False)
shutil.copyfile(REG, MIRROR)
print(f"registry: {before} -> {len(roots)} roots; regraded 17 rows; mirror updated")
