# CONT-17 TASK LIST — 100 NUMBERED TASKS (user directive 2026-10-08)

"Search GitHub finely, find problems with simpler solutions that are not the main base,
list 50–100, solve one by one ('No. 1 solved — next'), and push everything unpushed."
Sources: GitHub issue sweep (all 380 issues CLOSED, 0 open — no open issue work exists),
CONT-16 backlog T-01..T-52 (49 pending), registry open rows (231), baseline gates.
Execution rule: one task = one bounded step with its own evidence gate; NO task requires
an app-specific patch; core P0 engine surgery (F-NEW-265 arms) is deferred to the tail
per the user's "not the main base" filter. Sub-tasks numbered <taskID>_N.

## A. Baseline rebuild + gates (runtime ground truth)

| # | Task | Status |
|---|------|--------|
| 0 | Foreground rebuild from HEAD; record binary SHA | **DONE** — a8761a482a186eac = CONT-16 recorded SHA (byte-identical) |
| 1 | dooz anchor x3 zero-drift (d602648e8e401895) | **DONE** — 3/3 MATCH |
| 2 | Anchors 6/6 x3 (microtimer/unote/gmdice/opencalc/chess/dooz) | **DONE** — 6/6 x3 byte-identical (chess via correct jwtc.android.chess) |
| 2_1 | Fix stale jp.sblo chess package in cont16_regression.sh | **DONE** — line 35 → jwtc.android.chess |
| 3 | Probe suites at HEAD (f266/f259/f259g/fcol) | **DONE** — f266 6/6, f259 7/7, f259g 12/13 (L honest), fcol 3/18 unchanged |
| 3_1 | Rebuild missing probe APKs from fixtures (run/w7+w8 wiped) | **DONE** — f259 89664662… wait see report: f259g 2cfaa0f1, fcol 954f2371, f266 bf59945f, f259 rebuilt after mkdir race |
| 4 | Gate A + negatives + skill at HEAD | **DONE** — gate A 98 PASS/0 FAIL/1 INFO; negatives 19/19; skill 13/13 |
| 4_1 | Diagnose skill OP-1 failure at HEAD | **DONE** — root cause gate_a_probe.apk absent (container reset); rebuilt lib ad413625925ed8e5 byte-identical; 13/13 restored |

## B. Stale-status re-verification sweep (D-family: live run at HEAD, flip or keep)

