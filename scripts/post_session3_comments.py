#!/usr/bin/env python3
"""Post this session's 3 new milestone comments to issue #8 and read them back."""
import json, ssl, sys, urllib.request

with open("/home/z/.gh_token") as fh:
    token = fh.read().strip()
API = "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime"
ISSUE = 8

COMMENTS = [
"""**FIND-REUSE-005 — WineDroid validate_table law transferred: hostile-header DEX hardening (commit `b6ba545d`)** [implemented, tested]

Second pass over https://github.com/rickbergs/winedroid @ a784c0b (source-level, all 48 files inventoried) found one more transferable safety boundary beyond the MUTF-8/ULEB128 first pass: `dex.rs validate_table` — every section table needs offset≠0, 4-byte alignment, and a checked count×item_size BEFORE allocation, plus `file_size ≥ header_size`.

Transferred as ONE `DexParser::validate_section_table()` gate wired into all 6 section-table readers (string/type/proto/field/method/class_defs — 6 duplicated inline bounds checks collapsed to 1 repair point).

Real defect fixed: a hostile `string_ids_size = 0xFFFFFFFF` allocated ~16 GB of DexStringId BEFORE any bounds math → `std::bad_alloc` crash (reproduced as the discrimination proof: stale objects crash, hardened objects return a named error). Also closed: count>0 with offset=0 (silent header-area misparse), misaligned offsets, file_size < header_size.

Tests: mutf8 battery windows 10→14 (T7 zero-offset, T8 misaligned, T9 OOM guard, T10 header law — all require NAMED errors, no crash, no OOM). Battery 11/11 ALL PASS on clean build. Evidence: `docs/research/REUSE_TRANSFER_MATRIX.md` (WD-003 row), `docs/research/WINEDROID_DEEP_STUDY.md` §mechanism table.""",

"""**§25 dead-code audit — 10,258 LOC of unreferenced experiment chain removed (commit `41946f7c`)** [implemented, tested]

Build/link/test/call-graph proof (no filename-only reasoning): the main binary builds `dex_interpreter_batch.cpp`; the legacy chain had ZERO live references —
- `dex_interpreter.{cpp,h}` (851 LOC): not in any Makefile source list; only orphan `exp003a_main.cpp` included it
- `dex_interpreter_v2.{cpp,h}` (2,012 LOC): zero references in the entire tree
- `dex_interpreter_exp018.{cpp,h}` (2,733 LOC): referenced only by orphan standalone mains (`exp018_main.cpp`, `exp019_main.cpp`, `runtime_integration_exp019.{cpp,h}`) that NO Makefile target builds
- removed together: exp003a_main (476) + exp018_main (1,268) + exp019_main (728) + runtime_integration_exp019 (2,158)

Verification: `make clean` rebuild rc=0; battery **11/11 ALL PASS**; corpus simplestopwatch/gmdice/microtimer exit 0 + screenshots; gmdice run A vs B byte-identical. Binary size unchanged (60,244,136 B — the dead code was never linked; the win is 10,258 LOC of source-maintenance elimination on top of the prior −294). The live interpreter (`dex_interpreter_batch`) and `dalvik_engine` are untouched. Evidence: `docs/research/REUSE_TRANSFER_MATRIX.md` DEAD-001 row.""",

"""**FIND-GRAVITY-VERTICAL FIXED — AOSP LinearLayout main-axis gravity law (commit `d19bdd05`)** [implemented, tested, observed]

The queued P0-9 finding (container gravity centered children horizontally but top-aligned them vertically) is closed with the AOSP law (`LinearLayout.java@1cdfff55` layoutVertical/layoutHorizontal): the container's main-axis gravity now offsets the WHOLE child block when leftover space exists — CENTER_VERTICAL halves it, BOTTOM takes all of it.

Second real bug fixed in the same commit — axis-field equality law: a bare `gravity & 0x50` test misfires on CENTER 0x11 because `0x11 & 0x50 = 0x10`; the first fix attempt pushed the block to the BOTTOM (exposed by the golden analyzer, corrected by masking the axis field first: `& 0x70` / `& 0x7` then equality). The same misfire existed in the horizontal path's cross-axis law — a real F-Droid corpus app (simplestopwatch) had a CENTER-gravity child bottom-aligned; now centered.

Measured evidence:
- helloworld golden **26/26 ALL PASS** with the block truly centered (headline rows 881–945 of 1920); new screenshot SHA256 `87820741706277409bd0163ecad2855f86fcc5ed946b8a3fc6f1448a5fa30392` (re-baseline documented in `docs/evidence/GOLDEN_HELLOWORLD.md`)
- harness repair per §26: the validator's fixed row windows (`band(0,160)`) had ENCODED the buggy geometry — analyzer is now position-independent (full-frame ink-band clustering, density-based text/surface separation, measured ≤6-row split threshold)
- battery 11/11 ALL PASS; corpus: gmdice + microtimer pixel-IDENTICAL (law is opt-in per container), simplestopwatch changed 1,777 px (0.09 %) in exactly one 64×74 px element (diff oracle: `scripts/diff_screenshots.py`)""",
]


def api(url, method="GET", payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"token {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "miniandroid-campaign")
    try:
        with urllib.request.urlopen(req, context=ssl.create_default_context(), timeout=60) as r:
            body = r.read().decode()
            return r.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode(errors="replace")[:200].replace(token, "<tok>")}


posted = []
for i, body in enumerate(COMMENTS, 1):
    status, resp = api(f"{API}/issues/{ISSUE}/comments", "POST", {"body": body})
    if status == 201:
        print(f"POSTED {i}: {resp['html_url']}")
        posted.append(resp["html_url"])
    else:
        print(f"FAILED {i}: HTTP {status} {resp.get('error','')}")
        posted.append(None)

# mandatory read-back
status, comments = api(f"{API}/issues/{ISSUE}/comments?per_page=100")
live = {c["html_url"] for c in comments} if status == 200 else set()
print(f"read-back: issue #{ISSUE} has {len(comments) if status == 200 else '?'} comments")
for i, url in enumerate(posted, 1):
    print(f"comment {i}: {'VERIFIED' if url in live else 'NOT FOUND IN READ-BACK'} {url}")
