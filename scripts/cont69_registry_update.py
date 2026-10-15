#!/usr/bin/env python3
"""cont69_registry_update.py — F-NEW-369 CLASSIFIED -> ROOT-CAUSED-FIXED.

The collection-law family fix (5 laws, probe-first):
  1. CollectionShadow.subList nested-view resolution + __sublist_to__ window
  2. SubList view redirect: window [off,to) bounds on size/get/set/add/remove
     + the iterator() mint (THE app root: iterator on a view answered null)
  3. hasNext/next resolve the iterator's parent through the subList window
  4. NoSuchElementException on exhausted next() (AOSP Itr.next() law)
  5. Engine cascade stage-0 kind-faithful element carry (string/int elements
     no longer degrade to object-0 on copy-ctors)
"""
import json
import collections

P = 'root_registry.json'
d = json.load(open(P))

hit = False
for r in d['roots']:
    if r.get('id') == 'F-NEW-369':
        hit = True
        r['status'] = 'ROOT-CAUSED-FIXED'
        r['priority'] = 'P1'
        r['title'] = (
            "Memory (Privacy Friendly Memory) cold-first-launch white face — RESOLVED CONT-69. Root law chain (live-DEX disassembly + trace): "
            "getResIDs discards its fresh LinkedList (dead code) and serves the STATIC images1/images2 list built in <clinit> via List.add; reduce() "
            "returns list.subList(0, deckSize/2); ResIdAdapter.getResourceName for-eaches the subList. The subList VIEW box minted by CollectionShadow "
            "carried __sublist_parent__/__sublist_off__ but the view redirect DECLINED every unlisted face — iterator() answered NULL and hasNext "
            "NPE'd (f141-null-recv) → SplashActivity.onCreate APP BOUNDARY unwind → white 31ddd4d5b8e6d18e. FIVE generic laws (zero app-specific code): "
            "(1) subList nested-view resolution (AOSP AbstractList.SubList(offset+from, offset+to)) + the exclusive __sublist_to__ bound; "
            "(2) the view redirect now serves the WINDOW [off,to) on size/isEmpty/get/set/add/remove AND mints the F-237 iterator box (the root); "
            "(3) hasNext/next resolve the iterator's parent through the subList window (cursor counts inside the window); "
            "(4) NoSuchElementException on exhausted next() (OpenJDK Itr.next() law — was handled_null); "
            "(5) engine cascade stage-0 KIND-FAITHFUL element carry (string/int registry elements degraded to object-0 on copy-ctors — llk probe P3). "
            "PROBE: fixtures/linkedlist_probe 8/8 families PASS x3 byte-deterministic b75a1e7693ab8950 (pre-fix: P3/P6/P7/P8 FAIL — root shape P7 "
            "reproduced the exact hasNext NPE). ACCEPTANCE at binary 6e4758543e15996a: memory COLD x3 (fresh sandbox each) 3a3ba8734b662e55 REAL "
            "content (21.4% non-bg, 160 buckets, dark+blue-accent face = the warm face family; ResIdAdapter.getResourceName completes; DrawerArrowDrawable"
            "+setupNavigationView reached; 0 theme ISE); memory WARM x3 c559b630dd8f0f0f (record intact); notes x3 d0a409043ffc83a7 (record intact); "
            "wall 36/36 x3 MATCH; TSP 7/7 (record values); gate A 98/1/0; negatives 19/19; reinstall 8/8; goldens 4/4; skill 13/13.")
        r['evidence'] = ("evidence/cont69/cont69_evidence.json; evidence/cont69/cont69_mosaic.png "
                         "(https://tmpfiles.org/w1AEZ3j74lJV/cont69_mosaic.png); run/s69/llk_store4 data/com.probe.llk/files/linkedlist_results.jsonl; "
                         "run/s69/{coldfix_r1..r4,cold1,warmfix1,notes_r1..r3}/; scripts/cont69_build_llk.sh; scripts/cont69_disasm.py")
        r['probe'] = "fixtures/linkedlist_probe (apk 1a1c2998bd788b75); upload/canonical_apks/org.secuso.privacyfriendlymemory_100.apk"
        r['verified_current'] = True
        break

assert hit, 'F-NEW-369 not found'
d['total_roots'] = len(d['roots'])
d['total'] = d['total_roots']
d['count'] = d['total_roots']
sc = collections.Counter(r['status'] for r in d['roots'])
d['status_counts'] = dict(sorted(sc.items()))
d['generated'] = '2026-10-15 18:05:00 (CONT-69: F-NEW-369 ROOT-CAUSED-FIXED; counts reconciled)'

json.dump(d, open(P, 'w'), indent=1, ensure_ascii=False)
print('F-NEW-369 -> ROOT-CAUSED-FIXED; total_roots =', d['total_roots'],
      '| CLASSIFIED =', sc['CLASSIFIED'], '| ROOT-CAUSED-FIXED =', sc['ROOT-CAUSED-FIXED'])
