# CONT-16 TASK BACKLOG — 52 SMALL TASKS (user directive 2026-10-07)

"Pick the remaining ~50, turn each into a small task, solve many small problems instead
of one big one." Sources: registry open rows (231 remaining after this wave's 3 fixes),
GitHub #375 §3 known partials, CONT-15 frontier. Each task = one bounded step with its
own evidence gate; NO task requires an app-specific patch. Statuses updated in place.

## A. Compose measure-death family (F-NEW-265 arms — the P0 line, decomposed)

| ID | Task | Root | Status |
|----|------|------|--------|
| T-01 | ARM-1 null-text producer: trace Lvs0.c → Lkb; → Lm7;.<init> against compose 1.11.4 TextDelegate/LayoutCoordinator sources; name the exact upstream law that yields a null CharSequence | F-NEW-265 | PENDING |
| T-02 | ARM-2 deferred-throw continuation law: verify the throwing frame must unwind (not continue) after the Lm7 ctor getClass-check throw; write the semantic probe | F-NEW-265 | PENDING |
| T-03 | ARM-3 null-Throwable report-helper path: how a NULL Throwable reaches Lel0.Y(Throwable); exception-construction law when <init> dies mid-throw | F-NEW-265 | PENDING |
| T-04 | F-NEW-266a typed-null NPE gate (both layers) | F-NEW-266a | **DONE** (f266 6/6) |
| T-05 | F-NEW-264d LAW-A read-your-mutation coherence (K1 set/remove/indexOf) | F-NEW-264d | PENDING |
| T-06 | F-NEW-264d LAW-B iterator write-back (K2/K11/K12) | F-NEW-264d | PENDING |
| T-07 | F-NEW-264d LAW-C Java-8 default-method family (K13/K16/K17/K18) | F-NEW-264d | PENDING |
| T-08 | F-NEW-264d LAW-D deque views (K4/K5) | F-NEW-264d | PENDING |
| T-09 | F-NEW-264d LAW-E hash view coherence (K6/K9) | F-NEW-264d | PENDING |
| T-10 | F-NEW-264d LAW-F subList/Stream families (K3/K15) | F-NEW-264d | PENDING |
| T-11 | F-NEW-259g-a JDK list-get range law + shadow exception channel | F-NEW-259g-a | **DONE** (row K flip) |
| T-12 | F-NEW-259g-b Vector claim (NPE gone; row L artifact note) | F-NEW-259g-b | **DONE** |
| T-13 | F-NEW-340 recomposer re-post law: Recomposer suspension must re-post a frame callback (bounded pump, no budget inflation) | R-NEW-340 | PENDING |
| T-14 | F-NEW-250 kotlinx.serialization serializerOrNull chain probe at HEAD (sudokusolver) | F-NEW-250 | PENDING |
| T-15 | F-NEW-221 R8 merged-class TypeToken dispatch re-verify at HEAD + bounded probe | F-NEW-221 | PENDING |

## B. Success-path / deep-audit PENDING queue (evidence artifacts, zero risk)

| ID | Task | Root | Status |
|----|------|------|--------|
| T-16 | SP-1 success corpus + per-title signature JSON (every real-L4 title) | F-NEW-208 | PENDING |
| T-17 | SP-2/3/12 common-successful-chain proof artifact on one known-good title | F-NEW-209 | PENDING |
| T-18 | SP-4..8 renderer-selection authority audit (grep heuristics, FALSE_ADVERTISED candidates) | F-NEW-210 | PENDING |
| T-19 | DEEP-AUDIT legacy rendering path reachability proof (call graph + trace census) | F-NEW-198 | PENDING |
| T-20 | view_tree_lifecycle_owner window-canonical cross-check | F-NEW-205 | PENDING |
| T-21 | traversal-order cross-check vs AOSP ViewRootImpl (requestLayout-during-layout second pass) | F-NEW-206 | PENDING |
| T-22 | final visual gate hardening (placeholder/status-bar rejection matrix) | F-NEW-207 | PENDING |
| T-23 | successful-apps upstream source mapping (stopwatch/notes/dodge + 1 failed Compose counterpart) | F-NEW-211 | PENDING |
| T-24 | high-fan-out missing-laws search from the successful path | F-NEW-212 | PENDING |
| T-25 | SUCCESS-PATH REPORT compile (A..F) | F-NEW-213 | PENDING |

## C. GitHub #375 §3 carried partials

