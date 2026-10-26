#!/usr/bin/env python3
"""CONT-39 — registry update: R-NEW-548 (the memory-attribution instrument
bank + the TYPED ARRAY BACKING structural change + the telegram giant-block
frontier registration)."""
import json

PATH = "/home/z/my-project/root_registry.json"
rows = json.load(open(PATH))
ids = {r["id"] for r in rows}

new_rows = [
    {
        "id": "R-NEW-548",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P0",
        "layer": "runtime/memory (heap array representation + attribution bank)",
        "date": "2026-10-26",
        "title": "Heap arrays stored every element as an \"array[N]\" string key in the per-object fields map (~110-140B map-node+key overhead per element) — replaced with a dense typed DalvikValue vector behind the same field-name API; plus the memory-attribution instrument bank that falsified two standing theories and named the giant-block frontier",
        "root_cause": "HeapObject.fields is an unordered_map<string,DalvikValue>; arrays stored EVERY element as a synthetic \"array[N]\" key — a 1MB byte[] cost ~140MB of map nodes. Telegram's startup (SVG/SQLite/crypto/network buffers) materializes MB-scale arrays. The attribution trail (all instruments now in-tree): [BOOT-RSS] per-stage (statm VmRSS — the first cut misread field 1 = VmSize) — parse_dex +74MB only, the bulk accrues during execute_application; [ENGINE-MEM] mallinfo2 — in-use ~255-350MB vs total-mapped 4.5GB (mallinfo2 covers ONLY the main arena — the worker-thread arenas are invisible, so the in-use reading misled); [MALLOC-TRIM] — malloc_trim(0) recovered only 11MB (falsifies the free-list-churn theory); [SMAPS] /proc/self/smaps_rollup — Private_Dirty = Anonymous = 2890MB (ALL LIVE DATA, not churn); [SMAPS top-mappings] — 13 anonymous mappings, #0 = 2939.0MB CONTIGUOUS rw-p + 1489.5MB + 1024.0MB (a few GIANT live blocks, trim-immune — the top is pinned by a live allocation), growth window = the SvgHelper$ParserHelper parse loop (RSS 2052→2339→2850MB across the 300-400K-insn ticks, parseFloat/advance/read cycling at the same pcs).",
        "fix": "HeapObject gains {is_array, array_length, array_store: vector<DalvikValue>}; set_field/get_field parse the \"array[N]\" shape and route to the dense store (unset = REGISTER_UNSET semantics preserved; grow-on-write; the F-NEW-385 zero-init law now writes the vector instead of len map nodes); the length channels (__array_length__/__new_array_length__) stay ordinary map fields (one entry per array, zero behavior change); all 184 engine call sites unchanged (the API is the adapter). REGRESSION WALL at binary 48ab86dbac8015b8: anchors 6/6 BYTE-EXACT (opencalc 63020bc7 / chess 3f7e6707 / microtimer bbd350b6 / unote 7481e9b4 / tower3d 11a38a5a / dooz 851cc176), games 7/7 EXACT-TO-PIN (g2048 f43face0 / tetris b818a6a7 / snake_deluxe 5235683f / snakeneon 2617c81c / ttt_deluxe db1d633d / minicraft e77a073f / gmdice 3891679d), negatives 19/19, reinstall 8/8, skill 13/13 — zero drift.",
        "honest_frontier": "the telegram RSS envelope (2.85GB) was NOT moved by the array change — the giant blocks are NOT the heap arrays. The frontier is now named precisely: a ~2.9GB LIVE contiguous anonymous block (+1489MB +1024MB siblings), trim-immune, growing during the SvgHelper parse window — the next wave owns catching the allocator in the act (per-tick top-mapping size watch correlated with the PROGRESS method lines, then a decode of the SvgHelper$ParserHelper parseFloat loop and the Path/point storage it feeds). The k occupier is live data, so the 60s+ telegram windows stay sandbox-bound until it is cut.",
        "family": "runtime/memory attribution (F-NEW-542 → R-NEW-547 → R-NEW-548)",
    },
]

added = 0
for r in new_rows:
    if r["id"] not in ids:
        rows.append(r)
        added += 1

json.dump(rows, open(PATH, "w"), ensure_ascii=False, indent=1)
print(f"registry {len(rows)-added} -> {len(rows)} (+{added}) id-unique={len({r['id'] for r in rows}) == len(rows)}")
