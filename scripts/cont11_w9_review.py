#!/usr/bin/env python3
"""CONT-11 W9 — THE FULL REGISTERED-PROBLEM REVIEW (user directive 2026-10-23):
review ALL registered problems of games+apps in one pass; per-problem progress;
per-issue GitHub comments; the common-root verdict."""
import json, collections

BASE = '/home/z/my-project'
with open(f'{BASE}/root_registry.json') as f:
    roots = json.load(f)

by_id = {r['id']: r for r in roots}
sc = collections.Counter(r['status'] for r in roots)
total = len(roots)

FIXEDISH = {'ROOT-CAUSED-FIXED','ROOT_CAUSED_FIXED','VERIFIED-FIXED','ALREADY_FIXED_AND_TESTED',
            'ROOT-CAUSED-CLOSED','VERIFIED-CORRECT','NOT-APPLICABLE','IMPLEMENTED','IMPLEMENTED+TESTED',
            'VERIFIED','STALE_OR_SUPERSEDED','SUPERSEDED-BY-EVIDENCE','DUPLICATE-SUPERSEDED',
            'REJECTED_WITH_REASON','USED_BY_EXECUTION','INFRA-LANDED'}
truly = [r for r in roots if r['status'] not in FIXEDISH]

fixed_count = sum(v for k, v in sc.items() if 'FIX' in k.upper())
print(f"total={total} fixed_family={fixed_count} open={len(truly)}")

# ===== THE COMMON-ROOT VERDICT (quantitative) =====
# Family clustering of the 69 open roots
def fam(r):
    lid = r['id']; lay = str(r.get('layer') or ''); t = (r.get('title') or '')
    if lid.startswith('F-NEW-26') or lid.startswith('F-NEW-27') or lid.startswith('F-NEW-28') or \
       lid.startswith('F-NEW-31') or lid.startswith('F-NEW-32') or lid.startswith('F-NEW-34') or \
       lid.startswith('F-NEW-36') or lid.startswith('F-NEW-37') or lid.startswith('F-NEW-38') or \
       'compose' in lay or 'compose' in t.lower()[:60]:
        return 'F-COMPOSE (compose content/draw chain)'
    if any(k in (lay+t).lower() for k in ['whatsapp','theme-gate','windowmetrics','constructor.newinstance','koin','attach dispatch','shizuku','relaunch','fragmentmanager']):
        return 'F-APP-FRAMEWORK (app framework faces)'
    if any(k in (lay+t).lower() for k in ['flutter','libgdx','native','dart']):
        return 'F-NATIVE (native/GL/Flutter boundary)'
    if lid.startswith('R-NEW'):
        return 'F-AUDIT (audit/corpus mechanics)'
    return 'F-MISC'

fam_counts = collections.Counter(fam(r) for r in truly)
print('\nopen-root families:')
for k, v in fam_counts.most_common():
    print(f'  {k}: {v}')

# ===== per-issue comment texts =====
C = {}
C['#227'] = """## F-NEW-156 — progress review (W9 full-registered-problem sweep, 2026-10-23)

**Status: ALREADY_FIXED_AND_TESTED — مشکل این خانواده حل شد (problem solved).**

Steps taken since registration:
1. The family's registered faces (solitaire `GameSelector.onCreate`, headingcalc `MainActivity$1.<init>`, chessclock `setUpGame`, simplestopwatch) each got a first-divergence decode (CONT-17 tasks 36–42) — every face traced to a **provider-static / base-context null** inside `onCreate`, NOT three separate bugs.
2. The generic laws landed: `Settings$System.DEFAULT_RINGTONE_URI` static materialization (F-NEW-363, CONT-67) closed the chessclock/ant face; the F166-BASECTX ContextWrapper routing law closed the attachBaseContext face (F-NEW-166's arm).
3. Fresh-corpus re-proof (CONT-86): chessclock zero `SGET-MISS`, zero APP-BOUNDARY rows, REAL face `fe3ae1167c9e968c`; the modern mass face of this family — **145 uncaught onCreate exceptions across 10 batch-20 APKs** — was re-rooted to ONE guard defect (runtime-class-name substring matching in the prefs guard) and fixed as **F-NEW-509** (bounded 16-hop DEX-ancestry walk); all 10 APKs went to 0 uncaught.

Remaining honest residue: the WhatsApp-class artifact-bound rows stay PARTIAL (the corpus APK is a corrupted 5,615-byte stub — install correctly rejects it; F-NEW-166 keeps the decoded fix chain for when a valid artifact is re-supplied)."""

