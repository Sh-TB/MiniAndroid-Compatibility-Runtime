# ISSUE 518 [Coder4-W9] state=open

# [W7] Coder-4 wave 7 — Thunderbird's Koin NoDefinitionFoundException ×32 is DEAD: the root was `SecureRandom` REC-MISS minting ONE uuid for ALL 100 modules → `Module.equals` answered TRUE for every pair → flatten's visited-guard swallowed EVERY include · law F-C4-572 (SecureRandom real-stream) · all four titles now dispatch Activity `onResume`

**Track:** `4APP4` · **Owner:** Coder-4 · **Epic:** #430 · **Wave log:** #436 (W6 → W7)

**Base:** `main` HEAD `ea490b82` + `w6_stack.patch` (#517, 1306 lines) + `w6_laws.patch` (#517, F-C4-569/570/571). **Binary this wave:** `d5c99397dfd5aca9`. **APK pins re-verified byte-identical this session:** TB `473b33da5963d0a4` · NC `c9ba2e85b13fee45` · TK `8154cabe67374f2e` · CB `96cf501a83e89284`.

## WHAT THIS ISSUE IS ABOUT

Wave 7 of the four-title program. One live-proven root-cause chain that held Thunderbird at TB-M1 since W2 (the Koin DI starvation), the law that kills it, an honest correction to my own W6 conclusion, and the re-baselined state of all four titles on the final W7 binary. Everything below was measured this session on the pinned APKs.

## THE ACHIEVEMENT — TB's Koin NDFE ×32 root-caused to ONE unimplemented JDK method, and killed

**Forensic chain (every link live-proven this wave, tools: bytecode dumps of the pinned APK + env-gated engine probes):**

1. `[F566-IGET]` — `ThunderbirdApp.attachBaseContext` → `DI.start(context, listOf(appModule))` → the KoinApplication lambda calls `Koin.loadModules(SingletonList([appModule obj#181]))` — the SEED is the REAL static `ThunderbirdKoinModuleKt.appModule` (its includes list holds 5 modules: `[W6-INCL] list obj#203 __array_length__=5 arr[0]=o208 arr[1]=o433 …`).
2. **W6 correction (recorded honestly):** my W6 verdict "the top module's includes list is a HOLLOW ArrayList" was WRONG. On the W6 binary the list obj#203 answers `size()=5` (`[IFACE-RT] List.size()I via runtime ReversedList (recv obj#5329, delegate obj#203) ret_int=5`) and the backward `listIterator(5)` walk yields all 5 modules (`[F566-LI] listIterator(5) box=5331 parent=203`, `[F566-HP] pos=5→1 … pos=0→0` — 5×TRUE + final FALSE, a perfect walk). The W2–W6 collection laws WORK. The drop was one level deeper.
3. The flatten loop (`Koin.loadModules` pc 59–80, decoded from the DEX): `while (hasPrevious) { m = previous(); if (!visited.contains(m)) worklist.addLast(m) }` — live probes show `contains` runs for all 5 includes (`[F572-CONTAINS-ENTER] recv=5322 cls=LinkedHashSet item=o5112/4588/4540/433/208`) and **`ArrayDeque.addLast` is NEVER dispatched** (ARG-TRACE over every `kotlin/collections/ArrayDeque` invoke: `isEmpty/getSize/removeLast/registerModification/positiveMod` all present, `addLast` absent).
4. Why: the branch after `contains` (`if-ltz v5 → loop head`) — the shadow `contains` consults the element's own `equals` (`app_equals_slot` → `app_object_equals(181, candidate)` → the REAL DEX `Module.equals`). **Koin 4's `Module` overrides `equals`/`hashCode` by its `id`** (DEX: `Module; virtual: equals, hashCode, indexPrimaryType`), and `id = Uuid.random().toString()`.
5. **THE ROOT:** `kotlin-uuid`'s `Uuid.random()` → `SecureRandomHolder` → `Ljava/security/SecureRandom;.<init>` and `.nextBytes` are **REC-MISS** (live: `[REC-MISS] Ljava/security/SecureRandom;.nextBytes caller=Landroidx/work/OperationKt;.random` — the R8-renamed `Uuid.random`). The byte array stays zero → `[M3-LONG-PUT] mostSignificantBits=16384, leastSignificantBits=Long.MIN_VALUE` — **the IDENTICAL uuid for ALL 100 modules** → `Module.equals` answers TRUE for ANY two modules → `visited.contains(m)=TRUE` for every include → **every include is skipped as "already visited"** → the worklist dies at depth 1 → only the seed's 451 direct definitions are indexed (of 2707 created) → `Scope.resolveFromContext pc=734` throws `NoDefinitionFoundException` at the first `by inject()` (`Logger`, `GeneralSettingsManager`, …) ×32.
6. **THE FIX — law F-C4-572 (SecureRandom real-stream):** `SecureRandom.<init>` materializes an operational PRNG; `nextBytes(byte[])` fills the WHOLE buffer from a **xorshift64\* stream seeded with a constant** — byte-identical across runs (the evidence determinism law), distinct per call (OpenJDK stream semantics within a run). 40+ firings this run, every byte fill distinct (`b0=246, 99, 128, 179, 140 …`).
7. **RESULT (same APK, same data-root):** NDFE ×33 → **0 uncaught** (3 trace lines = ONE benign occurrence caught by `Scope.getOrNull`'s typed handler). The DI graph resolves; eager instantiation runs; **`Lnet/thunderbird/app/common/MainActivity;.onCreate` + `.onResume` DISPATCH for the first time** (`[FRAGMENT-LIFECYCLE] method=onResume declared_in=Lnet/thunderbird/app/common/MainActivity;` — TB's honest frontier moves from "arrested before first app draw op" to "inside the real Activity lifecycle").

**ONE-SIMPLE-TEST accept:** on a w6_stack+w6_laws tree with this law applied, `./build/miniandroid run --data-root <tb> --package net.thunderbird.android -o /tmp/tb7 --max-seconds 75 2>&1 | grep -c NoDefinitionFound` answers **≤ 3**, and `grep -c "MainActivity;.onResume"` on the same stderr answers **1**. **Reject:** revert the F-C4-572 hunk → NDFE returns to 33 and onResume disappears (independent: the law is one self-contained hunk in `dalvik_engine.cpp`).

## A/B — all four titles on the final W7 binary (same APKs, same data-roots as W6)

| App | W6 family | W7 family (crash.log census) | stderr sha16 (W7) | Lifecycle proof |
|---|---|---|---|---|
| Thunderbird | Koin NDFE ×32 (DI starvation) | **KILLED** → K9StoragePersister `Storage database upgrade failed!` Room/SQLite migration ×15 (caught, app continues) + Koin `InstanceCreationException` ×11 (the storage failure wrapped; caught) | `e04500569e256f0d` | **`MainActivity.onResume` dispatched** (first time) |
| Nextcloud | `DispatchingAndroidInjector.<init>` NPE ×32 (Guava ImmutableMap chain) | **MOVED**: `AndroidInjection.inject` IllegalArgumentException ×4 + `ActivitySplashBinding.inflate` NPE ×1 + the ImmutableMap ctor NPE now ×1 (was ×32) | `04806d32242fc906` | **`LauncherActivity.onResume` dispatched** (first time) |
| Tusky | conscrypt `checkAvailability` ULE + `Lig/a;.x` NPE, 20 errors | 14 exceptions: `Lri/a;.get` NPE ×5 ("length of null array") + conscrypt `NativeCrypto.checkAvailability` ULE ×1 — the JNI_OnLoad SIGSEGV message now carries the exact fault (`libconscrypt_jni.so extracted … JNI_OnLoad faulted (SIGSEGV/SIGBUS at the handshake) against the minimal JavaVM bridge`) | `6b6f1cf665ee035f` | **`MainActivity.onResume` dispatched — 139 real instructions executed** |
| ConnectBot | conscrypt `OpenSSLProvider.<init>` ULE, 5 errors | family UNCHANGED (the C3-tail) — but `MainActivity.onResume` now dispatches; ULE escapes at `MainActivity.onCreate pc=0x18e` via `TerminalManager.onCreate` → `OpenSSLProvider.<init>` | `a2ba8965c77418d4` | **`MainActivity.onResume` dispatched** |

## THE CODE CHANGE (exact, reviewable)

**`w7_laws.patch` — 137 lines, sha16 `ea55443a44263012`, `git apply` on a w6_stack+w6_laws tree (verified CLEAN this session).** Full text below. Two files:

1. `miniandroid/src/dex/dalvik_engine.cpp` — law F-C4-572: the `Ljava/security/SecureRandom;` bridge (`<init>` materialization + `nextBytes` whole-buffer xorshift64\* fill, bounded 64K, env-gated `[F-C4-572]` trace, `MINIANDROID_F572_DIAG`). Placed directly above the F-113 SecureRandom-IS-A-Random law (same determinism discipline: constant seed, per-call advance).
2. `miniandroid/src/framework/android_shadows.cpp` — the F-C4-572 forensic probes (bounded, env-gated `MINIANDROID_F572_PROBE`, zero behavior change): `[F572-CONTAINS-ENTER]` at the shadow `contains` law entry + `[F572-CONTAINS-RET]` on the array/identity/final-false exits — the instrument that pinned the silent `contains`→`app_equals`→`Module.equals` exit.

## VERIFY (60 s, one command each, on a w6_stack + w6_laws + w7_laws tree)

```bash
# 1. The law fires with distinct fills (40+ lines, b0 varies):
MINIANDROID_F572_DIAG=1 ./build/miniandroid run --data-root <tb> \
  --package net.thunderbird.android -o /tmp/tb572 --max-seconds 75 2>&1 \
  | grep "F-C4-572" | head        # b0=246 / 99 / 128 / … — NEVER the same twice

# 2. The NDFE family is dead and TB reaches the Activity lifecycle:
./build/miniandroid run --data-root <tb> --package net.thunderbird.android \
  -o /tmp/tb7 --max-seconds 75 2>&1 > /dev/null 2> /tmp/tb7.err
grep -c NoDefinitionFound /tmp/tb7.err          # ≤ 3 (was 33)
grep -c "MainActivity;.onResume" /tmp/tb7.err   # 1 (was 0)

# 3. The patch applies clean on the W6 tree:
git apply --check w7_laws.patch   # on w6_stack+w6_laws — silent = CLEAN
```

**How to reject me:** revert the single F-C4-572 hunk → VERIFY 1 goes to zero lines, VERIFY 2 returns to 33/0. Blast radius honestly: the law changes ONLY `Ljava/security/SecureRandom;.<init>`/`nextBytes` dispatch (previously REC-MISS — no app could have depended on the constant fill) — corpus-wide it can only ADD entropy where there was none; the deterministic constant seed keeps cross-run evidence byte-identical (the whole F-113 law family already follows this discipline).

## W8 QUEUE (honest frontiers, per app)

- **TB (TB-M1 first paint):** `K9StoragePersister.loadValues` → `DBUtil` "Storage database upgrade failed!" ×15 — the Room/SQLite migration family is now the honest blocker between the app and its first app-owned draw op (onboarding UI). Next: trace the migration failure under DBUtil (likely a SQLite DDL/transaction path in the shadow backend).
- **NC (NC-M1):** `AndroidInjection.inject` IAE ×4 — the Dagger activity-injection argument validation; then `ActivitySplashBinding.inflate` NPE (the splash layout inflation chain).
- **TK/CB (C3-tail, shared):** the conscrypt `JNI_OnLoad` JavaVM handshake — TK's fault message now pins the exact SIGSEGV site (`libconscrypt_jni.so` at the `JNI_OnLoad` handshake against the minimal JavaVM bridge). This remains the single biggest shared unlock (TK TLS + CB's `OpenSSLProvider`).
- **TK private family:** `Lri/a;.get` NPE ×5 ("length of null array") — next in line after C3.

## Diagnostics added this wave

`MINIANDROID_F572_DIAG` (law firings: arr, n, b0, caller — proved distinct fills) · `MINIANDROID_F572_PROBE` (`[F572-CONTAINS-ENTER/RET]` — the visited-guard forensics that pinned the silent `Module.equals` exit) · `MINIANDROID_ARG_TRACE` used over `kotlin/collections/ArrayDeque` (the addLast-absence proof) and `org/koin/core/module/Module` (the 100-ctor census + duplicate-seed disproof).

— **Coder-4** (wave 7, session evidence: binary `d5c99397dfd5aca9`, all runs this session on the four pinned APKs)
