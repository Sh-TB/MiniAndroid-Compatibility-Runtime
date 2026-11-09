## W16 — Coder-4 — SEVEN generic base-layer laws (4APP campaign)

**Binary**: `d1d4af34e8555793` (built from this patch; two-build wave, intermediate `9464373a77abbba5`).
**Patch**: `w16_laws.diff` — 1923 lines, sha16 `6c11ca3409676adb`, applies on `d3a8d0e` (current main) — includes the still-unlanded W15/W15b commits (fed170f, de78d22, e4ca6f7, 3b04355) + this wave. Fast-forward, zero conflicts.
**Commits**: `b66e027` (W16) on top of `3b04355` (W15b addendum) on top of `d3a8d0e`. Direct `git push` returns 403 with the current PAT (Issues RW only, no Contents W) — **main coder please land `b66e027`**.

---

### F-C4-622 — `String.regionMatches` BOTH overloads (+ `contentEquals`, `compareToIgnoreCase`)

**Root (live, Tusky v27.1, real-DEX)**: okhttp3 `HttpUrl` (R8-renamed `Llk/w;.j`) validates the URL scheme with
```dalvik
regionMatches(true, 0, "https:", 0, 6)   ; and (true, 0, "http:", 0, 5)
```
No bridge arm existed → the typed-zero default answered **false** → `IllegalArgumentException: "Expected URL scheme 'http' or 'https' but was 'https'"` — note the scheme string PRINTS correctly; the comparison was the lie. Uncaught → the Koin factory `te/r.get` unwind → `MainActivity` content never inflated (decor built, 0 children).

**Law (OpenJDK String.java)**:
- `regionMatches(int toffset, String other, int ooffset, int len)` == `regionMatches(false, ...)`.
- `regionMatches(boolean ignoreCase, ...)`: bounds `ooffset < 0 || toffset < 0 || toffset > length()-len || ooffset > other.length()-len` → **false** (NEVER an exception); then char-wise equality; ignoreCase folds via `toUpperCase(c1)==toUpperCase(c2) || toLowerCase(upper(c1))==toLowerCase(upper(c2))`; len==0 in-range → true.
- Arity dispatch by args-with-receiver count: 6 = (Z,I,String,I,I), 5 = (I,String,I,I). Z arg via `dalvik_bool_value`, ints via `dalvik_int_value`.
- Null `other` → deferred NPE (STR-BRIDGE). Null receiver arm extended to the new methods.

**Verify**: run Tusky 145 with the new binary; `grep "F-C4-622"` in the console log shows `regionMatches(ic=1, toff=0, other="https:", ...)-> true`; the IAE family `"Expected URL scheme"` is 0 hits. Tusky frontier moves to Material `BottomSheetBehavior` IAE `"The view is not a child of CoordinatorLayout"` (view-hierarchy family).

---

### F-C4-623 — `Matcher.start()/end()/start(int)/end(int)` + `find(int from)` (regex match-boundary law)

**Root (live, ConnectBot 11101000, real-DEX)**: `NavDeepLink.<init>` strips the query/fragment with a locally compiled `Pattern.compile("(\?|#|$)")` + `SequencesKt.findNext(matcher, 0, uri)` — kotlin's findNext calls `find(I)` and wraps the matcher in `MatcherMatchResult`, whose `getRange()` = `IntRange(matcher.start(), matcher.end())`.
`start()`/`end()` had NO arm → typed-zero **0** → `range.first = 0` → `uriPattern.substring(0, 0) = ""` → `buildRegex("")` never filled `pathArgs` → `getArgumentsNames() = []` → `NavDestinationBuilder.build`'s `missingRequiredArguments` reported every route argument as unmatched → `IllegalArgumentException "Cannot set route \"console/{hostId}\" ... missing: []"` → the whole NavHost graph died → CB stuck at a blank frame with a fatal uncaught IAE.

**Law (OpenJDK Matcher)**: after a successful match, `start()`/`end()` return the match boundaries (group 0); `start(i)`/`end(i)` the group's; no match yet → `IllegalStateException("No match available")`; non-participating group → -1. `find(from)` resets the search start (from<0 → IndexOutOfBoundsException). Group positions are stored per-find as `gpos<i>`/`gend<i>`/`gok<i>` heap fields (tail-relative + base).

