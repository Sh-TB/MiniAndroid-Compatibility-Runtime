# CONT-38v — Independent Verification of the Friend-Reported Findings
## "F-NEW-257" (Class objects as stable map keys) and "F-NEW-258" (non-null `ArrayList.listIterator()`)

Date: 2026-10-10 · Binary at wave start: `a181d7b317e015c8` (byte-exact CONT-37 record, HEAD `8cbd94e7`,
local == origin/main, clean tree). Binary at wave end: `f528f04483017c57` (one new generic law, F-NEW-299).
Directive frame: verify before patching · frame-truth only · reuse existing registry entries, no duplicates.

---

## 0. Registry-number conflict (the user's warning, confirmed)

The friend's two findings arrive **numbered F-NEW-257 and F-NEW-258 — but those numbers are already
occupied** in `root_registry.json` by two unrelated CONT-7-era roots:

| Registry id | Existing title (registered) | Status |
|---|---|---|
| F-NEW-257 | Bundle parcel-family content fidelity (putParcelable dropped values) | ROOT-CAUSED-FIXED |
| F-NEW-258 | instance-of on a STRING_REF register answered FALSE | ROOT-CAUSED-FIXED |

The friend's numbering is therefore **not usable as claimed** — per directive the claims were verified
by CONTENT (source inspection + probes), not by their numbers. His reported line numbers
(`android_shadows.cpp:238-250`, `:1241-1255`, `dalvik_engine.cpp:34369-34388`) do not match this
lineage's actual implementation sites either (real sites listed per finding below). Treated as
navigation hints, exactly as instructed.

## 1. Friend's "F-NEW-257" — Class objects as stable map keys

**Claimed root cause:** `const-class` can produce different runtime reference IDs for the same logical
Class; a later map lookup misses an earlier insertion.

**Verdict: VERIFIED_TESTED — as an ALREADY-REGISTERED, ALREADY-FIXED root.** The claimed mechanism is
exactly the registered **F-069 (R-NEW-293) const-class STABLE IDENTITY law**:

