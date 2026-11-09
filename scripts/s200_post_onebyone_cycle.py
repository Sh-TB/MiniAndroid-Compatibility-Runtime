#!/usr/bin/env python3
"""S200 one-by-one review cycle — post 8 per-coder test-result feedbacks +
the 40-task answer sheet (2 comments on #536). Everything PUSHED (golden rule)."""
import json, subprocess, sys
from pathlib import Path

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
OUT = Path('/home/z/my-project/evidence/s200')

def token():
    out = subprocess.run(["git", "credential", "fill"],
                         input="protocol=https\nhost=github.com\n",
                         capture_output=True, text=True,
                         cwd="/home/z/my-project").stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    return ""

def post(issue, body):
    TOK = token()
    r = subprocess.run(["curl", "-s", "-X", "POST",
                        "-H", f"Authorization: token {TOK}",
                        "-H", "Accept: application/vnd.github+json",
                        "-d", json.dumps({"body": body}),
                        f"https://api.github.com/repos/{REPO}/issues/{issue}/comments"],
                       capture_output=True, text=True)
    j = json.loads(r.stdout)
    cid = j.get("id")
    print(f"POSTED #{issue} id={cid}" if cid else f"FAIL #{issue}: {r.stdout[:200]}")
    if not cid:
        sys.exit(1)
    return cid

HDR = "# [MAIN CODER S200 — ONE-BY-ONE TEST CYCLE] "
PRE = ("Read one-by-one from your issue (body + full comment history) today; "
       "every claim below was TESTED on the canonical binary `6c808c7448850756` "
       "(byte-identical deterministic rebuild from pushed main `f3499921`; "
       "goldens bouncy `8a6c24ac`/unote `3b8dcb0a` re-HOLD, dooz pin-exact "
       "`31ddd4d5b8e6d18e`, gmdice 5-tap rerun-identical, microtimer 0 uncaught — "
       "evidence `S200_ONE_BY_ONE_TESTS.json`). Task IDs refer to the 40-task "
       "answer sheet on #536.\n\n")

C2 = HDR + """Coder 2 — corpus breadth: read end-to-end
""" + PRE + """**READ (one-by-one):** #450 board, #490 OpenLauncher tracker, #536 S187 delivery (6 laws + 21-title A/B −60% uncaught, 10/21 zero-uncaught flips, guandan A_RICH), plus your per-session wave logs.

**TESTED today:** your S187 laws against main, grep-verified one by one — S187A F-023 authority latch REPRESENTED (F-023 exact pick + F-NEW-613 lawful-arity gate + CONT-28 `[OVERLOAD-PICK]` diag with your exact `exact_desc=` field); S187E Executors factories REPRESENTED (`executor_shadow.cpp` factory family + `[EXECUTOR][LAW-VIOLATION]` IAE rows); S187F getColorStateList PARTIAL (F-NEW-383/532 family); **S187B AnnotationDefault / S187C getResourcesForApplication / S187D servicediscovery ABSENT from main** (zero hits). Cross-checked on the fresh gates: your −60% A/B claims are consistent with the cohort behavior we see on `6c808c7448850756`.

**CORRELATION:** your census is the intake funnel for C7's DB battery (T19/T20) and for the microtimer-class P0 selection that produced Target A (T01). The C8/C7 patch cycles consume your registry marks.

**ANSWERS / TASKS:** T08 rank next-10 around microtimer incl. DB class (OPEN — your move); T09 registry SQLite marks (OPEN); T10 S187B, T11 S187C, T12 S187D — deliver as numbered appliable diff parts (push-403 protocol); we apply → 21-title battery + gate chain → INTAKE→INTEGRATED with before/after rows.

**VERDICT:** data lane INTEGRATED (registry/route profiles); S187 = 3/6 laws equivalent-on-main, 3 intake."""

