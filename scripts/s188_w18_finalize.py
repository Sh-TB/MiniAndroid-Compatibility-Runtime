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
                "wave produced TEN engine laws (605-608d, 609, 611, 613). "
                "POST-WAVE RE-VERIFICATION: the sandbox wiped build/ AND "
                "dropped the wave's *.console.log files; the binary was "
                "rebuilt from HEAD AGAIN — byte-exact 1f05270d793a43b5 "
                "(reproducible-build law) — and the FULL gate battery was "
                "re-run on the rebuilt binary (battery p9x3+halmax3, "
                "goldens x3, floor 11 titles) with identical results; "
                "console logs restored. Determinism now 6 independent runs "
                "per app (3 original + 3 re-verification). The FT-probe "
                "console logs were unrecoverable; the 14 probe run dirs "
                "(runs/p9_w18ft*) with report.md/screenshot.png survive.",
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
  "uncaught=0 (compatibility-continue honesty law). RE-VERIFIED x3 more "
  "per app on the rebuilt byte-exact binary — 6/6 runs marker-identical.",
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
  "evidence/s188_w18/W18_RUNS.json (p9 x3 + halma x3 chain markers, "
  "re-run x3 on the rebuilt binary)",
  "evidence/s188_w18/W18_GOLDENS.json (ALL HOLD on the rebuilt binary)",
  "evidence/s188_w18/floor_rerun/FLOOR_RERUN.json (FLOOR CLEAN 11/11, "
  "dynamic-sha record on 1f05270d793a43b5)",
  "evidence/s188_w18/p9_w18_r{1,2,3}.console.log",
  "evidence/s188_w18/halma_w18_r{1,2,3}.console.log",
  "evidence/s188_w18/runs/p9_w18ft* (the 14 FT root-cause probe runs: "
  "report.md + screenshot.png; their console logs were lost in the "
  "sandbox restore)",
  "evidence/s188_w18/face_*.jpg",
  "scripts/s188_w18_smoke.py, s188_w18_battery.py, s188_w18_floor_rerun.py,"
  " s188_w18_matrix4_face.py, s188_w18_charset_face.py,"
  " s188_w18_ft_probe.py, s188_w18_finalize.py"
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