- `miniandroid/src/dex/dalvik_engine.cpp:16847-16905` — `execute_const_class`: per-descriptor
  `class_token_ids_` cache; the comment records the ORIGINAL failing face verbatim ("the
  viewModelFactory initializer registered its key under one Class value and the create(modelClass)
  lookup compared a DIFFERENT Class value → Intrinsics.areEqual false → IAE 'No initializer set for
  given class androidx.lifecycle.A' → first frame died") — the friend's exact scenario on the dooz APK.
- **F-103 (S58, R-NEW-378)** — tokens are REAL heap objects (`Ljava/lang/Class;` +
  `__referent_desc__`), so §19 runtime-class dispatch lands on `Ljava/lang/Class;`.
- **F-NEW-249** — `make_stable_class_token` (`dalvik_engine.cpp:19626`): `Object.getClass` answers the
  SAME per-descriptor token (the old `getClass` stamped `instruction_sequence_` — one DIFFERENT token
  per call site — which is precisely the friend's claimed mechanism).
- **F-NEW-282** — argument-boundary + `iput-object` materialization (`dalvik_engine.cpp:2839-2875`,
  `:18570-18600`): raw CLASS_REF values degrade across frames; they materialize to the same stable
  token at the boundary.
- **F-NEW-248** — `map_key_value_law` (`android_shadows.cpp:233`): String-object keys unwrap to
  CONTENT; the Class-key face keys by the stable heap token id, which IS stable per descriptor.

**What the friend proposed that is NOT in this lineage:** a `"class:<descriptor>"` string key form in
`map_key_value_law`. Not present — and not needed: the identity problem is solved at the TOKEN layer
(one heap object per descriptor for the whole run), so the generic `"obj:<heap-id>"` keying is already
stable for Class keys. Distinct descriptors never share a token; ordinary objects keep identity
semantics.

**Probe proof (new standing probe, `fixtures/classkey_probe`, package com.probe.ckey, real
aapt2/ECJ/D8):** rows CK-01..CK-06 PASS ×3 on BOTH the pre-wave binary (a181d7b317e015c8) and the
post-fix binary (f528f04483017c57): const-class identity, `getClass()` == `const-class` cross-production,
`HashMap<Class,V>` and `LinkedHashMap<Class,V>` put/get across separately produced tokens, distinct
descriptor discrimination, ordinary-object identity preservation.

## 2. Friend's "F-NEW-258" — non-null `ArrayList.listIterator()`

**Claimed root cause:** `listIterator()` falls through to DEX execution and returns null → NPE at
`ListIterator.hasPrevious()`.

**Verdict: VERIFIED_TESTED — as an ALREADY-REGISTERED, ALREADY-FIXED root.** This is exactly
**F-NEW-255 (CONT-7 W3)** + the **CONT-18 LAW-B write-back faces**:

- `miniandroid/src/framework/android_shadows.cpp:2565-2600` — the listIterator law: mints a REAL typed
  iterator box (`Ljava/util/ListIterator;` heap object carrying `__iterator_parent__` +
  `__iterator_pos__`), NOT the friend's "self-as-iterator" representation (which exists only as the
  heap-null fallback branch and never fires on live runs). The comment records the original dooz v23
  face verbatim ("List.listIterator() fell into the handled_void() stub — an OBJECT-returning method
  answered NULL — the app's ListIterator wrapper stored the null as its backing iterator and
  ListIterator.hasPrevious threw the NPE that killed composition before the first app frame").
- `android_shadows.cpp:461-540` — LAW-B: `set` overwrites lastReturned in the BACKING list;
  `remove` removes lastReturned with the double-remove `IllegalStateException`; `add` inserts at the
  cursor and advances past it. OpenJDK `AbstractList.ListItr` semantics.
- `dalvik_engine.cpp:38871-38930` — the engine-side iterator/listIterator family for array-backed
  lists (getBackStackEntry face).

**The directive's design question** ("a tagged list object is not automatically a real ListIterator"):
answered — the primary implementation is a typed box with independent cursor state; the behavioral
matrix below demonstrates the contract. PARTIAL is NOT warranted.

**Probe proof:** rows LI-01..LI-08 PASS ×3 on both binaries: full forward+backward cursor walk
(hasNext/hasPrevious/next/previous/nextIndex/previousIndex), empty-list non-null + no-crash,
`listIterator(1)` mid-list start, set-into-backing, add-at-cursor, remove + double-remove ISE,
pre-next set/remove ISE, repeated iteration. Existing standing coverage additionally re-verified:
cont7w3_probe W3-10/11/12 and fcol K2 (battery rows fnew253 147/0, fcol 140/0 — unchanged).

## 3. The verification probe discovered a NEW generic root (this wave's fix)

Row CK-07 — `m.put(new String("composable"), "NAV"); m.get("composable")` — **FAILED ×3** on the
pre-wave binary. Root cause (decoded): `bridge_to_api` handled ONLY the `String(byte[])` constructor
family; `new String()` / `new String(String)` fell to the generic stub, the heap String stayed
unmaterialized (no `__string_value__`), and F-NEW-248's `map_key_value_law` fell back to identity
keying (`obj:<id>`) while the const-string get keyed by content — put/get never met. OpenJDK law:
`String.equals` is content equality; a copy MUST be the same map key.

**Fix (F-NEW-299, one generic point)** — `dalvik_engine.cpp` String `<init>` block, before the byte[]
family: materialize `__string_value__` onto the caller's new-instance heap object and answer the
content as the STRING_REF result; structural discriminators only (STRING_REF source = copy;
OBJECT_REF source accepted only when its heap class is `Ljava/lang/String;` so byte[] sources keep
falling through; `args==1` = the empty-string form).

| Direction | Binary | Result |
|---|---|---|
| PRE ×3 | a181d7b317e015c8 | 14/1 (CK-07 FAIL each run) |
| POST ×3 | f528f04483017c57 | **15/0 all rows PASS** |

## 4. Phase-3 application targets (three fresh runs each, `scripts/cont38v_targets.sh`)

| Target | Result on a181d7b317e015c8 | Frame truth |
|---|---|---|
| Dooz (`io.github.yamin8000.dooz_23`, unchanged `31ddd4d5b8e6d18e` ×3 MATCH) | the CONT-37 honest keep-empty white; boot composition ~15.3 s > budget — PENDING root | honest |
| SimpleCalc (`com.simplemobiletools.calculator_8`, `7960bce447ac6d8f` ×3, rc=0) | FULL SUCCESS — this is the lineage's own law chain (the friend's absent patches are not involved) | app content |
| `com.tananaev.calculator` v1.10 vc11 (`294a68bd00debbdc…`, re-supplied from F-Droid) | **PARTIAL SUCCESS** — 1 uncaught NPE: `NotificationCompat$Builder.<init>` pc=64 "setSmallIcon on a null object reference" → `MainActivity.onCreate` dies (invoke_pc=29) → **frame = DEFAULT_BACKGROUND_ONLY (`d602648e8e401895` ×3), APP_DRAW_OPS missing** | background only |
| headingcalc (`org.debian.eugen.headingcalculator_1`, re-supplied SHA-exact `274ec873098eea51…` == the historical record) | rc=0, new deterministic baseline `be1cea9cf994b26a` ×3 (the old `a169346e` golden is from the pre-CONT-14 s127 era; the engine has changed by ~400 registered roots since) | recorded |

**Friend's "the calculator loads" claim, per target:** SimpleCalc — TRUE on this lineage (already
recorded in CONT-36/37; re-verified ×3). tananaev calculator — **NOT VERIFIED**: rc=1 with the NPE
above and a default-background-only frame; it does not meet the frame-truth gate. The tananaev face
(`NotificationCompat$Builder` null-receiver at construction) is recorded as a NEW dooz-independent
frontier — a candidate shared-runtime root for a later wave (it gates `MainActivity.onCreate` for the
whole NotificationCompat-family).

**Regression control caveat honored:** the unchanged calculator/headingcalc frames are NOT evidence
for the new laws — the CK/LI probe rows are; the apps are drift controls only.

