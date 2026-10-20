#!/usr/bin/env python3
"""CONT-114 registry update: F-NEW-462 ROOT-CAUSED-FIXED (refined), add
F-NEW-463/464 ROOT-CAUSED-FIXED, add F-NEW-465 CONFIRMED_OPEN_GAP.
main == mirror, id-unique."""
import json, sys

MAIN = "/home/z/my-project/root_registry.json"
MIRROR = "/home/z/my-project/canonical/root_cause_registry.json"

def load(p):
    with open(p) as f:
        r = json.load(f)
    return r["roots"] if isinstance(r, dict) and "roots" in r else r

main = load(MAIN)
mirror = load(MIRROR)
assert len(main) == len(mirror) == 777, f"unexpected registry sizes: {len(main)}/{len(mirror)}"

main_ids = {x["id"] for x in main}

# 1) F-NEW-462 -> ROOT-CAUSED-FIXED with the REFINED root cause
refined_462 = None
for x in main:
    if x["id"] == "F-NEW-462":
        x["status"] = "ROOT-CAUSED-FIXED"
        x["priority"] = "P0-CLOSED"
        x["title"] = ("GL frame pump dispatched Renderer callbacks on the VIEW object "
                      "(receiver law violation, not ctor this-binding)")
        x["root_cause"] = (
            "REFINED (CONT-114 fixture-first): the CONT-113 ctor-this-binding theory was "
            "REFUTED by the V1 probe rows (fixtures/c114_f462_probe C462-SELF/C462-CFG all "
            "correct pre-fix; probe apk sha16 8c1ab344a991c7a0). The true root is in "
            "DalvikExecutionEngine::dispatch_gl_surface_view_frame: the pump bound args[0] "
            "of onSurfaceCreated/onSurfaceChanged/onDrawFrame to the GLSurfaceView20 VIEW "
            "object (self = make_object(view_object_id,...)) while dispatching the RENDERER's "
            "class methods (rcls from the glRenderer field). AOSP GLSurfaceView.GLThread."
            "guardedRun invokes the callbacks ON THE RENDERER. Tower3d evidence: all 11 "
            "[IGET-MISS-DIAG] rows on obj#138 (heap class GLSurfaceView20) were "
            "AndroidGraphics;.onDrawFrame field reads (resume/running/pause/destroy/"
            "lastFrameTime/frames/frameStart) — the AndroidGraphics state landed on the view; "
            "setupGL read config NULL (NPE pc=29), updatePpi invoked getWindowManager on NULL. "
            "Fix: one line — args[0] = the renderer object stored by setRenderer. "
            "Bracket: f462 probe pre-fix 0/3 row families (ctorStamp/seq read 0 on every "
            "callback) -> post-fix 3/3 (777/4242 x6 frames, exit 0->0). Tower3d: obj#138 "
            "IGET-MISS rows 11 -> 0; setupGL completes (SGET ApplicationType.Android pc=20, "
            "SGET Gdx.app pc=85 — past the old death).")
        x["fix"] = "miniandroid/src/dex/dalvik_engine.cpp dispatch_gl_surface_view_frame: renderer receiver binding"
        x["date"] = "2026-10-20"
        refined_462 = x
        break
assert refined_462, "F-NEW-462 not found"

