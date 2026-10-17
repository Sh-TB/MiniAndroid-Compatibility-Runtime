#!/usr/bin/env python3
"""cont83_registry_update.py — CONT-83 wave registry updates.

1. F-NEW-387 (NEW, ROOT-CAUSED-FIXED P1): Android native dependency
   resolution law — in-process ELF64 DT_NEEDED parse + validated
   first-party soname anchors + bionic @LIBC version-tag strip in the
   runtime-owned extracted copy. First REAL corpus native engine lib
   (stack.tower3d libgdx.so) loads through the full dlopen path.
2. F-NEW-388 (NEW, ROOT-CAUSED-FIXED P1 with a named GLSL frontier): the
   GLES20 static bridge wiring — android.opengl.GLES20 statics previously
   fell through every shadow (REC-MISS, null returns); now marshalled into
   the real PortableGL bridge (state/buffer/draw/uniform ops execute for
   real; shader objects return 0 because PGL does not compile GLSL — the
   frontier is named, never faked).
3. F-NEW-389 (NEW, ROOT-CAUSED-FIXED P2): DisplayManager.getDisplay /
   Display.getRealMetrics law — the first divergence surfaced by the
   CONT-83 graphics trace on the REAL corpus app stack.tower3d after the
   native load (AndroidGraphics.getDisplayMode NPE at
   Display.getRealMetrics on a null receiver).
4. F-NEW-367 status update: BLOCKED → the native-bootstrap boundary is
   open (the load law exists; the load milestone is proven on libgdx.so).
5. GFX-TRACE infra note (not a root): the CONT-83 WS-B op-level graphics
   trace (MINIANDROID_GFX_TRACE) recorded as evidence infrastructure.
"""
import json

ROOT = "/home/z/my-project"
P1 = f"{ROOT}/root_registry.json"
P2 = f"{ROOT}/canonical/root_cause_registry.json"


