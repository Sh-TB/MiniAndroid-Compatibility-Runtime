#!/usr/bin/env python3
"""S188-W13: append chain-attribution (next_blocker) findings to the
loading-progress record + worklog entry. Evidence: the three titles with
the most informative loading chains on this battery."""
import json
from pathlib import Path

BASE = Path('/home/z/my-project')
OUT = BASE / 'evidence/s188_w13'
P = OUT / 'W13_LOADING_PROGRESS.json'
d = json.loads(P.read_text())

blockers = {
    'si.palcka.tarok': dict(
        route='FLUTTER',
        chain_advanced=[
            'Dart VM snapshot Bundle keys resolved '
            '(F0.e.vm-snapshot-data / F0.e.isolate-snapshot-data, has_obj=1)',
            'FlutterJNI.loadLibrary executed (pc=67)',
            'libflutter.so extracted (size=10942424, sha16=868783f8cd16acf4)'],
        next_blocker='dlopen of the extracted libflutter.so fails: the '
                     'virtual extraction path '
                     '/data/app/si.palcka.tarok/lib/arm64-v8a/libflutter.so '
                     'maps to the store path but the file is not dlopen-able '
                     'there (cannot open shared object file); second attempt '
                     'app_lib also absent. MISSING CONTRACT: extracted '
                     'native libs must physically exist + be dlopen-able at '
                     'the mapped codePath lib dir. No shim added until the '
                     'contract is pinned (W8 law).',
        state='PARTIAL_CHAIN'),
    'app.halma': dict(
        route='LIBGDX',
        chain_advanced=[
            'libgdx.so dlopen OK (size=193008, sha16=2e9dc948aab382e5, '
            'no JNI_OnLoad needed)',
            'GdxEglConfigChooser + GLSurfaceView20 class-init OK',
            'GL surface allocated -> rendered frame exists'],
        next_blocker='Surface content is uninitialized TV-snow noise '
                     '(visual-verdict gate demoted metric A_RICH to '
                     'NOISE_STATIC_SURFACE). MISSING CONTRACT: GL command '
                     'stream must actually draw (eglCreateContext -> draw '
                     'calls) before any visual-progress credit.',
        state='PARTIAL_CHAIN'),
    'se.tube42.p9.android': dict(
        route='LIBGDX',
        chain_advanced=[
            'SharedLibraryLoader.load executed (pc=27)',
            'libgdx.so extracted (size=338440, sha16=c8c6e37f9411517f)',
            'GLSurfaceView20 Java-side class-init OK'],
        next_blocker='dlopen fails: undefined symbol glCopyTexImage2D — '
                     'the runtime GLES symbol table lacks it. MISSING '
                     'CONTRACT (exact, actionable): export glCopyTexImage2D '
                     '(then audit the remaining libgdx.so undefined-symbol '
                     'list with androguard/elf tools).',
        state='PARTIAL_CHAIN'),
}
for row in d['titles']:
    if row['pkg'] in blockers:
        row.update(blockers[row['pkg']])
d['summary']['chain_findings'] = (
    'tarok=PARTIAL_CHAIN (flutter java embedding + snapshot keys OK; '
    'dlopen path contract missing), halma=PARTIAL_CHAIN (first libgdx.so '
    'native load OK; GL draw contract missing), p9=PARTIAL_CHAIN (exact '
    'GLES symbol gap: glCopyTexImage2D)')
P.write_text(json.dumps(d, indent=1))
print('progress JSON updated with chain findings')

# ── worklog append ──
wl = BASE / 'worklog.md'
entry = """
## S188-W13 — 24-title loading-progress battery (2026-11-07)

Directive: "test at least 20 apps and games, check loading progress."

- Battery: 24 titles (11 regression-floor + 13 fresh) on binary
  031ce03d54ff57b1. All 24 reached S6_SETTLED_FACE_TIERED.
- ROUTE_VIOLATION=0 across all 24; 0 regressions vs W12 floors.
- Goldens re-verified byte-exact before the battery: bouncy 8a6c24ac,
  unote 3b8dcb0a, dooz 31ddd4d5 — ALL HOLD.
- Effective tiers (visual-verdict gated): B_STRUCTURED=5, FLAT=17,
  NOISE_STATIC_SURFACE=2. New honesty gate: center-64x64 patch color
  count >=100 => NOISE_NOT_UI (caught 2 metric-A_RICH false positives:
  app.halma, se.tube42.p9.android — TV-snow, surface allocated, UI not
  drawn).
- Fresh title highlight: com.jeffliu.balancetheball renders real UI on
  FIRST run (instruction text + ball + "Tap to reset"), uncaught=0,
  B_STRUCTURED.
- Chain findings (next blockers, no shim until contract pinned):
  1. si.palcka.tarok (FLUTTER): snapshot Bundle keys resolved, JNI
     loadLibrary executed, libflutter.so extracted (10.9MB) but dlopen
     cannot open it at the mapped codePath path -> extraction-to-dlopen
     path contract missing.
  2. app.halma (LIBGDX): FIRST libgdx.so native load OK
     (sha16=2e9dc948aab382e5); GLSurfaceView20 init OK; GL draw contract
     missing (surface = noise).
  3. se.tube42.p9.android (LIBGDX): exact symbol gap — undefined symbol
     glCopyTexImage2D in libgdx.so dlopen.
- Data-integrity incident, resolved honestly: sandbox freeze/restore
  re-executed some run_one sequences mid-battery; in-memory fatal_marks
  were transient. All fields recomputed from current physical artifacts
  (logs+PNGs) in s188_w13_reconcile.py; apples-to-apples vs W12: quinb=1
  matches exactly, all other floor titles 0, frames-log fatal marks
  byte-identical to W12 frames logs (composeStopwatch 3x UEH, quinb 2x
  VM check) — deeper counting, not new behavior.
- Sandbox recycle killed the background battery once; incremental
  W13_BATTERY.partial.json made the resume lossless (4 titles re-run).
- Evidence: evidence/s188_w13/{W13_BATTERY.json, W13_LOADING_PROGRESS.json,
  W13_INTEGRITY_NOTE.json, battery.console.log, 24 face_*.jpg, runs/}
"""
with open(wl, 'a') as f:
    f.write(entry)
print('worklog updated')
