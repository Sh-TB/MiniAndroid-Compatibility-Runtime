#!/usr/bin/env python3
"""cont120_registry_update.py — CONT-120 registry wave (no inflation):
1. F-NEW-368 (PARTIAL): the five reflective rows landed UNCONDITIONAL in the
   default binary (memory F106-CTOR delivers in-frame; face 6da289aa
   reproduces CONT-71's F368-only activation byte-for-byte; 9/9 anchors zero
   drift — narrower than the CONT-71 full-pair activation, no opencalc
   divergence). Visual completion still pending F-NEW-374 MCM — stays PARTIAL.
2. F-NEW-449 (CONFIRMED_OPEN_GAP): W449 walk probe 3/3 PASS — walk ops
   verified engine-correct (count-token in-bounds, rotated-terminator
   reproduces the exact S36 signature, buffer 3-ints/field); divergence
   isolated to data construction (c3.<clinit>) — stays OPEN, root narrowed.
3. F-NEW-462 (ROOT-CAUSED-FIXED): facet-2 evidence — GLSurfaceView.getHolder
   holder-acquisition law landed (bouncy setFormat-null NPE closed,
   verified setFormat-null count=0; independent Set-add root remains open).
4. F-NEW-466 (NEW, root-caused-fixed): tictactoe SIGSEGV — the FIRST corpus
   process-death crash (CONT-118 W-06 / CONT-119 FIX-TTT decode) root-caused
   to libgdx.so faulting inside the host loader's dlopen (ELF constructors;
   fork-probe reproduced the fault; the tower3d libgdx.so of the same family
   loads clean = per-library defect). Fixed by the three-layer guarded-native
   law: fork dlopen probe → sigsetjmp fault guard around dlopen/JNI_OnLoad/
   symbol calls → loader-poison teardown law (_exit, no _dl_fini walk).
   Verified: rc 139→1, honest UnsatisfiedLinkError delivered into libGDX's
   own catch-all handler, 5 frames complete.
Sync: apply the same updates to root_registry.json (main) per the
CONT-111/117 sync-by-ID precedent; verify main==mirror, id-unique, count 781.
"""
import json
import sys

MIRROR = 'canonical/root_cause_registry.json'
MAIN = 'root_registry.json'


def load(path):
    with open(path) as f:
        reg = json.load(f)
    return reg, (reg['roots'] if isinstance(reg, dict) and 'roots' in reg
                 else reg)


def save(path, reg, roots):
    if isinstance(reg, dict) and 'roots' in reg:
        reg['roots'] = roots
        with open(path, 'w') as f:
            json.dump(reg, f, indent=1, ensure_ascii=False)
    else:
        with open(path, 'w') as f:
            json.dump(roots, f, indent=1, ensure_ascii=False)


UPDATES = {
    'F-NEW-368': {
        'status': 'PARTIAL',
        'title_append': (
            ' CONT-120 LANDED DEFAULT-ON (reflective subset): the five '
            'OpenJDK java.lang reflective rows (NoSuchMethodException/'
            'NoSuchFieldException/InstantiationException/IllegalAccessException/'
            'InvocationTargetException → ReflectiveOperationException) moved '
            'into the UNCONDITIONAL kBuiltinExcParent table — the memory app '
            'F106-CTOR NoSuchMethodException now delivers in-frame in the '
            'DEFAULT binary (deferred handler @0x53 type=Exception; the app '
            'own-log line "Default behavior class null could not be '
            'instantiated" proves the app catch RAN; F106-CTOR uncaught '
            'count 0, was ×24). Face 6da289aab14d2256 reproduces CONT-71\'s '
            'F368-only activation byte-for-byte across binary+container; '
            '9/9 wall anchors zero drift (narrower than the full-pair '
            'activation — opencalc does NOT diverge). Full visual '
            'completion still pending the F-NEW-374 MCM lever — PARTIAL '
            'stands honestly.'),
        'evidence_append': (
            ' run/c120/memory_fixed.log (delivery row + app own-log line + '
            'F106-CTOR uncaught=0); run/c120/memory_fixed/screenshot.png '
            'face 6da289aab14d2256 == the CONT-71 activation_f368only face; '
            'run/c120/battery.log 9/9 ANCHOR_MATCH.'),
    },
    'F-NEW-449': {
        'status': 'CONFIRMED_OPEN_GAP',
        'title_append': (
            ' CONT-120 ISOLATION PROBE (fixtures/cont120_fix449_walk, 3/3 '
            'PASS): walk ops verified ENGINE-CORRECT on a known-good '
            '10-string-field trio — count-token law in-bounds (count=11 '
            'consumed=11 entries=11 buffer=33), rotated-terminator law '
            'reproduces the EXACT S36 signature (AOOB length=11; index=11, '
            'caught by the fixture), buffer layout 3-ints-per-field holds. '
            'The live divergence is therefore isolated to the DATA '
            'construction upstream (c3.<clinit> info-string/entries build — '
            'the R337 rows); the bisect continues there with the probe as '
            'the isolation tool. Status stays OPEN honestly.'),
        'evidence_append': (
            ' run/c120/w449_out.log (W449- PASS ×3 + VERDICT '
            'WALK-OPS-OK divergence-isolated-to-data-construction); '
            'fixtures/cont120_fix449_walk/; run/c120/w449_probe.apk.'),
    },
    'F-NEW-462': {
        'status': 'ROOT-CAUSED-FIXED',
        'title_append': (
            ' CONT-120 FACET-2 LANDED: SurfaceView.getHolder holder-'
            'acquisition law reaches GLSurfaceView (AOSP GLSurfaceView '
            'extends SurfaceView) — one non-null holder per view, svHolder/'
            'svOwner back-link, same SurfaceHolder method law. bouncy '
            'GL20Renderer.<init> "SurfaceHolder.setFormat on a null object '
            'reference" NPE CLOSED (setFormat-null count 0, was the onCreate '
            'unwind at invoke_pc=148); the follow-up Set.add null root is '
            'now ISOLATED as independent (previously masked as a cascade of '
            'the GL unwind).'),
        'evidence_append': (
            ' run/c120/bouncy_fixed.log (setFormat-null=0; GL chain '
            'survives; Set-add null persists as an independent root); '
            'miniandroid/src/framework/gl_surface_shadow.cpp getHolder law.'),
    },
}

