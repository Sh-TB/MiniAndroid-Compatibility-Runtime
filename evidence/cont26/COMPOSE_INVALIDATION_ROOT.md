# CONT-26 / TRACK A — COMPOSE INVALIDATION-DELIVERY CHAIN + REAL-COMPOSE ORACLE INSTRUMENT

Wave: CONT-26 dual-track runtime root extraction. Track A continues F-NEW-277
(recomposition starvation) from the CONT-25 closeout: the pump-side arm of the
fix surface had landed ([F277-POLL] poll-timeout parity), the divergence had
moved to the invalidation-delivery link, and CONT-25 named the CONT-12
un-renamed real-Compose oracle as "the next wave's opening probe".

**VERDICT UP FRONT (no success inflation):** NO real app-owned Compose pixels
were produced this wave. The wave's concrete advances are: (1) the A1 state
re-proven live at HEAD; (2) the CONT-12 oracle rebuilt from surviving
artifacts and proven launchable — the name-level invalidation-chain
instrument restored; (3) TWO new generic roots root-caused, fixed, and
regression-proven (F-NEW-278 multi-DEX annotations, F-NEW-279 getSuppressed)
that blocked the oracle BEFORE the invalidation chain could be observed by
real name; (4) the oracle's current first divergence precisely decoded
(name + bytecode level) at the HostDefaultProvider chain. dooz's own
invalidation link stays PARTIAL — the 11-link chain stands at link 2.

---

## 0. TRUTH LOCK (Phase 0)

| item | value |
|---|---|
| git HEAD (start) | `364aa041f89941cdcbf8fef0795a7e7cd670d804` == origin/main (fetched; local was 47 behind, fast-forwarded) |
| working tree | clean except `tmp/flappycow` submodule test residue |
| baseline binary rebuilt from HEAD | BYTE-EXACT `e980887e39aee977c4634ea9944fb80aaec3ba6c1e01556f146054cc89b651d2` (the CONT-25 patch binary — F-277 poll-timeout law included) |
| pre-fix baseline binary | `fa88902fdee6e982...` (CONT-22/23/24 lineage; source delta = the F-277 poll-timeout law, audited CONT-25; NOT rebuilt this wave — the e980887e reproduction covers lineage verification because 364aa041 differs from 05f6d162 only by worklog/issue-comment files) |
| Issues read | #384 (HTML scrape — 5 comments; GitHub API rate-limited for the REST origin, recorded), #385 + #383 content from committed evidence (CONT-25 truth lock) |
| root registry at lock | 586 rows; F-NEW-277 CLASSIFIED P0; F-NEW-266/271/274/275 ROOT-CAUSED-FIXED (claim re-verified: all four present with their fix evidence) |
| dooz APK | `upload/canonical_apks/io.github.yamin8000.dooz_23.apk` sha256 `299eab21ac8b3c61...` == registry |
| oracle APK (rebuilt) | `run/w8/oracle12.apk` 8,233,173 bytes — size-EXACT vs the CONT-12 record (sha16 differs from the recorded `f65b13ad446d1a57`; recorded honestly — container toolchain drift, identity verified by size + id table + behavior) |

---

## 1. A1 — DOOZ BASELINE REPRODUCTION AT HEAD (directive D-A1)

Protocol: install + `run --package io.github.yamin8000.dooz --width 1080
--height 1920 --frames 5 --max-seconds 15` (canonical sweep).

