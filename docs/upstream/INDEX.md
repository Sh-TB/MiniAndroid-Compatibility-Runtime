# UPSTREAM LAW INDEX — MiniAndroid

Every important MiniAndroid fix implements a REAL upstream semantic contract.
This index records that contract per law: where it comes from, what
MiniAndroid implemented, and which test proves it. A fix without an upstream
contract is a workaround; workarounds do not land here because they do not
land in the engine.

Format: **Law** · Source (version) · Relevant API · MiniAndroid implementation · Proof.

---

## DEX dispatch / interpreter

| Law | Source | MiniAndroid implementation | Proof |
|---|---|---|---|
| Active-cycle identity must distinguish LEGITIMATE re-entrant static/nested coroutine starts from true cycles — key on (class, method) + receiver/leading object-arg identities, per-coroutine keys for nested starts | kotlinx-coroutines start helpers (static, depth-bounded, legitimately re-entrant — androidx-main sources) | F-076 static-identity law (S22) + F-098 instance-key law for nested per-LayoutNode observation (S33) | R-NEW-300 evidence (S22 [M3-19-CYCLE] trace); R-NEW-332 closed (S33); Recomposer runner loop starts |
| Dalvik registers are UNTYPED slots; the opcode defines source interpretation | AOSP `dalvik` interpreter | const/high16 float bits read as float through cmp/arith (F-028 float law) | F-028 fixture pixel golden (7 bands) |
| `invoke-*` pc-advance contract (return address vs next-instruction) | AOSP interpreter loop | F-055/R-NEW-355 pc-advance law; microtimer renders ungated | microtimer golden `c5126930…` |
| ArrayList(Collection) copy must honor the COLLECTION contract, not raw fields | OpenJDK `ArrayList(Collection)` | F-101 four-step cascade: array → size()/get() → iterator → backing-array; contract-mismatch restart guard | S45 evidence; `docs/maintenance/s45_session_record.md` §3 |

## Android framework

| Law | Source | MiniAndroid implementation | Proof |
|---|---|---|---|
| `View.post/postDelayed/removeCallbacks`, `Activity.runOnUiThread` enqueue on the SAME main Handler queue (AOSP `View.post` → `attachInfo.mHandler.post`) | AOSP `View.java` / `Activity.java` | ViewShadow/ActivityShadow enqueue on one MessageQueue, virtual-clock ordered | R-NEW-359 VERIFIED-FIXED; dooz compose request executes |
| `ContextImpl.getPreferencesDir()` — SharedPreferences live under the RUNNING application's package data dir, never a hard-coded package | AOSP `ContextImpl.java` | R-NEW-367: prefs path = `<app_data_root>/<manifest package>/shared_prefs` | battery 94/94 at S48; `docs/releases/RELEASE_v0.0.6-Leghorn.md` |
| First-traversal ordering: attach wave STRICTLY precedes measure for `setContentView(View)` | AOSP `ViewRootImpl.performTraversals` | R-NEW-349 law (attach wave first) | S43 evidence; dooz onCreate unblocked |
| `View.measure(final)` is receiver-based before shadow dispatch; `getMeasuredWidth/Height` are accessors on stored dims | AOSP `View.java` | F10 onMeasure extension + one-store write-through | R-NEW-347-era evidence |
| AOSP `addViewInner` child-attach law — pending attaches flush at subtree attach, mark-attached-first, one-shot guard | AOSP `ViewGroup.java` | ViewShadow pending_child_attaches_ + engine dispatch_attached_subtree_from | R-NEW-344 chain (S42) |
| Transparent containers do not mask ancestor backgrounds | AOSP `ViewGroup.drawChild` | R-NEW-336 transparent-container law | hello_widgets pixel forensics |
| `Button` is clickable by default (platform style `android:clickable=true`) | AOSP platform styles | R-NEW-356 clickable-default law | TicTacToe taps dispatch |
| `Resources.getIdentifier` resolves dynamic ids | AOSP `Resources.java` | R-NEW-357 law + receiver-shift fix | TicTacToe Classic gameplay |
| Frame pump: Choreographer callbacks must be posted and drained through the frame pipeline | AOSP `Choreographer` | F-050 family; post-lifecycle pump law (16 ticks before capture) | S39/S45 records |

## Collections / Kotlin / androidx

| Law | Source | MiniAndroid implementation | Proof |
|---|---|---|---|
| `Arrays$ArrayList` / kotlin `ArrayDeque` expose size/get/iterator per their REAL contracts (deque is a circular buffer) | OpenJDK / kotlin-stdlib | F-101 cascade step 2/3 handles R8-renamed wrappers | S45 record §3 |
| `Collections` iterator + singleton-list laws | OpenJDK `Collections.java` | F-036/F-039 | M5 evidence |
| SafeIterableMap forward pass: iterators tolerate append-during-iteration; `IteratorWithAdditions.next` follows the upstream contract | AOSP Lifecycle `SafeIterableMap.java` | iterator-reentry semantics implemented generically (no package special-cases) | R-NEW-331 evidence (S27; SafeIterableMap$IteratorWithAdditions.next churn documented) — **frontier open, not claimed closed** |
| androidx.collection ScatterMap probe math: 64-bit key compare (`Long.compare`) sign semantics + murmur h2/slot math | androidx.collection 1.4.x (upstream sources fetched) | **NO fix landed yet** — forensics verified the metadata `Arrays.fill` ([F040-DIAG]) and the wide `ushr/shr` laws correct; suspects are the DEX-object `key.hashCode()` identity law and the `neg-long/shr-long` slice chain | R-NEW-335/361 OBSERVED-FAIL — **primary frontier** (s45_session_record §4) |
| `checkNotNull` returns the reference (identity), enabling chained null-unwraps | Guava/androidx ` Preconditions` | identity law | S39 R-NEW-339 chain |
| Protobuf MessageSchema build path (`MessageInfo`/schema ctor) | protobuf-javalite 3.x | R-NEW-351/353/354 chain; ground truth in `docs/upstream/MessageSchema.java` | S43/S44 evidence |

## Coroutines / concurrency

| Law | Source | MiniAndroid implementation | Proof |
|---|---|---|---|
| `runBlocking`/BlockingCoroutine must not livelock the single-threaded dispatcher | kotlinx-coroutines | R-NEW-345 4-law fix | S41 evidence |
| atomicfu state via `sun.misc.Unsafe` offsets is heap-backed | kotlinx-atomicfu | full Unsafe shadow: offsets registry + CAS | R-NEW-337 (S39) |
| `JobSupport` await/completion state machine reads its own state through `getObjectVolatile` | kotlinx-coroutines | offsets registry serves volatile reads | R-NEW-337 post-fix |

## Sources consulted (pinned)

- AOSP main: `cs.android.com` / `androidx-main` fetches recorded per session
- androidx.collection 1.4.x sources (ScatterMap/ScatterSet)
- compose runtime/ui 1.11.4 sources (versions read from APK META-INF — `corpus_cache/dooz23_extracted/`)
- protobuf-javalite 3.x — ground-truth `MessageSchema.java` in this directory
- OpenJDK `ArrayList`/`Collections`/`File` (jdk17u)
