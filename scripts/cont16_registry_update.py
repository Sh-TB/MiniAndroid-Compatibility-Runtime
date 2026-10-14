#!/usr/bin/env python3
"""CONT-16: registry updates for the fix batch (266a, 259g-a, 259g-b) + bookkeeping."""
import json, datetime

P = '/home/z/my-project/root_registry.json'
reg = json.load(open(P))
roots = reg['roots']
today = '2026-10-07'
BIN = 'a8761a482a186eac'

anchors = ('anchors 6/6 x3 byte-identical at binary ' + BIN +
           ' (dooz d602648e8e401895 / microtimer da73010a37dd0189 / unote '
           '4f1a9e4e8f64fae8 / gmdice f3b483fe7b7cf51b / opencalc a976d2f9fb675cb3 '
           '/ chess b5a7a35d5fe0564b all UNCHANGED — zero native drift); '
           'f259 probe 7/7; fcol audit 3/18 (unchanged vs recorded state — '
           'no regression); negatives 19/19; skill selftest 13/13; '
           'evidence/cont16/cont16_reconciliation.md')

def upd(rid, new_status, title_suffix, evidence, probe, verified, fanout=None):
    for r in roots:
        if r['id'] != rid:
            continue
        r['status'] = new_status
        if title_suffix:
            r['title'] = (r['title'] + ' ' + title_suffix)[:2900]
        r['evidence'] = evidence
        r['probe'] = probe
        r['verified_current'] = verified
        if fanout:
            r['fanout'] = fanout
        r['date'] = today
        return True
    return False

ok1 = upd('F-NEW-266a', 'ROOT-CAUSED-FIXED',
    'CONT-16 TWO-LAYER RESOLUTION: '
    '(LAYER-1) DALVIK UNTYPED-REGISTER NULL LAW — DEX registers are untyped; const/4 vN,0 '
    '(the universal javac/D8 null materialization) left the engine register as DalvikValue '
    'INT32 0, so f141_is_null_receiver (NULL_REF / OBJECT_REF-id-0 only) missed the typed '
    'null on EVERY instance-invoke gate and the call fell through to a silent stub answer. '
    'Widened f141_is_null_receiver with the INT32-0 receiver arm (receiver slot of an '
    'instance invoke is verifier-guaranteed to be the callee class or null — an int 0 there '
    'IS null; invoke-static/range already excluded from the range gate). '
    '(LAYER-2) DEFAULT-METHOD ROUTE GATE — try_interface_default_invoke now gates the '
    'null receiver BEFORE the memo lookup (NPE is a receiver property, not a resolution '
    'property), covering the invoke-virtual transitive-interface-default path end-to-end. '
    'ART law: NPE at the call site before ANY callee body runs. No app/R8-name knowledge.',
    'evidence/cont16/cont16_reconciliation.md',
    'fixtures/f266_probe row D at binary ' + BIN + ': null-receiver NPE=true '
    'r4=0 — 6/6 PASS (was 5/6, D honest FAIL at 0ee46f5a719d2a8c).',
    anchors,
    'every typed-null invoke-interface/invoke-virtual in any app (null-guarded '
    'API surfaces, compose Modifier chains, SAM interfaces held in nullable fields)')

