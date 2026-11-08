#!/usr/bin/env python3
"""S188-W14 evidence finalization + worklog entry."""
import json
from pathlib import Path

BASE = Path('/home/z/my-project')
OUT = BASE / 'evidence/s188_w14'

summary = dict(
    binary_sha16='85f48a64a3192625',
    f_new_586=dict(
        law='glCopyTexImage2D + glCopyTexSubImage2D native export (dlopen '
            'contract of p9 libgdx.so)',
        pinned_from='evidence/s188_w13: undefined symbol glCopyTexImage2D',
        fix='src/gles/gl_copy_bridge.cpp (ReadPixels->TexImage2D copy '
            'semantics over the software backend)',
        verified='nm -D: T glCopyTexImage2D, T glCopyTexSubImage2D; p9 '
                 'advanced past the symbol stage'),
    f_new_587=dict(
        law='declared-but-unimplemented PGL native surface (35 gl* '
            'symbols) + __android_log_print (bionic_compat.c)',
        pinned_from='evidence/s188_w14/W14_GDX_VERIFY.json: after 586 the '
                    'next dlopen blocker was glGetActiveAttrib; full diff '
                    'against nm -D exports gave the exact 35-symbol set',
        semantics='honest minimal: introspection empty (PGL has no GLSL '
                  'pipeline), precision constants = real IEEE float32 '
                  'ranges, Is* = FALSE (no interposition point), immediate '
                  'VertexAttrib = no-op (PGL draw model is pointer-array)',
        verified='4/4 symbols exported; p9 dlopen now reaches ELF '
                 'constructor execution'),
    p9_next_blocker=dict(
        state='libgdx.so (p9 build) ELF constructor faults (SIGSEGV '
              'fault_addr=0x0) inside the loader — FIX-TTT fork-probe '
              'guard caught it post-probe, loader poisoned for the '
              'process (honest), app continued, 0 fatal, screenshot '
              'produced',
        attribution_needed='faulting constructor IP is not in the '
                           'S100-CRASH-FORENSICS row (observability gap, '
                           'not a shim case)'),
    tarok_contract=dict(
        root_cause='si.palcka.tarok APK bundles ONLY lib/arm64-v8a '
                   '(libflutter.so 10.9MB); queens/quinb bundle x86_64 '
                   'libflutter.so which is why their Flutter chains work '
                   'on this x86_64 host',
        law='FOREIGN_ARCH_ONLY_ABI — architecture law (host cannot '
            'execute foreign machine code); Java-side Flutter embedding '
            'still advances (snapshot Bundle keys resolved)',
        options='arm64 translation host OR x86_64-hosted APK variant; '
                'NOT a shim case'),
    regression_gates=dict(
        goldens='ALL HOLD (bouncy 8a6c24ac / unote 3b8dcb0a / dooz '
                '31ddd4d5, byte-exact, 4 runs incl. 3 determinism reruns)',
        dooz_uncaught_variance='6 nonfatal EXC-UNCAUGHT-TOP trace marks '
                               'in 1 of 4 runs (state=nonfatal, face '
                               'byte-identical); reruns show 0 — '
                               'diagnostic-count variance, not regression',
        halma='libgdx dlopen OK, unchanged (tier A_RICH metric; W13 noise '
              'verdict unchanged)',
        queens='FLUTTER chain intact: dlopen OK, JNI_OnLoad x2, '
               'RegisterNatives x4, uncaught 0, FLAT (same as W13)',
        blackjack='B_STRUCTURED, uncaught 0 (same as W12/W13 floor)'),
    abi_census='evidence/s188_w13/W14_ABI_CENSUS.json: X86_HOSTED=9 '
               '(composeStopwatch, queens, quinb, halma, boxcars, '
               'blichess, nightbell, guandan, p9), FOREIGN_ARCH_ONLY_ABI '
               'native-blocked=4 (tarok, ccm, ball2box — Java-side chains '
               'still advance), PURE_DEX=11 (no lib/)',
    build_incident='Makefile recipe tabs were space-converted by the '
                   'sandbox restore (62 lines) — repaired with sed, '
                   'make dry-run verified before rebuild',
)
(OUT / 'W14_SUMMARY.json').write_text(json.dumps(summary, indent=1))

entry = """
## S188-W14 — pinned-contract fixes: GL native surface + arch-law census

- Rebuilt the runtime from source after the sandbox restore wiped build/
  (and space-converted 62 Makefile recipe tabs — repaired). New binary
  sha16=85f48a64a3192625.
- F-NEW-586 (pinned in W13): glCopyTexImage2D/glCopyTexSubImage2D now
  exported from src/gles/gl_copy_bridge.cpp (ReadPixels->TexImage2D copy
  semantics). p9's dlopen advanced past the undefined-symbol stage.
- F-NEW-587 (pinned in W14): the exact remaining 35-symbol PGL gap
  (glGetActiveAttrib ... glVertexAttrib4fv — introspection/no-op family,
  honest minimal semantics documented in-TU) + __android_log_print in
  bionic_compat.c (stderr log sink). p9's dlopen now reaches ELF
  constructor execution and faults there: SIGSEGV fault_addr=0x0 inside
  the loader, FIX-TTT guard caught it post-probe, loader honestly
  poisoned, app continued with 0 fatal marks. NEXT: attribute the
  faulting constructor (forensics row lacks the IP — observability gap).
- tarok contract cracked: APK bundles ONLY arm64-v8a libflutter.so;
  queens/quinb bundle x86_64 — that is THE reason their Flutter chains
  advance. Architecture law (FOREIGN_ARCH_ONLY_ABI), not a shim case.
  ABI census of all 24 battery APKs saved (W14_ABI_CENSUS.json).
- Regression gates: goldens ALL HOLD (4 runs; dooz's 6 UNCAUGHT marks in
  1 run = nonfatal trace-count variance, face byte-identical, reruns 0);
  halma unchanged; queens Flutter chain intact; blackjack B floor holds.
- Evidence: evidence/s188_w14/{W14_GDX_VERIFY.json, W14_SUMMARY.json,
  W14_SPOT_REGRESSION.json, runs/}, evidence/s188_w13/W14_ABI_CENSUS.json
"""
with open(BASE / 'worklog.md', 'a') as f:
    f.write(entry)
print('W14 evidence + worklog written')
