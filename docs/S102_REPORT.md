# S102 WAVE REPORT — COMPOSE FAMILY ROOT-CAUSE SWEEP + SAVEDSTATE PREPARATION

Engine head: `198c922f` (S102 laws: d963ff1e, ab003d6e, 6c0d8f5f + ledger refresh)
Battery: **105/105 ALL PASS** on the final tree · secrets/hygiene/controls green.

---

## 1. Scope correction — the "46-title compose family" was a regex false-positive

The S101 ledger's compose-runtime family rule was
`r"compose/ui/platform|ensureCompositionCreated|ComposeView|snapshot was taken"`.
The phrase **"snapshot was taken"** matched unrelated engine diagnostics
corpus-wide, wrongly grouping 46 titles. Honest evidence after tightening to
real `androidx/compose` frames:

* **genuine androidx/compose stack: 1 title** (com.vayunmathur.games.solitaire)
* genuine kotlinx/coroutines stack: 1 title (com.helddertierwelt.mentalmath)
* honest compose-runtime family (refreshed ledger): **6 titles**

RULE 4 compliance: no Compose backlog was assumed; every family claim now
carries a log line.

## 2. Root laws landed (one commit per law, battery per commit)

| # | law | commit | upstream source | first real-APK evidence |
|---|-----|--------|-----------------|------------------------|
| 1 | MULTIDEX-INTERFACE-CLOSURE | `d963ff1e` | art::Class::IsAssignable (interface closure across all dex files) | mentalmath: `AndroidDispatcherFactory as MainDispatcherFactory` CCE at FastServiceLoader → Dispatchers.Main dead |
| 2 | SERVICELOADER-APK-ENTRY | `ab003d6e` | OpenJDK ServiceLoader (LazyIterator) + libcore ClassLoader.getResources | mentalmath: `ServiceLoader.iterator on null` NPE in CoroutineExceptionHandlerImplKt.<clinit>; FastServiceLoader fallback `list(...) must not be null` |
| 3 | BIGINT-VERSION-PARSE | `6c0d8f5f` | libcore java/math/BigInteger.java | solitaire: `BigInteger.shiftLeft on null` NPE killed SavedStateRegistryImpl.performAttach ← ComponentActivity.**<init>** — before any Compose ran |
| 4 | LONG-BITMATH-64 | `6c0d8f5f` | OpenJDK Long.java | solitaire+mentalmath: MutableScatterMap `Long.numberOfTrailingZeros` null → slot-0 probe corruption vector |

Details (subset boundaries, representation, diagnostics) are documented in the
law comments inside `src/dex/dalvik_engine.cpp`; each includes its dex-method-ref
surface verified by direct method_ids walks.

## 3. Measured impact (fresh 61-title census, identical S99/S101 protocol)

```
S101: 13 INTERACTIVE / 2 RENDERED-L2+ / 39 PARTIAL / 7 FAIL
S102: 14 INTERACTIVE / 2 RENDERED-L2+ / 38 PARTIAL /  7 FAIL
```

* flip: `org.secuso.privacyfriendlymemory` PARTIAL → **INTERACTIVE-EVIDENCE** (state-change pixels measured by the standard click protocol)
* zero regressions
* solitaire: 4 failure chains → 2 distinct remaining roots (chains A+B cleared)
* mentalmath: coroutine dispatch + ServiceLoader chains cleared

## 4. Remaining roots — filed as tickets (no duplicates)

| ticket | root | family |
|--------|------|--------|
| #349 | R8 field-promotion identity: `getSavedStateProvider` null receiver in ComponentActivity.<init> pc=224 (SavedStateRegistryController renamed/merged) | savedstate + compose |
| #350 | **compose frontier**: CompositionLocal provide/read semantics + ViewTree*Owner host wiring (`LocalDensity not present` ← getWindowRecomposer) | compose |
| #351 | Hilt generated-builder field identity (`ApplicationContextModule must be set`) — same R8 field-identity family as #349 | androidx-common (DI) |
| #352 | LockSupport park/unpark deterministic subset for CoroutineScheduler.tryPark (F084 50001-iteration spin) | coroutine |

## 5. SavedState preparation (RULE 16 dependency map)

```
COMPOSE_REQUIRED only : com.vayunmathur.games.solitaire
BOTH                  : com.vayunmathur.games.solitaire, com.helddertierwelt.mentalmath
SAVEDSTATE_REQUIRED   : firestrike, babydots, blidraughts, mancala, ballbreak,
                        klondike, no.thanks, mykanji, chess, secuso family (18
                        titles per the refreshed ledger savedstate-registry row)
NOT_REQUIRED          : remaining INTERACTIVE/L2+ titles
```

S103 entry point: the shared R8 field-identity law (#349 + #351 = one law, two
families), then #350 compose host wiring; SavedState implementations (registry
restore/save dispatch) ride the same laws.

## 6. Size / modularity (RULE 22)

* source delta: +789 LOC in `miniandroid/src` (dalvik_engine.cpp/h), all
  classified: ServiceLoader/ClassLoader/URL → ANDROIDX-COMMON,
  BigInteger/Long → CORE, engine-heap representation → CORE
* binary delta: engine 92.87 MB → 94.05 MB unstripped (+1.18 MB incl. all four
  law comment blocks; no new third-party dependencies, no fan-out changes)
* capability registry: no new capabilities — the laws extend existing
  CORE/ANDROIDX-COMMON rows; no Compose capability is registered (honest: no
  compose rendering yet)

## 7. Next queue (descending measured impact)

1. #350 compose host wiring (LocalDensity + ViewTree owner tags) — the only path to E3+ for the compose title
2. #349/#351 R8 field-identity law (2 families, 2 titles + every future R8 full-mode APK)
3. #352 LockSupport subset (unblocks Dispatchers.Default worker loops)
4. unclassified tail per refreshed ledger (22 titles, needs per-title triage)
5. SavedState restore/save dispatch on the S102 laws
