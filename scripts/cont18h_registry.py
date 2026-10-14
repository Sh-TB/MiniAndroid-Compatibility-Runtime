#!/usr/bin/env python3
"""CONT-18h registry update.

1. F-NEW-270 ROOT-CAUSED-FIXED: ROOT-059 route domain law (framework-only
   null-receiver routing). Live proof: dooz Lhv0.h->Lhv0.d wrong-site NPE
   eliminated at f882ca1832b955e3; ART NPE now at the true invoke site
   (Lnb0.S pc=185); anchors 18/18 byte-identical; full battery green.
2. F-NEW-265 evidence append: arms (a)+(b) VERIFIED at HEAD (deferred-throw
   aborts the throwing frame; catch-handler receives the real in-flight
   throwable via EXC-PROPAGATE), with live dooz trace pointers.
3. F-NEW-271 CLASSIFIED: composition invalidation field corruption —
   Lnb0 (CompositionImpl) instance o2838's field j (:Lqb0 invalidation
   holder) reads as STRING_REF/0 (alien type) — the iget-object guard
   family misses STRING_REF/0, the chained Lqb0.e read answers null, and
   the Lhv0.h invoke dies at f141. Root of F-265 arm (c).
"""
import json, collections

REG = '/home/z/my-project/root_registry.json'
d = json.load(open(REG), object_pairs_hook=collections.OrderedDict)
rows = d['roots']
by_id = {r.get('id'): r for r in rows}

TOTAL_270 = """ROOT-059 ROUTE DOMAIN LAW VIOLATION — FIXED. The S113 ROOT-059 law routes a null-receiver invoke on a shadow-claimed class to the shadow's materialization law instead of the ART NPE. It was built for PLATFORM classes (androidx WindowInsets chain). But ViewShadow's EXP-060 claim heuristic accepts ANY class that is not framework-prefixed ('could be a View subclass'), so claims_class() answered TRUE for every R8-obfuscated app class (dooz Lhv0; = a LongSet). The ungated route then (a) executed real DEX bodies with this=null — the exact wrong-site-exception disease F-141 eliminated (dooz face: Lhv0;.h self-calls Lhv0;.d; iget NPE fired at pc=17 INSIDE the callee instead of the ART NPE at the invoke site; the multi-NPE cascade killed CompositionImpl.composeContent), and (b) silently swallowed a paired null-receiver h() put with no exception at all. The route also existed ONLY at invoke-virtual 35c (5 other f141 sites never routed) — format-inconsistent. FIX: f141_is_framework_class() prefix allowlist (Landroid/, Landroidx/, Ljava/, Ljavax/, Lkotlin/, Lkotlinx/, Lcom/google/, Lorg/xmlpull/, Lorg/json/) gates the claims_class route; non-framework classes keep the ART-faithful throw. Caller identity added to the ROOT-059 log line."""

EVID_270 = "Live at be95a47f797d3d99 (pre-fix) run/cont18h/dooz_f265: [ROOT-059] routed Lhv0.h+Lhv0.d (user class) -> SYNTH-EXC iget-null-recv method=Lhv0;.d pc=17 inside callee -> cascade -> APP BOUNDARY. Post-fix run/cont18h/dooz_f270: zero ROOT-059 routes; f141-null-recv fires at the TRUE site (Lnb0;.S pc=185, message 'Lhv0;.h on a null object reference'); anchor d602648e8e401895 byte-identical x3. Regression at f882ca1832b955e3: anchors 18/18, fcol 18/18, f259 7/7, f259g 12/13 honest, f266 6/6, f268 12/12, negatives 19/19, reinstall 8/8, skill 13/13."

TOTAL_271 = """COMPOSITION INVALIDATION FIELD CORRUPTION (F-265 arm (c) root): Lnb0 (CompositionImpl, 'Reentrant composition is not supported' + 'Compose:recompose') instance o2838 reaches its composeContent path S(I,I,Object,Object) with field j (:Lqb0 invalidation holder, fidx 5585) holding an ALIEN-TYPED value STRING_REF/0 — not NULL_REF, not an Lqb0 object. Chain: iget-object v2 <- j (pc=0xa3) answers STRING_REF/0; the guard family (f141_is_null_receiver covers NULL_REF/OBJECT_REF-0/INT32-0) does NOT cover STRING_REF/0, so the chained read iget-object v4 <- v2.e (pc=0xb2, :Lhv0 field) skips the null-receiver law and answers NULL_REF; invoke-virtual Lhv0.h on it (pc=0xb9=185) then dies at f141 — uncaught cascade -> Lzs.m measure unwind -> blank frame. Bytecode side PROVEN coherent (cont18h disasm): both Lqb0 construction sites (Lnb0.S pc=0xf9/0x394) run the real <init> (TRI-F040 o3108/o3131 with healthy inner Lhv0.<init>+Arrays.fill chains), v11=new->invoke-direct->iput v11->j register-coherent; Lqb0.<init> unconditionally iputs a fresh Lhv0 into e (pc=0x3b, fidx 6617). So the corruption is engine-side state: either a wrong-typed default (R-NEW-414 initializer-materialization family / bare-vs-qualified field-key split-brain F-NEW-251) wrote STRING_REF/0 into j, or o2838's own construction path never stored j. NEXT ARMS: (i) heap-dump o2838 fields at the failing iget (extend F141-DIAG with source-object heap dump); (ii) audit the R-NEW-414/F-NEW-251 store keys for single-letter R8 fields; (iii) verify which Lnb0 owns the two healthy Lqb0 constructions."""

