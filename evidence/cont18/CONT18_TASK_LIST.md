# CONT-18 TASK LIST — WAVE 10 (F-264 collection laws → F-217 waiter-resume root)

Status vocabulary: `IMPLEMENTED / TESTED / VERIFIED / OBSERVED / PARTIAL / BLOCKED /
PENDING / DEFERRED / CLASSIFIED / REJECTED / SUPERSEDED / PROBE-BOUND`. No "DONE"
without runtime evidence (constitution law).

Baseline binary `a8761a482a186eac` → LAW-A `57a2612db3a70d39` → LAW-B `f6e9cd7315c6c9f1` → LAW-D `755774469a200f8b` → final `d762aa0f03d2ab0a` (+ LAW-E bounded diag).
Full battery at baseline AND at every fix binary: **ALL PASS, zero drift**
(`CONT18_BASELINE.md`; anchors 18/18 byte-identical at every checkpoint).

## A. PHASE 0 — baseline

| # | Task | Status | Evidence |
|---|------|--------|----------|
| 0 | Static identity + APK SHAs + toolchain | **IMPLEMENTED** | `t01_static_facts.json`; brief's `e752b6d9c669558a` = NOT-FOUND-IN-REPO (recorded) |
| 0_1 | Anchors 6/6 ×3 | **VERIFIED** | 18/18 MATCH byte-identical |
| 0_2 | Telegram ×3 | **OBSERVED** | 2/3 REAL_APP_CONTENT `cf4c41e62ceb6557`; run2 = 120 s wall-cap flake (recorded) |
| 0_3 | Probes f266/f259/f259g/fcol | **VERIFIED** | 6/6, 7/7, 12/13 honest, 3/18 = recorded state |
| 0_4 | Negatives + skill | **VERIFIED** | 19/19, 13/13 |
| 0_5 | 121-stage battery | **VERIFIED** | ALL PASS after 3 evidence-pinned env restorations (font re-added to tracking — repo defect from `46f56737`; fixture refetch = frozen SHAs; resource_trace rebuilt) |
| 0_6 | f084 spin probe (F-217 live law) | **VERIFIED** | HALT 50,001 deterministic, deferred VME, cap never raised (`t01_f084_probe.json`) |

## B. PHASE 1 — collection laws (F-264 family)

| # | Task | Status | Evidence |
|---|------|--------|----------|
| 1 | T-02 six-law reconstruction table | **IMPLEMENTED** | `CONT18_COLLECTION_AUDIT.md` |
| 2 | T-03 probe-artifact vs runtime residual audit | **IMPLEMENTED** | bundled-java.util hypothesis REFUTED for fcol.apk (no java/util entries); F-238-SET POISON = diag false-positive; all other FAILs genuine gaps |
| 3 | T-04 LAW-A source-law extraction | **IMPLEMENTED** | audit doc §T-04 |
| 4 | LAW-A implement: shared kind-faithful remove-by-index (both intercept sites) | **IMPLEMENTED** | `lawa_remove_index` in android_shadows.cpp |
| 5 | LAW-A implement: contains kind-aware slots | **IMPLEMENTED** | K9 flip PASS |
| 6 | LAW-A implement: indexOf/lastIndexOf real handler | **IMPLEMENTED** | K1 ix=1 |
| 7 | LAW-A implement: F-238 diag predicate fix | **IMPLEMENTED** | no POISON on legal string set |
| 8 | K1 self-decomposing probe detail (T-03 honesty) | **IMPLEMENTED** | fcol.apk `55dbde8e03ad4c6f` |
| 9 | LAW-A synthetic proof | **VERIFIED** | fcol 3/18 → **5/18** (K1+K9 PASS; K7/K8/K10 unchanged) |
| 10 | LAW-A regression: anchors | **VERIFIED** | 6/6 ×3 byte-identical at `57a2612db3a70d39` |
| 11 | LAW-A regression: f266/f259/f259g | **VERIFIED** | 6/6, 7/7, 12/13 honest |
| 12 | LAW-A regression: negatives + skill | **VERIFIED** | 19/19, 13/13 |
| 13 | LAW-A real-APK exercise (T-06) | **VERIFIED** | opencalc ArrayList.remove ×19, dooz ×9 via shadow channel (REAL_DALVIK_INTERPRETER traces); byte-identical ×3 = behavior-preserving on coherent stores |
| 14 | LAW-A 3-run proof (T-07) | **VERIFIED** | anchors ×3 + probe rows above |
| 15 | LAW-A registry update | **IMPLEMENTED** | F-NEW-264d evidence += LAW-A (`cont18_registry_lawa.py`) |
| 16 | LAW-B iterator write-back (K2 listIterator.set, K11 Iterator.remove+ISE, K12 ListIterator.add) | **IMPLEMENTED+TESTED** | fcol 5/18→8/18; lastReturned box law; ISE double-remove; probe-artifact expectations corrected per OpenJDK ListItr (K2 nix==0, K12 pidx==1) |
| 17 | LAW-C Java-8 default-method family (K13/K14/K16/K17/K18) | **IMPLEMENTED+TESTED** | fcol 10/18→18/18; dex_invoke_slot channel; boxed compareTo/Integer.sum laws; commit 75dae014 |
| 18 | LAW-D deque order (K4 LinkedList head/tail, K5 ArrayDeque FIFO) | **IMPLEMENTED+TESTED** | fcol 8/18→10/18 at 755774469a200f8b; kind-aware addFirst/addLast/peek/poll/removeFirst/Last + ArrayDeque added to handles_class (was entirely absent) |
| 19 | LAW-E map-default/hash-view coherence (K6 getOrDefault, K9-contains face done via LAW-A) | **IMPLEMENTED+TESTED** | K6 PASS (remOk=true def=42): root = dead-code kill (deque-block terminal return) + missing getOrDefault law; the earlier 'receiver identity loss' hypothesis REFUTED by the LAWCEF two-layer trace; commit 75dae014 |
| 20 | LAW-F subList view (K3) + stream family (K15) | **IMPLEMENTED+TESTED** | K3 PASS (write-through view + OpenJDK bounds); K15 PASS (bounded of/toList/filter/collect-toList eager pipeline; static-face gate exemption); rest of java.util.stream DEFERRED with scope; commit 75dae014 |
| 21 | AbstractCollection.toString face (K14 detail shows `@hash`) | **PENDING** | recorded as LAW-C sub-face (probe row detail cosmetics; no semantic row depends on it) |
| 22 | LAW-B..F each: implement → fcol row → anchors ×3 → negatives (one law = one fix cycle) | **PENDING** | standing queue, one at a time |

