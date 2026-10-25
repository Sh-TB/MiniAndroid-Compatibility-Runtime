#!/usr/bin/env python3
"""w8_registry_update.py — CONT-29 W1 registry update (no inflation):
F-NEW-520 REGISTERED -> ROOT-CAUSED-FIXED (PriorityQueue claim + laws,
probe 6/6, census crossing wocheneinkauf 0 -> real UI);
F-NEW-521 evidence refined (register evidence; stays CLASSIFIED, probe
honestly still PENDING — no live trigger at this head);
R-NEW-467 REGISTERED (field-resolution memoization throughput law).
"""
import json

PATH = "/home/z/my-project/root_registry.json"
reg = json.load(open(PATH))
by_id = {r.get("id"): r for r in reg}

r520 = by_id["F-NEW-520"]
r520["status"] = "ROOT-CAUSED-FIXED (PriorityQueue claim + heap-family laws)"
r520["evidence"] = (
    "CONT-29 W1 (binary e4da5315cfd95e46): the census face was DECODED "
    "DEX-first — wocheneinkauf Ly7;.a (BreakIterator line-breaking "
    "worklist): PriorityQueue.iterator() at pc 0xe4 answered NULL (the "
    "class was claimed by NO shadow) -> Iterator.hasNext NPE at 0xec. "
    "FIX (generic, java.util family, no app names): CollectionShadow "
    "claims Ljava/util/PriorityQueue; — add/offer (kind-faithful append), "
    "peek/poll (least-element law: all-int-key elements incl. autoboxed "
    "Integer kind-5 -> min value; all-STRING -> lexicographic min; "
    "mixed/app-object -> FIFO head, approximation RECORDED in the law "
    "comment — no shadow-side compareTo), size/isEmpty/clear/contains "
    "(contains unboxes autoboxed-Integer args); iterator() falls through "
    "to the generic Iterable law = array order (OpenJDK: iterator 'does "
    "not traverse in any particular order' — faithful, no sorted law "
    "needed). PROBE fixtures/fnew520_probe (real aapt2/ECJ/D8): 6/6 PASS "
    "(A array-order iteration 30,10,20; B drain 10,20,30 ascending; C "
    "empty poll null; D string min apple/fig; E peek non-removing + poll "
    "removing; F offer/contains/clear). CENSUS CROSSING: wocheneinkauf "
    "0 content px (1 color) -> 1356 colors / 8,579 content px real UI "
    "(evidence/cont29/batch20_census.json); batch-20 at this binary = "
    "5/20 content rows (bouncy 72622 / fossify_math 13071 / calendar "
    "12336 EXACT sha zero-drift; netguard 27059 content-retained minor "
    "delta). Remaining face: S102 compose-locals CNF (proven ART-faithful "
    "decoy, RECURRING_FACES_LAW_SPEC)."
)
r520["priority"] = "P1 (census-crossing wave closed; remaining faces named)"

r521 = by_id["F-NEW-521"]
r521["evidence"] = (
    r521.get("evidence", "") +
    " || CONT-29 W1 REFINEMENT (register evidence, run/w8/dooz_pcreg): "
    "MINIANDROID_PC_WATCH over Lhv0;.d pcs {0x84,0x88,0x9c,0xaa} — 194 "
    "rows: the threshold round-trip is PERFECT at the branch (v2 = "
    "6->5->4 across puts on obj#2418; if-nez correctly branches), but "
    "the maps are ABANDONED after 2-3 puts (o2418 -> o2452 -> o3188 -> "
    "o3211 -> o4372, each fresh map restarting at threshold 6) — the "
    "growth region is unreached because NO map reaches the threshold at "
    "this head (0 hits at 0x9c/0xaa across ~97 watched puts), NOT "
    "because the branch mis-routes. The W7 full-table spin face "
    "(0xFF40000000000000, 8/8 occupied) was the CONT-10-era binary; at "
    "the CONT-28+ head the family signature burns as WALL-CLOCK halts "
    "in the draw window (HALT-HISTO run/w8/dooz_halt: 39x Lt4;."
    "dispatchDraw, wide walks visits=1, zero tight loops — the F-NEW-381 "
    "throughput wall, NOT a spin). Root stays CLASSIFIED (P0 latent): "
    "the growth-on-put route is still unexercised live; the synthetic "
    "trigger needs the dooz APK's own DEX classes (Lhv0;/Lrh0;/Lmg1;) "
    "and cannot be source-built into a probe — the registry's probe "
    "item remains honestly PENDING, re-verification instrument = "
    "MINIANDROID_HALT_HISTO + MINIANDROID_PC_WATCH (both live)."
)