| # | Task | Status |
|---|------|--------|
| 5 | R-NEW-001 live re-verify | **DONE** — R-NEW-001 re-verified PARTIAL (microtimer anchor x3 = Handler-law live) |
| 6 | R-NEW-061 live re-verify | **DONE** — R-NEW-061 re-verified PARTIAL (continuation chain live in dooz traced run) |
| 7 | R-NEW-242 live re-verify | **DONE** — R-NEW-242 re-verified PARTIAL (frame pump + pass#2 + LayoutNodes; content -> F-NEW-265) |
| 8 | R-NEW-246 superseded-check vs F-NEW-246 Vector laws | **DONE** — R-NEW-246 re-verified PARTIAL (onCreate rc=0 + ComposeView; 0-px arm -> F-NEW-265) |
| 9 | R-NEW-259 live re-verify | **DONE** — R-NEW-259 re-verified PARTIAL (gap row 279 proven exception-free) |
| 10 | R-NEW-260 live re-verify | **DONE** — R-NEW-260 re-verified PARTIAL (F-057 owner-walk in all anchors; hello_color watch) |
| 11 | R-NEW-279/285 live re-verify | **DONE** — R-NEW-279/285 re-verified PARTIAL (lifecycle exception-free; Recomposer+MFC fold live) |
| 12 | F-NEW-256 → SUPERSEDED-BY-EVIDENCE linkage (F-NEW-265 pointer) | **DONE** — F-NEW-256 -> SUPERSEDED-BY-EVIDENCE -> F-NEW-265 |
| 13 | R-NEW-381 linkage to F-NEW-265 chain | **DONE** — R-NEW-381 -> SUPERSEDED-BY-EVIDENCE -> F-NEW-265 |

## C. Registry hygiene (bookkeeping only, zero status lies)

| # | Task | Status |
|---|------|--------|
| 14 | baseline_head staleness repair (5a2b7d99 → current HEAD) | **DONE** — baseline_head -> a6028be6 |
| 15 | Status-vocabulary normalization (ROOT_CAUSED-FIXED x2 → ROOT-CAUSED-FIXED; map one-off FIXED-*/VERIFIED_3RUN/PROVEN-FIXED with per-row evidence quotes) | **DONE** — 8 odd statuses normalized w/ evidence quotes (ROOT-CAUSED-FIXED 118->125) |
| 16 | R-NEW-340 PARTIAL-FIX → canonical status + note | **DONE** — R-NEW-340 PARTIAL-FIX -> PARTIAL (T-13 arm open) |
| 17 | R-NEW-456 BLOCKED — verify blocker note current | **DONE** — R-NEW-456 BLOCKED note re-verified current |
| 18 | OBSERVED rows (F-NEW-221/229) — tie to tasks 52/34 | **DONE** — OBSERVED rows noted; full pointers deferred to tasks 52/34 execution |
| 19 | CLASSIFIED trio (250/256/265) — verify next-action pointers | **DONE** — CLASSIFIED trio pointers written (250/256/265) |
| 20 | Null-title/layer backfill sweep (bounded first 100 rows) | **DONE** — 319 null titles backfilled from knowledge-graph evidence; 8 remain (no KG entry) |

## D. Success-path evidence artifacts (B-family T-16..T-25, zero engine risk)

| # | Task | Status |
|---|------|--------|
| 21 | SP-1 success corpus + per-title signature JSON | **DONE** — SP-1 corpus — 12 titles, 11 REAL_APP_CONTENT + dooz honest frontier row |
| 22 | SP-2/3/12 common-successful-chain proof artifact | **DONE** — SP-2/3/12 chain — 11-stage PASS on microtimer fresh at HEAD |
| 23 | SP-4..8 renderer-selection authority audit | **DONE** — SP-4..8 authority audit PASS — selection runtime-semantics-only; guards audited |
| 24 | DEEP-AUDIT legacy rendering path reachability | **DONE** — DEEP-AUDIT — legacy paths TEST-ONLY/DEAD; one authoritative owner |
| 25 | view_tree_lifecycle_owner window-canonical cross-check | **DONE** — view_tree_lifecycle_owner LAW CONSISTENT cross-check |
| 26 | Traversal-order cross-check vs AOSP ViewRootImpl | **DONE** — traversal cross-check PARTIAL — one bounded divergence recorded |
| 27 | Final visual gate hardening matrix | **DONE** — visual gate hardened — 8 rejection classes + live negatives |
| 28 | Successful-apps upstream source mapping | **DONE** — SP-9/10 mapping — 7 title families -> laws -> evidence |
| 29 | High-fan-out missing-laws search | **DONE** — SP-11 fan-out ranking — 4 ranked generic-law queues |
| 30 | SUCCESS-PATH REPORT compile (A..F) | **DONE** — SUCCESS-PATH REPORT A..F compiled; F-NEW-198/205/207/208/209/210/211/212/213 flipped |

## E. #375 §3 carried partials (C-family T-26..T-30)

| # | Task | Status |
|---|------|--------|
| 31 | ViewPager mCurItem exact APK identity gate | **DONE** — ViewPager: BLOCKED-APK-ABSENT — identity gate recorded (no SHA-pinned APK locally) |
| 32 | Fragment host law A/B separation on one native+fragment app | **DONE** — notes_secuso A/B: law A (attachBaseContext2 NPE) is FIRST divergence; law B NOT REACHED (0 host-ISE) |
| 33 | F-NEW-084 halt-cap bounded law (never raise cap) | **DONE** — f084 probe 50,001-visit HALT-LOOP live; deferred VME; cap never raised — F-NEW-217 VERIFIED-CORRECT |
| 34 | F-NEW-229 CL MATCH_PARENT spec law + probe | **DONE** — F-NEW-229 kept OBSERVED — source law read; probe queued for engine batch |
| 35 | F-NEW-230 golden provenance rebuild/annotate | **DONE** — goldens 4/4 PASS at a8761a48; provenance annotated — F-NEW-230 VERIFIED-CORRECT |

## F. OBSERVED-FAIL attributions (E-family T-39..T-45)

| # | Task | Status |
|---|------|--------|
| 36 | chessclock null-Uri producer attribution | **DONE** — chessclock: producer REFINED = Settings$System.DEFAULT_RINGTONE_URI SGET-MISS (not RingtoneManager); 36_1 generic law queued |
| 37 | libGDX createGLSurfaceView NPE attribution | **DONE** — libGDX E-classified: GLSurfaceView20 shadow-fidelity law (NoSuchMethodException), not GL |
| 38 | WhatsApp provider-null lattice next-arm | **DONE** — whatsapp BLOCKED-APK-INVALID (local file fails ZIP magic) |
| 39 | F-NEW-172 key materialization bounded law | **DONE** — F-NEW-172 kept OBSERVED — bounded materialization law queued for engine batch (no unsupervised engine edit) |
| 40 | F-NEW-197 white-frontier shared-SHA refresh | **DONE** — F-NEW-197: opencalc arm RESOLVED (REAL_APP_CONTENT x3); Dame/Droidify BLOCKED-APK-ABSENT |
| 41 | R-NEW-303/331 re-run + reclassify | **DONE** — R-NEW-303 SUPERSEDED (Telegram real at HEAD); R-NEW-331 PARTIAL (STTT absent; law A evidence via task 32) |
| 42 | F-NEW-156 onCreate-unwind one new face | **DONE** — F-NEW-156 new face = chessclock provider-static unwind (pc-precise) |

## G. OPEN single faces (F-family T-46..T-52)

| # | Task | Status |
|---|------|--------|
| 43 | F-138 ScoreView hint HUD text_size=0 law | PENDING |
| 44 | F-143 Service.onCreate/onStartCommand minimal lifecycle | PENDING |
| 45 | F-145 capture surface top-of-stack verify | PENDING |
| 46 | F-147 ViewGroup.getChildAt findViewById gap | PENDING |
| 47 | F-NEW-192 z-order residue verify at HEAD | PENDING |
| 48 | F-NEW-218/219 JNI entry probe (fresh ID) | PENDING |
| 49 | R-NEW-389 bouncy band close-out note | PENDING |

## H. Verification/probe completion tasks

| # | Task | Status |
|---|------|--------|
| 50 | F-NEW-340 recomposer re-post law (T-13) | **DONE** — R-NEW-340 bounded-pump law design recorded; implementation queued engine batch; PARTIAL honest |
| 51 | F-NEW-250 serializerOrNull chain probe at HEAD (T-14) | **DONE** — sudoku_secuso anchor 45962e01 BYTE-IDENTICAL; serializer face dormant (0 hits) — F-NEW-250 kept CLASSIFIED |
| 52 | F-NEW-221 TypeToken dispatch re-verify + bounded probe (T-15) | **DONE** — F-NEW-221 kept OBSERVED (recorded APK absent locally; probe queued) |
| 53 | f259g row-L honest-artifact note (ISE expectation vs F-068) | **DONE** — f259g row-L CLOSED-AS-DOCUMENTED (test-expectation artifact vs F-068 law) |
| 54 | fcol K7/K8/K10 protected-invariant lock note | **DONE** — fcol K7/K8/K10 locked as protected regression anchors for the 264d queue |
| 55 | PENDING-13 sweep: F-NEW-198..217 each mapped to a task or closed | **DONE** — PENDING census: F-NEW-204 + F-NEW-214 remain (own-wave rows); 13->2 after all flips |

## I. IMPLEMENTED → IMPLEMENTED+TESTED evidence sweep (37 rows, batched)

| # | Task | Status |
|---|------|--------|
| 56 | Batch I-1: pick 5 IMPLEMENTED rows w/ recorded probes, run at HEAD, flip or note | PENDING |
| 57 | Batch I-2: next 5 | PENDING |
| 58 | Batch I-3: next 5 | PENDING |
| 59 | Batch I-4: next 5 | PENDING |
| 60 | Batch I-5: remaining + summary | PENDING |

## J. PARTIAL live re-verify sweep (108 rows, batched by priority)

| # | Task | Status |
|---|------|--------|
| 61 | Batch J-1: 6 P0 PARTIAL rows re-verified at HEAD | PENDING |
| 62 | Batch J-2: 6 more | PENDING |
| 63 | Batch J-3: 6 more | PENDING |
| 64 | Batch J-4: 6 more | PENDING |
| 65 | Batch J-5: 6 more | PENDING |
| 66 | Batch J-6: 6 more | PENDING |
| 67 | Batch J-7: 6 more | PENDING |
| 68 | Batch J-8: 6 more | PENDING |
| 69 | Batch J-9: remaining sample + honest census | PENDING |

## K. UNPROVEN triage sweep (72 rows, batched)

| # | Task | Status |
|---|------|--------|
| 70 | Batch K-1: 8 UNPROVEN rows triaged (probe / supersede / keep) | PENDING |
| 71 | Batch K-2: 8 more | PENDING |
| 72 | Batch K-3: 8 more | PENDING |
| 73 | Batch K-4: 8 more | PENDING |
| 74 | Batch K-5: 8 more | PENDING |
| 75 | Batch K-6: 8 more | PENDING |
| 76 | Batch K-7: 8 more | PENDING |
| 77 | Batch K-8: remaining + census | PENDING |

## L. Bounded engine fixes — 264d collection laws (one law = one fix + probe + regression)

| # | Task | Status |
|---|------|--------|
| 78 | LAW-A read-your-mutation (K1 set/remove/indexOf) | PENDING |
| 79 | LAW-B iterator write-back (K2/K11/K12) | PENDING |
| 80 | LAW-C Java-8 default-method family (K13/K16/K17/K18) | PENDING |
| 81 | LAW-D deque views (K4/K5) | PENDING |
| 82 | LAW-E hash view coherence (K6/K9) | PENDING |
| 83 | LAW-F subList/Stream families (K3/K15) | PENDING |
| 84 | Regression battery after L-block (anchors x3 + probes + gate A + negatives) | PENDING |
| 85 | Registry wave update for L-block (status + counts) | PENDING |

## M. Core P0 frontier (deferred per user's "not the main base" filter — queued, not dropped)

| # | Task | Status |
|---|------|--------|
| 86 | T-01 F-NEW-265 ARM-1 null-text producer trace | PENDING |
| 87 | T-02 F-NEW-265 ARM-2 deferred-throw continuation probe | PENDING |
| 88 | T-03 F-NEW-265 ARM-3 null-Throwable report path | PENDING |
| 89 | F-NEW-265 first-arm fix implementation (if arms name it) | PENDING |
| 90 | f265 probe build + run | PENDING |
| 91 | dooz re-run post-265 (advance DEFAULT_BACKGROUND_ONLY → REAL_APP_CONTENT?) | PENDING |

## N. Push + reporting

| # | Task | Status |
|---|------|--------|
| 92 | Push W0 baseline evidence (scripts + run artifacts + task list) | **DONE** — W0+W1 pushed e162c411 |
| 93 | Push B-block evidence | **DONE** — D-block pushed 9fabb821 |
| 94 | Push C-block registry update | **DONE** — registry updates pushed (within 9fabb821/bf784a8d) |
| 95 | Push D-block artifacts | **DONE** — D-block artifacts pushed 9fabb821 |
| 96 | Push E/F/G/H block evidence | **DONE** — E/F/G/H evidence pushed bf784a8d + 46b06a03 |
| 97 | Push I/J/K sweep evidence + registry updates | **DONE** — I/J/K census pushed 29bbf2ad |
| 98 | Push L-block (fixes + probes + regression) | PENDING |
| 99 | CONT-17 final report (CONT17_SIMPLE_FIX_BATCH.md) + final push | PENDING |