## C. PHASE 2 — F-265 downstream reclassification

| # | Task | Status | Evidence |
|---|------|--------|----------|
| 23 | T-09 causal-order trace (F-084 HALT **before** Lm7 null-text) on live dooz | **PENDING** | must show order before any SUPERSEDED flip |
| 24 | T-10 F-265 reclassification (only with proof) | **PENDING** | currently CLASSIFIED |

## D. PHASE 3 — F-217 waiter-resume root (main target)

| # | Task | Status | Evidence |
|---|------|--------|----------|
| 25 | T-11 F-217 source reconstruction: waiter registration path | **CLASSIFIED** | real DEX extraction (17 methods, unlock 88 units) + disasm (CONT18_F217_FIRST_DIVERGENCE.md §1) |
| 26 | T-11a continuation capture | **PENDING** | |
| 27 | T-11b resume/unpark dispatch | **PENDING** | |
| 28 | T-11c Handler/Looper/MessageQueue interaction | **PENDING** | |
| 29 | T-11d re-entrant execution + nested interpreter state | **PENDING** | |
| 30 | T-11e queued side effects visibility | **PENDING** | |
| 31 | T-12 R-NEW-345 park/drain comparison (guarantees, invocation sites, gap vs refinement) | **PENDING** | |
| 32 | T-13 spin reproduction at HEAD (MutexImpl.unlock face: owner=NO_OWNER, permits=0, head=obj#366) | **PENDING** | CONT-17 evidence reproduced at baseline (f084 synthetic live) |
| 33 | T-14 CONT-17 bounded re-entry (ARM-A) audit: valid law vs mask | **PENDING** | |
| 34 | T-15 minimal F-217 fix (category decided by evidence only) | **BLOCKED** by 25–33 | |
| 35 | F-217 synthetic probe (semantic transition, not exception count) | **BLOCKED** by 34 | |
| 36 | F-217 Dooz ×3 (real Compose target) | **PENDING** | |
| 37 | F-217 independent Compose APK ×3 | **PENDING** | |
| 38 | F-217 non-Compose APK ×3 (normal lifecycle unbroken) | **PENDING** | |
| 39 | F-217 Telegram regression ×3 | **PENDING** | |
| 40 | F-217 game ×3 (async/nested-execution exerciser) | **PENDING** | |

## E. PHASE 5 — full regression + reporting

| # | Task | Status | Evidence |
|---|------|--------|----------|
| 41 | Full regression after F-217 change (anchors ×3, all probes, negatives, skill, gate battery, 5 APK families) | **PENDING** | gate list per brief |
| 42 | `CONT18_F217_SOURCE_LAW.md` | **PENDING** | |
| 43 | `CONT18_F217_RUNTIME_TRACE.md` | **PENDING** | |
| 44 | `CONT18_F265_RECLASSIFICATION.md` | **PENDING** | |
| 45 | `CONT18_REGRESSION.md` | **PENDING** | |
| 46 | `CONT18_FINAL.md` (A task ledger / B first-divergence map / C causal chain / D F-265 result / E regression / F deferred / G registry delta) | **PENDING** | |
| 47 | Registry delta + counts refresh | **PENDING** | F-NEW-264d already carries LAW-A evidence |
| 48 | Worklog + push discipline (commit after each evidence block) | **IMPLEMENTED** | baseline + LAW-A pushes |

**Count: 56 genuine tasks (0–48 + 7 derived `49_N` rows, CONT-18f wave). No filler.**
The remaining slots up to 100 stay **unfilled by design** — populated only by genuine
findings during execution (per the task-count rule; derived sub-tasks use `N_M` form).

## F. PHASE 0f — CONT-18f orphan-audit + reproduction wave (derived rows)

| # | Task | Status | Evidence |
|---|------|--------|----------|
| 49_1 | Clean-container lineage recovery + binary reproduction (recorded CONT-18 binary byte-identical) | **VERIFIED** | clean rebuild sha16 `8ee839e718877216`; addendum §7.2 |
| 49_2 | LAW-A..F cumulative impact re-proven live (fcol 18/18 at reproduced binary) | **VERIFIED** | `run/cont18f/probes/probe_report.json`; addendum §7.3 |
| 49_3 | Anchors 18/18 ×3 zero drift at reproduced binary | **VERIFIED** | `run/cont18/anchors/`; addendum §7.4 |
| 49_4 | T-01 tap exposure live-reproduced + registered as F-NEW-267 (CLASSIFIED) | **IMPLEMENTED** | `run/cont18f/tap1/`; registry 576 rows |
| 49_5 | Orphan-findings audit: all discrete findings dispositioned (no floats) | **IMPLEMENTED** | `evidence/cont18f/ORPHAN_FINDINGS_AUDIT.md` (14 rows) |
| 49_6 | Pre-push guard empty-list defect FIXED in main code + selftest law | **IMPLEMENTED+TESTED** | `scripts/security/check_secrets.sh` (no-op law + selftest arm) |
| 49_7 | Findings queue tool (registry+census → ranked usable queue) | **IMPLEMENTED** | `scripts/findings_queue.py`; `evidence/cont18f/findings_queue.{json,md}` (255 queued/321 terminal) |

**Count: 56 genuine tasks (0–48 + 7 derived `49_N`). No filler.**

## G. PHASE 0g — CONT-18g final source review (claims sweep + F-268/269 fix family)

| # | Task | Status | Evidence |
|---|------|--------|----------|
| 49_8 | Issue-claims sweep: #353–#381 fetched fresh; #381 (never audited) fully dispositioned | **IMPLEMENTED** | `evidence/cont18g/CONT18G_FINAL_REVIEW.md` §1–2 |
| 49_9 | F-NEW-268 exception-semantics family implemented (aget null/zero-len, aput zero-len, iget/iget-object null, new-array negative, throw-null) | **IMPLEMENTED+TESTED** | dalvik_engine.cpp; f268 probe 12/12 at `be95a47f797d3d99` |
| 49_10 | F-NEW-269 split dual-handler law parity (quote-strip, empty-delim per-char, trailing-empty removal; hang killed) | **IMPLEMENTED+TESTED** | f268 probe rows H–K; both dispatch layers |
| 49_11 | Refuted claims recorded (class_to_superclass end() — 32/32 guarded; write_v/monitor documented-design) | **IMPLEMENTED** | final review §2 |
| 49_12 | Full regression at fixed binary | **VERIFIED** | anchors 18/18 x3 byte-identical; fcol 18/18; f259 7/7; f259g 12/13 honest; f266 6/6; negatives 19/19; reinstall 8/8; skill 13/13 |
| 49_13 | Registry delta | **IMPLEMENTED** | 576→578 (F-268/269 ROOT-CAUSED-FIXED); queue refreshed 255 queued/323 terminal |
| 49_14 | Probe-infrastructure restoration in clean container (gate_a probe rebuilt+RUN, libprobe sha `ad413625925ed8e5` = recorded) | **VERIFIED** | negatives 19/19 + reinstall 8/8 unblocked |
| 50_1 | CONT-18h: F-265 live decomposition at HEAD — arms (a)+(b) VERIFIED (deferred-throw aborts frame; real throwable to handlers); measure-pass death (Lzs.m depth-17 unwind) still reproduced | **VERIFIED** | `evidence/cont18h/CONT18H_MAINLINE.md` §1; run/cont18h/dooz_f265 |
| 50_2 | F-NEW-270 ROOT-059 route-domain law fixed (framework-only gate + caller identity; wrong-site this=null DEX execution eliminated) | **IMPLEMENTED+TESTED** | `f141_is_framework_class` in dalvik_engine.h/.cpp; f882ca1832b955e3; anchors 18/18 |
| 50_3 | F-265 arm (c) re-rooted: F-NEW-271 registered (alien STRING_REF/0 in :Lqb0-typed field kills compose invalidation; bytecode coherence proven source-first) | **IMPLEMENTED** | registry 580 rows; CONT18H_MAINLINE §3 |
| 50_4 | CONT-18h full regression at f882ca1832b955e3 | **VERIFIED** | anchors 18/18 x3; fcol 18/18; f259 7/7; f259g 12/13 honest; f266 6/6; f268 12/12; negatives 19/19; reinstall 8/8; skill 13/13 |

**Count: 67 genuine tasks (0–48 + 14 derived `49_N` + 4 derived `50_N`). No filler.**
