#!/usr/bin/env python3
"""CONT-20 registry update — F-NEW-271 root-caused+fixed via the
NULL-ELEMENT KIND LAW, plus F-NEW-272 registration (next frontier).

F-NEW-271 closure chain (all live at b6ee41e77acb88ec):
  1. [F271-READ]  Lnb0;.S pc=163 field Lnb0;.j:Lqb0 answered STRING_REF ""
     from the QUALIFIED heap slot Lnb0;->j on recv#2838 (heap_cls=Lnb0;,
     declarer=Lnb0;, dex_defined=1) — the heap itself held the alien value;
     the read machinery is exonerated.
  2. [F271-WRITE] Lnb0;.p pc=1553 iput-object stored STRING_REF "" into
     Lnb0;.j — caught in the act; the store's source register v3 came from
     ArrayList.remove at pc=1537 (cont3 disasm: pc=0x5f7 iget Lnb0;.i →
     pc=0x5f9 size() → pc=0x5ff add-int/lit8 -1 → pc=0x601 remove(I) →
     pc=0x604 move-result-object v3 → pc=0x605 check-cast Lqb0 (optimistic
     pass, no CCE — masking defect) → pc=0x611 iput-object → j).
  3. [F271-COLL]  pre-fix: Lnb0;.u pc=4 added REAL Lqb0 holders (o3108,
     o3131) AND NULL_REF elements (t8/o0, x6) to ArrayList o2839 == the
     Lnb0.i queue (Lnb0.u = i.add(this.j); this.j = p1 — enqueue-current-
     holder idiom, null legal by design); Lnb0;.p pc=1537 remove(0) on the
     same list was SERVED t5/o0("") — the CollectionShadow null-element
     representation (kind 2 + "") leaked as a fabricated String.
  4. ROOT: the kind-2+"" encoding is LOSSY — genuine empty-string elements
     and null elements store identically, so every serve path answered
     STRING_REF "" where OpenJDK/ART return TYPED NULL (ArrayList "permits
     all elements, including null"; remove(int)/get(int) return the stored
     element).
  5. FIX: NULL-ELEMENT KIND LAW — null elements carry kind 4; writers
     (lawb_classify_arg, ArrayList.add tail, add(index,e), set faces, stream
     materialization) classify NULL_REF/zero-ref args as kind 4; readers
     (lawa_remove_index, lawa_serve_slot, slot_to_arg, iterator next, COW/
     removeAll equality, contains) serve kind 4 as typed null. STRING args
     (including "") stay kind 2 — the genuine-"" round-trip is preserved.
  6. PROOF: fcol K19/K20 (new rows, pure java.util — no dooz/Compose) FAIL
     pre-fix (headNull=false ... secondNull=false) and PASS post-fix with
     K1-K18 unchanged; dooz serve-face flips t5/o0("") -> t8/o0 (typed
     null) x2 runs; the Lnb0.S pc=185 death face is GONE x2; composition
     advances to new PCs (Lnb0.S pc=913/190 activity). Anchor d602648e
     unchanged (next root blocks visual progress — honest).

F-NEW-272 (CLASSIFIED, P0): the next divergence in the dooz chain — the
engine has NO Thread default UncaughtExceptionHandler law. The app's own
crash-report path (Llo;.K pc=65: invoke-interface
Ljava/lang/Thread$UncaughtExceptionHandler;.uncaughtException) runs on a
NULL handler (Thread.getDefaultUncaughtExceptionHandler has no engine law
-> null) and dies at f141; that NPE then propagates uncaught into
MainActivity.onCreate -> APP BOUNDARY. ART/AOSP law: the default handler is
NON-NULL by default (RuntimeInit LoggingHandler / KillApplicationHandler —
logs then kills the process). Generic Thread/runtime law, not Compose.
"""
import json, collections

REG = '/home/z/my-project/root_registry.json'
d = json.load(open(REG), object_pairs_hook=collections.OrderedDict)
rows = d['roots']
by_id = {r.get('id'): r for r in rows}

TOTAL_271 = ("NULL-ELEMENT REPRESENTATION LEAK — ROOT-CAUSED+FIXED. "
    "The CollectionShadow element store models one backing array as four "
    "parallel stores; the documented null-element encoding (kind 2 + "
    "elem_strings[idx]=\"\") is LOSSY — a genuine empty-string element and "
    "a null element store identically, and every serve path (remove(int)/"
    "get/iterator/deque heads/callback materialization) answers "
    "handled_string(\"\") -> STRING_REF/0 for both. ART/OpenJDK law: "
    "ArrayList 'permits all elements, including null'; remove(int) returns "
    "the stored element AS typed null. Live face (dooz, F-265 arm (c) "
    "root): Lnb0.u (i.add(this.j); this.j = p1 — enqueue-current-holder "
    "idiom) legally enqueues NULL holders into ArrayList o2839 (Lnb0.i); "
    "Lnb0.p (remove(size-1) -> check-cast Lqb0 -> iput j) popped one as "
    "STRING_REF \"\" and stored it into Lnb0.j:Lqb0 on o2838; the "
    "composeContent path Lnb0.S then read j (non-null), read j.e on the "
    "String (null), and died at f141 invoke Lhv0.h on null (pc=185) -> "
    "uncaught -> Lzs.m measure unwind -> blank frame. FIX = NULL-ELEMENT "
    "KIND LAW: kind 4 = null element, written by every classifier "
    "(lawb_classify_arg, add tail, add(index,e), set faces, stream "
    "materialization) for NULL_REF/zero-ref args, served as typed null by "
    "every reader (lawa_remove_index, lawa_serve_slot, slot_to_arg, "
    "iterator next, removeAll equality, contains). STRING args — including "
    "\"\" — stay kind 2 so the genuine-empty-string round-trip is "
    "preserved bit-for-bit. Zero app/package checks; one law for every "
    "current and future four-store consumer.")

