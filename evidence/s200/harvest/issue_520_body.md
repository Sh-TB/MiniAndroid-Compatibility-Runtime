# CODER 7 — Base Android Component Runtime Engineering: Work Log

**Owner:** CODER 7 (Android component runtime: Application/Activity, Service, BroadcastReceiver, ContentProvider, Intent & component resolution)
**Repository:** Sh-TB/MiniAndroid-Compatibility-Runtime
**Current base commit:** WAVE-8 is authored on the S185+W5+W6+W7 chain (W7 tree  (W6 tree `a386825baa5cf31aec382a2628cfca2e7362ac5d`). No pushes — the manager integrates from the unified patch comments (W5: 18/19, W6: 20/21, W7: 22). Main HEAD at authoring time: S188 `d3a8d0ec` (W5 not yet merged; W5+W6+W7 land as one chain).
**This issue is my single work log — all progress, evidence and handoff material lives here.**

**Delivery state (seven waves):**

| Wave | Scope | Verdict evidence |
|---|---|---|
| WAVE-1 (rebased) | ordered broadcasts + service-contract laws (14 laws) | BEFORE 1/11 → **AFTER 12/12 PASS**; results-file SHA-256 `a248cab28075521d…` **byte-identical to the original wave-1 record** |
| WAVE-2 | bring-down `onUnbind`, per-filter dispatch, sticky broadcasts, sticky/registration permissions, exported/foreign-sender model, `getReceiverInfo` | **19/19 PASS** (R0 same-pkg, R2 foreign+perms); R1 foreign-no-perms shows the exact predicted deny set; gate_a regression **byte-identical streams W1→W2** |
| WAVE-3 | **20 new generic laws**: task-stack/launch-flag set, service AUTO_CREATE/missing/stopSelf(int), broadcast matchData + unregister + sticky-ordered, ContentProviderClient, PackageManager REAL resolution (CATEGORY_DEFAULT + enabled) | **34/34 PASS ×3 cold runs** (c7 probe) + **8/8 PASS ×3 cold runs** (new activity-chain probe); R1 shows exactly the deny-matrix rows; gate_a verdict stream identical (95/2, pre-existing env-scoped FAILs only) |
| WAVE-7 | **cross-package ACTIVITY LAUNCH — the AOSP ActivityStarter law**: implicit resolution across the store index, SYNCHRONOUS checkComponentPermission gate (SecurityException / ActivityNotFoundException in the caller's frame), foreign activity REAL `<init>`+`onCreate` execution, task-stack integration; pending-order law (a thrown launch never queues) | **23/23 PASS ×3 cold + ×3 warm** (×6 byte-identical `4ddf418f…`; the W6 20-op contract `24ae2c3a…` reproduces byte-identically on the W7 binary) + W7-LAUNCH-CONTRACT PASS + androguard all-OK (incl. activity gate facts) + no-store regressions byte-identical (34-op `4aa8f51c…`, activity-chain `60b4a75a…`) |
| WAVE-8 | **permissions + intent-senders + install-store scale**: per-op provider read/write permission gate (SecurityException in frame), PendingIntent.send REAL dispatch (ONE_SHOT/IMMUTABLE/CanceledException; broadcast+service+activity through the gated pipelines), data-root auto-index (install-store ≡ explicit store, byte-identical), foreign launchMode (singleTask/singleTop reuse + clear-top) — plus 3 probe-discovered pre-existing law fixes (Intent-ctor Uri dead branch, sibling <data> authority merge, activity filter priority) | **33/33 PASS ×3 cold + ×3 warm** (×6 byte-identical `9831ee30…`; X01-X23 prefix == the W6 golden byte-identical) + W8-LAUNCH-CONTRACT PASS + auto-index ≡ explicit store byte-identical + androguard all-OK + no-store regressions byte-identical (34-op `4aa8f51c…`, act-chain `60b4a75a…`) |
| WAVE-6 | **S185 LOAD-FIRST applied to cross-package code — LoadedApk-lite: foreign components EXECUTE** (store dexes merged into the runtime class index; broadcast/service/provider dispatch runs real foreign bytecode; foreign-owner Context identity) | **20/20 PASS ×3 cold + ×3 warm** (×6 byte-identical `24ae2c3a…`; X01–X16 prefix == the W5 golden `664564f2…` byte-identical) + androguard cross-parser check all-OK + no-store regressions byte-identical (34-op `4aa8f51c…`, activity-chain `60b4a75a…`) |
| WAVE-4 | **S181 Family-2 root family**: UUID/ParcelUuid total-parse laws + AudioFocusRequest$Builder fluent-chain law — no silent null from framework value/factory APIs in the app-init path | **10/10 PASS ×3 cold** (new c7_w4_probe, results sha `9be150e8…` ×3) + **34/34 PASS ×3** (34-op component probe, sha `4aa8f51c…` ×3) + **first Coder-7-driven corpus verdict-class flip**: sunpiano `DEFAULT_BACKGROUND_ONLY → REAL_APP_CONTENT` (576,907 app px, ×3 byte-identical `af001924…`) |

---

---



---

# WAVE-5 (base S185 `8057943`): PMS-LITE — cross-package component index + REAL-SQLite package cache — **IMPLEMENTED / TESTED**

**The S185 SQLITE RULE (#536) applied to Coder-7 territory + the scale directive ("make the BASE run thousands of apps; solve the real BIG problems").** This wave removes the single biggest structural blocker in the component domain — the one-package engine — instead of patching small symptoms.

## W5.1 Missing/wrong: the engine was a ONE-package engine

1. **Every PackageManager resolution candidate came only from the running APK's own manifest** (`manifest_activity_filters_` / `manifest_service_filters_` / `manifest_receivers_`): `queryIntentActivities` / `queryIntentServices` / `queryBroadcastReceivers` / `resolveActivity` / `resolveService` / `resolveActivityInfo` saw an empty world beyond the running app. AOSP: PackageManagerService resolves across ALL installed packages (the `/data/app` scan + IntentResolver). This dead-ends whole FAMILIES in every app: CustomTabs/browser pickers (forkgram x8 evidence, W3), choosers, share flows, plugin/discovery flows.
2. **`getInstalledPackages` / `getInstalledApplications` / `queryContentProviders` answered a FABRICATED always-empty list** (dalvik_engine.cpp, the pre-W5 handler): a negative no Android device can ever produce. Launchers, backup tools, share-target enumeration, provider discovery — all fabricated-empty.
3. **`resolveContentProvider(authority)` / `getProviderInfo` / `getPackageInfo(pkg)` saw only the running package's manifest** — every cross-app authority lookup (FileProvider families, `ContentResolver.acquireProvider` across apps) was structurally impossible.

**Why this is a generic runtime problem (no per-app special-casing possible):** the missing piece is the SYSTEM's package registry, not an app behavior. AOSP source basis: `frameworks/base/services/core/java/com/android/server/pm/PackageManagerService.java` (package scanning, `mProviders` authority map, `queryIntentActivities` across packages), `IntentResolver.java` (filter matching + priority ordering), `frameworks/base/core/java/android/content/pm/PackageParser.java` (per-component filter records, enabled/exported), `com.android.server.pm.PackageManagerService.PackageSetting`/package cache (parse-once, load-on-boot — the pattern the SQLite cache implements).

## W5.2 The change (all six P0 items **IMPLEMENTED / TESTED**)

- **P0-1 `dex/c7_package_index.{h,cpp}` (new)** — the generic cross-package component index: per-package activities/services/receivers/providers/filters; the SAME WAVE-3 match law as a single source of truth (`C7PackageIndex::filter_matches` — action half, category half, MATCH_DEFAULT_ONLY/CATEGORY_DEFAULT, IntentFilter.matchData MIME+scheme/host/pathPrefix halves); disabled-component exclusion; priority-ordered candidates; deterministic sorted store scan. **IMPLEMENTED / TESTED**
- **P0-2 REAL-SQLite parse cache** — `pkg_cache(apk_path PK, apk_size, apk_mtime, manifest_sha, payload)` in a REAL libsqlite3 db (`<store>/c7_pkg_cache.sqlite3`; the vend is the already-linked libsqlite3 — the S185 law move; the AOSP pattern is PMS's package cache). Cold = AXML parse + EVP-SHA-256-keyed upsert; warm = JSON payload load with NO re-parse. **IMPLEMENTED / TESTED (cache=COLD ×3 rows then cache=WARM ×3 rows, failed=0 everywhere)**
- **P0-3 PM query/resolve consult the index** (cross-package candidates; `ResolveInfo.packageName` + `ComponentInfo.packageName` now served — the AOSP field every picker reads; single-package path fills it with the running package). **IMPLEMENTED / TESTED**
- **P0-4 installed-packages/provider identity from the index**: `getInstalledPackages` / `getInstalledApplications` (real lists), `queryContentProviders` (published enabled-provider table), `resolveContentProvider` (cross-package authority map, own-manifest path keeps precedence), `getProviderInfo` (foreign provider identity), `getPackageInfo(foreignPkg, GET_PROVIDERS|GET_SERVICES|GET_ACTIVITIES)`. The fabricated-empty dies WHERE A STORE EXISTS; without a store every handler is byte-identical to pre-W5 (no silent drift). **IMPLEMENTED / TESTED**
- **P0-5 broadcast dispatch foreign resolution** — foreign receivers RESOLVE from the index with loud `BCAST-XPKG` rows and are HONESTLY not executed (no fabricated onReceive — the foreign dex is not loaded by this engine; the row IS the delivery surface). **IMPLEMENTED / TESTED (row evidence)**
- **P0-6 store ingest wiring** — `MINIANDROID_PKG_STORE=<dir>` (the engine-side analogue of the AOSP `/data/app` scan) in `runtime/execution_engine.cpp`; the RUNNING package registers too (PMS resolves self); all ingest failures are loud `C7-STORE-ERR` rows (never silent, never swallowed). **IMPLEMENTED / TESTED**

## W5.3 Changed files (unified patch `c7_w5_on_s185.patch`, sha256 `b286c828f1034d797f9651c500df5d2134aa24a01e48fe18a9755abefd397565`, 2314 lines / 22 files — posted as comments below)

- NEW `miniandroid/src/dex/c7_package_index.h` / `.cpp` (the PMS-lite module)
- `miniandroid/src/dex/dalvik_engine.h` (index member + setter + WAVE-5 law comments)
- `miniandroid/src/dex/dalvik_engine.cpp` (6 wiring sites: PM query/resolve; installed/applications; queryContentProviders; resolveContentProvider; getProviderInfo; getPackageInfo; broadcast dispatch XPKG)
- `miniandroid/src/runtime/execution_engine.cpp` (store ingest + own-package registration)
- `miniandroid/Makefile` + `miniandroid/CMakeLists.txt` (source lists)
- NEW `scripts/c7_w5_run_probe.sh` (the ×3 cold / ×3 warm runner)
- NEW `fixtures/c7_pkg_store_probe/{c7pkgstore_browser,c7pkgstore_share,c7pkgstore_main}` (the three-package store fixtures)

## W5.4 Exact test commands (reproduce end-to-end)

```bash
# build (dalvik_engine TU at the CONT-37 -O2 -g0 rule; quickjs.c fetch-if-missing upstream bellard 2024-01-13)
make -C miniandroid -j2 && ls -la miniandroid/build/miniandroid

# probe APKs (aapt2-link binary-AXML recipe)
bash scripts/c7_build_probe.sh fixtures/c7_pkg_store_probe/c7pkgstore_browser fixtures/c7_pkg_store_probe/apks/c7pkgstore_browser.apk
bash scripts/c7_build_probe.sh fixtures/c7_pkg_store_probe/c7pkgstore_share   fixtures/c7_pkg_store_probe/apks/c7pkgstore_share.apk
bash scripts/c7_build_probe.sh fixtures/c7_pkg_store_probe/c7pkgstore_main    fixtures/c7_pkg_store_probe/apks/c7pkgstore_main.apk

# the ×3-cold + ×3-warm store probe (evidence: evidence/c7_w5/)
bash scripts/c7_w5_run_probe.sh <tag>
cat run/c7w5/<tag>/c7store_cold_results.jsonl

# engine-side rows (FileIoTrace JSONL, written per run by the runner)
grep -E '"op":"(BCAST-XPKG|PM-RCP-XPKG|PM-PKGINFO-XPKG|PM-INSTALLED|PM-PROVIDERS|C7-STORE)' run/c7w5/<tag>/main_cold1/file_io.jsonl
```

## W5.5 Before/after (same probe APK set, same capture protocol)

| op (app-side row) | BEFORE (base S185) | AFTER (W5) |
|---|---|---|
| `getInstalledPackages(0)` | fabricated empty list | **3 packages** (X01 PASS) |
| `getInstalledApplications(0)` | fabricated empty list | **3 applications** (X02 PASS) |
| `queryIntentActivities(VIEW http://example.org, MATCH_DEFAULT_ONLY)` | empty (own manifest only) | **c7.store.browser.BrowserActivity** (X03 PASS; disabled + no-DEFAULT excluded) |
| `resolveActivity(VIEW https, MATCH_DEFAULT_ONLY)` | null | **c7.store.browser.BrowserActivity** (X04 PASS) |
| exported=false identity in queries | n/a (nothing foreign existed) | visible (AOSP law; X05 PASS) |
| `queryIntentActivities(SEND text/plain)` | empty | **c7.store.share.ShareActivity** (X06 PASS) |
| CATEGORY_DEFAULT law across packages | n/a | lax-in / strict-out (X07 PASS) |
| `queryBroadcastReceivers` foreign | empty | **1 match** (X08 PASS) + `BCAST-XPKG` engine row |
| `queryIntentServices` foreign | empty | **c7.store.share.ShareService** (X09 PASS) |
| `resolveContentProvider("c7.store.clips")` | null (own manifest only) | **c7.store.browser.ClipProvider** (X10 PASS) |
| `queryContentProviders` | fabricated empty | **published table lists c7.store.clips** (X11 PASS) |
| disabled provider `c7.store.dead` | n/a | **unpublished** (X12 PASS) |
| unknown authority | null | null (X13 PASS — honest negative preserved) |
| `getPackageInfo("c7.store.browser", GET_PROVIDERS)` | own-package identity (wrong) | **foreign identity, providers=2** (X14 PASS) |
| `getPackageInfo("c7.store.share", GET_SERVICES)` | own-package identity (wrong) | **services=1** (X15 PASS) |
| self in installed set | n/a | visible (X16 PASS) |

**Probe verdict: 16/16 PASS ×3 cold + ×3 warm, row sets byte-identical across all six runs.**

## W5.6 Evidence chain

- base commit: S185 `8057943143282b0875d52faa47f5c433bb92639b`
- probe APK SHA-256: browser `e5252b70…`, share `0468a717…`, main `9bd75811…` (evidence/c7_w5/probe_apk_shas.txt)
- store verdicts ×3 cold: `664564f24cb19f5219747c6c597b1e9f5171ad1f082efca2ec3fb97bbf0e0e05` (each run; ×3 concat `dcdd3b15…`); warm identical — evidence/c7_w5/c7store_results_run{1,2,3}.jsonl
- SQLite cache law proof (run.log rows): cold `packages=3 cold=3 warm=0 failed=0` ×3 → warm `packages=3 cold=0 warm=3 failed=0` ×3 (evidence/c7_w5/store_cache_rows_{cold,warm}.txt) — **the app-load path skips the AXML re-parse on every warm boot**
- engine rows (file_io.jsonl `3a5fca4e…`): `BCAST-XPKG` (foreign receiver RESOLVED, honestly not executed), `PM-RCP-XPKG`, `PM-PKGINFO-XPKG` ×2, `PM-INSTALLED` ×3, `PM-PROVIDERS`, `PM-RESOLVE` ×7, `C7-STORE` ×3
- **regression (base↔W5 A/B, rebuilt base binary from the same commit):**
  - c7 34-op component probe: base `4aa8f51c…` == W5 ×3 `4aa8f51c…` — **byte-identical to the recorded WAVE-4 contract SHA**
  - activity-chain probe: base `60b4a75a…` == W5 ×3 (8/8 PASS)
  - gate_a: verdict stream byte-identical base↔W5 (88 PASS / 9 FAIL / 2 INFO on THIS sandbox; the ASSET/FD/NAT-family FAILs are base-inherited environment-scoped rows — the base binary produces the exact same 9 — gate_a evidence/c7_w5/gate_a_{BASE,w5tree}.jsonl)
  - the no-store path (every regression run above) is byte-identical → the no-silent-drift law holds

## W5.7 Known limitations (honest chain)

1. ~~Foreign components RESOLVE but do not EXECUTE~~ — **CLOSED by WAVE-6 below** (LoadedApk-lite): foreign receivers/services/providers now EXECUTE their real bytecode with exported/permission gates. Still single-process (the AOSP multi-process isolation is not modeled — documented, out of scope).
2. The store is env-gated (`MINIANDROID_PKG_STORE`). The engine's own `install`+`--data-root` store (`<data-root>/data/app/<pkg>/base.apk`) is the natural auto-index source — wiring the index to it is a small follow-up (this wave kept the two paths decoupled to avoid touching the manager's install flow).
3. `queryContentProviders` serves the identity fields consumers read (name/packageName/authority/authorities/exported); ProcessRecord-level fields are not modeled.
4. `getPreferredActivities` still answers empty (the preferred-activity model is a separate resolution law); `sendStickyOrderedBroadcast`/UserHandle overloads and FGS `onTimeout` remain PENDING from W3 (unchanged).
5. best-match refinement remains priority-ordered-first-match (the W3 documented simplification), now applied across packages.


## 1. Component coverage matrix (S170 refresh — after wave-2)

| Component / API | Implementation location | Expected behavior (AOSP source) | State at S170 base | Gap found this round | Test coverage | Evidence |
|---|---|---|---|---|---|---|
| Ordered broadcast dispatch | `dalvik_engine.cpp` sendBroadcast/sendOrderedBroadcast block | BroadcastQueueModernImpl priority tranches | TESTED (wave-1) | none | ORD-01..03 | 12/12 re-verified on S170 |
| Per-filter receiver resolution | `manifest_reader.{h,cpp}` + dispatch candidates | PackageParser: every `<intent-filter>` is its own matchable record (own priority/actions/categories); one receiver + 2 matching filters ⇒ 2 deliveries | PARTIAL (MAX-fold) | per-filter records absent | **ORD-08 / ORD-09** (wave-2) | `MFA,MFH,MFB,MFL,FINAL`, deliveries=2; category-selective filter |
| Service bring-down | `c7_service_bring_down` (new) | ActiveServices.bringDownServiceLocked: onUnbind BEFORE onDestroy when live bindings exist, on every teardown caller | MISSING (stop paths) | stopService/stopSelf skipped onUnbind (wave-1 §7 PENDING) | **SVC-10** (wave-2) | unbinds=1 destroys=1 + `SVC-UNBIND "bring-down (stopService)"` trace rows |
| Sticky broadcasts | `sticky_broadcasts_` cache + registerReceiver catch-up | ContextImpl: last sticky per action cached; delivered to every NEW matching receiver at registerReceiver; `removeStickyBroadcast` drops it | MISSING (0%) | sendStickyBroadcast was unrouted | **STK-01/02/04** (wave-2) | caught=1 initial=true v=v1 → removed → 0 → re-cache v2 |
| Sticky-send permission | dispatch sticky law | ContextImpl: sender must hold `android.permission.BROADCAST_STICKY` (SecurityException) | MISSING | — | STK deny rows R1 vs R0/R2 | foreign sender w/o perm → `BCAST-DENY`, no cache |
| Receiver registration permission | `DynamicReceiver.permission` | BroadcastFilter.requiredPermission enforced against the SENDER | MISSING (arg ignored) | — | **ORD-10** | perm receiver denied, control delivered |
| Exported gating (manifest receivers) | dispatch + wave-1 exported parse | ActivityManagerService.checkComponentPermission: foreign sender cannot reach `exported=false`; same-uid always may; absent attr + filter + targetSdk≤30 ⇒ exported | STRUCTURAL only (wave-1) | not observable single-package | **EXP-01..03** across R0/R1/R2 (modeled-sender env) | R1: EXP1 denied / EXP2 denied / EXP3 delivered; R2: EXP2 delivered; R0: all delivered |
| BroadcastReceiver natives | receiver-native block | isInitialStickyBroadcast | MISSING | — | STK-01 | initial=true during catch-up only |
| PackageManager.getReceiverInfo | new PM law (mirror of F-NEW-275 getServiceInfo) | ReceiverInfo(name/exported/permission), NameNotFoundException on miss | MISSING | stub jar has no `android.content.pm.ReceiverInfo` class ⇒ **Java probe cannot compile the call** | engine-level law + `PM-RECEIVER-INFO` trace | PARTIAL — see §7 |
| Service start/bind contract | wave-1 laws | startId guard, per-service counters, targeted unbind, onUnbind/onRebind, FGS tracking | TESTED | none | SVC-05..09 | 12/12 re-verified |
| ContentProvider CRUD/Cursor | `dalvik_engine.cpp` PROV ops | query/insert/update/delete, Cursor lifecycle, openFile | TESTED at base (probe PROV-02..09) | none found in scope this round | gate_a PROV rows | unchanged by wave-2 |
| Activity lifecycle/task stack | `dalvik_engine.cpp` + fragment drains | onCreate→…→onDestroy, launch modes | TESTED (README matrix) | out of this round's scope | corpus + gate_a | unchanged |
| Intent resolution (action/category) | IntentShadow + S123 registry | addCategory/hasCategory/filter match | TESTED (wave-1) | none | ORD-04/09 | unchanged |

---


---

# HISTORICAL WAVES 1–3 (compressed for fast load — full detail: patch comments 1–17 below, S177/S179 intake verdicts comments 14–15)

- **WAVE-1 (14 laws, base `25b5a01b` → rebased on S170 `439b0a3d`)**: ordered-broadcast priority tranches, result chain, final resultReceiver, abort law, goAsync/PendingResult, receiver permission, category match, stopSelfResult guard, per-service startIds, targeted unbind+IAE, onUnbind/onRebind, FGS tracking, manifest receiver/service attribute model. AFTER 12/12 PASS; results SHA `a248cab28075521d…` byte-identical across sandboxes. Status: IMPLEMENTED/TESTED.
- **WAVE-2 (base S170+w1)**: service bring-down delivers onUnbind BEFORE onDestroy on EVERY teardown caller (SVC-10); per-filter receiver resolution — every `<intent-filter>` its own matchable record, one receiver + 2 filters ⇒ 2 deliveries (ORD-08/09); sticky cache + catch-up delivery + isInitialStickyBroadcast (STK-01/02/04); sticky-send permission; dynamic registration-permission; exported/foreign-sender model (EXP-01..03 across R0/R1/R2); `getReceiverInfo`. 19/19 PASS; gate_a verdict stream byte-identical W1→W2. Status: IMPLEMENTED/TESTED.
- **WAVE-3 (20 laws, base W2 tree)**: task-stack/launch-flag set (singleTop/onNewIntent, CLEAR_TOP, startActivities FIFO, disabled-component launch gate, calling-identity laws), service AUTO_CREATE/missing/stopSelf(int) shapes, broadcast matchData + unregister + sticky-ordered, ContentProviderClient acquire/release lifecycle, PackageManager REAL resolution (CATEGORY_DEFAULT lax-in/strict-out, enabled law, queryIntentActivities/Services/BroadcastReceivers/resolveActivity/resolveService). 34/34 PASS ×3 cold + activity-chain 8/8 ×3 (`4aa8f51c…` / `60b4a75a…` — still byte-identical on the W6 tree). Status: IMPLEMENTED/TESTED.
- Manager intake: S177 chain integrity verified; **S179: full W1+W2+W3 chain ACCEPTED_FOR_INTEGRATION (merged to main `7d02b803`)**; S180 full-corpus battery byte-inert on 13/14 (no regressions — the corpus does not exercise those paths; the corpus flip arrived in WAVE-4).

---

# WAVE-8 (base S185+W5+W6+W7): PERMISSIONS + PENDINGINTENT + AUTO-INDEX + LAUNCHMODE — and 3 probe-discovered pre-existing law fixes

**Base commit:** W7 tree (S185 `80579431…` + W5 patch comments 18/19 + W6 patch 20/21 + W7 patch 22). W8 HEAD `95fad279` (branch `c7-w6`, local; no pushes). Main HEAD at authoring time: S188 `d3a8d0ec` (W5 not yet merged; W5..W8 land as one chain).

## W8.0 The four laws (generic, no per-app special-casing)

1. **W8-L1 — the per-op PROVIDER PERMISSION gate** (AOSP `checkContentProviderAccess`): `android:readPermission`/`android:writePermission` are parsed (PackageParser.Provider → ProviderInfo), ride the W5 index + SQLite cache (`rp`/`wp` payload keys — pre-W8 warm payloads load with "" defaults), and gate every CRUD op: read ops (query/getType/openFile*/acquire*) vs readPermission, write ops (insert/update/delete) vs writePermission. Same-package callers exempt (AOSP same-uid law); the running package's uses-permission list satisfies the check (deterministic install-grant). A denial is a REAL `SecurityException("Permission Denial: reading|writing <auth> requires <perm>")` in the caller's frame. Engine rows: `PROV-PERM-DENY` / `PROV-PERM-OK`.
2. **W8-L2 — PendingIntent.send is now a REAL dispatch** (AOSP `PendingIntentRecord.sendInner`): the M3-era loud boundary stub became the wired send channel — the shadow owns the RECORD laws (FLAG_ONE_SHOT: after one successful send the record cancels; a further `send()` throws a REAL `android.app.PendingIntent$CanceledException`; FLAG_IMMUTABLE: the fill-in intent is IGNORED; mutable records merge the fill-in extras), and ONE engine law (`c7_send_pending_intent`) routes the frozen intent through the EXACT pipelines the app-context calls use: BROADCAST → `bridge_to_api(ContextWrapper.sendBroadcast)` (full gated law), SERVICE → `startService`, ACTIVITY → the W7 resolve + synchronous gate + launch queue (the ContextImpl NEW_TASK gate does NOT apply — AOSP sendInner is AMS-level). Zero duplicated dispatch law (S185 VEND). `PendingIntent.cancel()` also implemented (record removal). Exception ancestry row added: `PendingIntent$CanceledException → java.lang.Exception`. Engine rows: `PI-SEND` / `PI-SEND-CANCELED` / `PI-SEND-FILLIN`.
3. **W8-L3 — the data-root auto-index** (AOSP /data/app scan): `MINIANDROID_PKG_STORE` unset ⇒ the engine indexes its OWN install store `<data-root>/data/app` recursively (`ingest_install_store`; the F-NEW-231 `<pkg>/base.apk` mapping), cache db `<data-root>/data/app/c7_pkg_cache.sqlite3`, loud `C7-STORE-AUTO` rows. Zero env AND zero install store ⇒ empty index = the pre-W5 one-package behavior, byte-identical.
4. **W8-L4 — the foreign launchMode law**: `c7_activity_launch_mode` falls back to the W5 index (C7IdxActivity.launch_mode — AOSP ActivityInfo.launchMode regardless of owning package); the launch drain treats singleTask(2)/singleInstance(3) as singleTop-at-top (onNewIntent reuse, no new instance) and clear-top-in-task. Also: **activity intent-filter `android:priority` is now parsed** (it existed only for receivers) and rides the index (`ef.priority`) — the AOSP IntentResolver priority refinement now decides cross-package resolution.

## W8.1 The three probe-discovered PRE-EXISTING engine bugs (each one closed with live evidence)

1. **Intent(String, Uri) ctor: the data-URI law was DEAD CODE** — the outer framework catch-all (`rfind("Landroid/",0)==0`) swallowed `Landroid/net/Uri;` before the `else if (Uri)` arm could ever run. Every ctor-built intent carried EMPTY scheme/host/path; only `setData()` filled the dims; the W3 matchData half never executed on the ctor path. Live evidence: the priority-10 singleTask fixture resolved for EVERY example.org URL (host/path never reached the index law). Fix: the three arms (Class-token → referent / Uri → data / other-app-class → component) expressed directly, no catch-all can swallow the Uri arm.
2. **Sibling `<data>` elements: authority-only elements were DROPPED** (the capture required mimeType or scheme) and the AOSP addDataAuthority law (authority applies to EVERY declared scheme) was unmodeled — BrowserActivity's three sibling `<data>` elements lost their host in the index. Fix: host/path-only elements STAMP onto every scheme-carrying spec lacking a host (manifest_reader).
3. **Activity filter priority unparseed** (see W8-L4).

## W8.2 Evidence chain (all machine-reproduced in this sandbox)

- unified patch `c7_w8_on_w7.patch`: 28 files, +1795/−49, sha256 `a2518d1d60cc054cee2566dc84f4a2fd05d3ec585e729cfe162b679741581898`, `git apply --check` CLEAN on pristine W7 tree
- binary sha256 `b4acdd571f102cf16d8529d65a09d748bba25f234c88d6acd5e08753324c0a17`
- **store probe: 33/33 PASS ×3 cold + ×3 warm — all six verdict files byte-identical `9831ee300041e01337e06a559ad3c1060f8f0fa6a08445ac4f84ea86ed1c4a0f`**
- **X01-X23 prefix == the W6 golden (21 lines) BYTE-IDENTICAL** — the W5/W6/W7 contracts hold unchanged on the W8 binary
- **W8-LAUNCH-CONTRACT PASS** (the foreign/own bytecode's own markers): `top-create=1 top-newintent=1 act-create=4 pi-recv=3`; `pi-recv:deliveries=1;k=frozen1 / 2;k=oneshot / 3;k=frozen`, NO `k=fillin` (the IMMUTABLE law held)
- **auto-index ≡ explicit store: BYTE-IDENTICAL 33-op verdict** (install-store path, ×2 cold; `C7-STORE-AUTO … packages=3 apks=3`)
- no-store regressions byte-identical: 34-op `4aa8f51c87291783…` ×1 (== recorded), act-chain `60b4a75acd3a223f…` ×1 (== recorded)
- SQLite cache law intact: cold `packages=3 cold=3 warm=0 failed=0` ×3 → warm `cold=0 warm=3 failed=0` ×3
- androguard cross-parser (`scripts/c7_w8_androguard_check.py`): `all_ok: true` — now also the provider readPermission/writePermission facts, TopActivity launchMode, and main's uses-permission set `{c7.perm.SHARE_READ}`
- engine rows (cold1): `PROV-PERM-DENY` ×2, `PROV-PERM-OK` ×1, `PI-SEND` ×5, `PI-SEND-CANCELED` ×1, `PI-SEND-FILLIN` ×4, `ACT-XPKG-RESOLVE` ×5

## W8.3 The 10 new verdict ops (X27-X36)

| op | law exercised | expected | observed |
|---|---|---|---|
| X27 | gated READ on foreign provider (perm DECLARED) | granted; real rows | PASS (PROV-PERM-OK) |
| X28 | gated WRITE on foreign provider (perm NOT declared) | SecurityException in frame | PASS |
| X29 | gated READ, no permission anywhere | SecurityException in frame | PASS |
| X30 | WRITE on read-only-gated provider (no writePermission) | GRANTED (per-op asymmetry) | PASS |
| X31 | PI broadcast send | own receiver executes (marker) | PASS |
| X32 | FLAG_ONE_SHOT second send | CanceledException | PASS |
| X33 | FLAG_IMMUTABLE + fill-in | frozen extra wins, fill-in ignored | PASS |
| X34 | PI ACTIVITY-kind send | resolve+gate+queue (no NEW_TASK demand) | PASS |
| X35 | foreign singleTask double launch | 2nd launch = onNewIntent reuse | PASS (markers) |
| X36 | foreign standard double launch | two REAL instances | PASS (act-create ×2) |

## W8.4 Known limitations (honest chain)

1. Single-process model unchanged (W6.6 #1). The URI-grant flags (FLAG_GRANT_READ/WRITE_URI_PERMISSION) are recorded as intent state but have no cross-package consumer in the single-process engine — recorded, not fabricated.
2. PI SERVICE kind dispatches through startService law but the probe exercises BROADCAST + ACTIVITY kinds (the corpus shapes); SERVICE-kind verdict op PENDING.
3. `getPreferredActivities` (W3), FGS `onTimeout` (W3) still PENDING. Sticky-ordered/UserHandle overloads unchanged.
4. Chooser law unchanged (deterministic first-match, W7.6 #5). The priority refinement (W8-L4) now makes that first-match the AOSP priority winner rather than pure ingest order.

## W8.5 Status

**IMPLEMENTED / TESTED** — every verdict row machine-reproduced (deterministic ×6 store battery + ×2 auto-index + ×2 no-store regressions, all byte-identical). W5 resolution + W6 execution + W7 launch + W8 permissions/intents/auto-index/launchMode = the cross-package component base now honors the AOSP security and intent-sender contracts on a package store that boots from the engine's own install dir.

# WAVE-7 (base S185+W5+W6): CROSS-PACKAGE ACTIVITY LAUNCH — the ActivityStarter law closes the last component-type gap

**Base commit:** W6 tree `a386825baa5cf31aec382a2628cfca2e7362ac5d` (S185 `80579431…` + W5 patch comments 18/19 + W6 patch comments 20/21). W7 tree HEAD `bc21689a` (branch `c7-w6`, local; no pushes). Main HEAD at authoring time: S188 `d3a8d0ec` (FragmentManager host-wiring recon — different territory; the S187/S188 dalvik_engine hunks sit at line ranges far from every W7 seam, composition is clean).

## W7.0 What the wave delivers (the generic law, no per-app special-casing)

The pre-W7 engine resolved a foreign activity (W5: `queryIntentActivities`/`resolveActivity` across the store) but could not LAUNCH it: implicit cross-package starts died with `ACTIVITY_NOT_FOUND: implicit intent`, and a denied start queued first and silently no-op'd at the drain. WAVE-7 completes the AOSP launch contract on the store tree:

1. **Implicit cross-package resolution** (AOSP `ContextImpl.startActivity` → `PackageManager.resolveIntent` across ALL installed packages): the W3 match law (action + categories + matchData + CATEGORY_DEFAULT for startActivity) evaluated over the W5 `C7PackageIndex` — own-manifest miss is NO LONGER the end of resolution. New engine rows: `ACT-XPKG-RESOLVE`.
2. **The SYNCHRONOUS launch gate** (AOSP `Instrumentation.checkStartActivityResult` via `ActivityManagerService.checkComponentPermission`): a DISABLED target throws `android.content.ActivityNotFoundException`; a NON-EXPORTED target owned by ANOTHER package throws `java.lang.SecurityException` ("Permission Denial … not exported"); same-uid starts of non-exported activities stay ALLOWED. Thrown IN THE CALLER'S FRAME, before any queueing (AOSP ordering: checkComponentPermission BEFORE the task insert — the W7 pending-order law).
3. **Foreign activity REAL execution** (LoadedApk-lite carried to the fourth component type): a launched foreign activity runs its REAL foreign bytecode — the F-118 `<init>` constructor law + real `onCreate` — through the unchanged `try_recursive_invoke` machinery over the W6 store-dex class index. New engine rows: `ACT-XPKG-EXEC`. The foreign context identity law (W6) answers `getPackageName()` with the owning package inside the foreign lifecycle.
4. **Task-stack integration**: the foreign launch is a first-class G08 launch — task record push, `A.onPause`/`A.onStop`, `stack_depth_after`, mFinished gate — all existing W3 laws apply unchanged.
5. **Drain-side defense-in-depth**: the drain re-applies the same gate (AOSP re-checks at ActivityStarter), refusing foreign disabled / cross-package non-exported targets loudly.
6. **One component table** (S185 VEND/DON'T-REWRITE): the shadow layer consults the ENGINE's `C7PackageIndex` through two wired callbacks (`set_c7_xpkg_activity_resolver` / `set_c7_activity_gate`) — zero duplicated resolution law. No store configured ⇒ callbacks unset ⇒ byte-identical pre-W7 behavior.

## W7.1 Files changed (patch `c7_w7_on_w6.patch`, 937 lines, 12 files, +737/−6, `git apply --check` CLEAN on pristine `a386825b`)

- `miniandroid/src/dex/dalvik_engine.{h,cpp}` (+189): `c7_activity_launch_gate()` + `c7_resolve_activity_xpkg()`; Site-A dispatch (non-Activity receivers + `startActivities`): xpkg resolution fallback + synchronous gate before queueing.
- `miniandroid/src/framework/android_shadows.{h,cpp}` (+102/−6): IntentShadow callback channel; Site-B (Activity receivers — the main path): WAVE-7 resolution fallback + gate + the AOSP pending-order law (set_pending moved BELOW the gate — a thrown launch never queues).
- `miniandroid/src/runtime/execution_engine.cpp` (+70/−0): wiring of both callbacks after `set_package_index`; drain-side gate; `ACT-XPKG-EXEC` evidence row after the foreign `onCreate` dispatch.
- `fixtures/c7_pkg_store_probe/`: `BrowserActivity` real `onCreate` (handshake marker `act-create:pkg=<getPackageName()>`), `Main` +3 ops (X24/X25/X26 below).
- `scripts/c7_w7_run_probe.sh` (new, 23-op contract), `scripts/c7_w6_androguard_check.py` (+activities cross-parser section), `evidence/c7_w7/*` (golden + first-run verdict).

## W7.2 The three new verdict ops (app-side rows, same handshake execution-proof channel as W6)

| op | law exercised | BEFORE (W6 tree) | AFTER (W7) |
|---|---|---|---|
| X24 | implicit cross-package START (`VIEW http://example.org/w7`, no component) | `ACTIVITY_NOT_FOUND: implicit intent` at the drain (own-manifest resolution only) | **no throw in-frame** (AOSP async contract) + `ACT-XPKG-RESOLVE → c7.store.browser.BrowserActivity` + the foreign activity's REAL `<init>`+`onCreate` execute (handshake marker `act-create:pkg=c7.store.browser` written by the FOREIGN bytecode) |
| X25 | explicit start of a NON-EXPORTED foreign activity (`HiddenViewActivity`, exported=false) | queued, then silently no-op'd at the drain | **`SecurityException` thrown synchronously** ("Permission Denial … not exported from package c7.store.browser") |
| X26 | explicit start of a DISABLED foreign activity (`DeadViewActivity`, enabled=false) | drain refused quietly after queueing | **`ActivityNotFoundException` thrown synchronously** |

**W7-LAUNCH-CONTRACT (runner-level, machine-checkable): PASS** — `launched=True`, component `Lc7/store/browser/BrowserActivity;`, `<init>` dispatched (2 instr), `onCreate` dispatched (36 instr), handshake marker present.

## W7.3 Exact commands (this sandbox)

```bash
cd /home/z/my-project/c7tree && git worktree add -f /home/z/my-project/c7tree a386825b  # (recreated from repo)
cd miniandroid && make -j1 && cd ..           # binary 2c3eb892…
for p in c7pkgstore_browser c7pkgstore_share c7pkgstore_main; do
  bash scripts/c7_build_probe.sh fixtures/c7_pkg_store_probe/$p \
       /home/z/my-project/c7tree/fixtures/c7_pkg_store_probe/apks/$p.apk; done
bash scripts/c7_w7_run_probe.sh w7final        # 23-op battery, COLD×3 + WARM×3
# backward-compat: W6-era fixtures (git archive a386825b) on the W7 binary
bash scripts/c7_w6_run_probe.sh w6onw7
# no-store regressions (no MINIANDROID_PKG_STORE):
#   34-op: fixtures/c7_bcast_service_probe, --frames 3   → c7_results.jsonl
#   act-chain: fixtures/c7_activity_probe, --frames 12   → act_results.jsonl
```

## W7.4 Before/after summary

| surface | BEFORE (W6) | AFTER (W7) |
|---|---|---|
| implicit cross-package activity start | `ACTIVITY_NOT_FOUND: implicit intent` (own manifest only) | resolved via store index (ACT-XPKG-RESOLVE) → REAL foreign launch |
| non-exported foreign start | silent no-op (queued then dropped) | synchronous `SecurityException` |
| disabled foreign start | silent no-op (queued then dropped) | synchronous `ActivityNotFoundException` |
| foreign activity bytecode | never executed (resolve-only; W6.6 limitation #2) | REAL `<init>`+`onCreate` (F-118 law) + ownership-law `getPackageName` |
| task stack on foreign launch | n/a | G08 record push, stack_depth 0→1, A.onPause/A.onStop |
| W6 20-op contract | `24ae2c3a…` | **byte-identical on the W7 binary** (`24ae2c3a…` ×6, w6onw7 run) |

## W7.5 Evidence chain

- base commit: W6 tree `a386825baa5cf31aec382a2628cfca2e7362ac5d`; W7 HEAD `bc21689a`
- unified patch `c7_w7_on_w6.patch`: 937 lines, sha256 `8c76baccabba5cf28bf31e71e8a2855889ab45ca187ed99747647f86f617cdc7`, `git apply --check` CLEAN on pristine `a386825b`
- binary sha256 `2c3eb89236ad8fd6d3f3682dad63ebaa20c79b5bd56fb3295b06aa5001dfa6ca`
- probe APKs (W7 fixtures): browser `3df6eb6e…`, share `14b43407…`, main `7fff5c30…`
- **store probe: 23/23 PASS ×3 cold + ×3 warm, all six verdict files byte-identical `4ddf418f852c7d898c743f206c047fc42dd49c7e5396df1351f96ba5c5c8bd61`**
- **W6 backward-compat, two independent proofs**: (a) the W6-era 20-op file (`24ae2c3af87e3870…`, rebuilt from `git archive a386825b` fixtures) is a byte-exact 21-line prefix of the W7 23-op file; (b) the W6-era fixtures run on the W7 binary → the whole 20-op contract reproduces `24ae2c3af87e3870…` ×6 exactly (X01–X16 prefix == the W5 golden `664564f2…` still byte-identical)
- no-store regressions byte-identical: 34-op component probe `4aa8f51c87291783…` ×3, activity-chain probe `60b4a75acd3a223f…` ×3 (both == the recorded WAVE-3/4 contracts)
- engine rows (cold1 `file_io.jsonl`): `ACT-XPKG-RESOLVE` (→ BrowserActivity), `ACT-START` ×2 deny rows (SecurityException / ActivityNotFoundException), `ACT-XPKG-EXEC` (c7.store.browser → Lc7/store/browser/BrowserActivity;) + the stderr rows `[C7-ACT-XPKG] foreign activity executed`, `[G08-LAUNCH] launched … stack depth now 1`
- lifecycle record (frames manifest `activity_launch`): `launched=true`, callbacks `<init>` dispatched 2 instr, `onCreate` dispatched 36 instr (the foreign onCreate that writes the marker)
- handshake markers (the FOREIGN bytecode's own writes): `ping:…deliveries=1`, `svc-create/svc-start`, **`act-create:pkg=c7.store.browser;cls=c7.store.browser.BrowserActivity`** — the W6 `getPackageName` ownership law answers correctly inside the foreign activity
- androguard cross-parser (`scripts/c7_w6_androguard_check.py`, extended): `all_ok: true` — now also verifies the ACTIVITY gate facts independently (BrowserActivity exported / HiddenViewActivity not-exported / DeadViewActivity disabled / NoDefaultActivity exported)
- SQLite cache law intact: cold `packages=3 cold=3 warm=0 failed=0` ×3 → warm `cold=0 warm=3 failed=0` ×3

## W7.6 Known limitations (honest chain)

1. Single-process model (unchanged from W6.6 #1): the foreign activity executes inside the running process; the ownership map models identity laws, not process boundaries.
2. Foreign `launchMode` (singleTop/singleTask/singleInstance) for cross-package targets is served by the W3 own-manifest helpers only; the drain consults the index for enabled/exported but not yet per-target launchMode (standard applies for foreign targets). PENDING.
3. Foreign activity `taskAffinity`/`allowTaskReparenting`/documented launch intents (PendingIntent parity) not modeled. PENDING.
4. Provider readPermission/writePermission gate (W6.6 #3) still PENDING; data-root auto-index (W6.6 #4) still PENDING; `getPreferredActivities` still PENDING (W3).
5. The resolution fallback prefers the index's top candidate (priority desc, ingest order). A real chooser (multiple equal-priority candidates) still resolves to the first — AOSP shows a chooser UI; a headless engine has no UI surface, so the deterministic first-match is the honest shape (recorded, not fabricated).

## W7.7 Status

**IMPLEMENTED / TESTED** — every verdict row above is machine-reproduced on this sandbox (deterministic ×6 store battery + ×3 + ×3 no-store regressions, all byte-identical). The last of the four component types now LAUNCHES cross-package; W5 resolution + W6 execution + W7 launch = the component-runtime base runs real foreign broadcast receivers, services, providers AND activities from a package store — the architectural shape needed to run thousands of real apps against real cross-app flows.


---

# WAVE-6 (base S185+W5): LOADEDAPK-LITE — foreign components EXECUTE (S185 LOAD-FIRST applied to cross-package code) — **IMPLEMENTED / TESTED**

**The S185 SQLITE RULE (#536) clause 2 (LOAD-FIRST) driven into the last structural gap of the component domain** (the user's scale directive: the BASE must run thousands of real apps — cross-app flows are where real apps live).

## W6.1 Missing/wrong (9-item, per law)

1. **Foreign components RESOLVED but never EXECUTED** (the W5 honest limitation #1): a broadcast to a foreign receiver produced a `BCAST-XPKG` row and NO delivery; `startService`/provider-acquire to a foreign component had no execution path at all. **Why generic:** AOSP `LoadedApk` + `ActivityThread.handleReceiver/handleCreateService/acquireProvider` load the TARGET package's code and run the REAL component class for every cross-package delivery — browser pickers, share targets, FileProvider consumers, plugin flows. **Change:** `DalvikExecutionEngine::inject_foreign_apk_code()` — every store APK's `classes.dex..classesN.dex` parsed at boot, classes merged into the SAME merged class index the running app uses (the EXP-088+ multi-DEX mechanics generalized per-STORE), each foreign dex occupying its own `per_dex_raw_data_` slot via `class_to_dex_index_` (the EXP-038 per-DEX resolution law — without this, foreign bytecode resolves its string/type/method IDX against the WRONG dex tables: live evidence, `BrowserPingReceiver.onReceive` resolved `ActivityInfo.name` constants), plus the EXP-095 superclass / S102 interfaces / F-087 annotations closure maps, and a foreign class → owning-package map. **Files:** `dalvik_engine.{h,cpp}`, call site in `execute_apk_with_activity` after `inject_secondary_dex_classes()`. **Status: IMPLEMENTED / TESTED.**
2. **Foreign broadcast EXECUTION + gates**: the dispatch now builds foreign candidates into the SAME priority-sorted candidate model (C7Cand.xidx), gated by AOSP `checkComponentPermission` (exported=false ⇒ `BCAST-DENY`, no delivery) + receiver permission (`c7_sender_holds`), then delivers through the unmodified shape: allocate → `<init>` → `onReceive(context, intent)` (real bytecode, ordered-chain/sticky laws included). A class that did not load keeps the W5 honest `BCAST-XPKG` row — no fabricated callbacks. **Status: IMPLEMENTED / TESTED (X20 +, X23 deny).**
3. **Foreign service EXECUTION + gates**: `startService`/`bindService` on a foreign service pass the exported/permission gate (`SVC-XPKG` row; deny = `SVC-XPKG-DENY` + AOSP not-started shape), then the existing newInstance law runs the REAL `<init>()V → onCreate → onStartCommand/onBind`. **Status: IMPLEMENTED / TESTED (X21).**
4. **Foreign provider ACQUISITION**: `resolve_provider_for_authority` on an own-provider miss installs the foreign provider from the W5 index (exported/grantUriPermissions gate ⇒ `PROV-XPKG-DENY`), mirroring `install_content_providers` GATE-A: allocate → `<init>` → ProviderInfo(index identity) → `attachInfo` → `onCreate` → publish every `;`-joined authority — then the UNMODIFIED CRUD dispatch runs the foreign `query/insert/update/delete/openFile` bytecode. **Status: IMPLEMENTED / TESTED (X22: real MatrixCursor rows cross the boundary).**
5. **Context identity for foreign components** (AOSP ContextImpl per-package base context): `Context.getPackageName` inside a foreign component answers the FOREIGN package (`CTX-XPKG-PKGNAME` row) via the ownership map; own classes are absent from the map ⇒ unchanged behavior. **Status: IMPLEMENTED / TESTED (X20's handshake carries `pkg=c7.store.browser` from real foreign code).**
6. **Heap-String receiver law** (generic Java law surfaced by the probe): the String bridge gated on `STRING_REF` receivers — methods on HEAP String objects (`new String(byte[])`, `StringBuilder.toString()`) fell to the typed-default answer; `indexOf` on a miss answered a non-negative garbage int (live evidence: X23's negative containment probe flipped). Fix: an OBJECT_REF receiver whose heap class is `Ljava/lang/String;` is read through `__string_value__` (the F-NEW-248/299 store) and processed by the SAME arms. **Status: IMPLEMENTED / TESTED.**
7. **Live file: observability law** (generic I/O law surfaced by the probe): `cached_asset_bytes` was insert-once — a `file:` stream re-read stale bytes after another stream appended. AOSP: every `read()` observes the file's current bytes once the writer closes. Fix: `file:` keys re-read when (size, mtime) changed; APK/asset entries stay immutable-cached. **Status: IMPLEMENTED / TESTED (the X20→X21 handshake channel proves cross-component visibility).**
8. **Probe extension (fixtures)**: `BrowserPingReceiver` (real onReceive writes its FOREIGN identity to the shared handshake file), new `NoisyReceiver` (exported=false deny-law fixture — real code that would write a marker if the gate ever broke), `ShareService` (real onCreate+onStartCommand), `ClipProvider` (real MatrixCursor rows), `Main` X20–X23 ops + the fresh-install runner law. **Status: IMPLEMENTED / TESTED.**
9. **Androguard cross-parser verification** (user directive): `scripts/c7_w6_androguard_check.py` re-derives the store APKs' component inventory (package/receivers/services/providers × exported/enabled) with androguard 4.1.4 — an INDEPENDENT AXML parser — and diffs against the fixture law; all OK. **Status: OBSERVED (all_ok=true).**

## W6.2 Changed files (unified patch `c7_w6_on_w5.patch`, sha256 `dc1b1a8552c7ee0ee52c…`, 1682 lines / 17 files — posted as comments below)

- `miniandroid/src/dex/dalvik_engine.{h,cpp}` (the six laws above; +699/−31 lines)
- `fixtures/c7_pkg_store_probe/*` (the W6 fixture set: 4 component rewrites + NoisyReceiver + Main X20–X23 + browser manifest)
- NEW `scripts/c7_w6_run_probe.sh` (cold ×3 / warm ×3 runner, fresh-install law, evidence collection)
- NEW `scripts/c7_w6_androguard_check.py` (independent cross-parser verification)
- `evidence/c7_w6/*` (verdict jsonl, cold/warm concats, androguard verdict, engine rows, golden prefix, EVIDENCE.txt)

## W6.3 Exact test commands (reproduce end-to-end)

```bash
make -C miniandroid -j2 && sha256sum miniandroid/build/miniandroid   # 85352ae03982fc4c…
for p in browser share main; do
  bash scripts/c7_build_probe.sh fixtures/c7_pkg_store_probe/c7pkgstore_$p \
    $(pwd)/fixtures/c7_pkg_store_probe/apks/c7pkgstore_$p.apk; done
python3 scripts/c7_w6_androguard_check.py        # all_ok:true
bash scripts/c7_w6_run_probe.sh <tag>            # cold ×3 + warm ×3
cat run/c7w6/<tag>/c7store_cold_results.jsonl    # 20/20 PASS rows
grep -E '"op":"(C7-STORE-DEX|BCAST-XPKG-EXEC|SVC-XPKG|PROV-XPKG-EXEC|CTX-XPKG-PKGNAME)"' run/c7w6/<tag>/main_cold1/file_io.jsonl
```

## W6.4 Before/after (same probe APK set, same capture protocol)

| op | BEFORE (W5 tree) | AFTER (W6) |
|---|---|---|
| `sendBroadcast(c7.store.BrowserPing)` to the foreign receiver | `BCAST-XPKG` row, delivered=0 — "resolved, not executed" | **REAL onReceive executes** (`BCAST-XPKG-EXEC`, delivered=1); foreign code writes `ping:pkg=c7.store.browser` (X20 PASS) |
| foreign receiver's `getPackageName()` | running package (wrong identity) | **`c7.store.browser`** (`CTX-XPKG-PKGNAME` law; X20 handshake content) |
| `startService` → foreign ShareService | not-executable (resolved only) | **onCreate+onStartCommand run** (`SVC-XPKG` + `SVC-INIT`/`SVC-START` rows; X21 PASS) |
| `ContentResolver.query(content://c7.store.clips/…)` | IllegalArgumentException("Unknown authority") | **foreign provider installed (attachInfo+onCreate) + REAL query returns 2 rows** (X22 PASS) |
| broadcast to exported=false foreign receiver | deny held (no execution existed) | **deny HELD with real code present** (`BCAST-DENY`, delivered=0, marker absent; X23 PASS) |
| String methods on heap String objects | typed-default garbage (indexOf miss ⇒ ≥0) | **OpenJDK-correct answers from `__string_value__`** |
| `file:` stream re-read after append | stale snapshot | **live bytes** ((size,mtime) freshness law) |
| X01–X16 (W5 PM laws) | 16/16 | **16/16, byte-identical rows (prefix SHA `664564f2…` == recorded W5 golden)** |

## W6.5 Evidence chain

- base: S185 `8057943143282b0875d52faa47f5c433bb92639b` + W5 patch (comments 18/19, reconstruction sha256 `b4aeb36281d41495…`, `git apply` CLEAN) → W6 tree HEAD `a386825baa5cf31aec382a2628cfca2e7362ac5d`
- binary sha256 `85352ae03982fc4c…`; probe APKs browser `53aee1f0…` / share `8fa92989…`→final `ccad8acd…` / main `ad6205da…`→final `ac30d913…` (see evidence/c7_w6/EVIDENCE.txt for the final set)
- **store probe: 20/20 PASS ×3 cold + ×3 warm, all six verdict files byte-identical `24ae2c3af87e3870…`** (concat cold `74117d304355fb2d…` == concat warm)
- **W5 backward-compat, two independent proofs**: (a) X01–X16 rows inside the 20-op file == the recorded W5 golden `664564f24cb19f52…` byte-for-byte; (b) the ORIGINAL W5 fixtures (extracted from the W5 patch, rebuilt) run on the W6 binary → the whole 16-op file reproduces `664564f24cb19f52…` exactly
- no-store regressions byte-identical: 34-op component probe `4aa8f51c87291783…`, activity-chain probe `60b4a75acd3a223f…` (both == the recorded WAVE-3/4 contracts)
- SQLite cache law intact: cold `packages=3 cold=3 warm=0 failed=0` ×3 → warm `cold=0 warm=3 failed=0` ×3
- engine rows (cold1 file_io.jsonl): `C7-STORE-DEX` ×2 (browser 9 + share 3 foreign classes), `BCAST-XPKG-EXEC`, `CTX-XPKG-PKGNAME` ×3, `SVC-XPKG`, `PROV-XPKG-EXEC`, plus the deny row `BCAST-DENY` (NoisyReceiver)
- androguard cross-parser: `all_ok: true` (evidence/c7_w6/androguard_check.json)

## W6.6 Known limitations (honest chain)

1. **Single-process model**: foreign components execute inside the running process (the engine IS one process). AOSP isolates per-app processes — the ownership MAP models the identity laws (getPackageName/ComponentInfo.packageName), not process boundaries. Multi-process isolation is out of scope for this engine by design.
2. Foreign ACTIVITY start (startActivity to a foreign activity) still resolves-only (the launch-drain pipeline is engine-run driven — the natural WAVE-7 item, now unblocked by the code path this wave built).
3. Foreign provider readPermission/writePermission not gated (C7IdxProvider carries exported/grantUriPermissions only) — PENDING.
4. The store remains `MINIANDROID_PKG_STORE`-gated; auto-indexing the engine's own data-root install store is the small follow-up recorded since W5.7#2 (kept decoupled from the manager's install flow by the same decision).
5. `getPreferredActivities`, `sendStickyOrderedBroadcast`/UserHandle overloads, FGS `onTimeout` remain PENDING from W3 (unchanged).


---

# WAVE-4 — S181 Family-2 root family: the "no silent null from framework value/factory APIs" wave

**Base commit:** `2102d1934063aee9713940fd38f49640903fddcf` (S181 HEAD, the C9+C7 main tree). All work on branch `c7-wave4` (local; no pushes — integration stays with the manager, per charter).

## W4.0 The three generic laws (nine-item format per law)

### W4-L2a — `java.util.UUID.fromString(String)` + bit getters — **IMPLEMENTED/TESTED**

1. **Missing/wrong:** no engine handler for `UUID.fromString`; the typed-default NULL answer flowed into Kotlin `checkNotNullExpressionValue`. Also `getMostSignificantBits`/`getLeastSignificantBits` had no law (typed-default 0).
2. **Why generic runtime:** every Kotlin app that parses a UUID constant (BLE service UUIDs, AndroidX SavedStateHandle keys, custom scheme deep links) dies at `<clinit>` when the parse half of the UUID value model answers null — package-independent, hits the whole family.
3. **Source basis:** OpenJDK `UUID.java.fromString` — strict 8-4-4-4-12 layout (36 chars, hyphens at 8/13/18/23, hex elsewhere, case-insensitive), `IllegalArgumentException("Invalid UUID string: " + s)` on ANY malformation; the method is TOTAL (never answers null). `toString()` renders the canonical LOWERCASE form.
4. **Change:** strict shared parser `c7_parse_uuid_strict` + `fromString` law (IAE via `throw_deferred`, never null) + canonical-lowercase storage + msb/lsb getters reading the F-090g field shape.
5. **Files:** `miniandroid/src/dex/dalvik_engine.cpp` (+helper, +2 blocks).
6. **Command:** probe `UUID-01..06` (below).
7. **Before/after:** BEFORE `UUID-01..06` all FAIL (`roundtrip=null`, `no IAE; toString=null`); AFTER all PASS incl. `IAE: Invalid UUID string: not-a-uuid` and bit-exact `msb=3b80e5aede84b33 lsb=a7516ce34ec4c700` for `03B80E5A-EDE8-4B33-A751-6CE34EC4C700`.
8. **Result:** 6/6 PASS ×3 cold.
9. **Limits:** `nameUUIDFromBytes`/`clockSequence`/`variant`/`timestamp` still lawless (unused by the corpus so far).

### W4-L2b — `android.os.ParcelUuid` value model — **IMPLEMENTED/TESTED**

1. **Missing/wrong:** the class existed only as type-hierarchy metadata (`view_ancestry.h`); `fromString` answered null; `<init>(UUID)` NPE'd (`PUUID-03` before-row: `threw java.lang.NullPointerException`).
2. **Why generic:** `ParcelUuid.fromString` is THE documented BLE/UUID entry point (`BluetoothLeScanner`, `BluetoothDevice` filters); Kotlin null-asserts the result → app-family-wide `<clinit>` death.
3. **Source basis:** AOSP `core/java/android/os/ParcelUuid.java` — thin Parcelable wrapper: `fromString` delegates to `UUID.fromString` (IAE PROPAGATES), `getUuid()` answers the wrapped UUID, `toString()` delegates.
4. **Change:** `fromString` (parses, allocates BOTH the UUID and the wrapper with the canonical-lowercase value), `<init>(UUID)` (stores verbatim), `getUuid()` (real object ref), `toString()`.
5. **Files:** `miniandroid/src/dex/dalvik_engine.cpp` (+4 blocks).
6. **Command:** probe `PUUID-01..04`.
7. **Before/after:** BEFORE `fromString.toString=null`, ctor NPE, `no IAE; null`; AFTER 4/4 PASS incl. the deny row `IAE: Invalid UUID string: garbage`.
8. **Result:** 4/4 PASS ×3 cold.
9. **Limits:** `equals/hashCode` and `writeToParcel` still lawless (no corpus consumer yet).

### W4-L2c — `android.media.AudioFocusRequest$Builder` fluent chain — **IMPLEMENTED/TESTED (corpus A/B ×3; dedicated probe op PENDING)**

1. **Missing/wrong:** no law; `setAudioAttributes` answered the typed-default NULL → the NEXT chain link died: `NullPointerException: …AudioFocusRequest$Builder.setOnAudioFocusChangeListener on a null object reference` at `Lg4/m;.<init>` invoke pc=0x1ca (sunpiano, post-UUID-fix frontier).
2. **Why generic:** the Builder-chain null is the same object family as the recorded AudioAttributes$Builder law (F-NEW-356, astroloop): any app chaining `new AudioFocusRequest.Builder(gain).setAudioAttributes(…).setOnAudioFocusChangeListener(…)` inside Activity/Application init dies before the first frame. Package-independent.
3. **Source basis:** AOSP `media/java/android/media/AudioFocusRequest.java` (API 26): ctor validates the four GAIN constants (IAE), setters `Objects.requireNonNull` (NPE) and return THIS, `build()` answers a non-null AudioFocusRequest carrying the state.
4. **Change:** ctor `<init>(I)` with the gain validation + field store; `setAudioAttributes`/`setOnAudioFocusChangeListener` (both overloads)/`setWillPauseWhenDucked` fluent-this with honest NPE deny rows; `build()` non-null with state transfer. Audio OUTPUT stays a no-op (no speaker in a software runtime) — object-model only, the same boundary the AudioAttributes law drew.
5. **Files:** `miniandroid/src/dex/dalvik_engine.cpp` (+1 block, 100 lines).
6. **Command:** sunpiano A/B (below).
7. **Before/after:** AFTER-UUID binary still `face=f6b35994` with the NPE at pc=0x1ca and `0` draw ops on the custom piano view (`Lb2/x;`, 1080x1920, onDraw dispatched ops=0); AFTER-L2c the init completes, no exceptions, the view draws.
8. **Result:** sunpiano verdict flip (below), ×3 byte-identical.
9. **Limits:** no dedicated probe op yet (PENDING next probe rev); `AudioManager.requestAudioFocus(AudioFocusRequest)` semantics still lawless.

## W4.1 THE CORPUS FLIP (the user's "big problems" directive, measured)

| Title | BEFORE (base `8438c423…`) | AFTER (`f3fa122b…`) |
|---|---|---|
| sunpiano (`code.alimiracle.sunpiano_2`) | face `f6b35994ff07b960` ×3 — **byte-identical to the S181 pin** (cross-sandbox determinism), verdict DEFAULT_BACKGROUND_ONLY, uncaught NPE storm 32 | face `af001924bf2b7554` ×3, verdict **REAL_APP_CONTENT**, app_owned_px **576,907**, draw_ops 446, colors 908, lifecycle RESUMED, uncaught 0 |
| sopadeletras (`app.sopadeletras_24`) | face `87553c6bf541d4da` == S181 pin | unchanged (different root — see W4.4) |
| just24hoursplus (`…_10400`) | face `88b1668a12a63880` == S181 pin | unchanged (different root — see W4.4) |

sunpiano root chain, fully decoded from dex + runtime trace (no package special-casing anywhere — three framework API laws):
`j4/b.<clinit>` @0x8 `ParcelUuid.fromString("03B80E5A-…")` → null → Kotlin intrinsics NPE ×32 storm (S181 Family-2) → **[W4-L2a/L2b kill the storm: uncaught 32→0]** → next frontier `g4/m.<init>` AudioFocusRequest$Builder chain NPE @0x1ca → **[W4-L2c]** → the app's OWN `Lb2/x;` custom view (1080x1920) draws its real content.

## W4.2 Changed files + runtime identity

| Artifact | SHA-256 (prefix) |
|---|---|
| base commit | `2102d1934063aee9713940fd38f49640903fddcf` |
| unified patch `c7_w4_on_s181.patch` (534 lines, `git apply --check` CLEAN on pristine base) | `ec5aa8674274b7b93b69a0ae5bc1dfcc8dcaa564ec1b64293f755d9d62728525` |
| BASE binary (pristine tree; dalvik_engine TU at `-O1 -g0`, see W4.5) | `8438c423a9d43e0f…` |
| AFTER binary (W4-L2a/b/c) | `f3fa122b1d65cbb9…` |
| `c7_w4_probe.apk` (10 ops, aapt2-linked, stub android-all-14-robolectric-10818077) | `bdbd9fbe7858503e…` |
| w4 probe results ×3 identical | `9be150e815f15a13…` |
| 34-op component probe (aapt2-linked rebuild of `fixtures/c7_bcast_service_probe`) | `f6dba40d4dbfb51b…` |
| 34-op results ×3 identical (34 PASS / 0 FAIL / 3 OBS) | `4aa8f51c87291783…` |

Files changed (patch): `miniandroid/src/dex/dalvik_engine.cpp` +306 (helper `c7_parse_uuid_strict` + W4-L2a/b/c blocks, zero deletions, additive laws only); `fixtures/c7_w4_probe/{AndroidManifest.xml,src/com/probe/c7w4/MainActivity.java}` new (178-line probe).

## W4.3 Exact commands (this sandbox)

```bash
# build (the big TU compiles 91 s at -O1 -g0 inside one call on this 3 GB host)
cd miniandroid && g++ -std=c++17 -Wall -Wextra -O1 -g0 -DMINIANDROID_HAVE_WEBP   -Isrc -Isrc/webview -Isrc/apk -Isrc/dex -Isrc/runtime -Isrc/api -Isrc/graphics   -Isrc/diagnostics -Isrc/resources -Isrc/renderer -Isrc/framework -Isrc/storage   -Isrc/fonts -Ithird_party/portablegl -I/usr/include/freetype2   -Ithird_party/nlohmann_json/include   -c -o build/dex/dalvik_engine.o src/dex/dalvik_engine.cpp && make -j1

# probe build (aapt2-LINK recipe, §3.10 law) + run ×3 fresh stores
tools/aapt2/aapt2 link -o base.apk -I tools/android-34.jar   --manifest fixtures/c7_w4_probe/AndroidManifest.xml --java gen
ecj -1.8 -d obj -cp tools/android-34.jar <src+gen>; d8 --release --lib tools/android-34.jar --output dexout <classes>
./build/miniandroid install base.apk --data-root /tmp/w4c_$i
./build/miniandroid run --package com.probe.c7w4 --data-root /tmp/w4c_$i --max-seconds 30
cat /tmp/w4c_$i/data/data/com.probe.c7w4/files/c7_w4_results.jsonl

# corpus A/B (S181 protocol)
./build/miniandroid install code.alimiracle.sunpiano_2.apk --data-root /tmp/sp_$arm
./build/miniandroid run --package code.alimiracle.sunpiano --data-root /tmp/sp_$arm   --max-seconds 45 --frames 5 --execution-mode real-dalvik --trace -o /tmp/run
sha256sum run/screenshot.png   # face
```

## W4.4 OBSERVED handoffs (out of the five Coder-7 areas, census-bound, with evidence)

- **sopadeletras** — TWO sub-frontiers, both outside component resolution: (a) androidx.navigation `NavDestination.setRoute` IAE storm `Cannot set route "newGame/{mode}" for destination vn(0x0). Following required arguments are missing: []` (origin `Lf01;.a` pc=284; the empty missing-list says the divergence is in OUR collection/`require` evaluation upstream of the message assembly — interpreter/core-lib territory); (b) `La;` (obfuscated CancellationException-family) unhandled chain `Ll6;.m pc=32 → Lph1;.m → Llt0;.b` (kotlinx.coroutines machinery). Faces unchanged both arms (S181 pin held).
- **just24hoursplus** — `WelcomeActivity.onCreate` NEVER RETURNS (zero `method_exit` rows for the frame while theClockActivity's own inflate worked: root=115, views=3); the stall window is `WindowCompat.setDecorFitsSystemWindows(false)` → `getDecorView` → `ViewCompat.<clinit>` (76 R$id statics OK) → silent stop, so `effective_content_root_()` answers 0 → SYSTEM_CHROME_ONLY. Root-cause needs the interpreter-level stall tools (cont120-class); PENDING.
- **Environment item (recorded, not a drift):** the act-probe harness quiesces after the ResAct finish cascade on THIS sandbox (rows A1a/A1b/A5 only, on base AND W4 — row-set sha `48cf38eb…` byte-identical both arms ⇒ zero W4 drift; the W3 8/8 record needs the original runner context).

## W4.5 Known limitations (honest chain)

1. **The dalvik_engine TU builds at `-O1 -g0` on THIS 3 GB sandbox** (the -O2 cc1plus peak OOM-kills even solo here; the repo's CONT-37 -O2 -g0 rule stands for the 4 GB build host). Both A/B arms use IDENTICAL flags — the comparison is fair and the semantics are flag-independent; all faces/verdicts were additionally confirmed against the S181 pins recorded on the -O2 main-line binary.
2. `W4-L2c` has corpus-level A/B evidence ×3 but no dedicated probe op yet (next probe rev).
3. The 34-op probe APK SHA differs from the W3 record (rebuilt from in-repo fixtures with the re-fetched stub jar); the VERDICT table is the regression contract and it is 34/0/3 ×3 byte-identical.
4. Family-1 (Compose init) and Family-3 (Insets) from the S181 census are untouched (outside the five areas this round).

## WAVE-9 (this round) — the LAW CONFORMANCE BATTERY — 22 real problems solved

*(body near the 64K limit: this section is the compact log; the FULL 9-item report rides the WAVE-9 patch comments (6712716858/7574/8300) above the diff fences.)*

**Method (tracer-then-prune + androguard + real AOSP source):** a 34-op battery APK (`c7laws`, package `c7.laws`) + a disabled-app neighbor (`c7laws_off`, app-level `android:enabled="false"`) whose REAL bytecode exercises the five ownerships' depth; manifest facts cross-validated with androguard (19/19); the Intent laws implemented FROM the AOSP android-14/main source (fetched, not guessed). 22 problems: provider depth (bulkInsert route + AOSP base fallback; notifyChange; real ContentObserver registry with the uri-filter + originator-exclusion laws; getCallingPackage per-op; acquire(String) overload; ContentValues absent-key nulls), Intent law (filterEquals; fillIn — AOSP changes-bitset semantics; setData/setType mutual-clear; setDataAndType+getDataString; normalizeMimeType), Activity/Application (finishAffinity; onTrimMemory/onLowMemory app-BEFORE-activity with the TRIM_COMPLETE alias; onConfigurationChanged with a real Configuration object), Service (bindService-to-stopped RESURRECTION — bringUpServiceLocked), PackageManager (the DISABLED-APP law end-to-end: application-level enabled parse→cache→resolution/delivery/foreign-start gates; getApplicationInfo for INSTALLED foreign packages; setComponentEnabledSetting runtime override; Intent.setPackage broadcast filter), + 3 probe-law honesty fixes (L07 IAE was already AOSP-correct; L08/L12 corrected against the source).

| before → after |
|---|
| battery BEFORE (W8 binary): 15 PASS / 17 FAIL + L19/L20 rows absent (`da5bae5a…`) → **AFTER: 34/34 PASS ×3 cold byte-identical** (`8be3ddc8…`) |
| regression: 33-op store `9831ee30…` ×6 byte-identical; W6 golden prefix `24ae2c3a…`; 34-op `4aa8f51c…`; act-chain `60b4a75a…`; auto-index ≡ explicit store; androguard all_ok |

patch `c7_w9_on_w8.patch` on the W8 tree `6615141e` → W9 HEAD `70f913b0` · sha `fc38091d…` · 2668 lines · 26 files · +2224/−10 · `git apply --check` CLEAN. State: IMPLEMENTED/TESTED; OBSERVED for the two documented harness stand-ins (trim/config signal source; the synchronous-stack finishAffinity count is honest-zero, never fabricated). Limitations + handoffs in the patch-comment report. No pushes, no new issues.