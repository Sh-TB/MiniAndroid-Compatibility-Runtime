# [W9] Coder-4 wave 9 — NINE generic laws (F-C4-578…586): the TB command-queue spin DEAD (PriorityBlockingQueue joins the BlockingQueue family law) · the Room converter family DEAD on BOTH NC and TK (Class.isInstance runtime-class law) · gson's String.matches · the NC account chain (AccountManager empty-array → Arrays.stream/Optional → Account ctor → java.net.URI) · **the JNI environment table REWIRED to the spec — conscrypt's RegisterNatives now lands LIVE (345 methods, CB 5→1)** · all four titles RESUMED

**Track:** `4APP4` · **Owner:** Coder-4 · **Epic:** #430 · **Wave log:** #436 (W8 → W9)

**Base:** `main` HEAD `69c871e` (S168 — already carries W6+W7 merged) + `w8_laws.patch` (#522, sha16 `5562609d0c3e30f` as extracted from the #522 comment; `git apply` CLEAN). **Base binary this wave:** `a87e2a2a38e4e68d`. **Final binary:** `de8735c1bb68c9d6`. **APK pins re-verified byte-identical (re-downloaded from F-Droid this session):** TB `473b33da5963d0a4` · NC `c9ba2e85b13fee45` · TK `8154cabe67374f2e` · CB `96cf501a83e89284`.

## WHAT THIS ISSUE IS ABOUT

Wave 9 executed the standing directive (**solve 20 problems from the work list**). The W9 queue was the six frontiers W8 pinned in #522. The work list below was censused LIVE at the W8-equivalent base (my rebuild `a87e2a2a38e4e68d` reproduces #522's final census **byte-for-family on every title**: TB 32 · NC 32 · TK 16 · CB 5 — the first thing this session did was re-verify that equivalence). Every root was proven with the corrected multi-dex disassembler (`dumpdex.py`, rebuilt this session — see Diagnostics) plus live engine traces, then fixed with a **generic, upstream-cited law**, then re-verified on the final binary with one-command tests. **Two W8 root-attributions were CORRECTED by this wave's bytecode evidence** (the TB loop was NOT OkHttp's TaskRunner; gson's IAE was NOT a charAt/const-string escape bug) — both corrections are documented in their law blocks, because a wrong root in the record costs the next wave a detour.

## THE 20-PROBLEM WORK LIST — status after W9 (all rows live-verified on `de8735c1bb68c9d6`)

| # | App | Problem (census row at base `a87e2a2a`) | Root (live-proven this wave) | Law / cascade | Status |
|---|---|---|---|---|---|
| 1 | TB | `MessagingController$1.run` F084 loop-halt → `VirtualMachineError` ×29 (the family wrapped through every Koin `InstanceFactory/Scope` resolution and `ThunderbirdApp.onCreate`) | **W8's attribution corrected**: PC=0x193 op=`const/4` (0x12 — matches the halt message) is K-9's OWN command-queue loop — `queuedCommands.take()` on a `PriorityBlockingQueue` (R8 merged the class; the TaskRunner code lives in other switch branches). PBQ was **NOT in the F-NEW-167 BlockingQueue family list** → `take()` answered the typed-null default → `if-eqz v0 → 0x193` re-looped 50,001× | **F-C4-578** | **CLOSED** (TB 32→4; `[F-C4-578] PBQ.take empty → park-yield at MessagingController$1.run` logged) |
| 2 | TB | `NotificationChannelManager` lambda NPE `List.iterator on null` — **FATAL at `MainActivity.onCreate`** (APP-BOUNDARY death at base) | cascade of #1 — the channel seeding depends on the messaging-controller graph that the VME killed | cascade | **CLOSED** (the boundary death is gone; TB completes to RESUMED) |
| 3 | TB | Koin `NoDefinitionFoundException` ×3 (`Scope.resolve/get`) | messaging-adjacent Koin definitions unresolved; caught by `getOrNull` — benign, non-fatal | honest row | PRESENT ×3 (caught) — W10 probe queued |
| 4 | TB | `DefaultTrustedSocketFactory.<clinit>` NPE `SSLContext.init on a null object reference` | `SSLContext.getInstance("TLS")` had NO bridge arm → typed-null receiver for `.init` | **F-C4-582** | **CLOSED** (`[F-C4-582] SSLContext.getInstance('TLS')` logged) |
| 5 | TB | OkHttp platform-probe CNFEs (`Conscrypt$Version`, `BouncyCastleJsseProvider`, `ReflectionFactoryImpl`) | TB ships **no** conscrypt classes — the CNFE is CORRECT Android behavior; OkHttp catches and falls back | honest no-op | UNCHANGED (correct, caught) |
| 6 | TB | `AppCompatDelegateImpl.ensureSubDecor` NoSuchMethodException (`FitWindowsFrameLayout.makeOptionalFitsSystemWindows`) | caught reflection probe (`F-NEW-219` family) | honest no-op | UNCHANGED (caught) |
| 7 | NC | Room `validateTypeConverters` IAE ×27 — "A required type converter (OfflineOperationTypeConverter) … is missing" | `Class.isInstance` used the probe's **STATIC** type (`Ljava/lang/Object;` from `List.get`) instead of its **RUNTIME** class → `assignable(Object→Converter)` = FALSE (proven live with `MINIANDROID_CLASS_LAW_TRACE`: `isInstance token=…OfflineOperationTypeConverter; -> FALSE` with probe a1=t7(Ljava/lang/Object;)) | **F-C4-579** | **CLOSED** (grep 0) |
| 8 | NC | gson `FormattingStyle.<clinit>` IAE + `GsonBuilder.<clinit>` chain — "Only combinations of \n and \r are allowed in newline." | **W8's attribution corrected**: no charAt/const-string bug — `FormattingStyle.<init>` validates with `newline.matches("[\n\r]*")` (bytecode pc=0xf), and `String.matches` had **NO bridge arm** → typed-false **even for the empty string** (`""` vs `[\n\r]*` is trivially true — Kleene-* matches the empty word) | **F-C4-580** | **CLOSED** (grep 0; `[F-C4-580] … -> true` ×4 logged) |
| 9 | NC | `UserAccountManagerImpl.getAllUsers` ARR-LEN-NULL (`array-length` on null at pc=6) | `AccountManager.getAccountsByType` answered **NULL** — the old code's own comment said "AOSP returns an empty array, never null" and answered null anyway ("callers null-guard" — disproven live) | **F-C4-583** | **CLOSED** |
| 10 | NC | `UserAccountManagerImpl.getCurrentAccount` NPE `Stream.filter on a null object reference` | `Arrays.stream(T[])` had NO arm → null Stream receiver (bytecode pc=0x18..0x21) | **F-C4-584** | **CLOSED** (`[F-C4-584] Arrays.stream(array len=0)` + `filter(Lambda0) over 0 -> kept 0` logged) |
| 11 | NC | `AccountExtensionsKt.isAnonymous` NPE `String.equals on a null` (pc=0x12 — `account.type` null) | `new Account(name, type)` had NO constructor arm — the heap object was minted with BOTH public fields unset (NC's own `getAnonymousAccount()` built it at getCurrentAccount pc=0x52) | **F-C4-585** | **CLOSED** (`[F-C4-585] Account.<init>(name='Anonymous', type='AnonymousAccountType')` logged) |
| 12 | NC | `AnonymousUser.fromContext` → NPE inside `AnonymousUser.<init>` (the Server anchor) | `java.net.URI` had **ZERO** engine coverage — `URI.create("")` (a legal empty URI) answered typed-null | **F-C4-586** | **CLOSED** (`[F-C4-586] URI.create("") -> o1620` logged) |
| 13 | NC | `ConnectivityServiceImpl.getKey/updateConnectivity` + `NetworkModule` + `DoubleCheck` + `injectMainApp` + both provider chains (~17 rows) | cascade of #9–#12 (each layer the engine fixed, the census peeled one deeper — five layers total this wave) | cascade | **CLOSED as family** (new frontier: `resolveNetworkCapabilities`) |
| 14 | NC | `NativeCryptoJni.init` UnsatisfiedLinkError / `NativeCrypto.<clinit>` ARR-LEN-NULL pc=72 | the JNI table mis-wiring (row 19) **plus** a remaining gap: the DEX→native dispatch for registered static natives (`NativeCrypto.get_cipher_names` — "JNI-UNSUPPORTED — no handler registered") | F-C4-581 + dispatch gap | PARTIAL (337 methods RegisterNatives LIVE on NC; the `get_cipher_names` dispatch = W10 frontier, 1 row) |
| 15 | NC | `AppCompatTextHelper.loadFromAttributes` / `AppCompatTextViewAutoSizeHelper` NPE ×2 (`obtainStyledAttributes on null`) + `ActivitySplashBinding.inflate` NPE ×2 | pre-existing theme-attrs/binding family | — | OPEN (W10) |
| 16 | NC | `FragmentActivity.onCreate` / `FragmentManager.dispatchCreate` NPEs | cascade of #13 (injection incomplete at the fragment stage) | cascade | MOVED (verify in W10 re-census) |
| 17 | TK | Room `validateTypeConverters` IAE family ×11 — "A required type converter (kg.u) for lg.b is missing" (the `te/r.get` IAE + `bf/k` onCreate chain) | **same root as #7** (ClassReference$Companion.isInstance → Class.isInstance static-type) — the W8 probe already showed the F527-HMAP map walk; this wave pinned the terminal | **F-C4-579** | **CLOSED** (grep 0; TK census moved to 33 NEW deeper families — see A/B) |
| 18 | TK | `te/r.get` NPE `kg/e.d on null` + `TuskyApplication` NPE chain | cascade of #17 (app init died before the service-locator fields were set) | cascade | **CLOSED as family** (rows absent from the final census; TK now RESUMED through deeper view-model code) |
| 19 | CB | conscrypt `OpenSSLProvider.<init>` UnsatisfiedLinkError ×5 (JNI_OnLoad SIGSEGV → FIX-TTT guard) — the "biggest shared unlock" | **the JNIEnv function table was mis-indexed for every slot ≥ 33**: the string family sat at 113/114/117/118/119/120 (spec: 163/164/167/168/169/170), RegisterNatives at 163 (spec: **215**), GetJavaVM at 167 (spec: 219), ExceptionCheck at 176 (spec: 228). PROVEN from the APK's own `libconscrypt_jni.so`: its calls are `*0xa8(%rax)`=33 GetMethodID, `*0x2f0(%rax)`=94 GetFieldID, `*0x6b8(%rax)`=215 RegisterNatives; the engine trace showed the UNSUPPORTED-slot call → conscrypt's own log "could not find field address" (its format string is "could not find field %s") → deref of the null id → SIGSEGV | **F-C4-581** | **CLOSED** (CB 5→1; `RegisterNatives: 345 methods for org/conscrypt/NativeCrypto` logged LIVE) |
| 20 | CB | nav-args: `console/{hostId}` `NamedNavArgument` registration never lands (W8 probe) + the NEW `Platform.<clinit>` NPE (1 row, caught) | W8-PROBE-mapped (the builder's `arguments` LinkedHashMap put never lands); Platform = conscrypt's own Android platform probes | — | OPEN (W10; pinned with the W8-PROBE trace) |

**Row accounting:** 10 rows closed by 9 laws · 4 closed as proven cascades · 3 honest rows (2 correct-behavior no-ops, 1 benign) · 3 open→W10. All four titles **RESUMED**.

## THE NINE LAWS (generic, upstream-cited, one-test acceptance each)

### F-C4-578 — BlockingQueue FAMILY law (PriorityBlockingQueue + LinkedTransferQueue + SynchronousQueue + DelayQueue join F-NEW-167)
**Root chain (bytecode of `MessagingController$1.run`, TB classes.dex, code_off 0x5325c8):** `0x190 Process.setThreadPriority(10)` → `0x193 const/4 v0,#5` → `0x194 iget queuedCommands` → `0x196 PriorityBlockingQueue.take()` → null → `0x19c if-eqz → 0x193` → 50,001 visits → F084. **Fix:** the four missing family members join the F-NEW-167 contract — take/remove/element on an EMPTY queue = the park-yield at the drain boundary (AOSP: "waiting if necessary until an element becomes available"); put/offer/add enqueue; poll/peek answer null when empty; **PBQ take serves the compareTo-minimum** when elements are DEX-Comparable (recursive invoke, F-C4-564 discipline — AOSP PBQ = unbounded heap with natural ordering), FIFO fallback otherwise.
**ONE-SIMPLE-TEST:** TB run `grep -c "F-C4-578" <stderr>` answers **≥1** and `grep -c "VirtualMachineError" <crash.log>` answers **0** (was 29). **Reject:** revert the hunk → the VME family returns.

### F-C4-579 — Class.isInstance RUNTIME-CLASS law (Room membership — NC + TK)
**Root chain (live, `MINIANDROID_CLASS_LAW_TRACE` on NC):** Room's `validateTypeConverters` walks required KClass → `ClassReference$Companion.isInstance(value, jClass)` (the Kotlin stdlib fallback — NC's `ReflectionFactoryImpl` CNFE is caught, by design) → terminal `Class.isInstance(value)` at pc=0x2f — the value arrived as OBJECT_REF carrying the **static** type `Ljava/lang/Object;` (from `List.get(i)`), so the law asked `assignable(Object→OfflineOperationTypeConverter)` → FALSE. **Fix (OpenJDK Class.java):** `isInstance(obj) { return obj != null && isAssignableFrom(obj.getClass()); }` — the RUNTIME class. The law now resolves the heap object's `class_descriptor` for every non-token probe. **Fans out to every Class-token membership test that receives objects through generic containers.**
**ONE-SIMPLE-TEST:** NC run `grep -c "A required type converter" <stderr>` answers **0** (was 27); same for TK (was the 11-row family). **Reject:** revert → the IAE families return.

### F-C4-580 — String.matches = Pattern.matches law (gson)
**Root chain (bytecode of `FormattingStyle.<init>`, NC classes4.dex, code_off 0x2319d0):** `Objects.requireNonNull(newline)` → `newline.matches("[\n\r]*")` at pc=0xf → **no String bridge arm** → typed-false → IAE at pc=0x2c. `<clinit>` died building COMPACT (`""`, `""`) — on any real engine `"".matches("[\n\r]*")` is TRUE. **Fix (OpenJDK String.java):** `matches(regex) { return Pattern.matches(regex, this); }` — the same F-104 std::regex ECMAScript engine Pattern/Matcher already use; empty regex matches only the empty input (OpenJDK edge).
**ONE-SIMPLE-TEST:** NC run `grep -c "Only combinations of" <stderr>` answers **0** (was ≥1); `grep -c "F-C4-580" <stderr>` ≥1. **Reject:** revert → the gson family returns.

### F-C4-581 — JNI SPEC-TABLE law (the conscrypt unlock — CB/TK/NC shared)
**Root chain (live CB run + harness + objdump of the APK's own `libconscrypt_jni.so`):** `System.loadLibrary("conscrypt_jni")` → real dlopen OK → `JNI_OnLoad` → `GetEnv` (VM slot 6 — was CORRECT) → `FindClass("[B")` OK → `GetMethodID` at `*0xa8` = slot 33 — **UNSUPPORTED** (returns 0) → … → `GetFieldID(org/conscrypt/NativeRef, "address")` at `*0x2f0` = slot 94 — **UNSUPPORTED** → conscrypt logs `could not find field address` (its string: "could not find field %s") → deref of the null id → SIGSEGV → FIX-TTT guard → UnsatisfiedLinkError ×5. The table itself was mis-indexed for every slot ≥ 33 (see row 19 for the exact old→new map). **Fix:** spec-exact indices (NewString=163, GetStringLength=164, NewStringUTF=167, GetStringUTFLength=168, GetStringUTFChars=169, ReleaseStringUTFChars=170, RegisterNatives=**215**, UnregisterNatives=216, MonitorEnter/Exit=217/218, GetJavaVM=**219**, ExceptionCheck=**228**; kJniSlots 181→240) **plus** the four reflection-ID lookups (33/94/113/144) answering stable interned opaque handles, `NewString` (UTF-16→UTF-8), and MonitorEnter/Exit. **Result: `RegisterNatives: 345 methods for org/conscrypt/NativeCrypto` — the real BoringSSL surface is registered and dispatchable.**
**ONE-SIMPLE-TEST:** CB run `grep -c "UnsatisfiedLinkError" <stderr>` answers **0** (was 5) and `grep -m1 "RegisterNatives: .* methods for org/conscrypt/NativeCrypto" <stderr>` matches. **Reject:** revert → the ×5 family returns.

### F-C4-582 — SSLContext OBJECT-SHAPE law (TB TLS init)
**Root (live, TB stderr):** `DefaultTrustedSocketFactory.<clinit>` pc=63 — `SSLContext.getInstance("TLS")` answered typed-null → `.init` on null → NPE (caught by the clinit's catch, but the trusted-socket factory stayed hollow). **Fix (AOSP javax.net.ssl.SSLContext):** getInstance NEVER answers null (unknown protocol → NoSuchAlgorithmException); init is the configuration no-op (the socket layer is the S100 NET-001 TLS bridge); getSocketFactory/getServerSocketFactory/createSSLEngine/getDefault answer objects. Same never-null discipline as F516-L3 (TrustManagerFactory).
**ONE-SIMPLE-TEST:** TB run `grep -c "F-C4-582" <stderr>` answers **≥1** and the `SSLContext.init' on a null` family is absent from crash.log. **Reject:** revert → the NPE returns.

### F-C4-583 — AccountManager NEVER-NULL EMPTY-ARRAY law (NC accounts)
**Root (live, NC post-580 census):** the shadow's own comment read "AOSP returns an empty array, never null, for getAccountsByType" — the code answered **null** ("callers null-guard"). NC's `UserAccountManagerImpl.getAllUsers` does `array-length` on it at pc=6 → ARR-LEN-NULL. **Fix (AOSP AccountManagerService):** zero-account profile → `new Account[0]`, never null.
**ONE-SIMPLE-TEST:** NC run `grep -c "F-C4-583" <stderr>` ≥1 and the `getAllUsers` ARR-LEN-NULL row is absent from crash.log. **Reject:** revert → the row returns.

### F-C4-584 — Arrays.stream + Stream EAGER-PIPELINE + Optional law (NC account streams)
**Root chain (bytecode of `getCurrentAccount` pc=0x18..0x21):** `Arrays.stream(accounts)` → no arm → null → `Stream.filter` on null. **Fix (OpenJDK):** `Arrays.stream(T[])` → a Stream over the heap array's elements (`__array_length__`/`array[i]` → `__eln__`/`__el<i>__`); `Stream.filter(pred)` keeps the elements whose **desugared-lambda `test(Object)` DEX body** answers true (recursive invoke — the app's filter logic is REAL bytecode); `findFirst()` → Optional; full Optional protocol (of/ofNullable/empty/isPresent/isEmpty/get/orElse). Eager evaluation is observably identical for these finite pipelines (honest note in the comment).
**ONE-SIMPLE-TEST:** NC run `grep -c "F-C4-584" <stderr>` ≥1 and `Stream.filter' on a null` is absent. **Reject:** revert → the family returns.

### F-C4-585 — android.accounts.Account CONSTRUCTOR + FIELD law (NC anonymous account)
**Root chain:** zero accounts → `getCurrentAccount` pc=0x52 falls back to NC's OWN `getAnonymousAccount()` → `new Account(name, type)` — **no constructor arm** → both public fields unset → `isAnonymous` pc=0x12 `account.type.equals(...)` on null. **Fix (AOSP android.accounts.Account.java):** `<init>(name,type)` stores both public final fields; getName/getType/toString serve them (AOSP toString spelling).
**ONE-SIMPLE-TEST:** NC run `grep -c "F-C4-585" <stderr>` answers ≥1 with the `Account.<init>(name='Anonymous'…)` line. **Reject:** revert → the isAnonymous NPE returns.

### F-C4-586 — java.net.URI MINIMAL OBJECT law (NC Server anchor + every WebDAV/REST app)
**Root chain:** `AnonymousUser.<init>(String)` pc=0x12 `URI.create("")` → **zero engine coverage** → typed-null → the Server construction chain died (the last layer of the NC connectivity cascade). **Fix (OpenJDK java.net.URI):** create(String)/`new URI(String)` store the spelling (never null for legal URIs — `""` is legal); toString/toASCIIString serve it; getScheme/getHost/getPort/getPath/getUserInfo/getAuthority/getFragment/getQuery parse the RFC3986 split (null when absent — the OpenJDK contract); equals compares spellings.
**ONE-SIMPLE-TEST:** NC run `grep -c "F-C4-586" <stderr>` ≥1. **Reject:** revert → the AnonymousUser chain dies again.

## A/B — all four titles (same APKs, same data-roots, base `a87e2a2a38e4e68d` → final `de8735c1bb68c9d6`)

| App | Base census (W8-equivalent) | Final W9 census | Lifecycle | Visual |
|---|---|---|---|---|
| Thunderbird | 32 errors: VME ×29 + NDFE ×3 (the K-9 command loop) | **4 errors**: NDFE ×3 (caught, benign) + `Fragment$$ExternalSyntheticLambda0.run` NPE (new frontier) | **RESUMED** (clean — no VME anywhere) | splash white `(252,248,248)` |
| Nextcloud | 32 errors: Room IAE ×27 + gson ×5 (the W8-pinned queue) | **29 errors, ALL MOVED PAST the W8 frontiers**: the account/connectivity cascade peeled FIVE layers (583→584→585→586→now `resolveNetworkCapabilities`); remaining: `ConnectivityServiceImpl.resolveNetworkCapabilities` + `AppCompatTextHelper`/`ActivitySplashBinding` theme family + `NativeCrypto.<clinit>` native-dispatch (1 row) | **RESUMED** | **splash paints the Nextcloud brand blue `(0,130,201)`** |
| Tusky | 16 errors: Room IAE family ×11 + te/r NPE + conscrypt | **33 errors, ALL NEW FAMILIES** — the Room family is dead (grep 0) and the app now executes DEEP view-model/provider code (R8 families `Lq8/b`, `Ln8/x`, `Ljk/a;.run`, …) that never ran before | **RESUMED** | white splash `(255,255,255)` |
| ConnectBot | 5 errors: conscrypt ULE ×5 (JNI_OnLoad SIGSEGV) | **1 error**: `Platform.<clinit>` NPE (caught) — **the JNI handshake now completes and registers 345 native methods** | **RESUMED** | dark theme bg `(48,48,48)` |

**Honest reading of TK 16→33:** the count went UP because the ladder moved — every one of the 33 rows is a family in code that previously NEVER executed (the Room IAE froze the app earlier in init). Same law as every wave: a dead shallow family is exchanged for pinned deeper ones. NC 32→29 is the same shape (five cascade layers peeled; the total holds while every family changes identity).

## KNOWLEDGE TRANSFER (for the main coder — how to think about these systems)

1. **The BlockingQueue/park model (F-C4-578):** the engine's serialized answer to "a thread parks forever" is the **park-yield at the drain boundary** — `park_yield_pending_` suspends the DEX frame chain and the scheduler re-checks next tick. This machinery already existed for `LockSupport.park` and Array/LinkedBlockingQueue (F-NEW-167, R-NEW-345). The lesson: **when an F084 loop-halt names a loop, dump the bytecode at that exact PC before theorizing** — W8's "OkHttp TaskRunner" attribution was plausible (the class really contains TaskRunner code in other branches — R8 class-merge) but the PC was K-9's own queue. The F084 message even prints `op_at_pc` — 0x12 = const/4 — use it.
2. **Static vs runtime type at bridge boundaries (F-C4-579):** `DalvikValue.class_desc` carries the STATIC type of the expression (what `List.get` declares), not the object's runtime class. For every reflection-family law (isInstance/isAssignableFrom/instance-of), the runtime class must be resolved from the heap object (`heap_.get(oid)->class_descriptor`), exactly as ART reads the object header. This is now done for non-token probes; Class tokens use `__referent_desc` (the F-NEW-440 discipline).
3. **The JNI table is pinned by the binary, not by memory (F-C4-581):** the correct slot order is fixed by the JNI spec's `JNINativeInterface` struct layout — a native lib's `call *<offset>(%rax)` IS the ground truth (0xa8/8=33 GetMethodID, 0x2f0/8=94 GetFieldID, 0x6b8/8=215 RegisterNatives). The old table was self-consistent but shifted ~50 slots for everything past GetObjectClass, which means **every prior native-lib session was talking to wrong handlers above slot 33 without anyone seeing it** (the loud UNSUPPORTED stub only fired for slots nobody filled). The registered-natives dispatch (`find_symbol` in dlopen_exec.cpp) matches by (class, method, sig) with `internal_from_descriptor` — it already works; with RegisterNatives now landing, the remaining gap for NC/CB is the DEX→native dispatch for STATIC natives (see W10 frontier 1).
4. **Never-null container contracts (F-C4-583/585/586, 578's park):** AOSP/OpenJDK APIs that "never return null" are load-bearing for app code written against them (Kotlin non-null types make the compiler DELETE the null checks). When a census NPE dereferences the result of a platform call, check the platform contract FIRST — three of this wave's laws (empty array, Account fields, URI.create) are the platform just keeping its own documented promise.
5. **The desugared-lambda dispatch pattern (F-C4-584's filter):** R8 compiles Kotlin/Java lambdas into `$$ExternalSyntheticLambdaN` classes implementing the functional interface (`test`, `apply`, `accept`). The engine can execute them via `try_recursive_invoke(lambda_class, "test", {lambda_recv, arg}, …)` — this is the same discipline as F-C4-564 and works for any functional-interface bridge (Consumer/Function/Predicate). Prefer this over hand-writing the predicate semantics.
6. **gson's FormattingStyle (F-C4-580):** gson 2.11+ validates its style constants with `String.matches` at class-init — a missing `matches` arm kills `GsonBuilder.<clinit>`, which kills every Gson consumer with an IAE that LOOKS like a gson bug. When an IAE's message quotes a validation string, find the `matches`/`charAt`/`equals` call in the <init> bytecode — the check itself is the witness.

## THE CODE CHANGE (exact, reviewable)

**`w9_laws.patch` — 1015 lines, sha16 `b708b8460eac637c`, `git apply` (no flags) on a `main(S168) + w8_laws` tree — verified CLEAN this session (fresh `git stash` → main → apply w8 → `git apply --check w9_laws.patch` silent).** Two files:

1. `miniandroid/src/dex/dalvik_engine.cpp` (+754): F-C4-578 (family list + PBQ compareTo take + evidence line), F-C4-579 (runtime-class resolution in the F-103 law), F-C4-580 (String.matches arm in the String bridge), F-C4-582 (SSLContext shadow beside TrustManagerFactory), F-C4-583 (AccountManager empty-array), F-C4-584 (Arrays.stream + Stream + Optional), F-C4-585 (Account ctor/fields/toString), F-C4-586 (URI object law), plus the W9 probe (env `MINIANDROID_W9_PROBE`, bounded 600 lines, zero behavior change — the Room/ClassReference chain tracer).
2. `miniandroid/src/jni/dlopen_exec.cpp` (+176/−32): F-C4-581 — the four ID-lookup handlers (interned opaque handles), NewString (UTF-16→UTF-8), MonitorEnter/Exit, the spec-exact `init_tables()` rewiring, kJniSlots 181→240.

The full patch text is in the first comment of this issue.

## VERIFY (one command each, on a main+w8+w9 tree)

```bash
# 1. TB: the command-queue spin is dead and the park-yield fires:
./build/miniandroid run --data-root <tb> --package net.thunderbird.android \
  -o /tmp/tb9 --max-seconds 75 2> /tmp/tb9.err
grep -c "F-C4-578" /tmp/tb9.err          # >=1 (the PBQ park-yield)
grep -c "VirtualMachineError" /tmp/tb9/crash.log   # 0 (was 29 rows)

# 2. NC: Room + gson + the account chain:
./build/miniandroid run --data-root <nc> --package com.nextcloud.client \
  -o /tmp/nc9 --max-seconds 75 2> /tmp/nc9.err
grep -c "A required type converter" /tmp/nc9.err   # 0 (was 27)
grep -c "Only combinations of" /tmp/nc9.err        # 0 (was >=1)
grep -cE "F-C4-58[0-6]" /tmp/nc9.err               # >=6 laws live

# 3. TK: the Room family is dead (same law as NC):
./build/miniandroid run --data-root <tk> --package com.keylesspalace.tusky \
  -o /tmp/tk9 --max-seconds 75 2> /tmp/tk9.err
grep -c "A required type converter" /tmp/tk9.err   # 0 (was 11 rows)

# 4. CB: the conscrypt handshake completes and registers natives:
./build/miniandroid run --data-root <cb> --package org.connectbot \
  -o /tmp/cb9 --max-seconds 75 2> /tmp/cb9.err
grep -c "UnsatisfiedLinkError" /tmp/cb9.err        # 0 (was 5)
grep -c "F-C4-581" /tmp/cb9.err                    # >=1 (the ID lookups)
grep -m1 "RegisterNatives: .* methods for org/conscrypt/NativeCrypto" /tmp/cb9.err

# 5. The patch applies clean on the maintainer path:
git stash && git apply w8_laws.patch && git apply --check w9_laws.patch && echo CLEAN
```

**How to reject me:** each law is an independent hunk at an independent site; revert any single one and its VERIFY line above returns to the base value. Blast radius, honestly: 578 touches ONLY queue-family dispatch (PBQ/LTQ/SQ/DQ previously fell to typed-null); 579 NARROWS a probe-type resolution (runtime class instead of static — strictly more Java-faithful); 580 claims ONLY `String.matches` (previously typed-false); 581 rewires slots that previously routed to wrong handlers or the UNSUPPORTED stub (strictly positive, but the corpus battery MUST re-run — it is maintainer-side as always, same honest caveat as W2–W8); 582–586 claim only previously-unhandled classes (typed-null before).

## NEW FRONTIERS OPENED THIS WAVE (the W10 queue)

1. **conscrypt native DISPATCH (NC row 14, CB tail):** `RegisterNatives` now lands (345 methods CB / 337 NC) but the DEX→native path answers `[JNI-UNSUPPORTED] NativeCrypto.get_cipher_names — no handler registered` → `NativeCrypto.<clinit>` ARR-LEN-NULL pc=72. W10 probe: route the registered-natives table through the static-native dispatch (find_symbol's RegisterNatives arm already matches (class,method,sig) — find why the static path misses it).
2. **NC connectivity tail:** `ConnectivityServiceImpl.resolveNetworkCapabilities` NPE — the `ConnectivityManager.getActiveNetwork`/`NetworkCapabilities` shadow family (R339-SVC answers the manager; the active-network probe is next).
3. **NC theme/binding family:** `AppCompatTextHelper.loadFromAttributes` (`obtainStyledAttributes on null` receiver) + `ActivitySplashBinding.inflate` — the W8-era family that persists.
4. **TB remainder:** Koin NDFE ×3 (benign, caught) + `Fragment$$ExternalSyntheticLambda0.run` NPE — the fragment-lifecycle runnable family.
5. **CB:** `Platform.<clinit>` NPE (1 row, caught) + the nav-args registration (W8-PROBE-mapped).
6. **TK deep census:** 33 new families in R8-minified view-model/provider code (`Lq8/b;.F`, `Ln8/x;.p/n/b`, `Ljk/a;.run` ISE, `La1/r`, `Lkh/g`, `Lgk/f`, `Lf1/g` …) — first run `MINIANDROID_W9_PROBE=1` + re-census to rank them; the old `te/r`+`kg/e` and Room families are gone.

## Diagnostics added this wave

`[F-C4-578]` (family-member park lines, bounded 12) · `[F-C4-580]` (matches verdicts, bounded 12) · `[F-C4-581]` (every ID lookup with class+name+sig, bounded 12) · `[F-C4-582]` (getInstance, bounded 8) · `[F-C4-583]` (empty-array answers, bounded 8) · `[F-C4-584]` (stream/filter/kept counts, bounded 8) · `[F-C4-585]` (Account ctor with name+type, bounded 8) · `[F-C4-586]` (URI.create, bounded 8) · `MINIANDROID_W9_PROBE` (Room/ClassReference chain tracer, bounded 600, zero behavior change). Session tooling: a fresh correct multi-dex disassembler (`dumpdex.py` — every overload, uleb/delta class_data walk, true 35c/3rc register decode, string/type/field/method index resolution; fixed the const-string offset and single-overload mis-decodes the in-tree tool carries).

— **Coder 4** (wave 9; session evidence: base `a87e2a2a38e4e68d` → `a2531908c487d603` → `a2acdc3fcbb8891c` → `f14ad802d84392ea` → final `de8735c1bb68c9d6`; all runs on the four byte-verified F-Droid pins)
