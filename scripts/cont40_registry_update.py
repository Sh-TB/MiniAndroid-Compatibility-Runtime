#!/usr/bin/env python3
"""CONT-40 — registry update: R-NEW-549 (the RAF streaming law — the SLURP
ban; telegram's +2.9GB envelope's real face: 36 RandomAccessFile opens over
the 120MB APK slurped and retained = 4.3GB live)."""
import json

PATH = "/home/z/my-project/root_registry.json"
rows = json.load(open(PATH))
ids = {r["id"] for r in rows}

new_rows = [
    {
        "id": "R-NEW-549",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P0",
        "layer": "runtime/memory (java.io.RandomAccessFile law)",
        "date": "2026-10-26",
        "title": "Every RandomAccessFile slurped its WHOLE file and kept it resident forever — telegram's 36 RAFs over the 120MB APK = 4.3GB live (the +2.9GB envelope's real face); the law is now a HANDLE (path + size, streamed reads)",
        "root_cause": "The F-NEW-474 RAF law (bouncy's MultiDex EOCD fix) resolved the path (falling back to the running APK per the single-APK domain law) and SLURPED the whole file via istreambuf_iterator into raf_bytes_[recv] — RETAINED PER RAF, never freed. The attribution trail: [TOPMAP] (the giant blocks born in the FIRST 160K insns: 1024MB between insn 25-30K at Lz/f;.<init>, growing to 2939MB by 120K); the GIANT-ARRAY watch (ZERO giant new-array — the giants are NOT arrays); the LD_PRELOAD malloc interposer (scripts/cont40_giant_malloc.c): 36 x malloc(125829121) = 120MB+1 EXACTLY (the APK size + 1 — the istreambuf assign's +1) = 4.3GB, backtrace = std::string::_M_construct<istreambuf_iterator> <- DalvikExecutionEngine::bridge_to_api <- execute_invoke_direct; the F104-BIGREAD ledger excluded the file:// site (0 hits) — the RAF <init> slurp was the only remaining istreambuf_iterator. Lz/f;.<init>(I) (new long[cap]+new Object[cap]) was DECODED and CLEARED — its ctor allocates sane arrays; the giant mappings were the RAF copies (the ctor correlation was a timing coincidence).",
        "fix": "raf_bytes_ (the slurp map) replaced by raf_paths_ + raf_sizes_: <init> records the resolved path (the single-APK fallback unchanged) + the real file size; length() answers the file size; read/readBytes STREAM the requested span per call (per-call ifstream — RAF reads are rare: the MultiDex EOCD scan + a few KB); read() single-byte streams one byte; read -1 at EOF preserved. Same OpenJDK semantics, zero resident bulk. EFFECT: telegram 12s RSS 2854MB -> 602MB (4.7x), and the interpreter executes ~10x more instructions in the same window (7.1M vs 0.7M by the 12s tick — the 4.3GB malloc pressure was also the throughput brake).",
        "evidence": "REGRESSION WALL at the RAF binary: anchors 6/6 BYTE-EXACT (opencalc 63020bc7 / chess 3f7e6707 / microtimer bbd350b6 / unote 7481e9b4 / tower3d 11a38a5a / dooz 851cc176), games 7/7 EXACT-TO-PIN, negatives 19/19, batch-50 census 50/50 rows with 13/13 content rows BYTE-EXACT RETAINED (evidence/cont40/batch50_census.json). Telegram 22s: 15.4M instructions, still F084 budget-bound at c4;.dispatchDraw (the next gate = the SvgHelper parse-loop throughput), screenshot face unchanged (31ddd4d5b8e6d18e).",
        "honest_frontier": "telegram's first complete painted frame is still beyond the 22s window — the budget now dies in the SvgHelper$ParserHelper.parseFloat loop (the theme-SVG parse, the named throughput lever from CONT-36, now reachable at 10x the prior instruction budget). The dooz board frontier (R-NEW-546) is untouched this wave.",
        "family": "runtime/memory attribution (F-NEW-542 -> R-NEW-547 -> R-NEW-548 -> R-NEW-549)",
    },
]

added = 0
for r in new_rows:
    if r["id"] not in ids:
        rows.append(r)
        added += 1

json.dump(rows, open(PATH, "w"), ensure_ascii=False, indent=1)
print(f"registry {len(rows)-added} -> {len(rows)} (+{added}) id-unique={len({r['id'] for r in rows}) == len(rows)}")
