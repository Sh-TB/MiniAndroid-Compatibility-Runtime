#!/usr/bin/env python3
"""Post the item-22 wave A + wave C progress comment to issue #354."""
import json, subprocess, sys, os

def gh_token():
    out = subprocess.run(["git", "credential", "fill"],
                         input="protocol=https\nhost=github.com\n\n",
                         capture_output=True, text=True).stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    return None

BODY = """## FINAL CAMPAIGN — item 22 wave A (17-item ADDITIONAL ROOT-CAUSE AUDIT) + wave C (F-NEW-181)

**Scope executed this wave:** the full 15-item additional audit (P0-1..P0-4, P1-1..P1-11) + wave C attribution + gate-law discovery. Commit `b24922ce`. Registry **474 → 484** roots (synced both copies). Worklist 681.

### STATUS TABLE

| ID | STATUS | SOURCE | FIRST DIVERGENCE | FAMILY | FIX | TEST / 3-RUN |
|---|---|---|---|---|---|---|
| P0-1 | **IMPLEMENTED+TESTED** (F-NEW-182) | `inflate_layout_resid` measured pre-attach | DEX onMeasure on unattached tree → windowRecomposer ISE | Compose-in-XML white screen | inflation = tree-only; engine consumes pending attach → attach wave → measure (traversal timing, S43-honoring) | microtimer `da73010a37dd0189` ×3 byte-identical |
| P0-2 | **IMPLEMENTED+TESTED** (F-NEW-183) | `next_window_content_id_++` per lookup | two content parents → split ViewTree | Compose/AppCompat blank | ONE stable content object per window (subtree search → per-window map → materialize-once, edge-dedup) | `[P0-2-CONTENT] REUSED` trace; goldens x3 |
| P0-3 | **IMPLEMENTED+TESTED** (F-NEW-184) | findViewById/getChildAt/getContentView returned generic `View;` | check-cast MaterialButton → CCE | UI construction stops | `real_view_class()` on all 5 bridge sites | goldens x3 |
| P0-4 | **IMPLEMENTED+TESTED** (F-NEW-184) | getContext() labeled `Context;` | `instanceof Activity` FALSE on the activity object | fragment/activity resolution | heap-class resolution via DalvikHeapAdapter | goldens x3 |
| P1-1 | **IMPLEMENTED+TESTED** (F-NEW-185) | setVisibility wrote state only | GONE left stale geometry | stale screenshot family | requestLayout law: layout_dirty raised, canonical traversal re-measures | `[P1-1-VIS]`; goldens x3 |
| P1-2 | **IMPLEMENTED+TESTED** (F-NEW-185) | setImage{Bitmap,Drawable,Icon,URI} = silent void | programmatic images never reached the pipeline | missing images | one canonical drawee state; BitmapStore provenance → real decode; else EXPLICIT BLOCKED | `[P1-2-IMAGE]`/`[P1-2-IMAGE-BLOCKED]` evidence |
| P1-3 | **IMPLEMENTED+TESTED** (F-NEW-186) | `Lcom/google/` blanket gate | bundled Material <init> skipped | partially-initialized widgets | DEX-existence is the authority (hook class-index check) | goldens x3 |
| P1-4 | **IMPLEMENTED+TESTED** (F-NEW-186) | `Lcom.example.MyView;` raw descriptor | class never matched DEX → bare-View fallback | custom XML views | dots→slashes (JVMS §4.2), `$` unchanged | goldens x3 |
| P1-5 | **VERIFIED wave-A** | catch→synthetic fallback | failed render stayed SUCCESS | false SUCCESS | wave-A census verdict law confirmed green | WhatsApp NO_ROOT verdict |
| P1-6 | **IMPLEMENTED+TESTED** (F-NEW-187) | 9 unchecked `stage_render_frame` returns | stale buffer laundered as frame k | false state-change evidence | final-capture skip + `render_ok` manifest bit + oracle diff suppression + `report[render_failures]` | 9 `[P1-6-RENDER]` sites |
| P1-7 | **VERIFIED wave-A** | silent caps | truncation invisible | partial UI as SUCCESS | env budgets + `PARTIAL_RENDER_BUDGET` (acceptance run proven in wave A) | census |
| P1-8 | **VERIFIED wave-A** | placeholders in frame | diagnostic pixels as content | false content | census diag_regions, never painted | dooz `d602648e8e401895` |
| P1-9 | **IMPLEMENTED+TESTED** | setContentView kept old subtree | two active content roots | stale views/overlaps | `detach_from_parent` on both View + res paths | `[P1-9-REPLACE]` |
| P1-10 | **IMPLEMENTED+TESTED** (F-NEW-185) | black-value guessing dropped explicit black | Color.BLACK lost | wrong text colors | provenance law: EXPLICIT_RUNTIME always wins; STYLE_RESOLVED marked at inflate | `[M3-SETTEXTCOLOR] provenance=` |
| P1-11 | **IMPLEMENTED+TESTED** (F-NEW-188) | evaluateJavascript silent drop | JS mutations never ran | blank WebView pages | routed into the REAL S109 QuickJS engine; JSON contract; ValueCallback fires via engine drain; explicit BLOCKED frontier only without a document | `[P1-11-WV]` executed/exception/BLOCKED |

### WAVE C — F-NEW-181 ROOT-ATTRIBUTED
Disassembled the app's own `RegularImmutableMap.get`/`createHashTable` (`run/wavec_get_disasm.txt`): the compiled probe **re-masks** every step — in-bounds by construction; exits = key match or sentinel. New **permanent SPIN-GET probe**: `table byte[3] sentinels=0 occupied=3` (FULL → livelock structural); all 3 slots → offset 0 → `alternating[0] = o1659 Integer(33604)` — **the exact F-NEW-173 placeholder**; `size=17750, tableSize=3` (chooseTableSize(17750) must be 32768) + builder-growth alternating (47,425 = 31,616×1.5+1). **F-NEW-181 = the F-NEW-173 family**: upstream key/size materialization. NEXT: trace the tableSize feed into createHashTable — one instrumented run.

### GATES + EVIDENCE LAWS
- dooz `d602648e8e401895` ×3 · simplestopwatch `10446aaf0cd642cc` ×3 · microtimer `da73010a37dd0189` ×3 · headingcalc `be1cea9cf994b26a` ×3 (stash-rebuild A/B: old-HEAD byte-identical — the 17 fixes are pixel-neutral; the previous 4d46… record was stale evidence) · WhatsApp `31ddd4d5b8e6d18e` ×3 (PARTIAL, F-016 honesty — the DI-lattice frontier).
- NEW GATE LAW (F-NEW-189): goldens require a FRESH data root — simplestopwatch persists elapsed time via SharedPreferences; reused data-root lawfully renders the restored state (`88377dd…`). Both states byte-identical ×3 on the same binary.

### REMAINING
- WhatsApp frontier: F-NEW-173/181 placeholder-materialization family (tableSize feed trace).
- Item-21 P1-2: full measure/layout single-truth unification (inflate-time measure already removed this wave).
- Phases 4-20: 6 closed (6/7/16/17/18/19), 7 advanced (5/8/9/11/12/13/15), 4 pending (4/10/14/20).
"""

def main():
    token = gh_token()
    if not token:
        print("NO TOKEN"); sys.exit(1)
    body_file = "/tmp/fc22_comment.md"
    open(body_file, "w").write(BODY)
    r = subprocess.run([
        "curl", "-s", "-X", "POST",
        "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/354/comments",
        "-H", f"Authorization: token {token}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({"body": BODY}),
    ], capture_output=True, text=True)
    try:
        resp = r.json()
        print("posted:", resp.get("id"), resp.get("html_url"))
    except Exception:
        print("FAIL", r.stdout[:300])

if __name__ == "__main__":
    main()
