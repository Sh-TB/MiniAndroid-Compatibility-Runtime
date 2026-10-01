#!/usr/bin/env python3
"""S134 wave 6 — registry bookkeeping: append F-NEW-163..169 to
root_registry.json (all copies) + canonical/master_worklist.json.

Every entry cites its worklog wave evidence. Statuses are the honest
wave-close states (no inflation):
  F-NEW-163 S135 trace logger        IMPLEMENTED/TESTED (S135 entry)
  F-NEW-164 font glyph corruption    ROOT-CAUSED-FIXED  (S135 entry)
  F-NEW-165 content-anchor law       ROOT-CAUSED-FIXED  (wave 3)
  F-NEW-166 base-context routing     PARTIAL            (wave 4)
  F-NEW-167 BlockingQueue law        ROOT-CAUSED-FIXED  (wave 5)
  F-NEW-168 fragment-host family     PARTIAL — face 1 (Context.getDir
                                     null → R8 null-check NPE)
                                     ROOT-CAUSED-FIXED this wave; faces 2+3
                                     (androidx ISE "No activity"/"not
                                     attached") remain, blocked behind
                                     F-NEW-169
  F-NEW-169 DI provider-null lattice NEW (this wave): WhatsApp Dagger/
                                     AppContext slot providers (00t.get →
                                     1QL.A01 arms) answer null when an arm's
                                     dependency invoke hit a REC-MISS stub;
                                     the A0F "INVOKE_RETURN must not be null"
                                     check then kills Application component
                                     init (08C/08B lattice) AND the Activity
                                     ctor chain (0IL/0IS → 0JY/0JZ host never
                                     constructed) — which is the gate in
                                     front of the fragment-host faces.
"""
import json, re
from pathlib import Path

BASE = Path('/home/z/my-project')

