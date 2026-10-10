#!/usr/bin/env python3
# cont41_registry.py — CONT-41 registry update: F-NEW-303 (the AOSP
# Notification$Builder fluent-chain object law — the CONT-38v recorded
# tananaev frontier). Dedup-checked append, standing conventions.
# ID NOTE: F-NEW-302 is deliberately SKIPPED — the standing frame-loop
# probe from CONT-40 is named fnew302 (fixtures/fnew302_probe); reusing
# the number for a root would make every battery line ambiguous.
import json, collections

P = '/home/z/my-project/root_registry.json'
d = json.load(open(P))
ids = {r.get('id') for r in d['roots']}
assert 'F-NEW-303' not in ids, 'F-NEW-303 already present — dedup check'

entry = {
  "id": "F-NEW-303",
  "title": "Notification$Builder fluent-chain law: every framework Notification$Builder set*() answered the STUBBED void instead of THIS, so the androidx NotificationCompat wrap chain wrote NULL into the builder field and the next chained call NPE'd (NotificationCompat$Builder.<init> pc=64 'setSmallIcon on a null object reference'); build() likewise could not return a Notification",
  "status": "ROOT_CAUSED_FIXED",
  "priority": "P1",
  "layer": "dex/notification-builder-object",
  "root_cause": "PROVEN BY PRE/POST A/B on the recorded CONT-38v frontier (evidence/cont38v/FRIEND_CLAIM_VERIFICATION.md §4: com.tananaev.calculator v1.10 vc11 294a68bd00debbdc = PARTIAL with 1 uncaught NPE 'setSmallIcon on a null object reference' at NotificationCompat$Builder.<init> pc=64 → MainActivity.onCreate died at invoke_pc=29 → frame DEFAULT_BACKGROUND_ONLY d602648e8e401895 ×3). The androidx NotificationCompatBuilder wraps a framework Landroid/app/Notification$Builder;: new-instance allocates the object (execute_new_instance allocates for ANY class), but with no bridge law EVERY fluent setX() fell to the STUBBED void → the DEX move-result-object wrote NULL → the stored-field chain NPE'd. AOSP law (frameworks/base Notification.java, API 21+ fluent convention): every public set*() (and addAction/addPerson/addExtras/extend) returns THIS (@NonNull); build() returns a non-null Notification. Same §12 family as the S83 AudioAttributes$Builder and F-NEW-296 LineBreakConfig$Builder laws.",
  "fix": "ONE generic bridge law in dalvik_engine.cpp bridge_to_api (inserted after the MediaPlayer block, before the F-NEW-296 LineBreakConfig law): for class_name == Landroid/app/Notification$Builder; — <init> → honest void (the object is already allocated by new-instance); method starting with 'set' or addAction/addPerson/addExtras/extend → result = args[0] (fluent THIS); build() → allocate a fresh Landroid/app/Notification; heap object (marked __from_builder__) and return it. Plus the Landroid/app/Notification; <init> honest-void contract. Keyed on the framework class descriptor — zero app knowledge, no name matching, no app branches. The one deprecated void setter (setLatestEventInfo) is harmless to answer fluent-this (void methods are never move-result'd — verifier-illegal). The Notification object is carried opaquely (a headless runtime presents no notification UI — the OBJECT law is what app flow depends on).",
  "synthetic_probe": "fixtures/notif_builder_probe (com.probe.notif, real toolchain aapt2/ECJ/D8, 8 rows): NB-01 both ctor forms non-null, NB-02 chained fluent setters return THIS (reference identity), NB-03 build() non-null + distinct per call, NB-04 builder stays fluent AFTER build(), NB-05 the NotificationCompat-style WRAPPER face (field-stored builder, fluent setters across methods — the exact real-APK mechanism), NB-06 void-context setters honest no-crash, NB-07 distinct builders stay distinct (identity law), NB-08 the deprecated direct new Notification() ctor non-null. PRE ×3 on the pre-law binary d3d6a5412a696122: 28/28 markers (NB-02 NPE, NB-03/04/05 build/wrapper faces dead — every row consistent ×3) → POST ×3 on e1fc1915e88fe2a8: 56/0 (8/8 rows PASS ×3).",
  "evidence": "evidence/cont41/FRIEND_PACKAGE_AUDIT.md (the full friend-package claim matrix); runs run/cont41/pre/{nb_r1..3,tanana_r1..3} + run/cont41/post/{nb_r1..3,tanana_r1..3}; scripts/cont41_pre.sh + cont41_post.sh; friend-package source material upload/cont41_audit/ (COMPLETE_KNOWLEDGE_TRANSFER.md + knowledge_transfer_document.md — the friend's 'F-NEW-253' analog, verified by CONTENT per the standing directive).",
  "not_claimed": "The tananaev frame remains DEFAULT_BACKGROUND_ONLY d602648e8e401895 ×3 after this law — the honest frontier ADVANCES from 'uncaught NPE kills MainActivity.onCreate (FAILURE, Errors=1)' to 'PARTIAL SUCCESS, Errors=0, next blocker = FragmentTransaction.commit REC-MISS (MainActivity.onCreate hosts a platform PreferenceFragment — DEX strings confirm Landroid/preference/PreferenceFragment; + addPreferencesFromResource)'. This wave does NOT claim the app renders: the Fragment/Preference family (the friend's 254/255/256 chain — pending-op drain, addPreferencesFromResource inflation, preference tag mapping WITHOUT the fixed-geometry symptom hacks) is the recorded next wave. NotificationChannel/notification PRESENTATION (Channel/notify rendering) stays out of scope (no display surface); only the object law is claimed.",
  "regression": "binary e1fc1915e88fe2a8 (POST): anchors 8/8 ×3 BYTE-IDENTICAL (dooz 31ddd4d5b8e6d18e, microtimer da73010a37dd0189, unote 4f1a9e4e8f64fae8, gmdice f3b483fe7b7cf51b, opencalc a976d2f9fb675cb3, tttdeluxe af6094295ecb50e3, flappycow 13cf47464d9787f4, g2048 59ca1526611c4622); composeStopwatch 3442d9a9dc0fa0f9 ×3; battery == CONT-28..40 records EXACTLY (fcol 140/0, f259 49/0, f259g 84/7-known, f266 42/0, f268 96/0, fnew253 147/0, fnew286 10/0, fnew289 28/0, ckey 105/0 (=15 rows ×7 logs), cpipe 119/0 (=17 rows ×7), fnew302 48/24 documented, fnew252 56/0, fnew290..297 == records, fnew298 19/0 KEEP=5 corner=PASS); simplecalc ×3 rc=0 7960bce447ac6d8f. PRE gate re-baselined first at d3d6a5412a696122 with the SAME results (24/24 + 3/3 + battery + control) after restoring the session environment (probe APKs rebuilt; microtimer data-root unblocked by moving a root-owned empty runtime/ dir aside). ZERO DRIFT."
}

d['roots'].append(entry)
d['total'] = len(d['roots'])
sc = collections.Counter(r.get('status') for r in d['roots'])
d['status_counts'] = dict(sorted(sc.items()))
d['meta']['last_update'] = ("CONT-41 session 2026-10-10: friend-package source-level audit — claim matrix closed "
                            "(7 REUSE-already-present incl. 2 with CONT-38v probe proofs, 2 REJECT-unsafe, "
                            "1 NOT-IN-PACKAGE, 1 genuinely missing → F-NEW-303 the Notification$Builder fluent-chain "
                            "law; notif_builder_probe 8/8 ×3 PRE→POST; tananaev frontier FAILURE→PARTIAL 0 errors; "
                            "zero drift). Registry 610→611 (302 skipped: standing probe name).")
d['generated'] = 'CONT-41 session'
json.dump(d, open(P, 'w'), indent=1, ensure_ascii=False)
print('roots now:', len(d['roots']), '| total field:', d['total'])
print('F-NEW-303 appended; status_counts:', sc.get('ROOT_CAUSED_FIXED'), 'ROOT_CAUSED_FIXED')