NEW_ROOT = {
    'id': 'F-NEW-466',
    'status': 'ROOT-CAUSED-FIXED',
    'priority': 'P1',
    'layer': 'jni/native-execution (host loader fault containment)',
    'title': (
        'Tictactoe SIGSEGV process-death (FIRST corpus rc=139, CONT-118 W-06 '
        '/ CONT-119 FIX-TTT decode) ROOT-CAUSED-FIXED CONT-120: libgdx.so '
        '(x86_64, 260696 bytes, sha16 553c8769776ff741) faults INSIDE the '
        'host loader dlopen (ELF constructor path; fork-probe reproduces '
        'the SIGSEGV standalone; the tower3d libgdx.so of the same family '
        'loads clean with no JNI_OnLoad = per-library defect, not a family '
        'law). Fixed by the three-layer GUARDED-NATIVE law in '
        'src/jni/dlopen_exec.cpp: (1) fork dlopen pre-probe (a faulting '
        'child dies by signal without exposing the parent loader lock; a '
        'cleanly refused probe still lets the parent dlopen for the REAL '
        'dlerror); (2) sigsetjmp fault guard around dlopen, JNI_OnLoad and '
        'every symbol call (a fault becomes an honest load failure / '
        'UnsatisfiedLinkError, crash-forensics handler saved+restored); '
        '(3) loader-poison teardown law (_exit on run completion after a '
        'poisoned-loader fault — the partially-loaded library\'s _dl_fini '
        'walk hangs exit). Verified: rc 139→1, honest UnsatisfiedLinkError '
        'delivered into libGDX SharedLibraryLoader.load\'s own catch-all '
        'handler (deferred handler @0x24 type=<catch-all>), 5 frames '
        'complete, tower3d anchor byte-identical (clean loads unaffected).'),
    'evidence': (
        'run/c120/tictactoe_fixed3.log (S2-NATIVE fault row + deferred '
        'handler delivery + PARTIAL SUCCESS); run/c119/tictactoe1.log (the '
        'crash: signal=11 si_code=1 fault_addr=0x0 right after the F-NEW-441 '
        'extract); /tmp probe bisect scripts (scripts/cont120_ttt_dlopen_'
        'probe.c — step1 FAULT inside dlopen vs tower3d step1 OK); '
        'run/c120/battery.log tower3d_ANCHOR_MATCH; '
        'miniandroid/src/jni/dlopen_exec.cpp (dlopen_probe/run_native_'
        'guarded/loader_poisoned); miniandroid/src/main.cpp (teardown law).'),
}


def main():
    for path in (MIRROR, MAIN):
        reg, roots = load(path)
        ids = {r['id'] for r in roots}
        # updates by ID
        for rid, upd in UPDATES.items():
            if rid not in ids:
                print(f'{path}: MISSING {rid}', file=sys.stderr)
                sys.exit(1)
            for r in roots:
                if r['id'] == rid:
                    r['title'] = r.get('title', '') + upd['title_append']
                    r['evidence'] = (r.get('evidence', '')
                                     + ' ' + upd['evidence_append'])
                    if upd.get('status'):
                        r['status'] = upd['status']
                    break
        # new root (both files stay in lockstep)
        if NEW_ROOT['id'] not in ids:
            roots.append(dict(NEW_ROOT))
        save(path, reg, roots)
        # verify
        reg2, roots2 = load(path)
        ids2 = [r['id'] for r in roots2]
        assert len(ids2) == len(set(ids2)), f'{path}: duplicate ids!'
        print(f'{path}: roots={len(ids2)} unique=True '
              f'F-NEW-466={"F-NEW-466" in set(ids2)}')
    # cross-file consistency
    _, mroots = load(MAIN)
    _, croots = load(MIRROR)
    mids = {r['id'] for r in mroots}
    cids = {r['id'] for r in croots}
    print(f'main==mirror: {mids == cids}')
    assert mids == cids


if __name__ == '__main__':
    main()
