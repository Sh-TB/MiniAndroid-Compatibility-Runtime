#!/usr/bin/env python3
"""S188-W18 finalize: write W18_IMPLEMENTATION.json + W18_WAVE_REPORT.json
(the wave evidence ledger) into evidence/s188_w18/."""
import json, hashlib
from pathlib import Path

BASE = Path('/home/z/my-project')
E = BASE / 'evidence/s188_w18'
BIN = BASE / 'miniandroid/build/miniandroid'
sha = hashlib.sha256(BIN.read_bytes()).hexdigest()[:16]

impl = {
 "wave": "S188-W18",
 "title": "LIBGDX primitive-array critical family IMPLEMENTED — p9 advances "
          "four death-layers (Gdx2DPixmap.load -> charset -> FreeType face "
          "-> glyph atlas); halma advances two (I18NBundle name composition)",
 "binary_sha16": sha,
 "binary_note": "rebuilt from HEAD after the sandbox wiped build/; the "
                "W17 binary a485e9826b618c35 lineage is reproducible. The "
                "wave produced TEN engine laws (605-608d, 609, 611, 613).",
 "law": "CONTRACT PINNED BEFORE ANY SHIM (W8 law carried) — "
        "W18_GDX2DPIXMAP_CONTRACT.json was pinned (objdump call-face of the "
        "APK's own libgdx.so/libgdx-freetype.so + androguard DEX face) "
        "before any slot implementation; every further fix was root-caused "
        "through the same oracle chain before the edit.",
 "implemented_laws": {
  "F-NEW-605": "JNIEnv slots 222/223/229 — GetPrimitiveArrayCritical / "
   "ReleasePrimitiveArrayCritical (spec copy semantics, mode-0 commit, "
   "JNI_COMMIT/ABORT) + NewDirectByteBuffer box registry; the engine-side "
   "primitive_array/primitive_array_write hooks snapshot the DEX heap "
   "array[i] fields into REAL malloc memory and commit back with "
   "per-element memcmp skip (32MB honest bound).",
  "F-NEW-606": "ELEMENT-TYPE-FAMILY law — the snapshot read ONLY "
   "INT32/INT64/FLOAT32 while the engine's own producers (aput-byte/char/"
   "short/boolean, InputStream.read) store BYTE/CHAR/SHORT/BOOLEAN "
   "typed values: the 31435B icons.png snapshot arrived as ZEROS and the "
   "commit pass then WROTE ZEROS over the live PNG bytes (data "
   "destruction — the 'commit 31435/31435 changed' tell). Snapshot and "
   "commit now read/write the full family per element width; the commit "
   "writes the descriptor-canonical make_* form (no representation "
   "drift). Rejection paths print the array's identity (desc) honestly.",
  "F-NEW-607": "DESCRIPTOR-EXACT NATIVE SELECTION — the native-precedence "
   "scan matched by NAME only: Matrix4 declares BOTH the static native "
   "mul([F[F)V and the virtual bytecode wrapper mul(Matrix4)LMatrix4;; "
   "the name-only scan served the static native to the virtual call (two "
   "Matrix4 receivers marshalled as 'float[]' criticals -> slot-222 NULL "
   "-> guarded SIGSEGV -> NPE -> APP BOUNDARY). ART order restored: pass "
   "1 exact (name, descriptor)+ACC_NATIVE; pass 2 name-only ONLY when "
   "the exact method does not exist in the class at all (the W10 "
   "conscrypt law verbatim for descriptor-unknown dispatches).",
  "F-NEW-608": "String.toCharArray (STRING_REF + heap-String faces, AOSP "
   "value.clone semantics, make_char elements) + the Character statics "
   "on the same demand chain (isAlphabetic/isLetter/toUpperCase/"
   "toLowerCase — ASCII + byte-char law, the honest boundary recorded). "
   "Live face: AssetLoaderService.createCharset died on array-length of "
   "the unbridged toCharArray result (ARR-LEN-NULL).",
  "F-NEW-608b": "String.getChars(I I [C I) both faces — AOSP bounds law "
   "(StringIndexOutOfBounds for the src range, IndexOutOfBounds for dst "
   "overflow). Live face: the I18NBundle name composition emptied every "
   "bundle name (StringBuilder.append0 -> getChars stub).",
  "F-NEW-608c": "String<-char[] materialization (new String([C) and the "
   "( [C I I) window form with the AOSP bounds law). Live face: libgdx's "
   "own StringBuilder.toString() minted UNMATERIALIZED strings — every "
   "composed bundle name degraded to \"\".",
  "F-NEW-608d": "STRING-ARG DUAL-FACE read law — a String argument "
   "arrives as inline STRING_REF or a MATERIALIZED heap String "
   "(__string_value__/value/sb_value); the File-ctor and String.replace "
   "laws read the CHARACTER CONTENT regardless of representation. Live "
   "faces: the freshly-minted 'strings_en_US.properties' degraded to \"\" "
   "inside File.<init>(String,String) and inside "
   "AndroidFileHandle.sibling's name.replace('\\\\','/').",
  "F-NEW-609": "PERSISTENT DIRECT-BUFFER BACKING — GetDirectBufferAddress "
   "snapshotted the DEX mirror into a FRESH malloc per call; a native "
   "that WRITES through the address (BufferUtils.copyJni streaming the "
   "126168B TTF) had its bytes erased by the next reader's snapshot "
   "(FreeType newMemoryFace read zeros -> face=0 -> GdxRuntimeException). "
   "JNI direct buffers are SHARED memory: the first Get mints the "
   "persistent backing, every later Get returns THE SAME pointer "
   "(documented boundary: DEX-side writes after the first Get are not "
   "re-snapshotted — the font/pixmap consumers are native-side only).",
  "F-NEW-611": "JNI NAME MANGLING law — mangle_escape passed every "
   "printable byte through; '$' (U+0024) survived raw while the .so "
   "exports the ART-faithful _00024 form. dlsym missed EVERY inner-class "
   "native (the whole FreeType Library/Face/Bitmap/Glyph family). One "
   "rule: every char outside [A-Za-z0-9_] carries _0xxxx; / ; [ keep "
   "their table entries.",
  "F-NEW-613": "DEX-HIERARCHY SHADOW-CLAIM GATE — the ViewShadow EXP-060 "
   "catch-all claims every class outside the known framework prefixes "
   "('could be a View subclass') and its dispatch answers View-geometry "
   "getters (getHeight/getWidth) with typed 0. libgdx's "
   "FreeType$GlyphMetrics.getHeight(J)I — a REAL ACC_NATIVE — was "
   "shadowed to 0 before the real-symbol attempt (x-height stayed 0 -> "
   "'No x-height character found in font' -> APP BOUNDARY) while "
   "getHoriAdvance (not a View getter) ran REAL. Gate: a shadow-"
   "IMPLEMENTED answer on a DEX-present native class is authoritative "
   "only when the declared superclass chain reaches an Landroid/ "
   "ancestor; otherwise the claim is demoted to the FIX-TTT fault-"
   "fallback and the real symbol runs (the tower3d faulting-allocator "
   "observable unchanged)."
 },
 "chain_advance": {
  "p9": {
   "before_w18": "Gdx2DPixmap.load faults under the JNI subset "
    "([MINIANDROID-JNI] UNSUPPORTED JNIEnv slot 222 -> guarded SIGSEGV -> "
    "IOException 'Error loading pixmap') — the W17 frontier.",
   "after_w18": "checkGL20 PASSES -> GLSurfaceView20 wired -> SpriteBatch/"
    "ShaderProgram/Mesh -> REAL asset streaming -> Matrix4.mul/inv/prj run "
    "REAL math on REAL critical copies (commit 2/16, 15/16 changed "
    "elements) -> Gdx2DPixmap.load REAL (gdx2d_load decoded the PNG, "
    "NewDirectByteBuffer minted, pdata[0..3] writeback committed) -> "
    "createCharset prints the app's OWN 'Language charset ENFRDESV' -> "
    "FreeType REAL (FT_Init_FreeType library pointer, FT_New_Memory_Face "
    "face pointer, FT_Set_Pixel_Sizes, real glyph metrics: HoriAdvance=1280, "
    "SizeMetrics.getAscender=5376/getDescender=-1408, "
    "GlyphMetrics.getHeight=4160) -> fonts generated -> glyph atlas "
    "getPixmap -> newPixmap(w=0,h=0).",
   "new_frontier": "FT_Glyph_To_Bitmap's output FT_Bitmap is EMPTY "
    "(rows=0/width=0/pitch=0 with pixel_mode=GRAY — the runtime memory "
    "hexdump pinned it) -> Bitmap.getWidth/getRows read 0 -> "
    "newPixmap(0,0,4) -> gdx2d_new fails -> Gdx2DPixmap.<init> "
    "'Error loading pixmap' -> APP BOUNDARY. W19 = the FT bitmap-render "
    "leg (why the raster left the struct empty)."
  },
  "halma": {
   "before_w18": "I18NBundle MissingResourceException 'Can't find bundle "
    "for base file handle strings, locale en_US' — the W17 frontier.",
   "after_w18": "the bundle names compose for real ('strings.properties', "
    "'strings_en_US.properties' — getChars + String(char[]) + the "
    "dual-face reads) and the properties FILE READS (PropertiesUtils.load "
    "runs).",
   "new_frontier": "PropertiesUtils.load pc=335: "
    "StringIndexOutOfBoundsException 'length=0; begin=0; end=10' — a "
    "line-parse window on an empty line string — W19 = the properties "
    "line-parse leg (the stream/reader content face)."
  }
 },
 "determinism": "p9 3/3 and halma 3/3 independent runs: same chain "
  "markers each run (charset print, 7 real direct-ByteBuffer returns, 0 "
  "guarded faults, FRAME_ANALYSIS REAL_APP_CONTENT x2), ROUTE_VIOLATION=0, "
  "uncaught=0 (compatibility-continue honesty law).",
 "regression_gates": {
  "goldens": "bouncy 8a6c24ac / unote 3b8dcb0a / dooz 31ddd4d5 — ALL HOLD "
   "byte-exact on 1f05270d793a43b5, uncaught=0 (dooz 6 = the recorded "
   "dooz-native count).",
  "floor_11": "FLOOR CLEAN 11/11 — every W12/W13 recorded tier holds "
   "tier-exact (floor_rerun/FLOOR_RERUN.json)."
 },
 "promotion_law": "p9/halma REMAIN stage6/NOISE faces (no tier promotion "
  "claimed) — the CHAIN advanced, the FACE did not (the honest-gate law: "
  "the app still dies inside onCreate before presenting UI).",
 "evidence_files": [
  "evidence/s188_w18/W18_GDX2DPIXMAP_CONTRACT.json (the pinned contract)",
  "evidence/s188_w18/W18_JNI_DEMAND_AUDIT.json",
  "evidence/s188_w18/W18_IMPLEMENTATION.json",
  "evidence/s188_w18/W18_RUNS.json (p9 x3 + halma x3 chain markers)",
  "evidence/s188_w18/W18_GOLDENS.json",
  "evidence/s188_w18/floor_rerun/FLOOR_RERUN.json",
  "evidence/s188_w18/p9_w18_r{1,2,3}.console.log",
  "evidence/s188_w18/halma_w18_r{1,2,3}.console.log",
  "evidence/s188_w18/p9_w18ft*.console.log (the FT root-cause probes)",
  "evidence/s188_w18/face_*.jpg",
  "scripts/s188_w18_smoke.py, s188_w18_battery.py, s188_w18_floor_rerun.py,"
  " s188_w18_matrix4_face.py, s188_w18_charset_face.py,"
  " s188_w18_ft_probe.py"
 ]
}
(E / 'W18_IMPLEMENTATION.json').write_text(json.dumps(impl, indent=1))