## 5. Full regression gate at the wave-end binary `f528f04483017c57` (`scripts/cont37_regression.sh`)

- Anchors **8/8 ×3 BYTE-IDENTICAL**: dooz `31ddd4d5b8e6d18e`, microtimer `da73010a37dd0189`, unote
  `4f1a9e4e8f64fae8`, gmdice `f3b483fe7b7cf51b`, opencalc `a976d2f9fb675cb3`, tttdeluxe
  `af6094295ecb50e3`, flappycow `13cf47464d9787f4`, g2048 `59ca1526611c4622`.
- composeStopwatch `bbaf8f76308dc267` ×3 (unchanged through the String law).
- Battery == CONT-28..37 records EXACTLY: fcol 140/0 · f259 49/0 · f259g 84/7-known · f266 42/0 ·
  f268 96/0 · fnew253 147/0 · fnew286 10/0 · fnew289 28/0 · fnew252 56/0 · fnew290 56/0 · fnew291 56/0 ·
  fnew292 70/0 · fnew293 56/0 · fnew294 77/0 · fnew295 49/0 · fnew296 42/0 · fnew297 42/0 · fnew298 19/0
  \+ **ckey 15/0** (new standing row).
- simplecalc ×3 rc=0 `7960bce447ac6d8f`. **ZERO DRIFT.**

## 6. Line-by-line checklist

| # | Item | Status |
|---|---|---|
| 1 | Phase-0 state recorded (HEAD/remote/binary/APK SHAs/registry/worklog) | PASS |
| 2 | Registry-number conflict detected (friend's 257/258 occupied) | PASS |
| 3 | "F-NEW-257" verified against source (5 token-law sites) | PASS |
| 4 | "F-NEW-257" probe rows CK-01..06 ×3 (both binaries) | PASS |
| 5 | "F-NEW-258" verified against source (F-NEW-255 + LAW-B) | PASS |
| 6 | "F-NEW-258" probe rows LI-01..08 ×3 (both binaries) | PASS |
| 7 | Pre-fix evidence for both re-discovered roots (registry + recorded live faces) | PASS |
| 8 | NEW root CK-07 decoded (String copy-constructor) | PASS |
| 9 | F-NEW-299 fix implemented (one generic point, structural discriminators) | PASS |
| 10 | CK-07 PRE ×3 FAIL / POST ×3 PASS | PASS |
| 11 | Dooz ×3 | PASS (PENDING root recorded) |
| 12 | SimpleCalc ×3 rc=0 | PASS |
| 13 | tananaev ×3 (PARTIAL; new NotificationCompat frontier recorded) | PARTIAL |
| 14 | headingcalc ×3 (APK re-supplied SHA-exact; new baseline recorded) | PASS |
| 15 | Full regression gate, zero drift | PASS |
| 16 | Registry 607→608 (F-NEW-299; friend claims recorded as evidence, no duplicates) | PASS |
| 17 | Probe wired into standing battery (w4_build_probes.sh + cont37_regression.sh) | PASS |
| 18 | Commit + push | PASS (see git log) |

## 7. Cross-check with the primary coder's prior decisions (Phase-4 table)

| Finding | Friend's claim | Prior coder decision (record) | Current HEAD result | Evidence | Final status |
|---|---|---|---|---|---|
| "F-NEW-257" | Stable Class map keys | F-069/R-NEW-293 ROOT-CAUSED-FIXED (dooz SavedStateHandlesVM face); F-103/F-NEW-249/F-NEW-282 complete the family | Implementation present; CK-01..06 PASS ×3 | registry + dalvik_engine.cpp:16847/19626/2839/18582 + probe | VERIFIED_TESTED (already implemented) |
| "F-NEW-258" | Functional non-null listIterator | F-NEW-255 ROOT-CAUSED-FIXED + LAW-B (CONT-18) | Implementation present; LI-01..08 PASS ×3 | registry + android_shadows.cpp:2565/461 + probe | VERIFIED_TESTED (already implemented) |
| Dooz navigation | "Navigator lookup now succeeds" | F-NEW-248 (String-content keys) + F-NEW-249 (Class-keyed name cache) fixed the Navigator face in CONT-6/7 | dooz advances past it (current anchor is the honest keep-empty white; the frontier is the boot budget, PENDING) | CONT-37 anchor + registry | VERIFIED_TESTED |
| Calculator control | "No regression" | SimpleCalc is this lineage's law chain | 7960bce447ac6d8f ×3 rc=0 | run/cont38v/targets | PASS |
| headingcalc control | "No regression" | Historical golden a169346e (s127 era) | new baseline be1cea9cf994b26a ×3, deterministic; APK re-supplied SHA-exact | run/cont38v/targets | RECORDED |
| tananaev calculator | (implicit: loads) | Not previously in the anchor set | PARTIAL — NotificationCompat$Builder null-receiver NPE; DEFAULT_BACKGROUND_ONLY | run/cont38v/targets + crash.log | NEW FRONTIER (PENDING) |