def main():
    r = json.load(open(P1))
    roots = r["roots"] if isinstance(r, dict) and "roots" in r else r
    ids = [x.get("id") for x in roots]
    assert len(ids) == len(set(ids)), "duplicate root ids"
    by_id = {x["id"]: x for x in roots if "id" in x}

    new_roots = [
        {
            "id": "F-NEW-387",
            "status": "ROOT-CAUSED-FIXED",
            "priority": "P1",
            "title": "Android native dependency resolution law (DT_NEEDED "
                     "anchors + bionic version-tag strip)",
            "layer": "jni/native-loader",
            "root_cause":
                "A real host dlopen of an extracted Android .so failed on "
                "the ANDROID platform sonames (libm.so/liblog.so/libc.so/"
                "libstdc++.so/libdl.so): the host loader cannot resolve "
                "them (Debian libm.so/libc.so are GNU ld scripts; liblog "
                "does not exist), and after the sonames are anchored the "
                "bionic version tags (name@LIBC) still fail the glibc "
                "versioned lookup ('undefined symbol: __cxa_finalize, "
                "version LIBC'). CONT-81's boundary was exactly here.",
            "evidence":
                "run/cont83/nat1_run5.log ([NAT1-ADD] add3=9, [NAT1-MATH] "
                "mathCheck=9 via the REAL libm through the anchor, 3/3 "
                "repeatable; [NAT1-NEG] UnsatisfiedLinkError honest block; "
                "ld-script masquerade rejected 'not an ELF object "
                "(ld-script/archive?)'); run/cont83/tower_run2.log: "
                "stack.tower3d libgdx.so (sha16 2e9dc948aab382e5, 193008B) "
                "dlopen ok — 13 @LIBC versym entries rewritten, 5 Android "
                "sonames served by validated anchors; gfx trace "
                "native.verstrip/native.dep/native.load rows; measured "
                "libgdx symbol surface: 14 UND, all standard C "
                "(readelf), zero Android-specific symbols.",
            "fix_surface":
                "src/jni/native_dep.cpp/.h (new): in-process ELF64 parse "
                "(DT_NEEDED + versym/verneed), is_real_elf64_dyn "
                "validation (ld-script/archive/wrong-arch rejection), "
                "prepare_dependencies classification (host-native → "
                "app-bundled → validated first-party anchor → "
                "missing-honest-block), strip_bionic_version_tags (LIBC "
                "versym indexes → VER_NDX_GLOBAL in the runtime-owned "
                "EXTRACTED copy, APK untouched, counted); "
                "scripts/cont83_build_anchors.sh (first-party anchor set "
                "with the ANDROID sonames: liblog.so = real stderr "
                "implementation of __android_log_print/write/vprint/"
                "buf_print, libm/libdl/libstdc++/libc = soname anchors "
                "whose own dependency chains pull the real host libs); "
                "dlopen_exec.cpp pre-pass wiring.",
            "honest_note":
                "ABI honesty: the anchors bind the app to the HOST C "
                "runtime — layout-free C symbols are SysV-stable (the "
                "measured libgdx surface), bionic struct layouts "
                "(pthread/FILE) remain the named risk recorded in the "
                "law. The anchor pre-pass is classified per-row and "
                "traced; unknown sonames fail loudly with the loader's "
                "own error (never a silent substitution). dlopen is a "
                "loader milestone, NOT a rendered-game claim (CONT-83 "
                "law): tower3d's next divergence moved to "
                "AndroidGraphics.getDisplayMode (F-NEW-389) and then to "
                "the AndroidGraphics object-graph fields (named residual).",
        },
        {
            "id": "F-NEW-388",
            "status": "ROOT-CAUSED-FIXED",
            "priority": "P1",
            "title": "GLES20 static bridge wiring (real PortableGL "
                     "dispatch) with the GLSL frontier named",
            "layer": "gles/graphics",
            "root_cause":
                "android.opengl.GLES20 statics fell through EVERY shadow "
                "(GLES20Bridge existed since CAMPAIGN 010 R9 but was "
                "never wired): every GLES20 call REC-MISSed and returned "
                "null — libGDX's GL20 wrapper and any GLES20 game got "
                "void for shader/buffer/draw/state ops. A second law bug: "
                "the shadow bridge call sites leave ctx.descriptor empty, "
                "so the return-kind was inferred as void for int-returning "
                "statics (glCreateShader et al).",
            "evidence":
                "run/cont83/gfx1_run.log (com.probe.gfx1, apk "
                "1be9d4382a1f1c90): [GFX1-GLES20-SEQ] vs=0 fs=0 prog=0 "
                "loc=0 err=0 — the PGL-true values (PGL's glCreateShader/"
                "glCreateProgram literally return 0: portablegl.h:15223 "
                "'return 0;' — GLSL not compiled), the 14-op sequence "
                "dispatched handled with glUniformMatrix4fv materializing "
                "a REAL float[] through the heap-array law; gfx trace "
                "rows api=GLES20 handled=true per op; the probe's GL10 "
                "rows show the ES1-FFP REC-MISS frontier (glColor4f) "
                "auto-derived as first_missing_transition.",
            "fix_surface":
                "gl_surface_shadow.cpp: the GLES20/GLES30 dispatch arm + "
                "the bounded marshal law (int/long/bool→int slot, float/"
                "double→float slot with the slot-0 placeholder contract, "
                "string→char*, engine heap arrays materialize to "
                "kMaxArrayElems, java.nio Buffer chase one ref-field "
                "level, NULL→nullptr; uniform-offset family honors the "
                "AOSP (T[], offset) signature; everything else = honest "
                "marshal-fail row); handles_class extended to GLES20/"
                "GLES30; the int-return table for empty descriptors; "
                "gles20_bridge.cpp: the fargs convention unified + "
                "glActiveTexture/glBindTexture/glGenTextures/glUniform1i/"
                "1f/2f/3f added.",
            "honest_note":
                "THE GLSL FRONTIER IS NAMED, NOT CLOSED: PortableGL does "
                "not parse GLSL — shader/program objects cannot exist, so "
                "shader-based rendering (every GLES20 game face) cannot "
                "produce app pixels yet. The options are on record "
                "(GLSL→C translation, or a Mesa-llvmpipe backend swap). "
                "No fake program handles were invented; the probe asserts "
                "the true 0 returns. The GL10 ES1-FFP translation layer "
                "remains the other registered GL frontier (glColor4f et "
                "al: honest REC-MISS rows).",
        },
        {
            "id": "F-NEW-389",
            "status": "ROOT-CAUSED-FIXED",
            "priority": "P2",
            "title": "DisplayManager.getDisplay / Display.getRealMetrics "
                     "law (fixed-portrait device model)",
            "layer": "framework/display",
            "root_cause":
                "getSystemService('display') returned the DisplayManager "
                "singleton (R-339) but every method REC-MISSed: libGDX "
                "AndroidGraphics.getDisplayMode NPE'd at "
                "Display.getRealMetrics on a null Display — the FIRST "
                "divergence surfaced by the CONT-83 graphics trace after "
                "the F-NEW-387 native load moved tower3d past the "
                "SharedLibraryLoadRuntimeException boundary.",
            "evidence":
                "run/cont83/tower_run2.log (pre-fix: [SYNTH-EXC] f141 "
                "NPE 'Display.getRealMetrics on a null object reference' "
                "at AndroidGraphics.getDisplayMode pc=24 → onCreate "
                "unwind); run/cont83/tower_run3.log (post-fix: the "
                "getDisplayMode chain completes, AndroidGraphics."
                "onSurfaceCreated/onSurfaceChanged/onDrawFrame EXECUTE, "
                "GL frames present; face changes 31ddd4d5→11a38a5a; "
                "frame-truth verdict moves NO_ROOT→"
                "DEFAULT_BACKGROUND_ONLY); the new frontier named: "
                "AndroidGraphics object-graph fields (cfg.useGL30 null "
                "receiver NPE at setupGL pc=29, getWindowManager null "
                "receiver at updatePpi pc=7).",
            "fix_surface":
                "src/framework/display_shadow.cpp/.h (new) + shadow "
                "registration: DisplayManager.getDisplay(int) → the "
                "canonical Display object; Display.getRealMetrics/"
                "getMetrics fill the AOSP DisplayMetrics field set on "
                "the CALLER's object (widthPixels/heightPixels/density/"
                "densityDpi/scaledDensity/xdpi/ydpi); getRotation→0; "
                "getWidth/getHeight; the density=1.0 mdpi device model "
                "the engine already uses (dp==px).",
            "honest_note":
                "The fixed-portrait 1080x1920/ROTATION_0 model mirrors "
                "the run config the frame pump and canvas laws already "
                "use — display-mode enumeration (getSupportedModes) and "
                "rotation remain the named frontier; no invented "
                "per-app values.",
        },
    ]

    added = 0
    for root in new_roots:
        if root["id"] in by_id:
            continue
        roots.append(root)
        by_id[root["id"]] = root
        added += 1

    # F-NEW-367 status update: the native-bootstrap boundary is open.
    f367 = by_id.get("F-NEW-367")
    if f367 and f367.get("status") == "BLOCKED":
        f367["status"] = "CONFIRMED_ADVANCED"
        f367["summary"] = (
            str(f367.get("summary", "")) +
            " | CONT-83 UPDATE (F-NEW-387): the native-lib load bridge "
            "now EXISTS and is proven on the REAL corpus lib "
            "(stack.tower3d libgdx.so dlopen ok through the validated "
            "anchor set + the bionic @LIBC version-tag strip). The load "
            "milestone is reached; the rendering frontier moved up-stack "
            "to AndroidGraphics (F-NEW-389 fixed getDisplayMode; the "
            "object-graph fields + the GLSL compile frontier are the "
            "named residuals).")

    # GFX-TRACE infra note.
    if "INFRA-GFXTRACE-1" not in by_id:
        roots.append({
            "id": "INFRA-GFXTRACE-1",
            "status": "IMPLEMENTED+TESTED",
            "priority": "P2",
            "title": "CONT-83 WS-B first-party op-level graphics trace "
                     "(MINIANDROID_GFX_TRACE, JSONL schema v1)",
            "layer": "diagnostics/observability",
            "root_cause":
                "A blank screenshot cannot tell whether the game never "
                "called GL, EGL fails, no context becomes current, no "
                "draw calls are submitted, buffers never swap, or host "
                "composition loses the frame (CONT-83 directive). The "
                "pre-existing GfxProvenance layer is chain-level (image "
                "bits); per-OP rows, native.load/dep rows, and frame "
                "correlation were missing.",
            "evidence":
                "gfx1 A/B: trace ON faces byte-identical ×3 (dooz "
                "31ddd4d5b8e6d18e + gfx1 f41dfdeab5cec584), overhead "
                "17.16s→17.18s mean (0.1%, within noise); first_missing "
                "auto-derivation proven on the gfx1 probe "
                "(GL10.glColor4f ES1-FFP REC-MISS); tower3d live rows "
                "(native.verstrip=13, 5 dep rows, 1 load ok); the "
                "14-game WS-D matrix at evidence/cont83/gfx_matrix.json "
                "with per-game summaries.",
            "fix_surface":
                "src/diagnostics/gfx_trace.h (header-only singleton): "
                "schema v1 rows {v,type,t_ns,frame,...}; gl.call "
                "(api/op/handled/argc/note) + gl.const-miss + gfx.frame "
                "(surface-created/changed/draw-frame/present) + "
                "native.load + native.dep + native.verstrip + "
                "marshal.fail; per-op budget (256) + drop counters; "
                "bounded summary JSON next to the run artifacts; hooks "
                "in gl_surface_shadow (GL10/EGL/GLES20), the frame pump "
                "(dalvik_engine), the present site + summary write "
                "(execution_engine), and the native loader (dlopen_exec/"
                "native_dep).",
            "honest_note":
                "The trace is opt-in (default off = one bool check), "
                "redacted (op names/handles/dims/rc — no pixel dumps, "
                "no user content), and bounded. Tracing ON never alters "
                "rendering semantics (byte-identical faces proven).",
        })

    out = {"roots": roots} if isinstance(r, dict) else roots
    json.dump(r if isinstance(r, dict) else roots, open(P1, "w"), indent=1)
    # canonical mirror
    r2 = json.load(open(P2))
    if isinstance(r2, dict) and "roots" in r2:
        r2["roots"] = roots
        json.dump(r2, open(P2, "w"), indent=1)
    else:
        json.dump(roots, open(P2, "w"), indent=1)

    ids2 = [x.get("id") for x in roots]
    assert len(ids2) == len(set(ids2)), "duplicate ids after update"
    print(f"registry: {len(roots)} roots (added {added} new + 1 infra)")


if __name__ == "__main__":
    main()