| item | value |
|---|---|
| screenshot | `d602648e8e401895b7b440bc9c0becd4af8748b37808ce0870735b19502dab71` — the frozen anchor, byte-identical x3 (regression §4) |
| verdict | DEFAULT_BACKGROUND_ONLY (first_missing_stage=APP_DRAW_OPS) |
| [F277-POLL] | fires ONCE: "quiescence poll-timeout fast-forward to virtual_ms=16 (delta=16ms)" |
| 16ms stranded task | **NOW RUNS** (CONT-25's fix confirmed live): `[QUEUE] Runnable id=2670 dequeued (ready_at=16ms <= now=16ms virtual)` → `[EXP090-DRAIN] Invoking Runnable id=2670 class=Ld4;` — the strand that was "removed-never-run" in the pre-fix baseline |
| pump end | `[F100-STATE] quiescence at tick=5 pending_cb=0 queue_size=0` — EMPTY queue; `[CHOREO-PUMP] 3 frame(s) fired (bound=8)` — no new frame callbacks post |
| composition #2 | STILL NEVER STARTS — the wake-up work (invalidation delivery) is not in the handler queue |

Trace: `run/cont26/logs/dooz_trace1.log` (MINIANDROID_METHOD_TRACE=1,
153,847 lines). Class census: Ltp1;(StateFlowImpl) 273 entries,
Lza1;(RecomposeScopeImpl) 123, Lzh; 396, Lh9; 8 — the collector/dispatch
link never materializes as queue work (matches the CONT-25 census law).

---

## 2. THE ORACLE INSTRUMENT — REBUILD + VERIFICATION (directive D-A2)

The CONT-12 oracle (un-renamed real Compose 1.11.4 + navigation 2.9.8,
D8-only, no R8) is the ONLY instrument that can observe the invalidation
chain by REAL method name. Its build inputs survived the container reset;
the final APK and `tmp/cont12_resbuild/apk/` did not.

Rebuild procedure (all local, no network):
1. `scripts/cont12_oracle_res2.sh` — aapt2 compile/link of all 55 local AARs'
   res/ → merged resources.apk **491,968 bytes == the recorded size**;
   R-package scan pointed at the surviving `tmp/cont12_oracle_build/dex/`
   (script fixed: run/w8 was wiped with the container) → 16 R packages,
   176 R classes, rclasses.jar 168,155 bytes; `view_tree_lifecycle_owner =
   0x7f05005a` == the recorded id.
2. `scripts/cont12_build_oracle.sh` — kotlinc 2.1.20 + compose compiler
   plugin + D8 over probe + 55 real jars + R classes.
3. Result: `run/w8/oracle12.apk` **8,233,173 bytes == the recorded size**.
   sha256 `d39040018708474b6fe8c3f943a4c79b1810f315848013768935fba631f4332c`
   (recorded sha16 was `f65b13ad446d1a57` — NOT byte-identical; the honest
   identity basis is size-exactness + the id-table check + behavior parity
   at the recorded divergence points, NOT a fabricated sha claim).

Oracle baseline run at HEAD binary e980887e (`run/cont26/oracle_base1/`):
2 uncaught faces past app frames — BOTH name-level, both FIXED this wave
(§3); the oracle thereby advanced past the three divergences CONT-12
bounded as "next wave" (navigator annotation lookup + the two follow-ons)
into the compose snapshot/view-tree machinery.

---

## 3. TWO NEW GENERIC ROOTS FIXED EN ROUTE (directive D-A3/A4)

### F-NEW-278 — multi-DEX class-annotation closure (P0, ROOT-CAUSED-FIXED)

- Face: `NavigatorProvider.Companion.getNameForNavigator` →
  `[F087] getAnnotation queried class=Landroidx/navigation/NavGraphNavigator;
  annotation=Landroidx/navigation/Navigator$Name; indexed=NO` → IAE "No
  @Navigator.Name annotation found for NavGraphNavigator" → rememberNavController
  dead → NavHost dead → composition never completes.
- DEX ground truth (`scripts/cont26_dex_ann_scan.py`): the annotation IS in
  the binary — `Navigator$Name` **vis=1 (RUNTIME) value='navigation'** on
  NavGraphNavigator, in classes2.dex.
- Root: `class_annotations_` populated only from DEX 0
  (dalvik_engine.cpp:692); `inject_secondary_dex_classes()` merged classes,
  superclasses (EXP-095) and interfaces (S102) but not annotations. Upstream
  law: ART copies runtime-visible annotations into the Class at load time,
  DEX-file boundary invisible.
- Fix: third closure loop in inject_secondary_dex_classes() (same dedup
  law). Post-fix: `[F087-MD-ANN] class-annotation index extended by 361
  secondary-DEX classes (total 698)`; the IAE is GONE.
- Affected surface: EVERY multi-DEX APK's runtime class annotations.

### F-NEW-279 — Throwable suppressed-exception law (P1, ROOT-CAUSED-FIXED)

- Face: the navigator IAE was caught by compose's GapComposer.doCompose
  catch-all, which attaches a compose stack trace →
  `ComposeStackTraceKt.tryAttachComposeStackTrace` →
  `JDK7PlatformImplementations.getSuppressed` →
  `Intrinsics.checkNotNullExpressionValue` → **NPE "getSuppressed(...) must
  not be null"** thrown INSIDE the exception handler → uncaught → APP
  BOUNDARY.
- Root: no getSuppressed handler at all (grep audit) → the typed stub
  answered null. OpenJDK law (Throwable.java, Java 7+): getSuppressed()
  returns an EMPTY array when none recorded — NEVER null; Kotlin asserts
  the non-null contract.
- Fix: Throwable-family law — getSuppressed() answers a heap
  `[Ljava/lang/Throwable;` array (recorded `__suppressed__` list or
  zero-length); addSuppressed(t) appends (self-suppression ignored).
  Post-fix: the face is GONE.
- Affected surface: every Kotlin exception-inspection path
  (getSuppressedExceptions family).

Dedup: no existing registry row covers either family (checked
annotation/getSuppressed/Navigator.Name across 586 rows; F-NEW-250 is the
kotlinx.serialization face — different family; F-NEW-191 is METHOD
annotations — different surface; R-NEW-464 is method records — different
surface). Both fixes carry no app/package/R8-name knowledge (grep audit on
the diff).

---

## 4. THE ORACLE'S CURRENT FIRST DIVERGENCE — THE HOST-DEFAULT CHAIN
   (directive D-A2: recorded, NOT claimed fixed)

After F-NEW-278+279 the oracle run advances into NavHost composition and
dies with a single ISE:

```text
IllegalStateException "NavHost requires a ViewModelStoreOwner to be provided
via LocalViewModelStoreOwner" at NavHostKt.NavHost pc=1780 (checkNotNull)
```

Decoded chain (all name-level, from the real-DEX trace
`run/cont26/logs/oracle_tr1.log` + disassembly
`scripts/cont26_dex_method_disasm.py`):

```text
LocalViewModelStoreOwner.getCurrent(composer)
  → GapComposer.consume (real DEX, 9 units)
  → CompositionLocalMapKt.read(map, local)          (25 units)
      map.get(local) — LocalViewModelStoreOwner never provided → NULL
      → local.getDefaultValueHolder$runtime() → ComputedValueHolder
      → readValue(scope) → computed lambda (compositionLocalWithHostDefaultOf$lambda$0)
          → HostDefaultProviderKt.getLocalHostDefaultProvider
          → scope.getCurrentValue(LocalHostDefaultProvider)  [map HIT — provider found]
          → provider.getHostDefault(key)                     ← EXECUTION DIVERGES HERE
             (upstream ViewTreeHostDefaultProvider.getHostDefault:
              key instanceof ViewTreeHostDefaultKey → TRUE;
              view-tree walk getTag(view_tree_view_model_store_owner)
              climbing getParentOrViewTreeDisjointParent)
```

Engine-side facts proven:
- The TAG data is present and correct: `[TAG-TRACE] setTag view=150 (decor)
  key=2131034206 kind=1 obj=12` (ComponentActivity.initializeViewTreeOwners
  ran by real name) and a later walk from the activity view HITS it
  (`getTag view=12 key=2131034206 hit=0 parent=150` → `getTag view=150
  key=2131034206 hit=1`).
- The computed-default lambda RUNS and the provider map lookup SUCCEEDS
  (`PersistentHashMap.get` chain → `valueAtKeyIndex`), but the lambda's
  tail (`check-cast v2, HostDefaultProvider;` + `invoke-interface
  getHostDefault`) NEVER EXECUTES — the method is never entered (zero
  METHOD-IN rows for ViewTreeHostDefaultProvider.getHostDefault) and no
  getTag walk happens during the lambda; the caller resumes with the
  resolved value being null → checkNotNull fires.
- The key class hierarchy is verified:
  `LocalViewModelStoreOwner_androidKt$ViewModelStoreOwnerHostDefaultKey$1`
  implements `ViewTreeHostDefaultKey` (cross-dex interface), so the
  upstream `key !is ViewTreeHostDefaultKey<*>` gate must answer FALSE (walk
  proceeds) — the engine skipped the walk entirely.

Classification: the divergent link is the engine's execution of the
computed-default lambda tail (invoke-interface dispatch / register
reconciliation inside a real-DEX lambda). NOT yet fixed — recorded with the
exact bytecode offsets (lambda$0 size=17: invoke getCurrentValue @0x0006,
getHostDefault @0x000c) as the next wave's opening target. Per directive
§8 this is a MOVED divergence, not a rendering claim: the oracle shows
DEFAULT_BACKGROUND_ONLY, zero app draw ops.

---

## 5. STATUS LEDGER

| item | status |
|---|---|
| Phase-0 truth lock (HEAD/binary/APK/issues/registry) | TESTED |
| A1 dooz baseline + 16ms strand status re-verified | TESTED |
| Oracle rebuilt from surviving artifacts | TESTED (size-exact; sha honestly recorded as non-identical) |
| F-NEW-278 root-caused + fixed | IMPLEMENTED+TESTED |
| F-NEW-279 root-caused + fixed | IMPLEMENTED+TESTED |
| Oracle invalidation-chain observation by real name | PARTIAL — next divergence decoded to bytecode level (§4) |
| dooz invalidation link reached | NOT YET — chain stands at link 2 (delivery), PARTIAL |
| Real app-owned Compose pixels | NOT ACHIEVED (no claim) |
| Skeleton/合成/chrome excluded from proof | OBSERVED (skeleton-light untouched, default OFF) |
| Full regression at final binary | TESTED (§REGRESSION_MATRIX) |
