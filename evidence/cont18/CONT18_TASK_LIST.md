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
| 17 | LAW-C Java-8 default-method family (K13/K14/K16/K17/K18) | **PENDING** | one machinery, seven faces |
| 18 | LAW-D deque order (K4 LinkedList head/tail, K5 ArrayDeque FIFO) | **IMPLEMENTED+TESTED** | fcol 8/18→10/18 at 755774469a200f8b; kind-aware addFirst/addLast/peek/poll/removeFirst/Last + ArrayDeque added to handles_class (was entirely absent) |
| 19 | LAW-E map-default/hash-view coherence (K6 getOrDefault, K9-contains face done via LAW-A) | **BLOCKED→FRONTIER-SCOPED** | K6 decomposed: Map.remove no-op + getOrDefault null; shadow law never reached (F089-REMOVE diag 0 hits); virtual-rewritten iface calls (invocation_type=virtual, class Ljava/util/Map;) lose receiver identity — execute_invoke_virtual bridge scope for next wave |
| 20 | LAW-F subList view (K3) + stream family (K15) | **PENDING** | |
| 21 | AbstractCollection.toString face (K14 detail shows `@hash`) | **PENDING** | recorded as LAW-C sub-face |
| 22 | LAW-B..F each: implement → fcol row → anchors ×3 → negatives (one law = one fix cycle) | **PENDING** | standing queue, one at a time |

## C. PHASE 2 — F-265 downstream reclassification

| # | Task | Status | Evidence |
|---|------|--------|----------|
| 23 | T-09 causal-order trace (F-084 HALT **before** Lm7 null-text) on live dooz | **PENDING** | must show order before any SUPERSEDED flip |
| 24 | T-10 F-265 reclassification (only with proof) | **PENDING** | currently CLASSIFIED |

## D. PHASE 3 — F-217 waiter-resume root (main target)

| # | Task | Status | Evidence |
|---|------|--------|----------|
| 25 | T-11 F-217 source reconstruction: waiter registration path | **PENDING** | |
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

**Count: 49 genuine tasks enumerated (0–48). No filler.** The remaining slots up to 100
stay **unfilled by design** — populated only by genuine findings during F-217 execution
(per the task-count rule: if only 47 exist, record 47; derived sub-tasks use `N_M` form).
