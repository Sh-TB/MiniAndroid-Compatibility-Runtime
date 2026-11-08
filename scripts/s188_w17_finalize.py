#!/usr/bin/env python3
"""S188-W17 finalize: the EGL Java-surface family contract IMPLEMENTED
(W16 pinned it; the W8 law said implement after pinning). Writes the
wave evidence JSON and appends the worklog entry.
"""
import json, hashlib
from pathlib import Path
from datetime import datetime, timezone

BASE = Path('/home/z/my-project')
W17 = BASE / 'evidence/s188_w17'
BIN = BASE / 'miniandroid/build/miniandroid'


def sha16(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()[:16]


report = {
    'wave': 'S188-W17',
    'title': 'LIBGDX EGL family contract IMPLEMENTED — p9 advances three '
             'death-layers (EGL gate -> GL20 stream -> asset pipeline -> '
             'Gdx2DPixmap.load native fault)',
    'binary_sha16': sha16(BIN),
    'binary_note': 'the sandbox wiped build/ between waves; the W15-final '
                   'binary was FIRST reproduced byte-exact from HEAD source '
                   '(50400036a6f16fe8) before any edit — the lineage is '
                   'reproducible. W17 binary = a485e9826b618c35.',
    'laws_landed': [
        {'id': 'F-NEW-601', 'name': 'interface->native exact dispatch',
         'file': 'dalvik_engine.cpp f281c walk',
         'law': 'an ACC_NATIVE method has code_offset==0 and is NOT '
                'abstract — it is a real dispatch target. The f281c_exact '
                'walk now counts natives, so invoke-interface resolves '
                'against the receiver runtime class (ART law) and reaches '
                'the native block.'},
        {'id': 'F-NEW-602', 'name': 'guest->host GL driver routing',
         'file': 'dalvik_engine.cpp native block (try_recursive_invoke)',
         'law': 'the libGDX JNI GL wrappers (AndroidGL20 family) route to '
                'the engine GLES20 driver surface (dispatch_gles20_static, '
                'F-NEW-505 GLSL ledger) BEFORE the real-symbol attempt — '
                'Anbox/emugl guest->host law; NOT a fail-soft stub (on '
                'miss: pre-W17 order preserved; F-C4-594 untouched).'},
        {'id': 'F-NEW-603', 'name': 'EGL Java-surface static routing',
         'file': 'dalvik_engine.cpp bridge_to_api entry',
         'law': 'EGL statics take execute_invoke_static -> try_recursive_'
                'invoke miss -> bridge_to_api, which never consulted the '
                'shadow registry; the khronos/egl + EGL14/EGLExt family now '
                'routes to GLSurfaceViewShadow.dispatch_egl at bridge '
                'entry. Instance EGL calls were already served.'},
        {'id': 'F-NEW-604', 'name': 'EGL shadow body completion',
         'file': 'gl_surface_shadow.cpp dispatch_egl_body',
         'law': 'eglGetCurrentContext -> EGLContext object; getGL -> GL10 '
                'object; eglGetConfigAttrib -> honest PGL software-config '
                'values written into the int[] holder; eglChooseConfig -> '
                'fills configs[0] AND writes 1 into the TRAILING int[] '
                'count holder (bytecode-proven gate: checkGL20 returns '
                'numConfigs[0] > 0).'},
    ],
    'p9_chain_advance': {
        'before_w17': 'checkGL20 EGL answers = typed-default stubs -> '
                      'createGLSurfaceView threw GdxRuntimeException '
                      '"Libgdx requires OpenGL ES 2.0" (bytecode-proven '
                      'gate: checkGL20()Z returns numConfigs[0] > 0)',
        'after_w17': 'checkGL20 PASSES; GLSurfaceView20 wired; SpriteBatch '
                     '+ ShaderProgram + Mesh class-init; REAL asset '
                     'pipeline (2/icons.png 31435B streamed via '
                     'ASSET-FD/STREAM-READ); Texture/Pixmap chain runs; '
                     'FRAME_ANALYSIS state=REAL_APP_CONTENT rf=OPENGL_GLES '
                     'x3 independent runs',
        'new_frontier': 'Gdx2DPixmap.load (ACC_NATIVE, libgdx.so) faults '
                        'under the engine JNI subset: [MINIANDROID-JNI] '
                        'UNSUPPORTED JNIEnv slot 222 -> guarded SIGSEGV '
                        '(FIX-TTT survived) -> getFailureReason null -> '
                        'IOException "Error loading pixmap: null" -> '
                        'GdxRuntimeException -> APP BOUNDARY unwind. The '
                        'GL frame is produced but contains uninitialized '
                        'noise (center-64x64 = 4092 colors -> NOISE_NOT_UI '
                        'honesty gate; the app never presented UI).',
    },
    'halma_advance': {
        'note': 'same family laws; halma now reaches I18NBundle '
                'createBundleImpl -> MissingResourceException "strings, '
                'locale en_US" (deeper than W15: no visual change — face '
                'noise->noise, honesty gate unchanged)',
    },
    'regression_gates': {
        'goldens': 'bouncy 8a6c24ac / unote 3b8dcb0a / dooz 31ddd4d5 ALL '
                   'HOLD byte-exact on a485e9826b618c35, uncaught=0',
        'floor_11': 'FLOOR CLEAN 11/11 — every W12/W13 recorded tier holds '
                    'tier-exact (floor_rerun/FLOOR_RERUN.json)',
        'libgdx_spots': 'blichess FLAT=FLAT, boxcars FLAT=FLAT, halma '
                        'noise=noise (center 1228->732, verdict unchanged)',
        'determinism': 'p9 3/3 independent runs REAL_APP_CONTENT, 8 '
                       'pipeline markers each',
    },
    'next_blockers': [
        'Gdx2DPixmap.load: engine-side pixmap ledger (decode via the '
        'runtime PNG pipeline + minted long-ptr record + '
        'getWidth/getHeight/getFormat/getPixelPtr family) — the W18 '
        'draw-contract step',
        'JNIEnv slot 222 (NewDirectByteBuffer family) — the JNI subset '
        'gap the real native hit before faulting',
        'halma I18NBundle: locale properties FileHandle resolution',
    ],
    'evidence_files': [
        'evidence/s188_w17/p9_w17b.console.log',
        'evidence/s188_w17/p9r1.log', 'evidence/s188_w17/p9r2.log',
        'evidence/s188_w17/p9r3.log',
        'evidence/s188_w17/p9_w17b_frame.png',
        'evidence/s188_w17/face_se.tube42.p9.android.jpg',
        'evidence/s188_w17/face_app.halma.jpg',
        'evidence/s188_w17/floor_rerun/FLOOR_RERUN.json',
        'evidence/s188_w17/W17_GOLDENS.json',
    ],
}
(W17 / 'W17_EGL_IMPLEMENTATION.json').write_text(json.dumps(report, indent=1))

# goldens as evidence
import subprocess
r = subprocess.run(['python3', 'scripts/s188_golden_check.py'],
                   capture_output=True, text=True, cwd=str(BASE), timeout=420)
rows = [json.loads(l) for l in r.stdout.splitlines() if l.strip().startswith('{')]
(W17 / 'W17_GOLDENS.json').write_text(json.dumps(rows, indent=1))

wl = BASE / 'worklog.md'
entry = f"""
## S188-W17 — LIBGDX EGL FAMILY CONTRACT IMPLEMENTED ({datetime.now(timezone.utc).date()})

Directive: "ادامه" — the W16-pinned EGL family contract implemented
after the pin (W8 law satisfied: contract first, then code). Binary:
rebuilt twice — first the byte-exact W15 reproduction (50400036a6f16fe8,
proving the lineage reproducible after the sandbox wiped build/), then
the W17 binary a485e9826b618c35 with four laws:

- F-NEW-601 interface->native exact dispatch: the f281c_exact walk
  skipped code_offset==0 methods — which excluded every ACC_NATIVE
  method from interface resolution (GL20.glCreateShader on the
  AndroidGL20 receiver never reached the native block → S186I-STUB
  answered 0 → ShaderProgram isCompiled=false → IllegalArgumentException
  → APP BOUNDARY unwind before the first frame). Natives are now exact
  hits (ART art_method law).
- F-NEW-602 guest→host GL driver routing: the libGDX JNI GL wrapper
  family (AndroidGL20 et al.) routes ACC_NATIVE gl* calls to the engine
  GLES20 driver surface (F-NEW-505 GLSL ledger) BEFORE the real-symbol
  attempt — Anbox/emugl law; the exported-symbol surface is the same
  driver minus GLSL (portablegl.h has no compiler); NOT a fail-soft
  stub — pre-W17 order fully preserved on a miss.
- F-NEW-603 EGL static routing: execute_invoke_static → bridge_to_api
  never consulted the shadow registry; the khronos/egl + EGL14/EGLExt
  family routes to GLSurfaceViewShadow.dispatch_egl at bridge entry.
- F-NEW-604 EGL shadow body completion: eglGetCurrentContext/getGL/
  eglGetConfigAttrib (honest PGL software config) + the eglChooseConfig
  count-holder law — androguard bytecode of p9's checkGL20 proved the
  gate is `numConfigs[0] > 0`; the old body wrote the config into the
  DISPLAY object and never touched the count.

RESULT (p9, 3 independent runs): checkGL20 PASSES (the
"Libgdx requires OpenGL ES 2.0" death is gone), GLSurfaceView20 wired,
SpriteBatch/ShaderProgram/Mesh init, REAL asset streaming
(2/icons.png 31435B via ASSET-FD/STREAM-READ), Texture/Pixmap chain,
FRAME_ANALYSIS state=REAL_APP_CONTENT rf=OPENGL_GLES x3. New frontier:
Gdx2DPixmap.load faults under the JNI subset ([MINIANDROID-JNI]
UNSUPPORTED JNIEnv slot 222 → guarded SIGSEGV (FIX-TTT) → IOException
"Error loading pixmap: null" → GdxRuntimeException → APP BOUNDARY
unwind). Face noise (center 4092 → NOISE_NOT_UI honesty gate; the app
never presented UI — honest). halma: deeper chain (I18NBundle
MissingResourceException "strings en_US"), face noise→noise unchanged.

REGRESSION GATES on a485e9826b618c35: goldens 3/3 byte-exact
(bouncy 8a6c24ac, unote 3b8dcb0a, dooz 31ddd4d5, uncaught=0);
floor rerun 11/11 tier-exact (FLOOR CLEAN); blichess/boxcars FLAT hold,
halma verdict unchanged. Promotion law respected: p9/halma remain
stage6/NOISE (no tier promotion claimed) — the CHAIN advanced, the
FACE did not.

NEXT: W18 = Gdx2DPixmap engine-side pixmap ledger (runtime PNG decode +
minted long-ptr record + the getWidth/getHeight/getFormat/getPixelPtr
family) + JNIEnv slot 222; halma I18NBundle locale-file law.
Evidence: evidence/s188_w17/{{W17_EGL_IMPLEMENTATION.json,
W17_GOLDENS.json, p9_w17b.console.log, p9r1..3.log, faces,
floor_rerun/FLOOR_RERUN.json}}; scripts/s188_w17_floor_rerun.py.
"""
with open(wl, 'a') as f:
    f.write(entry)
print('W17 finalized; goldens rows:', len(rows))