rows.append(collections.OrderedDict([
    ('id', 'F-NEW-270'),
    ('status', 'ROOT-CAUSED-FIXED'),
    ('title', 'ROOT-059 route domain law (FIXED): the f141 null-receiver shadow-materialization route was ungated — any shadow-claimed class routed, and ViewShadow\'s EXP-060 heuristic claims every non-framework class — so R8-obfuscated app classes (dooz Lhv0; LongSet) executed real DEX bodies with this=null (wrong-site NPE inside the callee) and silently swallowed a paired null-receiver put; route also existed only at invoke-virtual 35c. Fix = f141_is_framework_class() prefix allowlist gating the route; ART-faithful throw for non-framework classes; caller identity in the route log.'),
    ('priority', 'P1'),
    ('layer', 'dex/exceptions + framework/shadow-claim-domain'),
    ('evidence', EVID_270),
    ('probe', 'run/cont18h/dooz_f265 (pre-fix face) vs run/cont18h/dooz_f270 + dooz_f270b (post-fix); scripts/cont18h_regression.py battery; scripts/cont18h_newinst_xref.py + cont3_disasm_full.py source-first chain proof'),
    ('verified_current', 'fixed at binary f882ca1832b955e3; anchors 18/18 x3 byte-identical (d602648e8e401895, da73010a37dd0189, 4f1a9e4e8f64fae8, f3b483fe7b7cf51b, a976d2f9fb675cb3, b5a7a35d5fe0564b); full probe battery green at the same binary'),
    ('fanout', 'every R8-obfuscated Compose app: any null-receiver invoke on a user class previously executed the callee with this=null'),
    ('date', '2026-10-08'),
]))

rows.append(collections.OrderedDict([
    ('id', 'F-NEW-271'),
    ('status', 'CLASSIFIED'),
    ('title', 'COMPOSITION INVALIDATION FIELD CORRUPTION (F-265 arm (c) root): Lnb0 (CompositionImpl) o2838 field j (:Lqb0 invalidation holder) carries an alien-typed STRING_REF/0 — outside the f141_is_null_receiver domain (NULL_REF/OBJECT_REF-0/INT32-0) — so the chained Lqb0.e read skips the null law and the Lhv0.h invoke dies at f141, uncaught, killing composeContent (Lzs.m measure unwind, blank frame). Bytecode proven coherent; both Lqb0 constructions healthy; corruption is engine-side state (R-NEW-414 initializer-default / F-NEW-251 field-key split-brain families suspected).'),
    ('priority', 'P0'),
    ('layer', 'dex/fields + compose/invalidation'),
    ('evidence', 'run/cont18h/dooz_f270b: [F141-DIAG] Lnb0;.S pc=185 regs v2:t5/o0 (STRING_REF/0 in the j slot), v4:t8/o0; [TRI-F040] Lqb0;.<init> o3108/o3131 with healthy Lhv0;.<init>+fill chains; disasm (scripts/cont3_disasm_full.py + cont18h raw decode): Lnb0.S pc=0xf9/0x394 new-instance + real <init> + iput register-coherent; Lqb0;.<init> pc=0x3b iput fresh Lhv0 -> e unconditional. Issue: only two healthy constructions exist while o2838.j holds no Lqb0 — the store/read state split requires a heap-dump probe.'),
    ('probe', 'PENDING: extend MINIANDROID_F141_DIAG to dump the receiver source-object heap entry (all fields+types) at the failing iget; then audit scan_init_field_defaults/materialize_init_default store keys for single-letter R8 fields'),
    ('verified_current', 'registered at binary f882ca1832b955e3; anchors 18/18 x3 MATCH at the same binary (no drift while registering)'),
    ('fanout', 'every Compose app whose composition reaches the invalidation-record path on a composition instance whose j field was never DEX-initialized'),
    ('date', '2026-10-08'),
]))

# F-NEW-265 evidence append (arms a+b verified at HEAD)
f265 = by_id.get('F-NEW-265')
if f265:
    ap = (' CONT-18h pointer 2026-10-08: arms (a)+(b) VERIFIED at HEAD (binary be95a47f797d3d99/f882ca1832b955e3) — deferred-throw aborts the throwing frame (throw_deferred + frame_unwind + try_recursive_invoke caller-side catch search) and catch handlers receive the REAL in-flight throwable ([EXC-PROPAGATE] lines with live NPE messages in run/cont18h/dooz_f265); the recorded "deferred-throw continues the throwing frame" face is gone. The first death face has MOVED off Lm7 null-text (that ctor never fired this run) to the ROOT-059 bypass (F-NEW-270, fixed) and then to F-NEW-271 (j/e field corruption — the arm-(c) root). Lzs.m still unwinds at depth 17 in the live trace, confirming the measure-pass death persists at HEAD.')
    f265['evidence'] = (f265.get('evidence') or '') + ap
    f265['verified_current'] = (
        'CONT-18h: arms (a)+(b) verified live at HEAD; arm (c) re-rooted to F-NEW-271; '
        'measure-pass death (Lzs.m depth-17 unwind) still reproduced at be95a47f797d3d99/f882ca1832b955e3; '
        'historical chain link-by-link proof at aed46450/d701221b stands.')

d['total_roots'] = len(rows)
d['total'] = len(rows)
json.dump(d, open(REG, 'w'), indent=1, ensure_ascii=False)
print('registry rows:', len(rows))
print('F-NEW-270:', by_id_ok := ('F-NEW-270' in {r['id'] for r in rows}))
print('F-NEW-271:', 'F-NEW-271' in {r['id'] for r in rows})