EVID_271 = ("HEAD b6ee41e77acb88ec (CONT-20; engine diag family F271-READ/"
    "F271-WRITE committed in 0b019608 + F271-COLL this wave). PRE-FIX: "
    "run/cont18i/dooz_f271 [F271-READ] Lnb0;.S pc=163 field Lnb0;.j:Lqb0 "
    "answered STRING_REF len=0 from readkey=Lnb0;->j recv#2838 "
    "(heap_cls=Lnb0;, declarer=Lnb0; — heap slot itself corrupt); "
    "[F271-WRITE] Lnb0;.p pc=1553 <- STRING_REF \"\" (caught in the act). "
    "Pre-fix probe run/cont20/dooz_probe [F271-COLL]: add recv=o2839 "
    "a1:t7/o3108 + a1:t7/o3131 (real Lqb0) AND a1:t8/o0 NULL x6 "
    "caller=Lnb0;.u pc=4; remove recv=o2839 a1:t1/o0 -> served t5/o0(\"\") "
    "caller=Lnb0;.p pc=1537. Genericity pre-proof (pure java.util, no "
    "dooz/Compose): fcol K19 FAIL headNull=false lastNull=false "
    "poppedNull=false, K20 FAIL secondNull=false (run/cont20/fcol_before). "
    "POST-FIX: fcol K19 PASS headNull=true lastNull=true midStr=true "
    "poppedNull=true, K20 PASS firstNotNull=true firstEmptyStr=true "
    "secondNull=true, K1-K18 unchanged (run/cont20/fcol_after); dooz "
    "[F271-COLL] remove recv=o2839 -> served t8/o0 (typed null) x2 runs "
    "(run/cont20/dooz_after, dooz_after2); Lnb0.S pc=185 death face GONE "
    "x2; composition advances (Lnb0.S pc=913/190 activity; deeper "
    "worker/coroutine faces). REGRESSION at b6ee41e77acb88ec: anchors "
    "18/18 x3 BYTE-IDENTICAL (dooz d602648e8e401895, microtimer da73010a, "
    "unote 4f1a9e4e, gmdice f3b483fe, opencalc a976d2f9, chess b5a7a35d); "
    "fcol 20/20 (18 recorded + new K19/K20); f259 7/7; f259g 12/13 "
    "(known honest L row, unchanged); f266 6/6; f268 12/12. gate-A "
    "negatives harness scores 9/19 at BOTH the pre-fix and post-fix "
    "binaries with identical failing rows (A/B at b4937c81aba0998c) — "
    "pre-existing infrastructure drift, NOT a regression of this wave.")

FANOUT_271 = ("Every app that enqueues null into an ArrayList/LinkedList/"
    "ArrayDeque and later removes/reads it — pending-work queues, holder-"
    "swap idioms (the Compose CompositionImpl invalidation queue is one "
    "live instance), adapter recycling, tree builders, callback buffers. "
    "The primitive is heap-central (four-store element law), so fan-out "
    "does not depend on per-APK wiring. Independent target: fcol K19/K20.")

TOTAL_272 = ("THREAD DEFAULT UNCAUGHT-EXCEPTION-HANDLER LAW GAP (the next "
    "dooz divergence after F-NEW-271's fix). The engine has NO law for "
    "Thread.getDefaultUncaughtExceptionHandler()/setDefault.../getUncaught"
    "ExceptionHandler: the getter answers null, so the app's own crash-"
    "report path (dooz Llo;.K pc=65: invoke-interface "
    "Ljava/lang/Thread$UncaughtExceptionHandler;.uncaughtException) "
    "executes on a null receiver and dies at f141 (ART-faithful NPE at "
    "the true site); that NPE then propagates through the worker's "
    "catch-alls (Ltx;.run, La12;.y) and reaches MainActivity.onCreate "
    "uncaught -> APP BOUNDARY unwind (run/cont20/dooz_after diag line "
    "~3277). AOSP law: Thread.defaultUncaughtExceptionHandler is "
    "initialized by RuntimeInit to the LoggingHandler, and KillApplication"
    "Handler chains it (log + optional process kill) — i.e. the default "
    "answer is a REAL HANDLER OBJECT, not null. Minimal generic law "
    "candidates: (i) a heap-materialized default handler object stored "
    "per-process (+per-thread override map) with get/set laws; (ii) its "
    "uncaughtException(t, e) either dispatches the DEX body if the handler "
    "is app-provided or implements the RuntimeInit log-then-kill contract "
    "for the built-in one. Generic Thread/runtime law — NOT Compose-"
    "specific; any app with a custom Thread/coroutine crash hook benefits. "
    "NEXT ARMS: identify the ORIGINAL throwable the reporter was reporting "
    "(the worker exception upstream of Llo;.K); verify "
    "Thread.getDefaultUncaughtExceptionHandler call sites in dooz; decide "
    "the kill-process contract against the APP BOUNDARY unwind law.")