| ID | Task | Root | Status |
|----|------|------|--------|
| T-26 | ViewPager mCurItem: exact APK identity gate first; then reproduce or BLOCKED-with-identity | #375 §3 | PENDING |
| T-27 | Fragment host law A/B separation (ABI blocker vs FragmentManager host) on one native+fragment app | F-NEW-168 | PENDING |
| T-28 | F-NEW-084 halt-cap semantics: bounded execution law for the MutexImpl.spin family (never raise the cap) | F-NEW-217 | PENDING |
| T-29 | F-NEW-229 CL MATCH_PARENT spec law (AT_MOST→fill for anchorless MATCH_PARENT children) + probe | F-NEW-229 | PENDING |
| T-30 | F-NEW-230 golden provenance: rebuild/annotate the 4 stale goldens with config blocks | F-NEW-230 | PENDING |

## D. Stale-status reconciliation sweep (each = one live run at HEAD, then flip or keep)

| ID | Task | Root | Status |
|----|------|------|--------|
| T-31 | R-NEW-001 live re-verify | R-NEW-001 | PENDING |
| T-32 | R-NEW-061 live re-verify | R-NEW-061 | PENDING |
| T-33 | R-NEW-242 live re-verify | R-NEW-242 | PENDING |
| T-34 | R-NEW-246 live re-verify (superseded check vs F-NEW-246 Vector laws) | R-NEW-246 | PENDING |
| T-35 | R-NEW-259/260 live re-verify (CONT-10 fixes landed; PARTIAL rows may be stale) | R-NEW-259/260 | PENDING |
| T-36 | R-NEW-279/285 live re-verify | R-NEW-279/285 | PENDING |
| T-37 | F-NEW-256/265 status linkage (256 → SUPERSEDED-BY-EVIDENCE with the 265 pointer) | F-NEW-256 | PENDING |
| T-38 | R-NEW-381 status linkage (dooz v23 first-frame → F-NEW-265 chain pointer) | R-NEW-381 | PENDING |

## E. Named OBSERVED-FAIL frontiers (one bounded attribution each)

| ID | Task | Root | Status |
|----|------|------|--------|
| T-39 | chessclock null-Uri producer attribution (RingtoneManager.getDefaultUri family) | F-NEW-161 | PENDING |
| T-40 | libGDX createGLSurfaceView NPE attribution → E-classify GL family or bounded shadow | F-NEW-157/F-144 | PENDING |
| T-41 | WhatsApp provider-null lattice: next-arm naming at HEAD | F-NEW-169 | PENDING |
| T-42 | F-NEW-172 key-materialization spin: implement the bounded materialization law | F-NEW-172 | PENDING |
| T-43 | F-NEW-197 white-frontier 2-node tree family: shared-SHA attribution refresh | F-NEW-197 | PENDING |
| T-44 | R-NEW-303/331 OBSERVED-FAIL rows: read evidence, re-run, reclassify or fix | R-NEW-303/331 | PENDING |
| T-45 | F-NEW-156 onCreate-unwind family: pick ONE new face, name its first divergence | F-NEW-156 | PENDING |

## F. OPEN single-face tasks (small, self-contained)

| ID | Task | Root | Status |
|----|------|------|--------|
| T-46 | F-138 ScoreView hint HUD: text_size=0 legacy path — skip-or-correct law + probe | F-138 | PENDING |
| T-47 | F-143 Service.onCreate/onStartCommand minimal lifecycle for service-only manifests | F-143 | PENDING |
| T-48 | F-145 capture surface follows top-of-stack window (multi-activity) — verify + fix | F-145 | PENDING |
| T-49 | F-147 dooz v10 ViewGroup.getChildAt null receiver — findViewById resolution gap | F-147 | PENDING |
| T-50 | F-NEW-192 z-order residue: verify draw-order enforcement at HEAD, close or keep with note | F-NEW-192 | PENDING |
| T-51 | F-NEW-218/219 JNI wave entry probe (GLSurfaceView20.setPreserveEGLContextOnPause reflection) — fresh ID required | F-NEW-219 family | PENDING |
| T-52 | R-NEW-389 bouncy 81-px band: F-136 collateral close-out note + verify at HEAD | R-NEW-389 | PENDING |

## Execution rules (per the directive + constitution)

- Many small fixes > one big rewrite. One law = one generic fix + probe + regression slice.
- Batch engine changes → ONE rebuild → probes → anchors → negatives → skill before registry.
- Every registry flip needs fresh runtime evidence at the current binary.
- No app-specific code, no R8-name tables, no suppression, no budget inflation, no
  source-only status flips.
