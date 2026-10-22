#!/usr/bin/env python3
"""cont159_registry.py — CONT-159 registry update: F-NEW-500..508.
tower3d decode wave: 8 ROOT-CAUSED-FIXED generic engine laws + 1 honest
CLASSIFIED frontier (the app-level font-parse tab token).
"""
import json, hashlib, sys

REG = 'root_registry.json'
r = json.load(open(REG))
roots = r if isinstance(r, list) else r.get('roots', r.get('registry', []))
before = len(roots)

BIN = '2acd3a23e7064f2c'
WALL = ("wall 9/9 MATCH at binary " + BIN + " (dooz 31ddd4d5, klondike a77038da, "
        "unote 7481e9b4, chess a0319686, telegram 1671f5a3, tower3d 11a38a5a, "
        "opencalc 63020bc7, microtimer bbd350b6, sudoku be640e39 — zero drift "
        "across all 8 laws); negatives 19/19; skill selftest 13/13")

NEW = [
 ("F-NEW-500", "ROOT-CAUSED-FIXED", "P1",
  "String.compareTo(String) — REAL lexicographic law (OpenJDK: UTF-16 code-unit "
  "lexicographic; first differing unit answers the difference, common prefix answers "
  "the length difference; units walked via str_char_at_unit per the CONT-121 JVM law). "
  "ROOT CAUSE: the engine had NO compareTo handler; the unhandled virtual fall-through "
  "answered 0 — every pair of DISTINCT strings compared equal. Observable collapse "
  "(tower3d, libgdx 3D): Attribute.getAttributeType scans the registered-alias array "
  "with compareTo → returned 0 ('found' at index 0) for EVERY distinct alias → "
  "Attribute.register returned the same bit for every attribute class "
  "(DirectionalLightsAttribute.Type == ColorAttribute.Type == 1) → "
  "Environment.add(DirectionalLight) matched the foreign ColorAttribute instance under "
  "the DLA type key → the absent DirectionalLightsAttribute.lights field read through "
  "it (R-NEW-414 default) → death chain. Also poisons every libgdx Sort/TimSort "
  "consumer. Evidence: tower3d DLA.Type 1→128 (unique bits) post-fix; " + WALL,
  "run/c159/tower3d_fix1.log vs tower3d_v.log (f141-null-recv gone); "
  "run/c159/tower3d_rc.log ([RET-CALLER] decode)"),

 ("F-NEW-501", "ROOT-CAUSED-FIXED", "P1",
  "F-NEW-464 materializer passes the EXACT '()V' descriptor. ROOT CAUSE: with the "
  "descriptor empty, the lenient overload selection (EXP-078 largest-bytecode law) "
  "picked whichever same-name <init> had the biggest body — for libgdx Array the COPY "
  "ctor (Lcom/badlogic/gdx/utils/Array;-><init>(Lcom/badlogic/gdx/utils/Array;)V, 30 "
  "units > 7) — it read the fresh shell's ABSENT items field → getClass() on null → "
  "NPE → AndroidLauncher.onCreate death. The F-NEW-274 gate already verifies a local "
  "()V exists, so the exact-match law resolves it deterministically. Evidence: "
  "[RET-CALLER] pinned callee=Array;.<init> size=30 at the R414 site (Environment.add "
  "pc=18); post-fix the ()V chain (size=7→10) runs and the copy-ctor NPE is gone. " + WALL,
  "run/c159/tower3d_rc.log; run/c159/tower3d_fix2.log"),

 ("F-NEW-502", "ROOT-CAUSED-FIXED", "P1",
  "Class.getComponentType() — REAL array-component law (OpenJDK: array classes answer "
  "the component Class; non-arrays answer null; '[X' strips to X — bare primitive "
  "letters answer the primitive token, L...;/[[... keep the descriptor form). ROOT "
  "CAUSE: NO handler → null → the R-NEW-358 Array.newInstance shadow saw an EMPTY "
  "component descriptor → returned null → Array.resize's `newItems.length` (array-"
  "length on null) → NPE → death (tower3d: Array.add → resize → ArrayReflection."
  "newInstance(items.getClass().getComponentType(), newSize)). Evidence: post-fix the "
  "[REC-MISS] getComponentType row is gone and resize allocates real arrays. " + WALL,
  "run/c159/tower3d_fix2.log vs fix3.log"),

 ("F-NEW-503", "ROOT-CAUSED-FIXED", "P1",
  "GLES20 bridge POINTER-ARRAY indexing + null guards. ROOT CAUSE: the bridge indexed "
  "P(k) by JAVA-ARG position but P indexes the pointer-only array (marshal pushes only "
  "object args there) — glGenBuffers/glGenTextures/glBufferData/glVertexAttribPointer/"
  "glGetUniformLocation/glUniformMatrix4fv/glDrawElements all read PAST the array "
  "(bounds-checked → nullptr); portablegl's glGenBuffers wrote generated ids through "
  "the NULL out-param → SEGV fault_addr=0x0 (tower3d, the first libGDX-3D title to "
  "reach mesh building). Fix: single-pointer calls read P(0); null out-params/clients "
  "skip the native call with an honest trace note (ids stay 0 — minus the process "
  "death). F-NEW-503b (same train): glGetShaderiv/glGetProgramiv status-query family "
  "answered via the F-NEW-463 view-buffer identity (__bb_b0__: COMPILE_STATUS/"
  "LINK_STATUS → GL_TRUE for engine-minted handles; DELETE_STATUS → GL_FALSE) — the "
  "missing handler made ShaderProgram.isCompiled() read 0 → createDefaultShader IAE. "
  "Evidence: fix3 SEGV (addr2line: portablegl.h:12046 via GLES20Bridge::dispatch) gone "
  "at fix4; shader IAE gone at fix12 with the F-NEW-505 handle law. " + WALL,
  "run/c159/tower3d_fix3.log (S100-CRASH-FORENSICS signal=11); fix12.log"),

 ("F-NEW-504", "ROOT-CAUSED-FIXED", "P1",
  "APP-CLASS NATIVE LAYERING: an ACC_NATIVE method declared in an APP-DEX class never "
  "reached bridge_to_api — try_recursive_invoke finds the DEX class, the native block "
  "intercepts, JNIBridge has no handler → the REAL library attempt runs. For libgdx "
  "BufferUtils.newDisposableByteBuffer(I) the real libgdx.so allocator FAULTED under "
  "the engine's heap model (guarded, survived — FIX-TTT law) and answered null → the "
  "consumer's .order(ByteOrder.nativeOrder()) NPE'd on null → death. Law: consult "
  "bridge_to_api BEFORE the real-library attempt (framework-class natives reach the "
  "bridge only via the class-miss path — the same engine-side shadow surface now "
  "serves app-class natives). Plus the BufferUtils.newDisposableByteBuffer shadow: "
  "the S108 ROOT-022 allocateDirect heap-ByteBuffer shape (cap/pos/lim/order + lazy "
  "__bb_b<i>__ run), LITTLE-ENDIAN recorded. Evidence: the guarded-native fault row "
  "gone at fix6; the NPE chain resolved. " + WALL,
  "run/c159/tower3d_fix5.log vs fix6.log"),

 ("F-NEW-505", "ROOT-CAUSED-FIXED", "P1",
  "GLSL shader-handle family, ENGINE-SIDE. ROOT CAUSE: the PortableGL port stubs the "
  "whole GLSL surface (portablegl.h:15223 glCreateShader → { return 0; }; "
  "glCompileShader/glLinkProgram/glShaderSource no-ops) — the stubs leaked through the "
  "bridge as REAL answers: glCreateShader → 0 → ShaderProgram.loadShader's "
  "`if (shader == 0)` branch skipped the compile → isCompiled() false → "
  "SpriteBatch.createDefaultShader threw IllegalArgumentException('Error compiling "
  "shader: ') → death (tower3d). Law: the engine mints honest handles (shaders: "
  "type/compiled/deleted; programs: attached/linked/deleted; stable per-program "
  "name→location maps for glGetUniformLocation/glGetAttribLocation — the PGL stub "
  "returned 0 for EVERY name, collapsing all uniforms to slot 0); glUseProgram on "
  "engine-minted GLSL programs must NOT reach PGL's program namespace (unknown ids). "
  "The GLSL source stays stored-not-executed (the glsl-not-compiled honesty note "
  "stands — the fixed-function C-program path is the render bound). Evidence: "
  "fix11 shader IAE gone; the SpriteBatch/Mesh/GL pipeline executes (1520 IMPLEMENTED "
  "stub-census at fix13). " + WALL,
  "run/c159/tower3d_fix8.log (GL-DISPATCH decode); fix11.log"),

 ("F-NEW-506", "ROOT-CAUSED-FIXED", "P1",
  "GLES20 gen* OUT-PARAM WRITE-BACK law. ROOT CAUSE: glGenBuffers/glGenTextures write "
  "generated ids through the marshalled pointer — a COPY of the Java holder's "
  "contents; without a write-back the ids die in the hold — the caller's handle.get(0) "
  "read 0 → libGDX IndexBufferObject.bind threw GdxRuntimeException('No buffer "
  "allocated!') → death. Law: after a handled gen* call, copy the hold bytes back "
  "into the Java holder — heap arrays via the array[i] field convention "
  "(read_array_elems mirror), F-NEW-463 Buffer views via the __bb_b<i>__ element run "
  "(the same storage the typed-view get reads). Evidence: post-fix the bufferHandle "
  "lands (GL_INVALID_ENUM glBindBuffer rows = benign PGL notes on real ids) and the "
  "font/texture pipeline proceeds to FileHandle.read. " + WALL,
  "run/c159/tower3d_fix11.log vs fix12.log"),

 ("F-NEW-507", "ROOT-CAUSED-FIXED", "P1",
  "Class.getResourceAsStream / ClassLoader.getResourceAsStream — REAL classpath law. "
  "ROOT CAUSE: NO handler → null → libGDX ClasspathFileHandle.read threw "
  "GdxRuntimeException(path + ' does not exist') on the FIRST classpath resource "
  "(com/badlogic/gdx/utils/lsans-15.fnt — the libGDX default BitmapFont bundled at "
  "the APK ROOT, not under assets/) → death. Law (libcore): getResourceAsStream "
  "resolves against the classloader's class path — for an APK that is the APK's own "
  "entry table (the S102 SERVICELOADER-APK-ENTRY precedent); the leading '/' strips; "
  "the stream registers in open_assets_ under the 'apk-entry:' backing so the F104 "
  "read family answers REAL bytes (verified: readLine delivered the true info/common/"
  "page lines of lsans-15.fnt). Honest miss → null (caller throws its own exception). "
  + WALL,
  "run/c159/tower3d_fix12.log vs fix13.log (EXP071-READLINE real fnt lines)"),

 ("F-NEW-508", "CLASSIFIED", "P2",
  "tower3d app-level frontier: BitmapFontData.load parseInt('\\\\t') NFE. State after "
  "F-NEW-500..507: the engine-level death chain is fully cleared (compareTo collision "
  "→ copy-ctor overload → getComponentType/newInstance → GLSL stubs → write-back → "
  "resource streams all fixed); the app now builds SpriteBatch + Mesh + GL buffers "
  "and reads the REAL lsans-15.fnt bytes (readLine delivers the true info/common/page "
  "lines; the common-line split returns the true 7 tokens). The remaining kill: "
  "Integer.parseInt receives a TAB token inside BitmapFontData.load (deferred NFE → "
  "the app's own catch-all wraps it → GdxRuntimeException → onCreate death). The "
  "tab-token provenance is unresolved: the file bytes contain ZERO tabs (od-verified) "
  "and both split layers answer the true tokens, so the token originates between the "
  "engine's array delivery and the app's parse walk (candidate: a second split-layer "
  "array-shape divergence or a pair-split element path). Next lever: pair-split "
  "(delim '=') element identity audit at the 63828 site with F235-style element-value "
  "tracing. Named lever, machine-reproducible: MINIANDROID_F235_DIAG=1 + "
  "EXP071-READLINE rows at binary " + BIN + ".",
  "run/c159/tower3d_fix13.log (SYNTH-EXC PARSE-BRIDGE; 3 readLine rows; F235 splits)"),
]

for fid, status, prio, ev, paths in NEW:
    roots.append({
        "id": fid,
        "title": fid + (" (CONT-159 tower3d decode wave: " +
                        ("libGDX-3D engine rescue, 8-law chain" if status != "CLASSIFIED"
                         else "honest frontier") + ")"),
        "status": status,
        "priority": prio,
        "layer": None,
        "evidence": ev + " || paths: " + paths,
    })

# id-uniqueness check
ids = [x.get("id") for x in roots]
assert len(ids) == len(set(ids)), "DUP IDS"

main = len(roots)
json.dump({"roots": roots} if not isinstance(r, list) else roots, open(REG, 'w'), indent=1, ensure_ascii=False)
print(f"registry {before} -> {main} (id-unique)")