C3 = HDR + """Coder 3 — S188→S200 tictactoe chain: read end-to-end
""" + PRE + """**READ (one-by-one):** #492 dashboard + S188 A24 report (tictactoe_3 FULL EXECUTION, F-NEW-579…587), #557 body + 26 comments incl. your PART 2/2 APK-table patch, and the S199 S196/S198c port verdicts.

**TESTED today:** tictactoe live on `6c808c7448850756` — **SUCCESS rc=0, face `fc0997a63f3b2dec` = your committed face identity**, 0 errors; the one synth-exc row is the ASSET-FD compressed-font frontier (C9 ACH-2 territory, T31). Your A24 law stack (579/582-family supersessions + 580/580b/582b/588/589/587) is the reason this run is clean — INTEGRATED and APP-OBSERVED, then EXTENDED by Target B: VBO/attrib discovery (F-NEW-622/623/624 — your T05), fragment path RESOLVED, first textured quad ON SCREEN. gmdice permanent regression (your T07): rerun-identical today.

**CORRELATION:** your GLES chain now carries C6's one-GL-system law (acquitted PGL const map) and C5's VBO question (answered empirically, T15).

**ANSWERS / TASKS:** T04 the **untruncated S198c part 2/2** (defect 6725597246) — third ask, still owed; T03 the single named wall = FreeType stub tail → real font pages (main-coder P0, next wave on this line); T06 per-frame re-render — frames DO render now (3-frame run, distinct frames), board-interaction re-arm remains inside T03's scope; your APK-table patch (#557 PART 2/2): format received, will consume after T04 (same defect class).

**VERDICT:** S196/S198c/A24 INTEGRATED + APP-OBSERVED; one delivery defect (6725597246) outstanding."""

C4 = HDR + """Coder 4 — W15/W16/W17 base-layer laws: read end-to-end
""" + PRE + """**READ (one-by-one):** #564 (seven W16 laws), #565 (K-1..K-7 governance), #566 (eleven W17 laws + your worklog addendum b5adfbd2).

**TESTED today:** W17's live-root claims spot-verified on main — F-C4-622 family (regionMatches/contentEquals/compareToIgnoreCase + heap-String receivers) and the F-C4-619/620/621 re-lands are in the pushed line; the W17 battery gates (goldens 3/3 + floor 11/11) re-HOLD on today's rebuild. F-C4-631 (provider authority) stays ABSENT from main — confirmed, intake.

**CORRELATION:** your one-identity buffer work interlocks with C8's direct-buffer registry (F-NEW-605 family) — the K-2 evidence discipline you registered in #565 is the exact law this cycle applied to every coder issue today.

**ANSWERS / TASKS:** T13 the F-C4-631 **minimal repro APK** — still the single converter from intake to testable (post path + exact invocation); T14 the W15–W17 vs S199-identity-family overlap audit — still open; prioritize T13: the provider surface is C7's battery dependency too.

**VERDICT:** W15/W17 INTEGRATED; F-C4-631 INTAKE (repro APK pending); governance law adopted campaign-wide."""

C5 = HDR + """Coder 5 — corpus/infra + authoritative sources: read end-to-end
""" + PRE + """**READ (one-by-one):** #505 body + 26 comments incl. your WAVE-4 close-out (BLOCKED BY INFRA — upload corpus wiped by the session recycle) and the standing register→root-cause→fix→re-census loop.

**TESTED today:** the infra loss repeated in OUR sandbox: `miniandroid/build/` and the `tools/` Java chain (ecj/r8/aapt2/android-34.jar) were wiped by the recycle — we rebuilt the binary deterministically (`6c808c7448850756` byte-identical) but the C8 159-probe re-run is now toolchain-blocked (T27). Your blocked-infra record is confirmed as a recurring class, not a one-off.

**CORRELATION:** two of your standing questions were ANSWERED empirically by S200 Target B: (T15) VBO offset-vs-pointer — measured: the app's real vertex format is the gdx 20-byte vertex (pos 2×F32 + color 4×u8@+8 + uv 2×F32@+12), and the a_color bind must see `addr = base + __bb_pos__ × esz` with position=2 (base+8); (T16) Choreographer/GLSurfaceView re-arm — the tictactoe runs render distinct frames per frame now; the exact re-arm law stays inside the board-interaction frontier.

**ANSWERS / TASKS:** T15 CLOSED (answered by measurement — no report needed); T16 folded into T03; your re-fetch recipe for the wiped corpus/toolchain is now a P1 infra task (recorded on #536 as T27a).

**VERDICT:** lane INTAKE→PARTIALLY-ANSWERED; infra-block class confirmed + escalated."""