ok2 = upd('F-NEW-259g-a', 'ROOT-CAUSED-FIXED',
    'CONT-16 RESOLUTION via the GENERIC SHADOW EXCEPTION CHANNEL: (1) CallResult gained '
    'an exception kind (is_exc/exc_class/exc_msg + handled_exception factory) — the shadow '
    'channel previously had NO exception kind (documented F-165/F-NEW-239 precedent), so '
    'contract violations answered silent null/bool; (2) the three try_shadow_dispatch '
    'conversion sites (pass-1/pass-2/hierarchy walk) convert a shadow exception into '
    'throw_deferred at the call site — the same semantics as the engine-side F-141/F-036 '
    'laws; (3) CollectionShadow list get() now enforces the OpenJDK ArrayList/LinkedList '
    'RANGE LAW (index<0 || index>=size → IndexOutOfBoundsException "Index: N, Size: S") '
    'with the authoritative size mirroring the size() law (shadow store, else the engine '
    'array-fields store). Probe row K flipped: the 4-iteration walk is now the faithful '
    'IOOBE propagation (n=2).',
    'evidence/cont16/cont16_reconciliation.md',
    'fixtures/fnew259g_probe row K at binary ' + BIN + ': PASS n=2 k1,k2 '
    '(was FAIL n=4); rows H..T 12/13 with L unchanged-honest.',
    anchors,
    'every ArrayList/LinkedList get() consumer that relies on the JDK bounds law — '
    'AbstractList$Itr walks (iterate-while-hasNext over size()-derived counts), '
    'manual range-guarded reads, error paths that expect IOOBE')

ok3 = upd('F-NEW-259g-b', 'ROOT-CAUSED-FIXED',
    'CONT-16 RESOLUTION: the registered finding was the materialization/iterator NPE — '
    'java.util.Vector was claimed by NO shadow and the F-NEW-246 engine law covers '
    '<init>/addElement/add/size/isEmpty/get/elementAt/elements/hasMoreElements/nextElement '
    'but NOT the iterator() mint, so new Vector().iterator() answered null → '
    'Iterator.hasNext NPE. FIX: CollectionShadow::handles_class now claims '
    'Ljava/util/Vector; — the generic F-237 iterator-box law mints a real box over the '
    'Vector engine array-fields store (__array_length__ + array[i], the F-NEW-246 '
    'convention) which hasNext/next already read; F-NEW-246 keeps precedence for its own '
    'methods (bridge_to_api returns before the shadow dispatch). PROBE-AUTHORING NOTE '
    '(honest): row L still reports threw=false because its authored expectation '
    '(IllegalStateException) contradicts ART dispatch honesty — NoSlots DEFINES its own '
    'iterator() whose DEX body must run (F-068 most-derived law, try_recursive_invoke '
    'precedes the engine laws), and an empty Vector iterates zero elements on real '
    'Android too; the NPE (the actual registered finding) is GONE and the iteration is '
    'JDK-honest. Row-L expectation classified as a probe artifact, NOT an engine root; '
    'no suppression added anywhere.',
    'evidence/cont16/cont16_reconciliation.md',
    'fixtures/fnew259g_probe row L at binary ' + BIN + ': no NPE, zero-iteration '
    'empty-Vector walk (was NPE at iterator()). Rows H..T 12/13 (K PASS).',
    anchors)

print('updates applied:', ok1, ok2, ok3)

# status counts refresh
from collections import Counter
c = Counter(r['status'] for r in roots)
reg['status_counts'] = dict(c)
reg['meta']['last_update'] = ('CONT-16 fix-batch session ' + today + ': F-NEW-266a '
    '(typed-null NPE law, f266 6/6), F-NEW-259g-a (shadow exception channel + JDK list-get '
    'range law, f259g row K flip), F-NEW-259g-b (Vector claim, NPE gone; row L expectation '
    'classified probe artifact) all ROOT-CAUSED-FIXED at binary ' + BIN + '; anchors 6/6 x3 '
    'byte-identical, f259 7/7, fcol 3/18 unchanged, negatives 19/19, skill 13/13. '
    'CONT-16 52-task backlog: evidence/cont16/CONT16_TASK_BACKLOG.md')
reg['generated'] = today
json.dump(reg, open(P, 'w'), indent=1)
print('registry saved; new counts:', dict(list(c.items())[:8]))
print('open-ish remaining:', sum(v for k, v in c.items() if k in {
    'PARTIAL','UNPROVEN','RESEARCHED-NOT-IMPLEMENTED','PENDING','OBSERVED-FAIL',
    'REGISTERED','OPEN','CLASSIFIED','OBSERVED','PARTIAL-FIX','BLOCKED'}))
