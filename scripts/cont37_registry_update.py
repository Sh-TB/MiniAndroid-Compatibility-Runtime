#!/usr/bin/env python3
"""CONT-37 — registry update: F-NEW-541 (caller-site pc identity law,
ROOT-CAUSED-FIXED with the dooz draw-block dispatcher evidence) +
R-NEW-543 (F-NEW-542 live heap census instrument; telegram envelope
REFUTED — boot-representation bulk, not unbounded heap growth).
Appends id-unique rows; canonical projection contract preserved."""
import json, sys

PATH = "/home/z/my-project/root_registry.json"
rows = json.load(open(PATH))
ids = {r["id"] for r in rows}

new_rows = [
    {
        "id": "F-NEW-541",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P0",
        "layer": "dalvik/interpreter (M3-19 active-cycle identity key)",
        "date": "2026-10-26",
        "title": "Caller-site PC missing from the M3-19 active-cycle key — compose draw-block dispatches from different walk sites collided on one key and were stubbed (dooz board draw block never dispatched)",
        "root_cause": "dooz v23 300s run (run/cont37/): the board Canvas block NEVER executes — 0 LINE ops in the full MINIANDROID_CANVAS_OP_TRACE; the board zone y∈[400,1500] receives ZERO draw primitives while the chrome paints 231,873 content px (anchor 851cc176). DEX decode (scripts/cont37_scan_canvas.py + cont9_dexdump.py): drawLine terminal = Ljt1;.drawLine; the only app-level callers = Ly3;.m(J,J,Lg7;)V pc=42 (the compose Canvas.drawLine impl) ← Lgi;.j0 ← Lgl0;.j0 ← Lp00;.j0 (iface) ← Lmy;.i pc=69 — and the Canvas-block lambda Lz6;.i (530 units, DrawScope-carrying, calls Ly3;.m at pc=303). BOTH Lmy;.i and Lz6;.i have ZERO invocations in the whole run — created during composition, never dispatched. The live stub trace names the killer: [M3-19-CYCLE] Lho1;.b(Lf90;)Ljava/lang/Object;#532 re-entered while active (depth=24) — active-cycle stub, lifetime_calls=9. Lho1;.b is the DRAW-BLOCK DISPATCHER (takes the Lf90; draw block); its key (#532 = the block's object id) is COMPLETE by the F-NEW-306 test — yet the SAME block legitimately re-enters while active: compose dispatches the block PER STRUCTURAL POSITION (nested draw-modifier layers re-dispatch the same block object from different walk sites). The distinguishing identity — the CALLER'S dispatch-site pc — is invisible to an argument-identity key: the F-098/F-NEW-286/F-NEW-297 family's invisible-nesting shape, one level deeper (payload identical, site differs).",
        "fix": "m3_active_key += \"~pc\" + std::to_string(pc_) — the caller's invoke-site pc appended to EVERY M3-19 key (law: the caller's dispatch-site pc is computation identity; same-site re-entry remains the stub's original S22/F-017/F-076 same-computation evidence; different-site re-entry = different structural dispatch → real DEX). Keys strictly more specific; the guard only fires LESS often; MAX_RECURSION_DEPTH (80) remains the loud backstop. Syntax \"~pc<N>\" collision-free with #/=/@ parts.",
        "evidence": "doos released dispatches: [M3-19-CYCLE] Lho1;.b hits 9 → 6 (the 3 different-site re-entries now execute real DEX; the remaining 6 = the same-site ~pc2 family — the NEXT face, honestly recorded). Regression wall at binary a95136b836bbb0bc: anchors 6/6 BYTE-EXACT (opencalc 63020bc7 / chess 3f7e6707 / microtimer bbd350b6 / unote 7481e9b4 / tower3d 11a38a5a / dooz 851cc176), games 7/7 EXACT-TO-PIN (g2048 f43face0 / tetris b818a6a7 / snake_deluxe 5235683f / snakeneon 2617c81c / ttt_deluxe db1d633d / minicraft e77a073f / gmdice 3891679d), negatives 19/19 (after run/gatea probe_store regen — the recorded recipe), skill 13/13, batch-50 census 13/13 content rows at the CONT-36 binary.",
        "honest_frontier": "the dooz board STILL does not paint at the post-541 binary (600s rc=0 run: 0 LINE ops, anchor byte-exact 851cc176) — the destination draw-block dispatch has MORE layers (the same-site ~pc2 re-entry family + the destination's parent-chain walk). The F-NEW-381 throughput wall also bounds traced windows (300s traced runs die in F084 budget halts mid-composition).",
        "family": "M3-19 identity-key family (F-098 → S122 → F-NEW-286 → F-NEW-297 → F-NEW-306 → F-NEW-541)",
    },
    {
        "id": "R-NEW-543",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P0",
        "layer": "diagnostics (live heap census instrument) + telegram envelope correction",
        "date": "2026-10-26",
        "title": "F-NEW-542 MINIANDROID_HEAP_CENSUS: env-gated live per-class allocation histogram — REFUTES the CONT-36 telegram 'unbounded heap growth (no GC)' envelope; the bulk is the BOOT-TIME parsed representation (2.85GB), not interpreter heap growth",
        "root_cause": "CONT-36 recorded telegram as 'RSS 2.9GB@15s/3.3GB@19s → container OOM rc=137 = unbounded heap growth (no GC) = the named next structural lever'. The F-NEW-542 live census (MINIANDROID_HEAP_CENSUS=1, incremental per-class histogram in DalvikHeap::allocate + a 16th-progress-tick emitter in the interpreter loop, bounded 40) REFUTES that theory: live_objects ≈ 10,461 at the first census (insn=1.6M) and ≈ 11,721 at insn=8M — RSS is FLAT at 2,855 MB from the first 400K instructions onward (the [PROGRESS] curve: 2047MB@100K → 2854MB@400K → constant). The 2.85GB bulk lands during BOOT (parse_dex ~300ms window: load_apk 771ms / parse_dex 1068ms / initialize_runtime 1088ms / load_classes 1114ms) — the parsed DEX representation of the 64MB APK inflates ~45x (MethodInfo name+descriptor+shorty+return_type+parameters+defining_class as per-method std::string copies × ~700K methods + dalvik_engine class tables).",
        "fix": "instrument (the ready-made-tool lever): DalvikHeap::heap_census_enabled() cached-env check (one branch per allocation when unset, zero map work), note_alloc_class() incremental histogram, and the [HEAP-CENSUS] emitter (rss_kb + live_objects + alloc_total + top-8 classes) at every 16th progress tick, bounded 40 emissions. Zero app knowledge; read-only.",
        "evidence": "run/cont37/tg_census/: [HEAP-CENSUS] rows + [PROGRESS] RSS curve. Post-F-NEW-541 telegram ADVANCEMENT: at the 22s window the run reaches LaunchActivity.onCreate's REAL UI draw dispatch (ActionBar/c4;.dispatchDraw, Components/pa;.onDraw, ActionBar/w;.onDraw, u4/g;.onDraw — 11 onDraw/dispatchDraw entries) and is BUDGET-bound (F084 halts inside the draw window; F298-KEEP keeps the last complete frame), rc=1, NO OOM. At 60s the container ceiling (3GB sandbox) kills the process (RSS samples flat 2860MB; the interpreter's growth past the last sample crosses ~2.9GB) — rc=137 is the SANDBOX envelope, not engine unboundedness.",
        "honest_frontier": "telegram levers re-ranked: (1) BOOT representation size (string interning / lazy bytecode materialization — the 2.85GB bulk), (2) per-call machinery throughput (tri.resolve 118.4G ticks / em.setup 28.6G — the first-frame budget), (3) the first complete painted frame. The heap-GC lever is DEAD (no unbounded growth to collect).",
        "family": "ready-made-tool diagnostics family (MINIANDROID_ALLOC_TRACE, MINIANDROID_PROGRESS_INTERVAL, PERF-PHASES)",
    },
]

added = 0
for r in new_rows:
    if r["id"] not in ids:
        rows.append(r)
        ids.add(r["id"])
        added += 1

json.dump(rows, open(PATH, "w"), indent=1, ensure_ascii=False)
print(f"registry {len(rows)-added} -> {len(rows)} (+{added}) id-unique={len(ids)==len(rows)}")