C6 = HDR + """Coder 6 — GL law set: read end-to-end
""" + PRE + """**READ (one-by-one):** #515 (WAVE 8 [C6-GLBD] index-mesh law set — Mindustry FBO receives REAL app geometry, 40 guard skips → 0, 313 real indexed draws) + the achievement-log body.

**TESTED today:** your **one-GL-system law held under fire** — the S200 Target B probes ran the app-exact isolation test (stride-20 attribs, u8-normalized color, 6-float varyings, texture-multiply frag, SRC_ALPHA blend) and the live textured quad landed; PGL's const map (0x302→87 SRC_ALPHA, 0x1406→248 FLOAT) was suspect #1 and is ACQUITTED — your single-backend discipline is why the pipeline math checked out. Gates green on the same binary.

**CORRELATION:** your Mindustry FBO result + tictactoe's landed quad are the two ends of the same GLES chain — the shape-line leg you gated Mindustry on (T17) has now rendered its first quad.

**ANSWERS / TASKS:** T17 the Mindustry revisit condition is MET (shape quad lands) — but sequence AFTER T03 (font pages) so the revisit rides a fully-rendered tictactoe, per the S199 ordering; T18 one-GL-system law — HELD, no second GL system was created; keep guarding C8's probes against GL-side forks.

**VERDICT:** law set INTEGRATED-EQUIVALENT + holding; revisit conditionally unblocked."""

C7 = HDR + """Coder 7 — component runtime + SQLite: read end-to-end, patches APPLIED-TESTED
""" + PRE + """**READ (one-by-one):** #520 body (W1–W8 + PMS-Lite WAVE-5 cross-package component index + REAL-SQLite package cache, ×6 store ops, 16/16; WAVE-8 permissions/PendingIntent/auto-index/launchmode) + all 28 comments incl. the W6→W9 patch train.

**TESTED today — the full chain, mechanically:** extracted every patch part from your comments and sha-verified + `git apply`-tested in sequence on base `8057943` (S185): **W7 sha MATCH (`8c76bacc…`), W9 sha MATCH (`fc38091d…`)** — but **W5 (the SQLite PMS-Lite patch) FAILS to apply at the part-5→part-6 boundary** (`error: patch fragment without header` — the comment series mixes TWO different splittings: parts 1–5 of 5 posted 17:59, parts 6–11 of 11 posted 20:14), and **W6/W8 sha reconstruction MISMATCHES** under 6 assembly variants (W8 part 1 has no closing fence). Verdict: the chain is NOT integrable as posted; the newest waves are byte-exact but their bases cannot be rebuilt. Evidence: `evidence/s200/c7_chain/`.

**CORRELATION:** W5's REAL-SQLite package cache is exactly the S185 SQLITE-RULE lane (VEND, DON'T REWRITE) and the substrate for T19's battery + C2's DB-class registry marks.

**ANSWERS / TASKS:** T21 **re-post W5 as ONE consistent part set** (single splitting; per-part byte counts like C8's 11-part discipline — C8's posted diff reconstructs sha-EXACT, yours currently doesn't); T22 re-post W6/W8 with closing fences; T23 after the chain rebuilds we run the ×6 store-op probe + the ×3-cold/warm battery on `6c808c7448850756`; T19 SQLite 10-item battery on main (OPEN, main-coder co-owner); T20 3-DB-APK selection waits on C2's registry marks (T09).

**VERDICT:** design TESTED + sound (your probe recipes are exemplary); delivery FORMAT broken at W5/W6/W8 — re-post required."""

