# CONT-122 Ledger — «حل ۳۶۴ با این روش تمامشون رو حل بکن و جواب بده» UNPROVEN probe-battery wave

- **Wave:** CONT-122, one train, all terminal at base 79b226a2 (CONT-121). Binary rebuilt deterministically after container reset (**5th byte-identical reproduction**: 1abe5c6a), then advanced by the wave's laws to **72018b03**.
- **Method:** the #364 total codex — glow-worm light into dark rows (the 72 UNPROVEN audit-era rows), one train of wagons, fixture-first (every gap observed live BEFORE any law landed), zero-drift wall at every landing.

## W-01 · Deterministic rebuild + wall base
- Container reset → `git reset --hard origin/main` (stale-snapshot law) → front-ground chunked make → binary `1abe5c6a7abc6060` byte-identical to CONT-121's recorded hash. Baseline wall green.

## W-02 · The 16-probe behavioral battery (fixture `cont122_unproven`, two-dex APK)
- Real toolchain build (aapt2/ECJ/D8); U16's Companion class lives in **classes2.dex by construction**.
- **Pre-fix faces (honest, all live): 6 PASS / 10 FAIL.** Post-fix: **13 PASS / 3 honest FAIL.**
- Every verdict line `C122- U## PASS/FAIL <detail>` printed by the fixture itself; no inventory-mention shortcuts (the CONT-119 refuted-upgrade law held: only live behavior upgrades a row).

## W-03 · Seven product laws landed (each verified live by its probe)
1. **FIX-ASC / R-NEW-010** — aput-object ArrayStoreException store-check (AOSP HandleAPutObject). Pre: `U01-STORED no-exception value=7`; post: `U01-RAISED java.lang.ArrayStoreException`.
2. **FIX-ASC-B / R-NEW-010b** — System.arraycopy component-mismatch pre-validation. Pre: `U02-COPIED no-exception dst0=1`; post: raised+typed.
3. **FIX-OOM / R-NEW-169** — new-array OutOfMemoryError law (per-descriptor byte size > 1 GiB → ART-style message). Pre: `U03-ALLOCATED size=2147483645`; post: `Failed to allocate a 8589934580-byte allocation`.
4. **FIX-INTF-002 / R-NEW-097** — IntentFilter categories + matchAction. Pre: `cats=0`; post: `cats=1`.
5. **FIX-COMP / R-NEW-283** — Intent component identity round-trip + ComponentName.getPackageName/getClassName.
6. **FIX-BNDL / R-NEW-055** — Bundle sparse/arraylist/bundle object arms identity round-trip.
7. **FIX-MTX / R-NEW-193** — View.getMatrix() composition (rotation+scale about pivot → m0..m8).

## W-04 · The store-check exposed FOUR deeper pre-existing silent bugs — all fixed, never suppressed
- **make_array_elem_desc malformed arrays** (the real tower3d lie): `[L` + descriptor-form element + `;` → `[LLcom/...;;` mis-typed arrays since the F-119 era; now form-aware (tower3d restored to `11a38a5a` MATCH, 0 rejects).
- **Class token referent**: Array.newInstance now prefers the heap token `__referent_desc` over the register's class-of-the-class.
- **Assignable start-class interfaces**: `AndroidApplication$1 implements LifecycleListener` answered FALSE (own interfaces never consulted) — JVMS 5.1 law added before the super walk.
- **Framework hierarchy gaps**: android.animation (12 edges) + android.text (7 edges) chains added (telegram's legal ValueAnimator→Animator / SpannableStringBuilder→CharSequence stores).

## W-05 · Honest FAILs stay honest (3 CONFIRMED gaps, levers named, nothing faked)
- **R-NEW-161** /proc passthrough blocked by the sandbox (canRead=false) — raw passthrough would leak host identity; curated /proc/self law is the lever.
- **R-NEW-083** GET_SIGNATURES → signatures=null; v2 signing-block parse is the lever; **no fake signatures**.
- **R-NEW-151** androidx.core.content.FileProvider CNFE; getUriForFile law is the lever.

## W-06 · Registry hygiene (no inflation, independent-id law honored)
- 12 UNPROVEN rows upgraded on live evidence (5 ROOT-CAUSED-FIXED + 7 VERIFIED-CORRECT); 3 → CLASSIFIED CONFIRMED_OPEN_GAP; **48 untitled 'no trace'/'-' husk rows → STALE_OR_SUPERSEDED** (CONT-105 triage + double-scan citations; nothing merged into another root).
- Registry: 783 ids unique, main==mirror **row-equal**, UNPROVEN **72 → 9**, terminal share **81.5%** (638/783).

## W-07 · Zero-drift wall (final binary 72018b03)
- **9/9 ANCHOR_MATCH** (dooz d602648e / opencalc d5f3c7b5 / unote 90a67cc1 / microtimer bbd350b6 / chess a0319686 / tower3d 11a38a5a / sudoku be640e39 / klondike 31ddd4d5 / telegram 20ac8cbbbb), selftest rc=0, **negatives 19/19** (probe_store rebuilt after container reset — the CONT-111 remedy re-applied), registry id-unique + main==mirror row-equal.
- Honest fixture note: ECJ constant-folded the first OOM probe's unused allocation (dead-code elimination) — the fixed fixture stores to a static field; the compiler-behavior face is recorded, not hidden.