for r in rows:
    if r.get('id') == 'F-NEW-271':
        r['status'] = 'ROOT-CAUSED-FIXED'
        r['title'] = ("NULL-ELEMENT REPRESENTATION LEAK (F-265 arm (c) root, "
                      "CLOSED): the CollectionShadow four-store element model "
                      "encoded null elements as kind 2 + \"\" — LOSSY, so "
                      "remove/get/iterator served a fabricated STRING_REF \"\" "
                      "where ART/OpenJDK return typed null; dooz's legal "
                      "CompositionImpl invalidation-queue null (Lnb0.u "
                      "enqueue-current-holder) round-tripped into Lnb0.j and "
                      "killed composeContent at f141 (Lnb0.S pc=185). FIX: "
                      "NULL-ELEMENT KIND LAW (kind 4 = null element) across "
                      "all writers/readers of the four parallel stores.")
        r['root_cause'] = TOTAL_271
        r['evidence'] = EVID_271
        r['probe'] = ("MINIANDROID_F271_COLL_TRACE (add/remove channel with "
                      "live arg kinds + served value, bounded 100), "
                      "MINIANDROID_FIELD_LAW_DIAG (F271-READ/F271-WRITE), "
                      "fcol K19/K20 null-element rows")
        r['verified_current'] = ("CONT-20 at b6ee41e77acb88ec: serve-face "
                                 "flips to typed null x2 dooz runs; fcol "
                                 "K19/K20 PASS with K1-K18 unchanged; anchors "
                                 "18/18 x3 byte-identical; battery equals the "
                                 "recorded green state (f259g 12/13 known L).")
        r['fix'] = ("miniandroid/src/framework/android_shadows.cpp — one law, "
                    "eleven sites: writers lawb_classify_arg, ArrayList.add "
                    "tail, add(index,e), List set face, stream materialize "
                    "-> kind 4 for NULL_REF/zero-ref args (STRING stays "
                    "kind 2); readers lawa_remove_index, lawa_serve_slot, "
                    "slot_to_arg, iterator next, removeAll member_of_other, "
                    "contains -> kind 4 serves typed null. No app-name, no "
                    "package checks, no exception suppression, no PC "
                    "advancement.")
        r['date'] = '2026-10-08'

rows.append(collections.OrderedDict([
    ('id', 'F-NEW-272'),
    ('status', 'CLASSIFIED'),
    ('title', 'THREAD DEFAULT UNCAUGHT-EXCEPTION-HANDLER LAW GAP: the engine '
              'answers Thread.getDefaultUncaughtExceptionHandler() with null '
              '(no law exists), so an app crash-report path executing '
              'UncaughtExceptionHandler.uncaughtException on the null default '
              'handler dies at f141 and the reporter NPE propagates uncaught '
              'to the app boundary (dooz post-F-271 frontier: Llo;.K pc=65).'),
    ('priority', 'P0'),
    ('layer', 'framework/threads + exceptions'),
    ('root_cause', TOTAL_272),
    ('evidence', 'run/cont20/dooz_after (+dooz_after2) at b6ee41e77acb88ec: '
                 'f141-null-recv "Thread$UncaughtExceptionHandler.'
                 'uncaughtException on a null object reference" method=Llo;.K '
                 'pc=65 x2; propagate chain Ltx;.run catch-all -> '
                 'La12;.y no-handler -> MainActivity.onCreate invoke_pc=317 '
                 'APP BOUNDARY; zero UncaughtExceptionHandler references in '
                 'miniandroid/src (grep).'),
    ('probe', 'PENDING: capture the ORIGINAL worker throwable that the '
              'reporter was reporting (one frame above Llo;.K); enumerate '
              'Thread.get/setDefaultUncaughtExceptionHandler call sites in '
              'the dooz DEX; then implement the AOSP RuntimeInit handler law '
              '(non-null default, log-then-kill contract).'),
    ('verified_current', 'registered at binary b6ee41e77acb88ec; anchors '
                         '18/18 x3 MATCH at the same binary.'),
    ('fanout', 'any app using custom Thread subclasses, coroutine exception '
               'hooks, or explicit crash reporters chained onto the default '
               'handler.'),
    ('date', '2026-10-08'),
]))

d['roots'] = rows
json.dump(d, open(REG, 'w'), indent=1, ensure_ascii=False)
print('registry roots:', len(rows))
print('F-NEW-271 ->', by_id['F-NEW-271']['status'] if 'F-NEW-271' in by_id else 'MISSING')
for r in rows:
    if r.get('id') in ('F-NEW-271', 'F-NEW-272'):
        print(r['id'], r['status'])
