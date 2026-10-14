#!/usr/bin/env python3
# cont38v_registry.py — CONT-38v registry update: F-NEW-299 (String
# copy-constructor content law) + friend-claim verification verdicts
# (recorded as evidence pointers, NOT duplicate registry entries).
import json, collections

P = '/home/z/my-project/root_registry.json'
d = json.load(open(P))
ids = {r.get('id') for r in d['roots']}
assert 'F-NEW-299' not in ids, 'F-NEW-299 already present — dedup check'

entry = {
  "id": "F-NEW-299",
  "title": "String copy-constructor content law: new String()/new String(String) left the heap object unmaterialized (no __string_value__) — String-object map keys fell back to identity keying and content lookups missed; discovered BY the CONT-38v independent-verification probe",
  "status": "ROOT_CAUSED_FIXED",
  "priority": "P1",
  "layer": "runtime/string-construction",
  "root_cause": "PROVEN BY THE VERIFICATION PROBE (fixtures/classkey_probe, row CK-07, real aapt2/ECJ/D8 toolchain): bridge_to_api handled ONLY the String(byte[]) constructor family; new String() and new String(String) fell to the generic stub — the new-instance Ljava/lang/String; heap object carried NO __string_value__, so F-NEW-248's map_key_value_law read no content and keyed the put as obj:<id> while the get with the SAME text as a const-string keyed by CONTENT — put/get never met. PRE ×3 on a181d7b317e015c8: CK-07 FAIL (98/7 across the repeated frame reports). OpenJDK String.java: new String() is the empty string; new String(String) copies the source's characters; String.equals is CONTENT equality — the copy is a distinct identity but MUST be the same map key.",
  "fix": "ONE generic point in bridge_to_api (the String <init> block, before the byte[] family): the copy-constructor content law — materialize __string_value__ onto the CALLER's heap object register (the same new-instance → <init> identity convention the byte[] law honors) and answer the content as the STRING_REF result. Structural discriminators only: STRING_REF source = direct copy; OBJECT_REF source accepted ONLY when its heap class is Ljava/lang/String; (byte[] sources keep falling through to the byte[] law); args==1 = the empty-string form. No name matching, no app branches.",
  "synthetic_probe": "fixtures/classkey_probe (package com.probe.ckey): 15 generic rows — CK-01..CK-06 cover the friend-reported Class-token map-key identity (const-class identity, getClass==const-class cross-production, HashMap/LinkedHashMap<Class,V> cross-site round-trips, distinct-descriptor discrimination, ordinary-object identity preservation); CK-07 is the probe-discovered copy-constructor face; LI-01..LI-08 cover the friend-reported ListIterator contract (full cursor walk, empty list, listIterator(index), set/add/remove with lastReturned semantics, double-remove ISE, pre-next ISE, repeated iteration). PRE ×3: 14/1 (CK-07 FAIL) → POST ×3 on f528f04483017c57: 15/0. Wired into scripts/w4_build_probes.sh + cont37_regression.sh (standing battery).",
  "evidence": "evidence/cont38v/FRIEND_CLAIM_VERIFICATION.md; runs run/cont38v/ckey_{r1..3} (PRE) + ckey_post_{r1..3} (POST); scripts/cont38v_build_probe.sh + cont38v_targets.sh",
  "not_claimed": "new String(char[]) / new String(StringBuffer/StringBuilder) forms remain honest untested scope (same posture the byte[] entry originally recorded); the fix does NOT change any recorded anchor (full regression gate below).",
  "regression": "binary f528f04483017c57: anchors 8/8 ×3 BYTE-IDENTICAL (dooz 31ddd4d5b8e6d18e, microtimer da73010a37dd0189, unote 4f1a9e4e8f64fae8, gmdice f3b483fe7b7cf51b, opencalc a976d2f9fb675cb3, tttdeluxe af6094295ecb50e3, flappycow 13cf47464d9787f4, g2048 59ca1526611c4622); composeStopwatch bbaf8f76308dc267 ×3; battery == CONT-28..37 records EXACTLY (fcol 140/0, f259 49/0, f259g 84/7-known, f266 42/0, f268 96/0, fnew253 147/0, fnew286 10/0, fnew289 28/0, fnew252 56/0, fnew290 56/0, fnew291 56/0, fnew292 70/0, fnew293 56/0, fnew294 77/0, fnew295 49/0, fnew296 42/0, fnew297 42/0, fnew298 19/0) + ckey 15/0; simplecalc ×3 rc=0 7960bce447ac6d8f. ZERO DRIFT.",
  "friend_claims_verified": "The friend-reported 'F-NEW-257' (Class objects as stable map keys) and 'F-NEW-258' (non-null ArrayList.listIterator) are RE-DISCOVERIES of already-registered roots — F-069/R-NEW-293 + F-103 + F-NEW-249 + F-NEW-282 (const-class/getClass/forName stable heap-backed Class tokens; one identity per descriptor) and F-NEW-255 + the CONT-18 LAW-B write-back faces (typed iterator box, full cursor + set/add/remove contract). Both claims verified against the CURRENT source and probe rows CK-01..06 / LI-01..08 PASS ×3; the friend's line numbers and the 'class:<descriptor>' key form / 'self-as-iterator' representation do NOT match this lineage (equivalent-or-stronger guarantees exist at the token layer / typed-box layer). No duplicate registry entries created."
}

d['roots'].append(entry)
d['total'] = len(d['roots']) + 3   # total counts roots + the 3 legacy summary buckets (preserve arithmetic)
prev_total = d.get('total')
sc = collections.Counter(r.get('status') for r in d['roots'])
d['status_counts'] = dict(sorted(sc.items()))
d['meta']['last_update'] = ("CONT-38v verification session 2026-10-10: F-NEW-299 (String copy-constructor content law, "
                            "classkey probe CK-07 flip 14/1→15/0 ×3 both directions) + the friend-claim verification "
                            "verdicts ('F-NEW-257'→F-069/F-103/F-NEW-249/F-NEW-282 family; 'F-NEW-258'→F-NEW-255/LAW-B "
                            "family) recorded as evidence, no duplicate entries.")
d['generated'] = 'CONT-38v session'
json.dump(d, open(P, 'w'), indent=1, ensure_ascii=False)
print('roots now:', len(d['roots']), '| total field:', prev_total)
print('F-NEW-299 appended; status_counts updated:', sc.get('ROOT_CAUSED_FIXED'), 'ROOT_CAUSED_FIXED')