**Verify**: run ConnectBot 11101000; `grep "F-C4-623"` shows `Matcher.start(0) -> 43 rx='(\?|#|$)'` (the end-anchor truth, was 0). `grep -c "Cannot set route"` = **0** (was the fatal). Uncaught marks **0**. The Compose pipeline runs (`AndroidComposeView` dispatches live).

---

### F-C4-624 — ArrayList-family `toString`/`contains` DUAL-STORE COHERENCE

**Root (CB, compounding with 623)**: in registry mode the framework `CollectionShadow::CollectionState` (parallel vectors `elem_kinds`/`elem_strings`/`elem_ints`/`elements`) is the authoritative store for `isEmpty/size/get`; `add()` through the shadow dispatch populates ONLY that store. F-C4-564's `toString` (and the G-6 `contains`) read the engine-side heap fields (`array[i]`) only → a shadow-populated list rendered `"[]"` in the IAE message (`missing: []`) while `isEmpty()` correctly said non-empty, and `contains()` answered false for shadow-stored elements.

**Law**: `toString`/`contains`/`containsAll` now read the shadow store FIRST (kind 2 = string, 3 = int, 1 = object id — mirrored to DalvikValues), falling back to heap fields; empty shadow state falls back too. This is the read-side twin of the F-101 write-back law.

---

### F-C4-625 / F-C4-625b — `MediaStore` CONTENT_URI static + `getContentUri` method families

**Root (live, Nextcloud 3.5.x)**: `BackgroundJobManagerImpl.scheduleContentObserverJob` (called from `MainApp.onCreate`):
1. `MediaStore.Images.Media.INTERNAL_CONTENT_URI` → SGET-MISS → typed-null → Kotlin `checkNotNullExpressionValue` NPE `"INTERNAL_CONTENT_URI must not be null"` → **MainApp.onCreate DIED** → the whole Koin DI wiring aborted → every lateinit service (accountManager...) stayed null → `LauncherActivity` `throwUninitializedPropertyAccessException` at first touch.
2. The very next line: `MediaStore.Files.getContentUri("external")` → typed-null → NPE `"getContentUri(...) must not be null"` (same death).

**Laws (AOSP MediaStore.java)**:
- Statics seeded via the F-NEW-363 `seed_uri` mechanism (real heap Uri objects with `uri_raw`): Images/Video/Audio `INTERNAL_CONTENT_URI` + `EXTERNAL_CONTENT_URI` (+ `Audio.Media.CONTENT_URI`, Images/Video `Thumbnails.EXTERNAL_CONTENT_URI`, `Downloads.EXTERNAL_CONTENT_URI`), `AUTHORITY="media"`; plus the high-frequency `ContactsContract` roots (`Contacts`, `RawContacts`, Phone/Email `CONTENT_URI`, `AUTHORITY`).
- Methods: `getContentUri(String volumeName[, long id])` on `MediaStore$Files/Images$Media/Video$Media/Audio$Media/Albums/Artists/Playlists/Genres` → real Uri `content://media/<volume>/<table>` (table map: file, images/media, video/media, audio/media, audio/albums, audio/artists, audio/playlists, audio/genres); 2-arg form appends `/{id}`. Static call shape: `args[0]` IS the volume (no receiver), matching the `Uri.fromFile` pattern.

**Verify**: run Nextcloud 350000290; `grep "F-C4-625b"` shows `getContentUri("external") -> content://media/external/file`; `grep -c INTERNAL_CONTENT_URI` NPE = 0; `MainApp.onCreate` proceeds past scheduleContentObserverJob (WorkManager ForceStopRunnable cleanup logs).

---

### F-C4-626 — `JobScheduler` METHOD family

**Root (NC, wall 3 of the same cascade)**: WorkManager `ForceStopRunnable` → `JobScheduler21.getAllPendingJobs` → unbridged → typed-null → NPE `"getAllPendingJobs(...) must not be null"` (depth 9).

**Law (AOSP android.app.JobScheduler)**: `getAllPendingJobs()` → a FRESH non-null `List<JobInfo>` every call (empty when nothing is scheduled; scheduled jobs tracked on the scheduler singleton's `js_job<i>` heap fields so the engine's ArrayList iteration laws agree); `getPendingJob(int)` → null (cold-boot truth); `schedule`/`scheduleAsPackage` → `RESULT_SUCCESS` (1) and track the JobInfo; `cancel`/`cancelAll` → void + untrack; `forNamespace` (R-NEW-559 law) restructured into the same family block, unchanged semantics.

---

### F-C4-627 — `java.time.Duration` factory + accessor family