reg.append({
    "id": "R-NEW-467",
    "title": "Field-resolution memoization (interpreter throughput law): "
             "field identity (class/name/type) + the S134 declarer/key pair "
             "are run-invariant per (dex, field_idx); the interpreter "
             "re-derived them on EVERY field access (raw DEX re-parse + "
             "hierarchy chain walk + string concat). PERF-OPS evidence "
             "(60s dooz, MINIANDROID_PERF_PHASES): iget-object 2.29M calls "
             "= #1 burn opcode at ~1.9us each; sget-object ~3.5us.",
    "status": "ROOT-CAUSED-FIXED",
    "priority": "P0 (60% core-structure lever: the F-NEW-381 wall's "
                "dominant named burn)",
    "layer": "dalvik/throughput",
    "fix": "resolve_field memo fast path + FieldMemo bank (res + s134 "
           "decl/fkey) at both success returns; execute_iget/iget_object/"
           "iput/iput_object route through resolved_field_memo (const-ref, "
           "zero-copy on hit); epoch = dex_index ^ super-table size ^ "
           "class-info size folded so ANY mid-run hierarchy growth "
           "(secondary-DEX injection, [EXP095-HIER] extension) "
           "invalidates every memo once. Hit requires res.resolved AND "
           "s134_valid (the res-only bank must never serve an empty "
           "fkey — the first A/B caught exactly that: dooz 851cc176 -> "
           "d602648e anchor collapse, fixed, honest).",
    "evidence": "A/B at the same container: pre-memo 586d15da9b62b692 "
                "vs post-memo e4da5315cfd95e46 (rebuild byte-identical "
                "after source replay). PERF-OPS deltas: iget-object "
                "12.78G -> 8.86G ticks (-30.6%), iget 2.53G -> 1.76G "
                "(-30.5%), iget-wide -26.9%, iput-object -22.2% (top-12 "
                "burn -10.5%). SEMANTIC NEUTRALITY: dooz 851cc176 x3 "
                "byte-identical; anchors 6/6 at pinned faces (opencalc "
                "63020bc7 / chess 3f7e6707 / microtimer bbd350b6 / unote "
                "7481e9b4 / tower3d 11a38a5a / dooz 851cc176); negatives "
                "19/19 (after probe-store regeneration — the 9/19 was "
                "the CONT-158 stale-store artifact, not a regression); "
                "skill selftest 13/13; user goldens 4/4; games battery "
                "6/7 EXACT (g2048 f43face0 / tetris b818a6a7 / "
                "snake_deluxe 5235683f / ttt_deluxe db1d633d / minicraft "
                "e77a073f / gmdice 3891679d) + snakeneon 2617c81c "
                "deterministic x3 IDENTICAL on BOTH arms (pre/post memo "
                "A/B) — the recorded b669ce89 was the CONT-28-container "
                "face; real-content verdict unchanged, zero regressions. "
                "snakeneon shape note: the game's own deterministic "
                "render is stable; face movement across containers is "
                "recorded, not hidden.",
})

json.dump(reg, open(PATH, "w"), indent=1, ensure_ascii=False)
print("registry updated:", len(reg), "roots (837 ->", str(len(reg)) + ")")
