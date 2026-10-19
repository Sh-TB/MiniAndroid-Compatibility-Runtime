#!/usr/bin/env python3
"""cont106_registry_update.py — CONT-106 batch wave registry changes.
F-NEW-445: refresh CLASSIFIED -> ROOT-CAUSED-FIXED (root = F-NEW-446 gate).
F-NEW-446: S123-CLINIT-MAT over-broad gate (new, ROOT-CAUSED-FIXED).
F-NEW-447: ROOT-059 null-recv shadow routing intercepts pre-NPE (OPEN_GAP, probe row ready).
F-NEW-448: chess Toolbar height=0 (l/m3.a static theme-dimension never resolved, OPEN_GAP).
F-NEW-449: telegram play_billing n2.r aget-oob @0x568 decode (OPEN_GAP, fixture lever named).
"""
import json

REG = "root_registry.json"
MIRROR = "canonical/root_cause_registry.json"

new_roots = [
    {
        "id": "F-NEW-446",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P0",
        "title": "S123-CLINIT-MAT fired on HEALTHY classes: the shared-geometry static materialization gate (`attempted || stored_null`) invented Paint/RectF/Rect/Point objects for statics that a COMPLETED <clinit> deliberately left null, defeating app null-sentinel guards (issue #364 CONT-106 batch, fixture-first).",
        "layer": "framework (dalvik_engine sget static-field materialization law)",
        "root_cause": "S123's documented purpose was failed-clinit recovery (forkgram he1$d → AndroidUtilities.rectTmp, clinit ABORTED mid-way), but its gate fired on ANY attempted-or-stored-null static of the four whitelisted types. Live telegram PRE (run/cont105/tg_pre.log): o6.<clinit> result=OK (1736 sputs) — k0/m0/u1 are deliberately owned by the lazy factory o6.P(Context) (single u1 writer across all 4 dexes; callers o6.R / Cells.r4.<init> / CheckBoxSquare.<init>, none executed pre-crash) — yet [S123-CLINIT-MAT] materialized o6.k0/m0 on first sget → o6.k's own `sget k0; if-nez k0,+3; return-void` guard (classes3.dex 0x0..0x8) fell through → iput-boolean xj0.Y:Z on the never-factory u1 → uncaught NPE @o6.k pc=46 (engine pc = insn index of 0x5c). JVMS/AOSP: a completed clinit that leaves a static object null means the app owns the first assignment — sget MUST return that null.",
        "fix": "Gate tightened to failed_clinit_classes_ (the F-NEW-215 evidence map) — S123 now fires ONLY for a genuinely FAILED <clinit>, exactly its original intent. Probe fixtures/cont106_clinitsentinel (c106a, real aapt2/ECJ/D8, sha16 fe29697e17cbc6c4): PRE on frozen afaad5bd4f56f9d3 — [C106-SENTINEL] guardEscaped=true (AOSP false), [C106-INVOKE2] result=NO-EXC (AOSP NPE), 3 S123 firings; POST at f72413b74525d3b0 — guardEscaped=false, zero healthy-class firings, failed-clinit materialization retained (Broken.rectTmp clinit_failed=true), [C106-FACTORY] true. Real-app POST (run/cont106/tg_post.stderr, 12511 lines): S123 count 0; o6.k executes with REAL factory Paints (F298-SETCOLOR recv=6740/6747 @pc=13/24), xj0.<clinit> OK, xj0.Q invoked — the iput-null NPE face is GONE; run advances to LaunchActivity.onCreate invoke_pc=1375 and terminates on the known F084 wall-clock pacing family only. Regression: wall 12/12 byte-identical (dooz d602648e / opencalc f25b754c / unote 90a67cc1 / microtimer bbd350b6 x3), goldens 4/4, negatives 19/19 (after documented container-fresh probe repair: gate_a_probe rebuilt 628ce8e8… + canonical install+run), reinstall 8/8, MG-310 7/7, MG-150 3/3, skill 13/13, F-NEW-376 70/70, c104i 4/4, c74esc 5/5 — ZERO DRIFT.",
        "evidence": "run/cont106/{c106a_pre2.stderr,c106a_post.stderr,tg_post.stderr,battery.log} + scripts/cont106_scan_u1.py + scripts/cont106_scan_P.py + scripts/cont106_scan_k.py (androguard xrefs) + fixtures/cont106_clinitsentinel",
        "registered_wave": "CONT-106",
        "registered_date": "2026-10-19",
    },
    {
        "id": "F-NEW-447",
        "status": "CONFIRMED_OPEN_GAP",
        "priority": "P2",
        "title": "ROOT-059 null-recv shadow routing intercepts before the AOSP NPE: unguarded invoke-virtual on a never-assigned static Paint (Never.k0b.setStrokeWidth) returns NO-EXC — a separate pre-existing law routes null receivers of shadow methods to the shadow silently (issue #364 CONT-106 batch; probe row ready).",
        "layer": "framework (invoke null-receiver routing vs AOSP NPE parity)",
        "root_cause": "Probe row [C106-INVOKE2] (fixtures/cont106_clinitsentinel): after the F-NEW-446 gate closes the sget-time materialization, the invoke-time face still returns NO-EXC — stderr shows `[ROOT-059] null-recv routed to shadow law: Landroid/graphics/Paint;.setStrokeWidth`. On ART the same call raises NullPointerException (receiver is genuinely null). ROOT-059 is an old, load-bearing routing law (unknown fan-out across the corpus); changing it in the same wave as F-NEW-446 would conflate two variables, so it is recorded as its own root with the probe row already in place.",
        "fix": "PENDING fixture-first next wave: A/B the ROOT-059 routing set, decide the law (NPE parity for app DEX receivers vs shadow routing for framework-owned receivers), flip probe expectation to NPE after the fix.",
        "evidence": "run/cont106/c106a_post.stderr (ROOT-059 line + INVOKE2 row) + fixtures/cont106_clinitsentinel",
        "registered_wave": "CONT-106",
        "registered_date": "2026-10-19",
    },
    {
        "id": "F-NEW-448",
        "status": "CONFIRMED_OPEN_GAP",
        "priority": "P1",
        "title": "Chess (jwtc 298) boots with f141=0 (CONT-104 family closed) but the appcompat Toolbar measures to height 0: onMeasure reads static I Ll/m3;.a twice and gets 0 — the R8 static that should carry the theme-derived action-bar default height never received its value (issue #364 CONT-106 batch).",
        "layer": "framework (theme dimension resolution → static action-bar height law)",
        "root_cause": "run/cont106/chess_post.stderr: [DEFAULT-MEASURE] Toolbar overrides_onMeasure=1; Toolbar.onMeasure pc=0 sget Ll/m3;.a value=0 (x2) then setMeasuredDimension via superclass chain → Toolbar (0,0 1080x0) unrendered. The static holds the resolved action-bar default height upstream (obtained from the theme's ?attr/actionBarSize / abc_action_bar_default_height_dimension during appcompat init); on MiniAndroid nothing populates it, so the toolbar collapses. Deferred-but-handled faces in the same run: F275-SVCINFO g.h0, F-NEW-219 makeOptionalFitsSystemWindows, R350-FORNAME kotlin-reflect ReflectionFactoryImpl, 371-GETXML-NOTFOUND — all caught; the height-0 static is the visible root.",
        "fix": "PENDING fixture-first: minimal probe reading a theme attr (actionBarSize) into a static then measuring a Toolbar-like view; generic law = populate the dimension static from the resolved theme TypedValue at appcompat init (no app-specific patch).",
        "evidence": "run/cont106/chess_post.stderr (DEFAULT-MEASURE + SGET l/m3.a value=0 + C013-CUSTOMVIEW 1080x0)",
        "registered_wave": "CONT-106",
        "registered_date": "2026-10-19",
    },
    {
        "id": "F-NEW-449",
        "status": "CONFIRMED_OPEN_GAP",
        "priority": "P1",
        "title": "Telegram play_billing n2.r (protobuf-lite MessageSchema builder) aget-oob 'length=11; index=11' boundary decoded: rotated-loop boundary read at 0x568 re-indexes the Field[]/String[] entries array (v24) one past its length after `add-int/lit8 v4, v10, 1` (issue #364 CONT-106 batch; CONT-104 U3 carry).",
        "layer": "framework (reflection metadata array construction vs walk-count agreement)",
        "root_cause": "Androguard decode (scripts/cont106_scan_n2r.py, run/c106/n2r_scan.txt, classes.dex): n2.r (s2 t1 t1)n2; is 597 insns; the walk resolves String entries via n2.B(Class,String)→Field then Unsafe.objectFieldOffset (n2.<clinit> seeds k=sun/misc/Unsafe). The OOB face is the loop boundary: 0x564 add-int/lit8 v4, v10, 1 → 0x568 aget-object v29, v24, v10 with v10 == v24.length. The entries array (v24, length 11) and the walk count disagree — the array is built from one metadata source while the loop bound derives from another (MessageInfo count). Engine reflection must answer IDENTICAL counts for both sources (getDeclaredFields-family laws).",
        "fix": "PENDING fixture-first (c106b, next wave): probe two count sources over the same class (getDeclaredFields().length vs the count protobuf derives) and assert agreement; then the generic fix targets whichever reflection law disagrees.",
        "evidence": "run/c106/n2r_scan.txt (n2.r 0x4d6..0x570 window + n2.<clinit>) + CONT-104 ledger U3 decode",
        "registered_wave": "CONT-106",
        "registered_date": "2026-10-19",
    },
]