report = {
 "wave": "S188-W18",
 "verdict": "The pinned primitive-array critical family is IMPLEMENTED and "
  "the LIBGDX EGL-family apps advanced through FOUR additional death-"
  "layers (p9) and TWO (halma) with the fleet's regression floor clean.",
 "binary": sha,
 "laws_count": 10,
 "keys": [
  "F-NEW-605 primitive-array critical family (slots 222/223/229) — the "
  "W18 pinned contract, implemented after the pin",
  "F-NEW-606 element-type family (data-destruction face caught + fixed)",
  "F-NEW-607 descriptor-exact native selection (Matrix4 overload face)",
  "F-NEW-608/608b/608c/608d the String char-chain family (toCharArray / "
  "getChars / String(char[]) / dual-face reads)",
  "F-NEW-609 persistent direct-buffer backing (the copyJni->FT face)",
  "F-NEW-611 JNI $ mangling (the inner-class native family unlock)",
  "F-NEW-613 the DEX-hierarchy shadow-claim gate (the ViewShadow "
  "heuristic vs the real-native precedence)"
 ],
 "next": [
  "W19a — p9: FT_Glyph_To_Bitmap empty-render leg (the FT_Bitmap struct "
  "dump is the pinned evidence: rows/width/pitch zeroed with pixel_mode "
  "GRAY); the getLastErrorCode bss read is the first oracle.",
  "W19b — halma: PropertiesUtils.load line-parse face (the "
  "'length=0; begin=0; end=10' window).",
  "Standing: tarok FOREIGN_ARCH_ONLY_ABI (arch-bound, closed); W8 Dart VM "
  "double-thread stall (untouched)."
 ]
}
(E / 'W18_WAVE_REPORT.json').write_text(json.dumps(report, indent=1))
print('W18_IMPLEMENTATION.json + W18_WAVE_REPORT.json written; binary', sha)