new_roots = [
 {
  "id": "F-NEW-463",
  "title": "java.nio typed view-buffer family absent (ByteBuffer.asIntBuffer answered null) + GLES20 state-query-into-Buffer missing",
  "status": "ROOT-CAUSED-FIXED",
  "priority": "P0-CLOSED",
  "layer": "DEX_BRIDGE_NIO",
  "date": "2026-10-20",
  "root_cause": (
    "tower3d post-F-NEW-462 run: libGDX BufferUtils.newIntBuffer does "
    "ByteBuffer.allocateDirect(cap).order(ByteOrder.nativeOrder()).asIntBuffer(); "
    "asIntBuffer had NO handler (REC-MISS rows) -> the IntBuffer field answered null -> "
    "DefaultTextureBinder.getMaxTextureUnits NPE'd on IntBuffer.get (SYNTH-EXC, "
    "AndroidLauncher.onCreate APP BOUNDARY unwind). The S108 ROOT-022 ByteBuffer algebra "
    "stopped at the ByteBuffer class; every typed view was the generic null. Second half: "
    "GLES20.glGetIntegerv(pname, params) had no path that writes the queried state into a "
    "typed view object (marshal_gles20 only materializes java arrays)."),
  "fix": (
    "dalvik_engine.cpp: F-NEW-463 view-buffer family — ByteBuffer.as{Int,Short,Long,Float,"
    "Double,Char}Buffer allocate the typed view with the SAME __bb_* algebra (cap = "
    "remaining()/element_size, __bb_parent__ = byte receiver) and the typed views implement "
    "get()/get(i)/put/position/capacity/remaining/flip/clear/rewind over the __bb_b<i>__ "
    "element run (OpenJDK buffer algebra). gl_surface_shadow.cpp dispatch_gles20_static: "
    "glGetIntegerv state-query-into-Buffer family writes the answer into the view object's "
    "__bb_b0__ (ES2 spec-minimum table, documented model — GL_MAX_TEXTURE_IMAGE_UNITS/"
    "COMBINED 8, VERTEX_ATTRIBS 8, MAX_TEXTURE_SIZE 2048). Tower3d: getMaxTextureUnits "
    "progressed past the NPE (pc=1 -> Gdx.gl read at pc=6)."),
 },
 {
  "id": "F-NEW-464",
  "title": "R-NEW-414 initializer-default materializer allocated the object but never executed its ()V constructor",
  "status": "ROOT-CAUSED-FIXED",
  "priority": "P1-HIGH",
  "layer": "DEX_SHADOW_HEAP",
  "date": "2026-10-20",
  "root_cause": (
    "F-NEW-274 gates initializer fabrication on the ()V ctor's EXISTENCE, but "
    "materialize_init_default only allocated + seeded framework shells — every DEX-defined "
    "zero-state stayed a BARE SHELL. Tower3d evidence: "
    "[R414-INIT-DEFAULT] DirectionalLightsAttribute.lights = new Array (obj#346) — pre-fix "
    "an Array with ZERO fields; Array.add then read size off nothing -> ARR-LEN-NULL NPE "
    "-> AndroidLauncher.onCreate death."),
  "fix": (
    "materialize_init_default now EXECUTES the ()V ctor via try_recursive_invoke for "
    "DEX-defined types (class_info_index_ hit + class_has_no_arg_ctor gate), marks "
    "initialized, with a same-type in-flight re-entrancy guard (nested same-type "
    "materialization returns the bare shell — documented honest frontier). obj#346 class "
    "of faces now materialize with their real zero-state."),
 },
 {
  "id": "F-NEW-465",
  "title": "Bare-shell ctor-skip face: DEX-defined objects created outside DEX frames (frame=0/pc=0) dispatch methods with zero fields",
  "status": "CONFIRMED_OPEN_GAP",
  "priority": "P1-HIGH",
  "layer": "DEX_SHADOW_HEAP",
  "date": "2026-10-20",
  "root_cause": (
    "tower3d post-F-NEW-464: the SECOND DirectionalLightsAttribute instance's lights Array "
    "(obj#393) was allocated frame=0 pc=0 seq=392 ([ALLOC-TRACE] — NOT execute_new_instance, "
    "NOT materialize_init_default) and dispatched Array.add with ZERO field keys "
    "[IGET-MISS-DIAG] -> ARR-LEN-NULL -> onCreate death. Correlated rows: "
    "[REC-MISS] java/lang/reflect/Array;.newInstance caller=libGDX ArrayReflection.newInstance; "
    "[F106-CTOR] ClassReflection.getConstructor + Constructor.newInstance path creates the "
    "attribute copy. The ctor-skip happens on a non-DEX-frame allocation path whose identity "
    "is not yet pinned (CONT-28 'an object whose <init> never ran must be identifiable' is "
    "the named lever). Next wave: instrument the remaining (0,0) allocate sites, pin the "
    "Attribute-copy allocation, and make a DEX-defined <init> dispatch miss LOUD (no silent "
    "no-op) — fixture-first."),
  "evidence": "run/c114/tower3d_diag/stderr2.log rows: ALLOC-TRACE obj#393 pc=0 frame=0 seq=392; IGET-MISS-DIAG obj#393 keys:<none> caller=Array.add",
 },
]

for nr in new_roots:
    assert nr["id"] not in main_ids, f"{nr['id']} already exists"
    main.append(nr)

ids = [x["id"] for x in main]
assert len(ids) == len(set(ids)) == 780, f"registry not id-unique at 780: {len(ids)}"

# mirror == main
with open(MAIN) as f:
    pass
main_doc = json.load(open(MAIN))
mirror_doc = json.load(open(MIRROR))
if isinstance(main_doc, dict) and "roots" in main_doc:
    main_doc["roots"] = main
    json.dump(main_doc, open(MAIN, "w"), indent=1, ensure_ascii=False)
else:
    json.dump(main, open(MAIN, "w"), indent=1, ensure_ascii=False)
if isinstance(mirror_doc, dict) and "roots" in mirror_doc:
    mirror_doc["roots"] = json.loads(json.dumps(main))
    json.dump(mirror_doc, open(MIRROR, "w"), indent=1, ensure_ascii=False)
else:
    json.dump(json.loads(json.dumps(main)), open(MIRROR, "w"), indent=1, ensure_ascii=False)

print("registry updated: 777 -> 780 id-unique (main == mirror)")
for nr in new_roots:
    print(f"  + {nr['id']} {nr['status']}")
print("  ~ F-NEW-462 CONFIRMED_OPEN_GAP -> ROOT-CAUSED-FIXED (refined root cause)")