d = json.load(open(REG))
roots = d if isinstance(d, list) else d.get("roots", [])
have = {r["id"] for r in roots}
added = []
for nr in new_roots:
    if nr["id"] not in have:
        roots.append(nr)
        added.append(nr["id"])

# F-NEW-445 refresh: CLASSIFIED -> ROOT-CAUSED-FIXED (root identified as F-NEW-446)
for r in roots:
    if r["id"] == "F-NEW-445":
        r["status"] = "ROOT-CAUSED-FIXED"
        r["fix"] = ("CLOSED VIA F-NEW-446 (CONT-106): the root was the engine's S123-CLINIT-MAT "
                    "over-broad gate materializing o6.k0/m0 on first sget of a healthy-clinit class, "
                    "defeating o6.k's `if-nez k0 → return-void` sentinel. Decode completed this wave: "
                    "o6.u1 single writer = static factory o6.P(Context) (sput-object in P); P callers = "
                    "o6.R / Cells.r4.<init> / CheckBoxSquare.<init>; o6.k callers = o6.P (post-assignment, "
                    "safe) and o6.n1 (unguarded). With the F-NEW-446 gate, telegram POST runs the REAL "
                    "factory chain (k0/m0 real Paints, xj0.<clinit> OK, xj0.Q invoked) and the iput-null "
                    "NPE @o6.k pc=46 is gone — run advances to LaunchActivity.onCreate invoke_pc=1375, "
                    "terminating only on the known F084 pacing family.")
        r["evidence"] = "run/cont106/tg_post.stderr + scripts/cont106_scan_{u1,P,k}.py + fixtures/cont106_clinitsentinel"

json.dump(roots, open(REG, "w"), indent=1, ensure_ascii=False)

m = json.load(open(MIRROR))
have_m = {r.get("id") for r in m}
for nr in new_roots:
    if nr["id"] not in have_m:
        m.append({k: nr[k] for k in
                  ("id", "title", "status", "priority", "layer", "evidence",
                   "registered_wave", "registered_date")})
# mirror status refresh for 445
for r in m:
    if r.get("id") == "F-NEW-445":
        r["status"] = "ROOT-CAUSED-FIXED"
json.dump(m, open(MIRROR, "w"), indent=1, ensure_ascii=False)

ids = [r["id"] for r in roots]
ids_m = [r.get("id") for r in m]
assert len(ids) == len(set(ids)), "main id-unique violated"
assert len(ids_m) == len(set(ids_m)), "mirror id-unique violated"
print("added:", added)
print("main:", len(roots), "mirror:", len(m))