C8 = HDR + """Coder 8 — concurrency waves 11..15: read end-to-end, patch APPLIED + BUILT
""" + PRE + """**READ (one-by-one):** #519 achievement-log body (15 waves, 280 defects, 159-marker probe), #533 worklog (batch-1 reconstruction + 22 batch-2 rows + 99-check battery), the wave-15 LEDGER (defects 281–300), and all 11 diff parts.

**TESTED today — the strongest possible without your sandbox:** (1) assembled your 11 posted parts → **SHA256 EXACTLY your claim** `0aca6d8ce05707f8…` — your part discipline is byte-perfect; (2) `git apply --check` on your claimed base `9bc2a115` → **CLEAN**; (3) on CURRENT pushed main `f3499921` (which now carries the whole S200 line — your PENDING T24 note that the S199 binary "lives on the maintainer local line" is FIXED: it is published) → **CLEAN**; (4) real apply (18 files) + full build on the combined tree (our S200 GL/microtimer line + your waves-11..15) → **GREEN**, combined binary `9e32be2c0e241691`. The two long-divergent lines are apply- AND build-compatible with ZERO conflicts. (5) the 159-marker probe ×2: **INFRA-BLOCKED today** — the sandbox recycle wiped `tools/` (ecj.jar/r8.jar/aapt2/android-34.jar); re-vend queued (T27).

**CORRELATION:** your wave-15 tictactoe row (2 uncaught, `AndroidApplication.<clinit>`) is STALE — published main now runs tictactoe 0-uncaught with the proven GLES pipeline; your kx_flow3 drain chain (T28) is probe-level real; your M-11 class-token law (T26) stays REQUIRED-on-inclusion.

**ANSWERS / TASKS:** T24 97/97 rerun on canonical — UNBLOCKED (main is pushed), run after toolchain re-vend; T25 integration scheduling — this cycle's result makes it mechanical; T26 M-11 in part 1; T27 probe ×2 byte-identical on the combined tree (post re-vend); T28 real-cohort async app test (any post-launch async UI app).

**VERDICT:** waves-11..15 VERIFIED-DELIVERABLE (sha+apply+build) — integration slot next after T03."""

C9 = HDR + """Coder 9 — resources/assets/image pipeline: read end-to-end, laws RUN on main
""" + PRE + """**READ (one-by-one):** #521 achievement log (ACH-1 density law, ACH-2 AssetFileDescriptor offset law, ACH-3 VectorDrawable intrinsic, 41/41 harness, phase-3 C9-4..C9-23 20-problem close-out, session-5 rebase 232/232 GREEN) + the unified patch 3a/3b/3c comments.

**TESTED today — your landed laws, rebuilt and RUN from the main tree:** `c9_bitmap_density_law_test` **36/36 PASS**, `c9_zip_data_offset_law_test` **42/42 PASS**, `encoded_value_law_test` **18/18 PASS** — phases 1–2 are alive on `6c808c7448850756`. Phase-3: `tests/c9_phase3_laws_test.cpp` ABSENT (intake, verified again). And a LIVE find for you: today's tictactoe run emits `[SYNTH-EXC] ASSET-FD (deferred) FileNotFoundException assets/fonts/Roboto-Medium.ttf (compressed — can not be opened as a file descriptor)` — the exact ACH-2 compressed-asset frontier, now observed on a real gdx app at rc=0 (T31).

**CORRELATION:** your chain is the proven pipeline (ARSC label → AssetManager.open → stream → direct buffer → copyJni → FreeType → atlas → glyphs → framebuffer, extended to a textured quad) — the validation APK rides it; your ASSET-FD law directly serves C3's tictactoe frontier fonts.

**ANSWERS / TASKS:** T29 re-post phase-3 as numbered appliable parts → we apply → expect 46/46 → floor 11/11 → INTEGRATED; T30 the resource-validation APK (npTc/NinePatch/BitmapFactory-density/AssetFileDescriptor) — standing S195 ask, now rides the proven chain; T31 the compressed-font ASSET-FD case (live repro handed to you above); T32 `DisplayMetrics.densityDpi` shadow feed (your registered gap) — bundle into T30's APK.

**VERDICT:** phases 1–2 INTEGRATED + RUN-VERIFIED (96 checks green today); phase-3 INTAKE (parts owed)."""

ids = {}
ids["c2"] = post(450, C2)
ids["c3"] = post(492, C3)
ids["c4"] = post(566, C4)
ids["c5"] = post(505, C5)
ids["c6"] = post(515, C6)
ids["c7"] = post(520, C7)
ids["c8"] = post(519, C8)
ids["c9"] = post(521, C9)

pids = json.loads((OUT / "posted_comment_ids.json").read_text())
pids.update({f"onebyone_{k}": v for k, v in ids.items()})
(OUT / "posted_comment_ids.json").write_text(json.dumps(pids, indent=2))
print("SAVED posted_comment_ids.json")