# ── worklog entry (the W17 finalize pattern) ────────────────────────────
from datetime import datetime, timezone
wl = BASE / 'worklog.md'
entry = f"""
## S188-W18 — LIBGDX PRIMITIVE-ARRAY CRITICAL FAMILY IMPLEMENTED
({datetime.now(timezone.utc).date()}; finalize completed post-wave after
the sandbox wiped build/ and the wave's console logs)

Directive: "ادامه" — the W17 frontier family implemented after the pin
(W18_GDX2DPIXMAP_CONTRACT.json, pinned before any shim — W8 law
carried). Binary 1f05270d793a43b5, TEN engine laws:

- F-NEW-605 JNIEnv slots 222/223/229 GetPrimitiveArrayCritical/
  ReleasePrimitiveArrayCritical + NewDirectByteBuffer box registry —
  the pinned contract itself (spec copy semantics, mode-0 commit,
  JNI_COMMIT/ABORT, engine-side snapshot hooks, 32MB honest bound).
- F-NEW-606 ELEMENT-TYPE-FAMILY law: the snapshot read only
  INT32/INT64/FLOAT32 while the engine's own producers store
  BYTE/CHAR/SHORT/BOOLEAN — the 31435B icons.png arrived as ZEROS and
  the commit WROTE ZEROS over the live PNG (data destruction, the
  "commit 31435/31435 changed" tell). Full family per element width.
- F-NEW-607 DESCRIPTOR-EXACT NATIVE SELECTION: the name-only scan
  served Matrix4's static native mul([F[F)V to the virtual
  mul(Matrix4) call (two receivers as 'float[]' criticals -> slot-222
  NULL -> guarded SIGSEGV). ART order restored: exact (name,
  descriptor)+ACC_NATIVE pass 1; name-only ONLY when the exact method
  does not exist at all (the W10 conscrypt law verbatim).
- F-NEW-608/608b/608c/608d the String char-chain family:
  toCharArray (value.clone, make_char), getChars (AOSP bounds law),
  String<-char[] materialization (both ctors), STRING-ARG DUAL-FACE
  read law (inline STRING_REF vs MATERIALIZED heap String — the
  File-ctor and name.replace faces).
- F-NEW-609 PERSISTENT DIRECT-BUFFER BACKING: GetDirectBufferAddress
  re-snapshotted per call, erasing BufferUtils.copyJni's streamed TTF
  bytes before FT_New_Memory_Face read them (face=0). First Get mints
  the persistent backing; every later Get returns THE SAME pointer
  (documented boundary: DEX-side writes after the first Get are not
  re-snapshotted).
- F-NEW-611 JNI NAME MANGLING: '$' survived raw while the .so exports
  the ART-faithful _00024 form — dlsym missed EVERY inner-class native
  (the whole FreeType Library/Face/Bitmap/Glyph family). One rule:
  every char outside [A-Za-z0-9_] carries _0xxxx.
- F-NEW-613 DEX-HIERARCHY SHADOW-CLAIM GATE: the ViewShadow EXP-060
  catch-all shadowed libgdx's REAL ACC_NATIVE FreeType$GlyphMetrics
  .getHeight(J)I to typed-0 (x-height 0 -> "No x-height character
  found in font"). A shadow-IMPLEMENTED answer on a DEX-present native
  class is authoritative only when the declared superclass chain
  reaches an Landroid/ ancestor; otherwise demoted to FIX-TTT fault-
  fallback and the real symbol runs.

RESULT: p9 advanced FOUR death-layers — checkGL20 -> GLSurfaceView20
-> SpriteBatch/ShaderProgram/Mesh -> REAL asset streaming -> Matrix4
REAL critical math (commit 2/16, 15/16 changed) -> Gdx2DPixmap.load
REAL (PNG decoded, NewDirectByteBuffer minted, pdata writeback
committed) -> createCharset prints the app's OWN "Language charset
ENFRDESV" -> FreeType REAL (FT_Init_FreeType, FT_New_Memory_Face,
FT_Set_Pixel_Sizes, real glyph metrics HoriAdvance=1280,
SizeMetrics ascender=5376/descender=-1408, GlyphMetrics.getHeight=4160)
-> fonts -> glyph atlas getPixmap -> newPixmap(w=0,h=0). NEW FRONTIER:
FT_Glyph_To_Bitmap's output FT_Bitmap is EMPTY (rows/width/pitch=0,
pixel_mode=GRAY — memory-hexdump pinned) -> W19a = the FT bitmap-render
leg. halma advanced TWO — bundle names compose for real
(getChars + String(char[]) + dual-face reads) and PropertiesUtils.load
RUNS; NEW FRONTIER: pc=335 StringIndexOutOfBounds 'length=0; begin=0;
end=10' (empty-line window) -> W19b = the properties line-parse leg.

GATES (all re-verified post-wipe on the REBUILT byte-exact binary):
goldens 3/3 ALL HOLD (bouncy 8a6c24ac, unote 3b8dcb0a, dooz 31ddd4d5,
uncaught 0/0/6 = recorded counts); floor 11/11 tier-exact FLOOR CLEAN
(dynamic-sha record); battery 6/6 marker-identical runs; ROUTE_VIOLATION=0
everywhere. Promotion law respected: p9/halma REMAIN stage6/NOISE —
the CHAIN advanced, the FACE did not (honesty gate).

NEXT: W19a p9 FT_Glyph_To_Bitmap empty-render leg (getLastErrorCode
bss read is the first oracle); W19b halma PropertiesUtils.load
line-parse face. Standing: tarok FOREIGN_ARCH_ONLY_ABI (arch-bound,
closed); W8 Dart VM double-thread stall (untouched).
Evidence: evidence/s188_w18/{{W18_GDX2DPIXMAP_CONTRACT.json,
W18_JNI_DEMAND_AUDIT.json, W18_IMPLEMENTATION.json, W18_RUNS.json,
W18_GOLDENS.json, floor_rerun/FLOOR_RERUN.json, p9/halma console logs,
runs/ incl. 14 FT probe dirs}}; scripts/s188_w18_*.py.
"""
with open(wl, 'a') as f:
    f.write(entry)
print('W18_IMPLEMENTATION.json + W18_WAVE_REPORT.json + worklog written;'
      ' binary', sha)