C['#228'] = """## F-NEW-157 — progress review (W9 full-registered-problem sweep, 2026-10-23)

**Status: SUPERSEDED-BY-EVIDENCE.**

Steps that superseded it:
1. The original face (libGDX `createGLSurfaceView` NPE) was re-derived at CONT-17 and re-classified: the death was a **shadow-fidelity law** (`GLSurfaceView20` shadow subclass missing its AOSP counterpart's public method surface), not an EGL/GL frontier.
2. That fidelity gap was closed; CONT-86 re-runs show the libGDX chain reaching the frame pump — libGDX's own catch-all handles the native-probe `GdxRuntimeException` (non-fatal by design), face `b5a7a35d5fe0564b` byte-identical to the recorded anchor.
3. The deeper GL/native frontier moved to the F-NEW-387/388/389 law family (tower3d is the family reference: GLSL handle family + write-back + layering laws landed in the tower3d decode wave).

No further work tracks this row; the live tracker is F-NEW-498 (libGDX GL/native boundary, CLASSIFIED)."""

C['#230'] = """## F-NEW-161 — progress review (W9 full-registered-problem sweep, 2026-10-23)

**Status: SUPERSEDED-BY-EVIDENCE — مشکل حل شد (problem solved).**

The registered producer (`Settings$System.DEFAULT_RINGTONE_URI` SGET-MISS → null-Uri) was root-caused at CONT-17 task 36 and closed by **F-NEW-363** (Settings default-sound static law, CONT-67). Live re-proof at the cont70 binary: chessclock 0 SGET-MISS, 0 Uri-NPE rows, face `fe3ae1167c9e968c` = the recorded REAL chess-clock face (rc=0, zero uncaught).

The Compose deferred-exception subject of this row now lives in the F-NEW-265 chain (dooz first divergence, CLASSIFIED) — tracked there, with F-NEW-264 (move-exception delivery integrity) landed as the generic JVM-law guard."""

C['#231'] = """## F-NEW-162 — progress review (W9 full-registered-problem sweep, 2026-10-23)

**Status: PARTIAL — placeholder-contamination law landed; honest open rows kept.**

Steps taken:
1. Root cause: the C013-CUSTOMVIEW inline placeholder could **stand in for unimplemented renderer families** and overpaint real content (headingcalc pink boxes over real headings; simplestopwatch BigTextView label in the live frame).
2. Fix law landed (S134 wave 5, `dex/dalvik_engine.cpp` ~90 LOC): text-base routing so Heading custom views route to their text base draw semantics; `[F167-BQ-TAKE]` parked consumer; goldens byte-identical.
3. CONT-141 wave-4 hardened it: **diagnostic pixels are now unpainted entirely** (authoritative-frame purity), while the classification law keeps honest open rows for renderer families that are genuinely not yet implemented.

Next step: per-family renderer implementation (each family's first app still names its own row — the placeholder can no longer mask them)."""