ENTRIES = [
    {
        'id': 'F-NEW-163', 'status': 'IMPLEMENTED', 'priority': 'P0',
        'summary': 'S135 visual runtime boot/trace logger: ONE event backbone on '
                   'TraceEngine (runtime_event + ring/JSONL/stage/first-divergence '
                   'sinks) + semantic overlay composed on a COPY; authoritative '
                   'byte-stable (dooz x3 = golden with logger ON).',
        'evidence': 'worklog S135 entry; docs/BOOT_TRACE_LOGGER.md; dooz '
                    'ba8a95eb2278594f x3; overlay-OFF A/B zero-delta.',
    },
    {
        'id': 'F-NEW-164', 'status': 'ROOT-CAUSED-FIXED', 'priority': 'P1',
        'summary': 'BitmapFont 5 corrupt glyphs (dot drew solid block) — generator '
                   'tight-crop law; re-rendered full-cell from DejaVuSansMono.',
        'evidence': 'worklog S135 entry; scripts/s135_fix_font_glyphs.py; goldens '
                    'byte-identical.',
    },
    {
        'id': 'F-NEW-165', 'status': 'ROOT-CAUSED-FIXED', 'priority': 'P0',
        'summary': 'Window.setContentView content-anchor law (AOSP PhoneWindow): '
                   'decor android.R.id.content parent + mContentParent.addView + '
                   'ActivityShadow anchor + layout_dirty. droidify white screen '
                   '→ REAL_APP_CONTENT (3883 px), 3-run 59fdbfcd60b86a23.',
        'evidence': 'worklog S134 wave 3; dex/dalvik_engine.cpp R005-DECOR; '
                    'goldens byte-identical; laws130 51/51.',
    },
    {
        'id': 'F-NEW-166', 'status': 'PARTIAL', 'priority': 'P0',
        'summary': 'ContextWrapper base-context law: Context-family receivers '
                   'reach the S110 getBaseContext/attachBaseContext law; '
                   'ContextWrapper.<init>(base) delegates per AOSP. WhatsApp '
                   'boots past attachBaseContext NPE into onCreate with real '
                   'window content (23472 px). Residual: downstream clinit '
                   'family (F-NEW-167) was the next face.',
        'evidence': 'worklog S134 wave 4; try_shadow_dispatch routing; A/B '
                    'false-alarm disproven (shared-data-root prefs drift).',
    },
    {
        'id': 'F-NEW-167', 'status': 'ROOT-CAUSED-FIXED', 'priority': 'P0',
        'summary': 'BlockingQueue law: heap-field FIFO (put/offer/add → take/'
                   'poll/peek) + empty blocking take = R-NEW-345 park-yield at '
                   'the drain boundary. WhatsApp Log.<clinit> completes; F084 '
                   'halt-loop / VirtualMachineError escape eliminated.',
        'evidence': 'worklog S134 wave 5; dex/dalvik_engine.cpp ~90 LOC; '
                    '[F167-BQ-TAKE] parked consumer; goldens byte-identical.',
    },
    {
        'id': 'F-NEW-168', 'status': 'PARTIAL', 'priority': 'P0',
        'summary': 'Fragment-host family (WhatsApp). FACE-1 ROOT-CAUSED-FIXED '
                   '(S134 wave 6): Context.getDir(String,int) REC-MISS → stub '
                   'null → app-baked Intrinsics null-check (LX/00i;.A06) NPE → '
                   'APP-BOUNDARY unwind from LX/004;.onCreate. AOSP '
                   'ContextImpl.getDir law implemented: app_data_root/app_<name> '
                   '+ create-if-needed + F-NEW-179 pathed stable File identity; '
                   'AOSP getDir NEVER returns null. First divergence MOVED: app '
                   'now reaches onCreateWithUlitralightReady/'
                   'AbstractAppShellDelegate.onCreate; 3-run deterministic '
                   'eb16ab5c68fa9b6c. FACES 2+3 remain: androidx FragmentManager '
                   'ISE "No activity" (0JZ.A0c via onStart chain) + "FragmentManager '
                   'has not been attached to a host." (0JZ.A0G via onResume '
                   'chain) — the 0JZ host (A08) is never constructed because '
                   'Main/0I9 ctor chain dies in the DI lattice → F-NEW-169 gate.',
        'evidence': 'run/s134/wa_w6_* (r1 baseline, f1 post-law, g1..g3 '
                    'determinism); disassembly ground truth LX/00A;.A06 → '
                    'Context.getDir → LX/00i;.A06; reg battery dooz '
                    'ba8a95eb2278594f + simplestopwatch e00fe7e082c385f8 '
                    'byte-identical, headingcalc 823 colors / 466062 px exact, '
                    'laws130 51/51, F168 fired 0x on goldens.',
    },
    {
        'id': 'F-NEW-169', 'status': 'OBSERVED-FAIL', 'priority': 'P0',
        'summary': 'WhatsApp DI provider-null lattice (NEW frontier, wave 6): '
                   'AppContext slot providers (00t.get → 1QL.A01 packed-switch '
                   'arms over ~900 slots) null-check dependency invokes with '
                   'LX/00i;.A0F "INVOKE_RETURN must not be null"; when a '
                   'dependency hit a REC-MISS stub the arm NPEs and the whole '
                   'component lattice (08C.<clinit>/08B/088/089 ctors, 07r.<init>) '
                   'unwinds uncaught (2 of the 4 F-016 in-flight chains). Same '
                   'null-provider face kills Main.onCreate at pc=0x5ba '
                   '(0gV.A02 → 00t.get() → null → 08k.A0B() NPE) which blocks '
                   'F-NEW-168 faces 2+3 (0I9.<init> constructs 0JY/0JZ host). '
                   'Attack order: identify which REC-MISS stub feeds the first '
                   'failing arm (slots 169/864/112/109 via 00T.A03/00C.A02 '
                   'getters), fix the generic API law, re-measure.',
        'evidence': 'run/s134/wa_w6_f1 stdout THROWABLE-STACK (00i.A0F ← 07f.A00 '
                    '← 07P.A08 ← AbstractAppShellDelegate.onCreate ← '
                    '004.onCreateWithUlitralightReady), crash.log chains 1+2 '
                    '(08C lattice) + Main.onCreate pc=1470 NPE; disassembly of '
                    '00C.A03/06E.A00/069.get/06F.A00/1Vq.BTm/07r.<init>.',
    },
]


def upsert(items, e):
    for i, x in enumerate(items):
        if x.get('id') == e['id']:
            items[i] = {**x, **{k: v for k, v in e.items() if k != 'id'}}
            return 'updated'
    items.append(dict(e))
    return 'added'


for reg in [BASE / 'root_registry.json', Path('/tmp/my-project/root_registry.json')]:
    r = json.load(open(reg))
    roots = r['roots']
    changed = [upsert(roots, e) for e in ENTRIES]
    r['total'] = r['count'] = len(roots)
    json.dump(r, open(reg, 'w'), indent=1)
    print(reg, dict(zip([e['id'] for e in ENTRIES], changed)), 'total=', r['total'])

wl = BASE / 'canonical/master_worklist.json'
w = json.load(open(wl))
changed = [upsert(w['items'], e) for e in ENTRIES]
c = {}
for x in w['items']:
    c[x.get('status', 'UNCLASSIFIED')] = c.get(x.get('status', 'UNCLASSIFIED'), 0) + 1
w['counts'] = c
json.dump(w, open(wl, 'w'), indent=1)
print(wl, dict(zip([e['id'] for e in ENTRIES], changed)), 'items=', len(w['items']))
