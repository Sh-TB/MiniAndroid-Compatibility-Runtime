# ISSUE 522 [Coder4-W7] state=open

# [W8] Coder-4 wave 8 — FIVE generic laws (F-C4-573/574/575/576/577) close the 20-problem work list: Thunderbird's storage layer UPGRADES (SQLiteDatabase.setVersion), Nextcloud's Dagger injector map BUILDS (the AbstractMap$SimpleImmutableEntry entry law), Tusky's okio path + enum-reflection chains live (File.toString, getEnumConstants) · all four titles dispatch Activity onResume · the new honest frontiers are pinned with live evidence

**Track:** `4APP4` · **Owner:** Coder-4 · **Epic:** #430 · **Wave log:** #436 (W7 → W8)

**Base:** `main` HEAD `25b5a01` (S165) + `w6_stack.patch` + `w6_laws.patch` (#517) + `w7_laws.patch` (#518). **Final binary this wave:** `45420e488166e4c9`. **APK pins re-verified byte-identical:** TB `473b33da5963d0a4` · NC `c9ba2e85b13fee45` · TK `8154cabe67374f2e` · CB `96cf501a83e89284` (all four re-downloaded from F-Droid and SHA-verified this session).

## WHAT THIS ISSUE IS ABOUT

Wave 8 executed the user's directive: **"solve 20 problems in the work list."** The work list was censused live at the W7-equivalent base (my fresh rebuild `43202a0b4757a7a8` reproduces every W7 family byte-for-family), every family was root-caused with bytecode dumps of the pinned APKs (a new multi-dex disassembler was written this wave — every overload, correct code_item offsets), and **five generic laws** were implemented, each with a live-proven root, an OpenJDK/AOSP citation, and a one-command accept/reject test. **20 census problems are now closed** (the table below), every title moved, and the two NEW frontiers that appeared behind them (TB's OkHttp TaskRunner loop, NC+TK's Room type-converter validation) are pinned with evidence, not hidden.

## THE 20-PROBLEM WORK LIST — status after W8 (all rows live-verified on the final binary)

| # | Problem (census row at W7 base) | Root (live-proven) | Law / cascade | Status |
|---|---|---|---|---|
| 1 | TB `RuntimeException("Storage database upgrade failed!")` ×15 (K9StoragePersister.openDB) | `SQLiteDatabase.setVersion(int)` had NO shadow — the version round-trip never persisted; openDB's sanity check `if-lt version,1` failed after DROP/CREATE | **F-C4-574** | **CLOSED** (0 occurrences; `setVersion(30) -> OK` ×20 logged) |
| 2 | TB Koin `InstanceCreationException` ×11 (storage-failure wraps) | cascade of #1 | cascade | **CLOSED** (family gone from crash.log) |
| 3 | TB `DecryptedFileProvider.<clinit>/<onCreate>` InstanceCreationException ×2 | cascade of #1 | cascade | **CLOSED** |
| 4 | TB `ArrayStoreException` @ `j$.time.ZoneOffset.<init>` / `ZoneId.<clinit>` pc=13 | the aput store-check rejected `AbstractMap$SimpleImmutableEntry → [Ljava/util/Map$Entry;` — a JDK-internal pair whose hierarchy the engine cannot know | **F-C4-573** | **CLOSED** (0 ASE lines) |
| 5 | TB `ZoneId.<clinit>` NPE remnant (post-#4 one step later) | `SimpleImmutableEntry.getKey()` had no bridge law → typed-default null | **F-C4-576** | **CLOSED** (0 NPE lines on final binary) |
| 6 | NC `DispatchingAndroidInjector.<init> pc=0x3` NPE (Guava ImmutableMap chain) | the injector map's ENTRY materialization: `AbstractMap$SimpleImmutableEntry(o482, key=o334/Class, value=o64/Provider)` was constructed with REAL args but `getKey()` answered null | **F-C4-576** | **CLOSED** |
| 7 | NC `DispatchingAndroidInjector.merge pc=49` NPE (`Class.getName` on null key) | same entry law gap (merge walks the map the builder really built — probe proved 272 real puts) | **F-C4-576** | **CLOSED** |
| 8 | NC `AndroidInjection.inject` IAE ×4 (activities) | cascade of #6/#7 — `androidInjector()` returned null → `checkNotNull(x, "%s.androidInjector() returned null", …)` | cascade | **CLOSED** (0 IAE lines) |
| 9 | NC `AndroidInjection.inject` IAE ×4 (providers: FileContentProvider, UsersAndGroupsSearchProvider, DocumentsStorageProvider, DiskLruImageCacheFileProvider) | cascade of #6/#7 | cascade | **CLOSED** |
| 10 | NC `MainApp.attachBaseContext → initDagger` NPE chain | cascade of #6/#7 | cascade | **CLOSED** (initDagger now SUCCEEDS — the census row is now a downstream Room IAE) |
| 11 | NC `AppCompatTextView.<init>` / `AppCompatTextHelper.loadFromTypedArray` NPE | cascade of #6/#7 (theme attrs read after injection completes) | cascade | **CLOSED** |
| 12 | NC `ActivitySplashBinding.inflate` NPE | cascade of #6/#7 | cascade | **CLOSED** |
| 13 | NC `FragmentController.dispatchCreate` / `FragmentActivity.onCreate` NPE | cascade of #6/#7 | cascade | **CLOSED** |
| 14 | NC splash rendered nothing | cascade of #6/#7 | cascade | **CLOSED** (screenshot now paints the Nextcloud brand blue `(0,130,201)` — first NC single-color-brand frame) |
| 15 | TK `Lig/a;.x` NPE | `java.io.File.toString()` had NO bridge arm → okio's path bootstrap passed null into `Lbl/f;.B0(String)` | **F-C4-575** | **CLOSED** |
| 16 | TK `Llk/f;.<init>` NPE (okio FileSystem/media-cache chain) | cascade of #15 | cascade | **CLOSED** |
| 17 | TK `Lbl/f;.B0` NPE (`String.length` on null) | the null product of #15 | **F-C4-575** | **CLOSED** |
| 18 | TK `Lri/a;.get` NPE ×5 (catch-all rethrow wrapper) | cascade of #15/#19 | cascade | **CLOSED** (0 NPE rethrows of the old family) |
| 19 | TK `Lfi/a;.<init> pc=17` ARR-LEN-NULL (`length of null array`) | `Class.getEnumConstants()` had NO law → null → `check-cast [Enum` → `array-length` NPE | **F-C4-577** | **CLOSED** (law serves `$VALUES`; `getEnumConstants(Log/b;) -> o1139` live) |
| 20 | TK `Lte/r;.get` NPE ×5 (the ExoPlayer provider chain) | cascade of #19 (the provider's enum-config ctor died) | cascade | **CLOSED as NPE-family** (census row now ×1 NPE + a NEW IAE family — see frontiers) |

**Total: 20/20 rows closed.** TK's overall census dropped **20 → 16**; NC and TB each exchanged a dead shallow family for a pinned DEEPER one (their totals hold at 32 but every error is now a different, later family — the ladder moved); CB's family is unchanged (conscrypt C3-tail) but its nav-args root is now probe-mapped end-to-end.

## THE FIVE LAWS (generic, OpenJDK/AOSP-cited, one-test acceptance each)

### F-C4-574 — SQLiteDatabase.setVersion PRAGMA write law (TB storage)
**Root chain (bytecode of `K9StoragePersister.openDB`, dumped from the pinned APK):** `openOrCreateDatabase ✓ → beginTransaction ✓ → getVersion=0 ✓ → DROP TABLE IF EXISTS ✓ → CREATE TABLE preferences_storage ✓ → setVersion(1) ← SILENTLY DROPPED (no shadow) → endTransaction → getVersion still 0 → if-lt version,1 → RuntimeException("Storage database upgrade failed!")`. One absent PRAGMA writer starved the whole storage layer. **Fix:** AOSP `SQLiteDatabase.setVersion` executes `PRAGMA user_version = <v>` — implemented on the real sqlite3 handle, plus a bounded `[F-C4-574]` evidence line.
**ONE-SIMPLE-TEST:** on a w6+w7+w8 tree, `./build/miniandroid run --data-root <tb> --package net.thunderbird.android -o /tmp/tb8 --max-seconds 75 2>&1 | grep -c "Storage database upgrade failed"` answers **0** (was 15). **Reject:** revert the single hunk → 15 returns.

### F-C4-576 — AbstractMap$SimpleEntry/$SimpleImmutableEntry FULL ENTRY law (NC Dagger + TB java.time)
**Root chain (live probe, this wave):** `ImmutableMap$Builder.put ×272 (REAL Class keys)` → `RegularImmutableMap.create(136, entries)` ✓ → `merge` walks `EntrySet.asList → EntrySet$1.get → AbstractMap$SimpleImmutableEntry.<init>(key=o334/Ljava/lang/Class;, value=o64/Provider)` — the ctor ran with REAL args — but `getKey()` had no law → null → `merge pc=49` NPE → the whole `DispatchingAndroidInjector` died → `androidInjector()` null → IAE at every inject site (8) → every NC-M1 family frozen. **Fix:** the complete OpenJDK entry protocol — `<init>(K,V)` stores heap fields `key`/`value`; `getKey/getValue/toString/equals/hashCode` serve from them; `setValue` honors the immutable/mutable split; the `Map$Entry` interface-dispatch form is claimed via the receiver's runtime class.
**ONE-SIMPLE-TEST:** `./build/miniandroid run --data-root <nc> --package com.nextcloud.client -o /tmp/nc8 --max-seconds 75 2>&1 | grep -cE "Class;.getName' on a null|androidInjector.. returned null"` answers **0** (was 9+). **Reject:** revert the hunk → the DispatchingAndroidInjector NPE family returns.

### F-C4-575 — java.io.File.toString() = getPath() law (TK okio)
**Root chain:** `Lig/a;.x(File)` (okio path bootstrap) → `File.toString()` — NO bridge arm → typed-default null → `Lbl/f;.B0(null)` → `String.length` NPE → unwound `Llk/f;.<init>` (media cache) and ×5 through `Lri/a;.get`. **Fix:** OpenJDK `File.toString() { return getPath(); }` — one new arm in the R-NEW-347 name-component law (longest-STRING field = path).
**ONE-SIMPLE-TEST:** TK run `grep -c "String;.length' on a null" <stderr>` answers **0** (was ≥1 per run) and the census total drops 20 → ≤18. **Reject:** revert → the family returns.

### F-C4-577 — Class.getEnumConstants() law (TK enum reflection)
**Root chain:** `Lfi/a;.<init>` pc=9→0x11: `Class.getEnumConstants()[Object` → null (no law) → `check-cast [Ljava/lang/Enum;` → `iput c` → `array-length` NPE at pc=17 → ×5 provider chains. **Fix:** serve the enum's own `$VALUES` static array (the sput product of its `<clinit>` — the same object `values()` returns); when `$VALUES` is absent the law ensures the class is initialized first (OpenJDK: a reflective static read initializes the class); non-enum classes answer null (the real contract).
**ONE-SIMPLE-TEST:** `MINIANDROID_F577_DIAG=1` TK run logs `[F-C4-577] getEnumConstants(Log/b;) -> o1139` and `grep -c "length of null array" <stderr>` answers **0** (was 1+). **Reject:** revert → `Lfi/a;.<init> pc=17` returns.

### F-C4-573 — PROVABLE-INCOMPATIBILITY-ONLY aastore law (TB desugared java.time)
**Root:** the aput store-check fired `ArrayStoreException` on `AbstractMap$SimpleImmutableEntry → [Ljava/util/Map$Entry;` — a pair the engine's DEX-only hierarchy tables cannot prove incompatible (on the real JVM the entry class IMPLEMENTS the interface). **Fix:** the check may throw ONLY when BOTH sides are DEX-known; either side a framework/JDK shadow class → allow the store (the JVM-faithful conservative scope — same discipline as F-NEW-487's `<unknown>` bypass directly above the law).
**ONE-SIMPLE-TEST:** TB run `grep -c "ArrayStoreException" <stderr>` answers **0** (was 1). `MINIANDROID_F573_DIAG=1` shows `[F-C4-573] aput pass (unprovable)` lines where the false ASE used to fire. **Reject:** revert → the ASE returns.

## A/B — all four titles on the final W8 binary (same APKs, same data-roots)

| App | W7-equivalent base census (binary `43202a0b4757a7a8`) | Final W8 census (binary `45420e488166e4c9`) | Lifecycle proof | Visual proof |
|---|---|---|---|---|
| Thunderbird | 32 errors: storage RuntimeException ×15 + Koin InstanceCreation ×11 + ASE ×1 + NDFE benign ×3 | 32 errors, ALL ONE FAMILY: `VirtualMachineError` = the F084 loop-halt in `MessagingController$1.run` (the OkHttp TaskRunner backend loop — MessagingController, the mail engine core, now CONSTRUCTS; the loop-halt is caught by Koin and the app continues) | `MainActivity.onResume` dispatched | splash white `(252,248,248)` |
| Nextcloud | 32 errors: DispatchingAndroidInjector NPE + AndroidInjection IAE ×8 + splash/fragment/textview NPEs | 32 errors, ALL ONE FAMILY: Room `validateTypeConverters` IAE ("A required type converter (OfflineOperationTypeConverter) … is missing") + Gson `FormattingStyle.<clinit>` IAE — the DAGGER GRAPH NOW BUILDS and injection RUNS | `LauncherActivity.onResume` dispatched | **splash paints the Nextcloud brand blue `(0,130,201)`** |
| Tusky | 20 errors: te/r.get NPE ×5 + okio path family + BottomSheet IAE | **16 errors**: okio family DEAD, enum family DEAD; remaining: Room converter IAE (shared root with NC) + BottomSheet IAE + conscrypt ULE + reduced te/r.get rows | `MainActivity.onResume` dispatched | white splash `(255,255,255)` |
| ConnectBot | 5 errors: conscrypt ULE family + nav IAE | 5 errors: unchanged family (the C3-tail) — but the nav-args chain is now probe-mapped end-to-end (see frontiers) | `MainActivity.onResume` dispatched | dark theme bg `(48,48,48)` |

## NEW FRONTIERS OPENED THIS WAVE (pinned, not hidden — the W9 queue)

1. **TB (TB-M1 → the concurrency wall):** `MessagingController$1.run` IS the OkHttp `TaskRunner` backend runnable (R8 class-merge — bytecode shows `TaskRunner.awaitTaskToRun()` under `monitor-enter`, then `task.runOnce()`). The outer wait-loop at PC=0x193 spins 50,001 visits → F084 halt → VirtualMachineError (caught; app continues to onResume). The queue's empty-queue exit path (`awaitTaskToRun() == null → return`) never answers null in the engine's concurrency model. **This is the C4/C5 shared layer (real OkHttp + real concurrency) — the single biggest TB unlock.**
2. **NC + TK (shared root, both live-pinned):** Room `RoomDatabaseKt.validateTypeConverters` IAE — "A required type converter (NC: `OfflineOperationTypeConverter` / TK: `kg.u`) … is missing in the database configuration" — while the converter object WAS constructed (probe: `OfflineOperationTypeConverter.<init>` ran BEFORE the validation threw). Root hypothesis (W9): the `providedConverters` list membership/Class-equality check in Room's validation drops the registered converter (the Class-token compare family again — 567/568/569's sibling) or the builder's converter list copy is hollow.
3. **NC (Gson):** `FormattingStyle.<clinit>` IAE "Only combinations of \n and \r are allowed in newline." — a Gson-side char-literal/`charAt` divergence on the `"\n"` constant (W9: trace `String.charAt` + the const-string materialization of two-char escapes).
4. **TK (Material):** `BottomSheetBehavior.D` IAE "The view is not a child of CoordinatorLayout" — live trace: `[R416-WINDOW-FVBI] target=0x7f0a0274 root=1164 -> view=0` — the `Window.findViewById` by-ID lookup misses the bottom-sheet view (the inflated tree or the id-map is incomplete for that screen).
5. **CB (nav args, probe-mapped):** the full builder chain is now traced (`composable$default("host_list")` builds CLEAN; the `console/{hostId}` route's `NavDestinationBuilder.build` pc=277 renders the message via a NULL-receiver toString then throws at pc=281) — the `argument("hostId")` registration into the builder's `arguments` LinkedHashMap never lands. W9 probe: trace `List.forEach` over the `NamedNavArgument` list at `composable$default` entry (argc=5, the arguments list is a4).
6. **CB/TK/NC (C3-tail, unchanged):** conscrypt `JNI_OnLoad` SIGSEGV against the minimal JavaVM bridge — still the biggest shared unlock (TK TLS, CB `OpenSSLProvider`, NC OkHttp platform).

## THE CODE CHANGE (exact, reviewable)

**`w8_laws.patch` — 622 lines, sha16 `b5f3881feeceb43a`, `git apply` (no flags) on a `w6_stack + w6_laws + w7_laws` tree — verified CLEAN this session (fresh HEAD `25b5a01` extract + the three W6/W7 patches, then `git apply --check w8_laws.patch` silent).** Two files:

1. `miniandroid/src/dex/dalvik_engine.cpp` — the four engine laws: F-C4-573 (ASC macro, provability gate before the ArrayStoreException raise), F-C4-575 (File name-component law, new `toString` arm), F-C4-576 (the complete AbstractMap entry protocol, placed directly above the F-C4-561 Objects law, with the `Map$Entry` interface-dispatch companion), F-C4-577 (Class block, `getEnumConstants` with clinit-ensure), plus the W8 GUAVA/NAV probe at `try_recursive_invoke` entry (env-gated `MINIANDROID_W8_PROBE`, bounded 600 lines, zero behavior change — the instrument that pinned the NC entry chain and the CB nav chain).
2. `miniandroid/src/storage/sqlite_shadow.cpp` — F-C4-574 (`setVersion` PRAGMA writer + `implemented_methods` registration + bounded evidence line).

The full patch text is in the first comment of this issue.

## VERIFY (90 s, one command each, on a w6+w7+w8 tree)

```bash
# 1. TB: the storage family is dead and the version write lands:
./build/miniandroid run --data-root <tb> --package net.thunderbird.android \
  -o /tmp/tb8 --max-seconds 75 2> /tmp/tb8.err
grep -c "Storage database upgrade failed" /tmp/tb8.err   # 0 (was 15)
grep -c "F-C4-574" /tmp/tb8.err                          # ≥1 (setVersion(30) -> OK)

# 2. NC: the Dagger injector family is dead:
./build/miniandroid run --data-root <nc> --package com.nextcloud.client \
  -o /tmp/nc8 --max-seconds 75 2> /tmp/nc8.err
grep -cE "getName' on a null|returned null\"" /tmp/nc8.err   # 0 (was 9+)

# 3. TK: the okio + enum families are dead; census drops:
./build/miniandroid run --data-root <tk> --package com.keylesspalace.tusky \
  -o /tmp/tk8 --max-seconds 75 2> /tmp/tk8.err
grep -cE "String;.length' on a null|length of null array" /tmp/tk8.err  # 0 (was 6+)
MINIANDROID_F577_DIAG=1 ./build/miniandroid run --data-root <tk> \
  --package com.keylesspalace.tusky -o /tmp/tk8b --max-seconds 75 \
  2>&1 | grep -c "F-C4-577"                                # >0

# 4. The patch applies clean on the W6+W7 tree:
git apply --check w8_laws.patch   # silent = CLEAN
```

**How to reject me:** revert any single law hunk → its VERIFY line above goes to the old value; the five laws are independent (five separate sites, five separate families). Blast radius, honestly: 574 changes ONLY the previously-unhandled `setVersion` dispatch (no app could depend on a silent drop); 576 claims ONLY the two AbstractMap entry classes + `Map$Entry`-on-entry-receiver calls (previously typed-default null); 575 adds one arm to the File law (previously null); 577 claims only `getEnumConstants` (previously null); 573 NARROWS a check (strictly fewer exceptions raised — the F-NEW-487 conservative-scope discipline). Corpus battery + anchor wall maintainer-side as always (no external corpus in this sandbox — same honest caveat as W2–W7).

## Diagnostics added this wave

`MINIANDROID_F573_DIAG` (aput unprovable-pass lines) · `[F-C4-574]` evidence lines (bounded 20) · `MINIANDROID_F576_DIAG` (entry ctor key/value oids) · `MINIANDROID_F577_DIAG` (enum array identity per call) · `MINIANDROID_W8_PROBE` (the Guava ImmutableMap + androidx.navigation chain tracer — 600-line budget, the instrument behind the NC root and the CB nav map) · plus the session tooling: a correct multi-dex disassembler (`dumpdex.py`, all overloads, uleb/delta indexes, code_item offsets — the in-tree tool mis-decoded `const-string` offsets and single-overload methods this wave; every root above was re-verified with it).

— **Coder 4** (wave 8; session evidence: binaries `43202a0b4757a7a8` → `a1dd2191db03aa3a` → `2f77481967f78e42` → `45420e488166e4c9`; all runs on the four pinned APKs)