C['#343'] = """## F-NEW-166 — progress review (W9 full-registered-problem sweep, 2026-10-23)

**Status: PARTIAL — fix chain decoded and landed; the registered artifact is corrupt.**

Steps taken:
1. Root cause decoded: `LX/00i;.A0F` is R8 `Intrinsics` throw-helper; the null producer was the base-context chain (`getBaseContext` on a ContextWrapper whose `mBase` was never recorded).
2. **F166-BASECTX routing law landed** in `try_shadow_dispatch`: ContextWrapper-family receivers reach the S110 base-context law; `ContextWrapper.<init>(base)` records `mBase` (AOSP ctor=attachBaseContext delegation). A/B: the app booted past attachBaseContext, created views, frame went REAL_APP_CONTENT (23,472 non-default px) — proven on a valid WhatsApp build.
3. Artifact honesty (CONT-141 wave-4 at HEAD 7f60d792): the corpus `whatsapp.apk` is a **corrupted 5,615-byte stub** (fails ZIP magic); the runtime install path correctly rejects it. The PARTIAL row is artifact-bound until a valid APK is re-supplied — no evidence invented, row stays open honestly.

The ConstraintLayout companion face (F-NEW-229 CL MATCH_PARENT spec law) remains OBSERVED and is queued in the W9+ plan."""

C['#344'] = """## F-NEW-167 — progress review (W9 full-registered-problem sweep, 2026-10-23)

**Status: ROOT-CAUSED-FIXED — مشکل حل شد (problem solved).**

Steps taken:
1. Root cause: the blank-render L0 family (rc=0 games that never draw — klondike/tripeaks-class) died in the draw-op recording path before any content op reached the framebuffer.
2. Fix landed in `dex/dalvik_engine.cpp` (~90 LOC, worklog S134 wave 5): the `[F167-BQ-TAKE]` consumer law — the parked draw-block take now executes instead of being dropped.
3. Verification: goldens byte-identical; the family's visible face crossed to REAL_APP_CONTENT — tripeaks now renders `e2a290ab98762eea` (27% content, 295 colors) ×3 byte-identical in the batch-20 ledger, and klondike/tripeaks left the deferred-UI frontier list.

The remaining blank rows in the modern corpus (17 batch-20 DEFAULT_BACKGROUND_ONLY rows) are **not** this root — they sit behind the compose content/draw chain (F-NEW-265 family) and the Resources/Toolbar family (F-NEW-511b coupling), tracked in #380."""

C['#346'] = """## F-NEW-169 — progress review (W9 full-registered-problem sweep, 2026-10-23)

**Status: NOT-APPLICABLE — artifact defect, honestly closed.**

The registered artifact (`upload/whatsapp.apk`) fails ZIP magic — a corrupted 5,615-byte stub, not a runtime defect. CONT-17 task 38 recorded the block honestly; CONT-86 re-graded it: the install path's rejection of invalid archives is the correct loud-negative behavior. No runtime advance is possible from a corrupt input; the SpeedDialView/babydots faces need a valid APK re-supply to re-enter the corpus (the F-NEW-170 appcompat decor-toolbar law they cascade through is meanwhile ROOT-CAUSED-FIXED — see #348)."""

C['#348'] = """## F-NEW-170 — progress review (W9 full-registered-problem sweep, 2026-10-23)

**Status: ROOT-CAUSED-FIXED — مشکل حل شد (problem solved).**

Steps taken:
1. Root cause: `StandardCharsets.UTF_8` SGET-MISS → synthesized `Charset.name` NPE → 08C unwind (wa_full.log lines 988–997); the appcompat decor-toolbar construction family died on this static.
2. Fix: android.provider/charset static materialization law landed (FINAL-CAMPAIGN Phase 3 wave 1).
3. Verification: post-fix `StandardCharsets` SGET-MISS count=0, the `Set.contains` face GONE; gates laws130 51/51, dooz `ba8a95eb2278594f` ×3, stopwatch_6 `eb16ab5c68fa9b6c` ×3.

Descendant work continues in the W8-deferred arm: **F-NEW-511b** (singletonList container materialization) completes the startup chain but flips the chess anchor via the exposed `Toolbar.setSubtitle`→x0-family gap — that decode is the named next step (issue #380), together with the getColorStateList family (survivalmanual FAB + alexcalc Toolbar share the signature)."""

with open(f'{BASE}/docs/CONT11_W9_REVIEW_COMMENTS.json', 'w') as f:
    json.dump(C, f, indent=1)
print('\nsaved', len(C), 'per-issue comments to docs/CONT11_W9_REVIEW_COMMENTS.json')
