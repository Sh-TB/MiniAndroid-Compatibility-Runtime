# CONT-18 Class-A Closeout Ledger — IMPLEMENTED-but-never-verified (35 roots)

Definition: registry status `IMPLEMENTED` = the fix law landed in the engine, but
the closure chain (synthetic probe / real-APK ×3 / regression battery / status
advance) was never recorded. These are fixes that exist but were never officially
 UTILIZED — the user's "fixes' orphaned achievements" class.

## Shared-battery verification at binary aed46450c103f2ea (this session)
All 35 roots' fix code is IN this binary. The shared battery proves the binary
is regression-clean, NOT that each root individually still holds. Per-root
closeout (status → ROOT-CAUSED-FIXED / VERIFIED_3RUN) requires each root's own
probe or recorded face to be re-executed at this binary.

Shared gates green this session:
- 5 anchors ×3 byte-identical (dooz/microtimer/unote/chess/opencalc)
- Gate A probe 98/0/1 · negatives 19/19 · skill 13/13

## Per-root ledger
| id | prio | title (trunc) | closeout requirement |
|---|---|---|---|
| F-NEW-179 | P0 | Per-frame canonical pump | re-run gate A stage + one compose app ×3 |
| F-NEW-199 | P0 | ArchTaskExecutorShadow dispatch | probe: executeOnDiskIO ordering ×3 |
| F-NEW-215 | P0 | CLASS-INIT HONESTY LAW | probe: failed clinit → observable, anchors |
| F-NEW-216 | P0 | ENUM-CONSTANT NAME LAW | probe: TimeUnit ordinals ×3 (fixtures exist: fnew259_probe covers enum-ordinal compareTo) |
| F-NEW-218 | P0 | CLASS-TOKEN BACKING VALIDATION | probe: instanceof F-105c arm |
| F-NEW-219 | P0 | REFLECTION METHOD-FAMILY LAW | probe: getMethod identity ×3 |
| F-NEW-220 | P0 | CONTENT-PARENT REUSE LAW | opencalc anchor already byte-identical ×3 (covered) |
| F-NEW-222 | P0 | Collections emptyMap/emptySet factory | hmap_probe re-run |
| F-NEW-223 | P0 | VIRTUAL EXTERNAL-STORAGE VOLUME | probe: Environment dir creation ×3 |
| F-NEW-224 | P1 | ONE CANONICAL DESCRIPTOR NORMALIZATION | corpus run ×3 |
| F-NEW-225 | P0 | GENERIC-TYPE + FRAMEWORK-REFLECTION (4 sub) | Field.getGeneric* probe |
| F-NEW-226 | P0 | VIEW PAINT IDENTITY LAW | TextView.getPaint probe |
| F-NEW-227 | P1 | PAINT.MEASURETEXT LAW | measureText overload probe |
| R-NEW-300 | P0 | (title in registry) | probe re-run |
| R-NEW-345 | P0 | runBlocking joinBlocking livelock | **PARTIALLY COVERED**: dooz anchor ×3 byte-identical exercises it; F-217 T-01 probe re-exercises runBlocking (FACE B PASS). Note: F-217's T-01 proves the REMAINING wake-law gap — R-NEW-345 must NOT be closed until the F-217 fix lands. |
| R-NEW-347 | P0 | dooz23 first-frame chain | dooz anchor ×3 (covered, byte-identical) |
| R-NEW-349 | P0 | dooz23 onCreate eager measure | dooz anchor ×3 (covered) |
| R-NEW-350 | P0 | protobuf-javalite 3-arg Class.forName | probe ×3 |
| R-NEW-402 | P1 | S81 visual audit instrument | diagnostics-only; verify instrument runs |
| R-NEW-428 | P1 | View.scrollTo/scrollBy onScrollChanged | probe ×3 |
| R-NEW-430 | P1 | computeScroll per-frame dispatch | probe ×3 |
| R-NEW-431 | P1 | View.setChecked family | probe ×3 |
| R-NEW-433 | P1 | View listener storage family | probe ×3 |
| R-NEW-435 | P1 | ViewPropertyAnimator record/settle | probe ×3 |
| R-NEW-436 | P1 | Scroll-clip walk law | probe ×3 |
| R-NEW-454 | P1 | Browser DOM/URL surface family | s133 probe ×3 |
| R-NEW-455 | P1 | Browser resource-forensics instrumentation | s133 probe ×3 |
| (remaining rows enumerated in DISCONNECTED_INVENTORY.json class A) | | | |

## Rule
A root may advance to ROOT-CAUSED-FIXED / VERIFIED_3RUN ONLY when its own probe
or recorded face is re-executed at the current binary with the shared battery
green in the same session. No blanket flips.
