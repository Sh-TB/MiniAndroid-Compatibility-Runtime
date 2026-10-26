#!/usr/bin/env python3
"""CONT-38 — registry update: F-NEW-543 (the M3-19 re-entry budget law —
the last same-site re-entry kills released with anchors byte-exact) +
R-NEW-546 (the draw-window census / L0 probe / NEW-WATCH instruments — the
dooz board frontier advanced a level: the board lambda is never CONSTRUCTED)
+ R-NEW-547 (the BOOT-RSS per-stage instrument — the F-NEW-542 envelope
attribution CORRECTED: parse_dex is only +74MB; the bulk accrues during
execute_application, engine-side)."""
import json

PATH = "/home/z/my-project/root_registry.json"
rows = json.load(open(PATH))
ids = {r["id"] for r in rows}

new_rows = [
    {
        "id": "F-NEW-543",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P0",
        "layer": "dalvik/interpreter (M3-19 active-cycle stub semantics)",
        "date": "2026-10-26",
        "title": "The active-cycle stub was a first-re-entry kill, not a recursion bound — upstream-legal reentrant-monitor nestings (compose snapshot advance, nested Looper dispatch) were fabricated to null at their FIRST re-entry",
        "root_cause": "Post-F-NEW-541 the remaining M3-19 kills are same-site same-payload re-entries whose intervening walk is DEEP upstream structure. dooz v23 (run/cont38/dooz_probe2, MINIANDROID_M3_CALLER=1 caller-chain dump — the new env-gated instrument): [M3-19-CYCLE] Lho1;.b(Lf90;)~pc2#532 re-entered (depth=24) with the walk Lho1;.b (snapshot observer-dispatch loop) → Li7;.h → Lto1;.c (CAS invalidation-queue drain) → Lso1;.a → Lww;.i → Lww;.h (the snapshot ADVANCE) → Lkc0;.m → Lho1;.c → the killed b — SEVEN upstream frames. opencalc (run/cont38/opencalc_probe): LN1/d;.b + LN1/g;.b (Lr1/i;+Runnable handler dispatch) re-entered across a NINE-frame walk (LL1/a;.c → Looper dispatch → choreographer → view tree → Runnable → back into the SAME call site pc=44). Both are upstream-legal REENTRANT-MONITOR semantics: compose's snapshot lock (Lho1;.c monitor) and Looper's dispatch are reentrant in ART; the nested dispatch observes the DRAINED state and returns quickly. F-NEW-541 exhausted the argument/site discriminators — site AND payload identical; only the internal drain state differs, invisible to any argument-identity key by construction.",
        "fix": "The per-key ACTIVE-DEPTH map (m3_key_active_depth, thread_local) replaces raw set-membership as the stub trigger: for a COMPLETE-payload same-key re-entry, execute real DEX while the same-key active depth is under the budget (M3_REENTRY_BUDGET=2); stub at depth >= budget. The guard remains the recursion bound it was always meant to be: genuine cycles (the F-017 probe-null shape) still terminate at the budget with the same fabricated-null unwind one frame deeper; the set erases only when the LAST same-key frame leaves (the stale-erase-under-nesting shape is gone). Released re-entries are loudly traced [M3-19-REENTRY]. The env-gated caller-chain dump at the kill site (MINIANDROID_M3_CALLER=1) landed with the law.",
        "evidence": "dooz post-fix: [M3-19-CYCLE] kills 0 (was 1 Lho1;.b + 1 Lo52;.c), [M3-19-REENTRY] 2 releases (Lho1;.b#532 + Lo52;.c) — anchor 851cc1761a1dfcdf byte-exact at 90s AND 600s (rc=0). opencalc anchor 63020bc7334048fe byte-exact. FULL WALL at the final binary: anchors 6/6 BYTE-EXACT (opencalc 63020bc7 / chess 3f7e6707 / microtimer bbd350b6 / unote 7481e9b4 / tower3d 11a38a5a / dooz 851cc176), games 7/7 EXACT-TO-PIN (g2048 f43face0 / tetris b818a6a7 / snake_deluxe 5235683f / snakeneon 2617c81c / ttt_deluxe db1d633d / minicraft e77a073f / gmdice 3891679d), negatives 19/19, reinstall 8/8, skill 13/13, batch-50 census 13/13 content rows BYTE-EXACT RETAINED (evidence/cont38/batch50_census.json).",
        "honest_frontier": "the released dooz re-entry executed real DEX but the board STILL does not paint — the frontier moved a level DEEPER (see R-NEW-546): the board lambda is never CONSTRUCTED (a composition-side stop, upstream of the whole draw chain). The Lo52;.c WindowInsets re-entry (released once) needs its own walk decode if it resurfaces.",
        "family": "M3-19 identity-key family (F-098 → S122 → F-NEW-286 → F-NEW-297 → F-NEW-306 → F-NEW-541 → F-NEW-543)",
    },
    {
        "id": "R-NEW-546",
        "status": "REGISTERED",
        "priority": "P0",
        "layer": "compose-ui/draw (dooz board composition frontier)",
        "date": "2026-10-26",
        "title": "The dooz board draw block (Lz6;) is never CONSTRUCTED — the NavHost destination composition stops before the Canvas{} lambda materializes; four allocation sites identified, none ever executes",
        "root_cause": "Post-F-NEW-543 the draw chain was traced end-to-end with three new env-gated instruments: (1) MINIANDROID_DRAW_WINDOW_TRACE_CAP (the S26 draw-window census, cap env-tunable) — 200K entries across 6 C013 windows: the cascade RUNS (Lpz0;.L0 x1555 / M0 x1769 / Luc0;.g x205 / rc0.e x203 / rc0.c x971 — the block INVOCATION fires 971x for OTHER nodes) but Lz6;/Lmy;/Loc0; = 0 entries; (2) MINIANDROID_L0_TRACE (reads each Lpz0;.L0 receiver's P field live) — 22 of 25 nodes have P=NULL (the InnerNodeCoordinator is created ONLY in Lpz0;.r1, the draw-block installer; nodes without r1 draw as childless arm-2 translations); (3) MINIANDROID_NEW_WATCH (new-instance watch) — Lz6; NEVER allocated in a whole 60s run. METHOD-IN census (1.09M entries, 45s): Lel0;.<init> x90 (90 nodes exist), Lpz0;.r1 x105 (105 installs), Luc0;.<init> x19, Lz6;.<init> = 0. Static decode (the corrected complete length-table scanner, scripts/cont38_scan_exact2.py): Lz6; has exactly 4 new-instance sites — Lcx0;.p(I,Bundle,Lgy0;)Z pc=341 / Le7;.b(Lfw1;,Lgf0;,Lr1;,Lsq;)V pc=0 / Lfn0;.f pc=208 / Lqu0;.q pc=241 — ALL ZERO METHOD-IN entries (never execute); Lcx0; runs its other methods (a/b/c/e/h/i/j/k/o/r) but never p.",
        "fix": "None yet — registered with the full tooling bank. The next wave owns: WHO should invoke the four allocation sites (lambda/virtual dispatch from the destination composable), why Lcx0;.p never runs, and whether the destination composition dies silently (exception swallowed inside the NavHost content lambda) or is never reached (the destination content lambda never dispatched).",
        "evidence": "evidence/cont38/{dooz_drawwin2 stderr census, dooz_l0 L0-TRACE, dooz_nw NEW-WATCH, dooz_mtrace2 METHOD-IN 1.09M}; scripts cont38_disasm_ho1.py / cont38_decode_walk.py / cont38_decode_lt4.py / cont38_decode_el0.py / cont38_decode_pz0.py / cont38_decode_rc0.py / cont38_decode_luc0.py / cont38_decode_ctors.py / cont38_scan_exact2.py; runs run/cont38/{dooz_probe2, dooz_post, dooz_600, dooz_drawwin, dooz_drawwin2, dooz_l0, dooz_nw, dooz_nw2, dooz_mtrace, dooz_mtrace2}.",
        "family": "compose draw/composition frontier (CONT-37's 'destination parent-chain walk' face, now composition-side)",
    },
    {
        "id": "R-NEW-547",
        "status": "REGISTERED",
        "priority": "P0",
        "layer": "runtime/memory (telegram envelope attribution CORRECTED)",
        "date": "2026-10-26",
        "title": "The F-NEW-542 boot-representation attribution is WRONG — parse_dex adds only +74MB; the ~2.7GB accrues DURING execute_application (first ~100K instructions consume ~1.9GB), engine-side, outside DalvikHeap",
        "root_cause": "New per-stage RSS instrument ([BOOT-RSS] in boot_stage, /proc/self/statm resident-pages read — R-NEW-547's first cut misread field 1 = VmSize 5936MB, corrected to field 2 = VmRSS): telegram 12s run (run/cont38/tg_rss2): load_apk 72MB → parse_dex 146MB (+74MB) → initialize_runtime 154MB → load_classes 159MB → execute_application 2869MB (+2710MB) → render 2883MB. The [PROGRESS]/[HEAP-CENSUS] agreement (2852MB at both gates) validates the metric. DalvikHeap census at 50K-insn ticks (run/cont38/tg_hc2): live_objects 10.3K → 13.4K over 14.4M insns — the interpreter heap is NEGLIGIBLE; the bulk is ENGINE-SIDE allocation during the first ~100K instructions (the ContentProvider/init cascade class materialization path — ClassInfo/RuntimeClassInfo/MethodInfo/string-copies per first-touch), NOT the boot-time parse. F-NEW-542's 'GC lever is dead' conclusion STANDS (no unbounded heap growth), but its 'boot-representation bulk' naming does not: the lever is the EXECUTION-TIME engine-side allocation rate (~19KB/instruction during the first 100K insns).",
        "fix": "Instrument landed ([BOOT-RSS], default-on, zero behavior change). The next wave owns: allocation attribution inside execute_application — env-gated per-subsystem counters at the class-materialization/cache sites (ClassInfo materializations, MethodInfo copies, string pools, decode caches) or a heap-profile run (heaptrack/massif) to name the exact 1.9GB/100K-insns allocator.",
        "evidence": "run/cont38/{tg_rss, tg_rss2, tg_hc, tg_hc2, tg_22, tg_60}; the tg_60 60s window was OOM-KILLED by the 3GB sandbox ceiling (rc=137-equivalent) — the envelope holds; tg_22 22s reaches LaunchActivity.onCreate REAL UI draw dispatch (c4;.dispatchDraw, F084 budget-bound, RSS flat 2849MB) — same face as CONT-37.",
        "family": "telegram structural envelope (F-NEW-542 → R-NEW-547 correction)",
    },
]

added = 0
for r in new_rows:
    if r["id"] not in ids:
        rows.append(r)
        added += 1

json.dump(rows, open(PATH, "w"), ensure_ascii=False, indent=1)
print(f"registry {len(rows)-added} -> {len(rows)} (+{added}) id-unique={len({r['id'] for r in rows}) == len(rows)}")