**Root (NC, wall 4 of the same cascade)**: `Duration.ofSeconds(...)` → NO bridge → typed-null → NPE `"ofSeconds(...) must not be null"` (depth 3, MainApp.onCreate chain).

**Law (OpenJDK Duration)**: `ofSeconds(s)` = (s, 0ns); `ofSeconds(s, nano)` normalized (carry whole seconds, nano-of-second in [-999999999, 999999999]); `ofMinutes`=60s; `ofHours`=3600s; `ofDays`=86400s; `ofMillis`=ms×1e6 ns; `ofNanos`=ns. Objects carry `__dur_seconds__`/`__dur_nanos__` (I64); `toMillis()` = s×1000 + ns/1e6; `getSeconds()` (I64); `getNano()` (I32). Statics: args[0] IS the first parameter.

---

## Measured results (4APP, 40s real-dalvik runs)

| App | Before W16 | After W16 |
| --- | --- | --- |
| **ConnectBot** | fatal uncaught IAE (NavHost dead), blank | **0 uncaught; NavHost graph builds; Compose AndroidComposeView executing** — deepest CB run ever |
| **Tusky** | DI wall: okhttp IAE → content never inflates | **DI wall DEAD** (`regionMatches->true`); frontier now Material `BottomSheetBehavior` "view is not a child of CoordinatorLayout" (view-attachment family) |
| **Nextcloud** | MainApp.onCreate dead at `INTERNAL_CONTENT_URI` NPE | **FOUR walls of the MainApp-init cascade killed** (MediaStore×2, JobScheduler, Duration); WorkManager ForceStopRunnable cleanup runs; new frontier = `WorkContinuationImpl.mWork` null ("getWork(...) must not be null" at `EnqueueUtilsKt.checkContentUriTriggerWorkerLimits` — an upstream silent-null producer in the enqueue list build) |
| **Thunderbird** | Koin NoDefinitionFound at depth 43 | unchanged (W17 target — see below) |

## Regressions: ZERO

- dooz `a0fae9072313e2d1` ✓, bouncy `8a6c24ac8a7d718e` ✓ **byte-exact**, unote `3b8dcb0adbbc17a9` ✓ **byte-exact**, solitaire `ba50a4d28ea62fe7` ✓, tranquilstopwatch `11a38a5aeeff45a6` ✓ — all 0 uncaught.
- W2 anchors: mines **686** colors ✓ / memory **256** ✓ / blackjack **65** ✓ (all B_STRUCTURED, 0 uncaught).

## Reproduce (self-contained)

```bash
cd miniandroid && make -j1                     # binary sha16 d1d4af34e8555793
cd /home/z/my-project && python3 scripts/w15_baseline.py com.keylesspalace.tusky org.connectbot com.nextcloud.client net.thunderbird.android
python3 work/w2anchors.py                      # W2 anchors
# laws firing: grep "F-C4-62" work/evidence/w15/*.console.log
```

## Tooling persisted (androguard — verdict on the user's question: CONFIRMED HELPING)

`scripts/w16_koin_disasm.py` (class/method disasm, multidex), `w16_list_methods.py` (overload census with code sizes), `w16_find_class.py` (name-substring finder), `w16_search_string.py` (const-string owner locator). Every root this wave was pinned by androguard bytecode ground truth (okhttp scheme check, `MatcherMatchResult.getRange`, the NavDeepLink parse chain, the Koin merged-class registry). Coder 3's issues #560/#561 are androguard-driven too — the tool is now a standing part of the campaign.

## W17 targets

1. **NC**: `WorkContinuationImpl.mWork` null — census the enqueue list build (`WorkManagerImpl.beginUniqueWork` callers; suspect a silent-null collections answer upstream of the ctor).
2. **TB**: Koin `NoDefinitionFoundException` (depth 43, `okhttp3/Dispatcher.getViewModel$lifecycle_viewmodel` chain) — the registry is STRING-keyed (`getFullName(kclass)+":"+qualifier+":"+scope` via `CHM`); R8 type-merged `InstanceRegistry` lives on `Lorg/slf4j/event/EventRecodingLogger;` with `resolveDefinition$koin_core`. Census which module's definitions never registered.
3. **Tusky**: CoordinatorLayout child-attachment (BottomSheetBehavior family) — coordinate with Coder 6 (View pipeline).
4. **CB**: Compose frame production (draw ops → framebuffer).

— Coder 4
