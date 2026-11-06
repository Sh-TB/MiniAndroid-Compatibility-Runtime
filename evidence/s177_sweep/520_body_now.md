# ISSUE 520 [Coder7] state=open

# CODER 7 — Base Android Component Runtime Engineering: Work Log

**Owner:** CODER 7 (Android component runtime: Application/Activity, Service, BroadcastReceiver, ContentProvider, Intent & component resolution)
**Repository:** Sh-TB/MiniAndroid-Compatibility-Runtime
**Current base commit:** WAVE-3 is authored on the S170+wave-1+wave-2 integration tree (the wave-2 patch parts 1–5 below applied to S170 `439b0a3d`; the W2 test-tree HEAD is `42f4353e`, the W3 test-tree HEAD `93c2d238`). No pushes — the manager integrates from the unified patch comments.
**This issue is my single work log — all progress, evidence and handoff material lives here.**

**Delivery state (three waves):**

| Wave | Scope | Verdict evidence |
|---|---|---|
| WAVE-1 (rebased) | ordered broadcasts + service-contract laws (14 laws) | BEFORE 1/11 → **AFTER 12/12 PASS**; results-file SHA-256 `a248cab28075521d…` **byte-identical to the original wave-1 record** |
| WAVE-2 | bring-down `onUnbind`, per-filter dispatch, sticky broadcasts, sticky/registration permissions, exported/foreign-sender model, `getReceiverInfo` | **19/19 PASS** (R0 same-pkg, R2 foreign+perms); R1 foreign-no-perms shows the exact predicted deny set; gate_a regression **byte-identical streams W1→W2** |
| WAVE-3 (this round) | **20 new generic laws**: task-stack/launch-flag set, service AUTO_CREATE/missing/stopSelf(int), broadcast matchData + unregister + sticky-ordered, ContentProviderClient, PackageManager REAL resolution (CATEGORY_DEFAULT + enabled) | **34/34 PASS ×3 cold runs** (c7 probe) + **8/8 PASS ×3 cold runs** (new activity-chain probe); R1 shows exactly the deny-matrix rows; gate_a verdict stream identical (95/2, pre-existing env-scoped FAILs only) |

---

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

## 2. WAVE-1 (REBASED + RE-VERIFIED) — summary

Wave-1 (recorded in the original body + patch comments 1–3 against `25b5a01b`) delivered 14 generic laws: ordered priority tranches, result chain (resultCode/Data/Extras), final resultReceiver, abort/clear/getAbort, log-only non-ordered hint, goAsync/PendingResult, receiver permission, category match, stopSelfResult guard, per-service startIds, targeted unbind + IAE, onUnbind/onRebind, FGS contract tracking, manifest receiver/service attribute model.

**S170 rebase re-verification (this round):** the wave-1 patch applies CLEAN on `439b0a3d`; rebuilt and re-ran with the SAME probe APK SHA `00b012b7…`:
- BEFORE (unpatched S170): **1 PASS / 11 FAIL** (same disorder signature as the original before-run).
- AFTER (wave-1 on S170): **12 PASS / 0 FAIL**; results-file SHA-256 `a248cab28075521d198550713d9763dff1fa67db0c892cea6ceb9bd98c0c114d` — **byte-identical to the wave-1 issue's recorded AFTER prefix** (cross-sandbox determinism).
- gate_a regression on wave-1: 95 PASS / 2 FAIL (S170's own baseline; the two FAILs are the pre-existing environment-scoped ops, outside this domain).

**Wave-1 status labels: unchanged (IMPLEMENTED/TESTED). The old 25b5a01b-based patch comments are SUPERSEDED for integration by parts 1–5 below.**

---

## 3. WAVE-2 — IMPLEMENTED generic semantic laws (with AOSP source)

1. **IMPLEMENTED — Service bring-down path delivers onUnbind** (`ActiveServices.bringDownServiceLocked`: when a live service is torn down while bound connections exist, `onUnbind(bindingIntent)` is delivered BEFORE `onDestroy` — for EVERY teardown caller).
   - New shared helper `DalvikExecutionEngine::c7_service_bring_down(ServiceInstance&, reason)`; wired into Context `stopService` AND Service `stopSelf`/`stopSelfResult` (the wave-1 tree only delivered onUnbind on the unbind-driven path — wave-1 issue §7 recorded this exact gap as PENDING).
   - Evidence op **SVC-10**: start + bind + stopService ⇒ `unbinds=1 destroys=1` (before: `unbinds=0 destroys=1`). Machine trace: `SVC-UNBIND "bring-down (stopService): onUnbind delivered"` rows precede the `SVC-STOP` row (seq 41/48 in the recorded fio run).
2. **IMPLEMENTED — Per-filter receiver resolution** (AOSP PackageParser/IntentResolver: every `<intent-filter>` is a separate matchable record with its own priority/actions/categories; a receiver matching through two filters is delivered once PER matching filter).
   - `manifest_reader` now opens a per-filter record at every receiver `<intent-filter>` (priority read per filter; the receiver-level MAX/union fields are kept for existing consumers); `execution_engine` transfers the records; the dispatch builds candidates per `(receiver, filter)` pair and sorts stable by filter priority. Receivers transferred without filter records synthesize one from the union (old behavior preserved).
   - Evidence op **ORD-08**: receiver with two filters over the SAME action (prio 60/15) + witnesses at 30/5 ⇒ order `MFA,MFH,MFB,MFL,FINAL`, deliveries=2 (before: single delivery at the MAX priority ⇒ `MFA,MFH,MFL,FINAL`, deliveries=1).
   - Evidence op **ORD-09**: the second filter (action MFCAT + category MFCC) matches the categorized intent exactly once and rejects an undeclared category (`+1` then `+0`).
3. **IMPLEMENTED — Sticky broadcast cache + catch-up delivery** (`ContextImpl.sendStickyBroadcast`: the LAST sticky intent per action is retained and delivered to every NEW receiver whose filter matches at registerReceiver time; `removeStickyBroadcast` drops the slot).
   - `sticky_broadcasts_` per-action cache; `sendStickyBroadcast` = permission gate → cache → deliver as a normal (non-ordered) broadcast; `registerReceiver` immediately delivers every matching cached sticky with `initial_sticky_delivery_ = true` and returns the last matching sticky Intent (AOSP return contract; was hard-coded null); `removeStickyBroadcast` erases by action (loud trace on missing slot).
   - Evidence ops **STK-01** (caught=1, initial=true, v=v1), **STK-02** (after removal: late register gets 0), **STK-04** (fresh send re-caches; fresh receiver gets v2).
4. **IMPLEMENTED — isInitialStickyBroadcast** (`BroadcastReceiver.isInitialStickyBroadcast`: true ONLY during the initial sticky catch-up delivery). Evidence: STK-01's `initial=true`; false for all normal sends (all other ops).
5. **IMPLEMENTED — Sticky-send permission law** (`ContextImpl.sendStickyBroadcast` requires `android.permission.BROADCAST_STICKY`; violation = SecurityException in AOSP — here a loud `BCAST-DENY` trace row with NO delivery and NO caching, consistent with this runtime's deny convention).
   - Evidence: R1 (foreign sender without the permission) STK-01/04 catch-ups get nothing (`caught=0`) and the run shows the BCAST-DENY row; R0/R2 (sender holds it) STK ops pass.
6. **IMPLEMENTED — Dynamic registration-permission law** (`registerReceiver(receiver, filter, broadcastPermission, scheduler)` — BroadcastFilter.requiredPermission is enforced against the SENDER for every delivery; the base ignored the argument entirely).
   - Evidence op **ORD-10**: receiver registered with permission `…DYNPERM` (not held) is denied while the permission-less control on the same action delivers (perm=0, ctrl=1).
7. **IMPLEMENTED — Exported law made observable via a modeled foreign sender** (`ActivityManagerService.checkComponentPermission`: a foreign sender cannot reach a manifest receiver with `exported=false`; same-package sends are never gated; absent attr + filter + targetSdk≤30 defaults to exported).
   - The single-package runtime gets an env-gated caller-identity model: `MINIANDROID_C7_SENDER_PKG` (sender package; equal to the running package ⇒ same-package law) + `MINIANDROID_C7_SENDER_PERMS` (comma list of permissions the modeled sender holds). The model is documented, env-gated, package-agnostic — no framework object is fabricated and the deny path is always a loud `BCAST-DENY` row.
   - Evidence ops **EXP-01/02/03** (OBS rows) across three run modes:

   | Op | Receiver | R0 same-pkg | R1 foreign, no perms | R2 foreign + `…PERMISSION,BROADCAST_STICKY` |
   |---|---|---|---|---|
   | EXP-01 | ExpLocked (`exported=false`) | delivered ✓ | **denied** ✓ | **denied** ✓ |
   | EXP-02 | ExpOpen (`exported=true` + permission) | delivered ✓ | **denied** (perm) ✓ | **delivered** ✓ |
   | EXP-03 | ExpDefault (no attr + filter, targetSdk 30) | delivered ✓ | **delivered** ✓ | **delivered** ✓ |
   | STK-01/04 | sticky catch-up | pass ✓ | **denied** (BROADCAST_STICKY missing) ✓ | pass ✓ |
   | ORD-01..10, SVC-05..10 | lifecycle/ordering laws | 19/19 PASS | pass except the documented deny-dependent rows (ORD-06 held-case, STK-01/04) | 19/19 PASS |

8. **IMPLEMENTED (evidence PARTIAL) — PackageManager.getReceiverInfo law** (mirror of the F-NEW-275 getServiceInfo law: ComponentName lookup with the same normalize/matching walk; returns name/exported/permission; throws NameNotFoundException on miss; emits `PM-RECEIVER-INFO` trace rows).
   - **Blocker (documented):** the local ECJ/D8 stub set (`tools/android-34.jar`) ships NO `android.content.pm.ReceiverInfo` class (verified: zero `ReceiverInfo` references in the stub PackageManager constant pool), so a Java probe op cannot compile a direct call. Engine-level law + trace evidence only; probe-level verification PENDING on the stub upgrade. No VERIFIED claim is made.
9. **PROBE FIX (harness, not engine) — Order recorder rebuilt on String.concat**: the wave-1 recorder used `StringBuilder.setLength(0)` for resets, which this runtime does not implement (silent no-op — appends work, truncation never lands). The probe now uses `String`/`concat`/`isEmpty`. The `StringBuilder.setLength` gap is recorded as an OBSERVED core-lib frontier for its owning domain (outside Coder 7's five areas).
10. **PROBE INFRA LAW — binary-manifest fixture builds:** the S170 re-run initially showed ZERO manifest receivers because the generic `scripts/build/build_fixture_apk.sh` takes its legacy plain-text-manifest path for fixtures without `res/` — the engine's ManifestReader is an AXML parser and parses nothing out of a plain-text manifest. All Coder-7 probes MUST be built with the aapt2-link (binary AXML) recipe (the wave-1 comment-3 build script; saved as `/scripts` recipe in my worklog). gate_a works because it carries `res/`. Documented so no one re-diagnoses this.

---

## 4. Changed files (wave-2, on top of the wave-1 rebase)

| File | Δ |
|---|---|
| `miniandroid/src/apk/manifest_reader.h` | +11 (per-filter FilterInfo model) |
| `miniandroid/src/apk/manifest_reader.cpp` | +31/−? (per-filter open/dual-record; per-filter priority) |
| `miniandroid/src/dex/dalvik_engine.h` | +60 (filters model, DynamicReceiver.permission, sticky cache + initial flag, bring-down decl) |
| `miniandroid/src/dex/dalvik_engine.cpp` | +436/−? (bring-down helper + wiring, sticky laws, registration permission, exported/foreign-sender model, per-filter candidates, isInitialStickyBroadcast, removeStickyBroadcast, getReceiverInfo) |
| `miniandroid/src/runtime/execution_engine.cpp` | +11 (per-filter transfer) |
| `fixtures/c7_bcast_service_probe/**` | 14 new/changed files: manifest (sticky permission, Exp*/MF* receivers, SvcF, wave-1 receivers exported=true), MainActivity +152 lines (SVC-10, ORD-08/09/10, STK-01/02/04, EXP-OBS), 12 new component classes, Order.java String fix |

Unified patch (S170-rebased wave-1 + wave-2, canonical): **sha-256 `d1cf984824caf83ef2c7f2fdeb100052c47ff4cf53d5ddcfae3da65d0ab5ac3e`** — posted as comments **parts 1–5 below** (concatenate in order → `c7_w1w2_on_s170.patch`). Verified: `git apply --check` CLEAN on pristine `439b0a3d`, and pristine+patch tree **byte-identical** to the tested build tree. The old wave-1 comments (25b5a01b-based) remain as history; use parts 1–5 for integration.

## 5. Runtime binary identity + test inputs (SHA-256)

| Artifact | SHA-256 |
|---|---|
| BASE binary (pristine `439b0a3d`, unpatched) | `0cf11922c61d7aad0f86e8899e8b74f841547e758694fa60370cf92da8b9acae` |
| W1 binary (S170 + wave-1 rebase) | `2e7744acd36454f25252fdf924ccc5d6723819feb47548f25b1249c74a54e32a` |
| W2 binary (S170 + wave-1 + wave-2) | `a4c8ff214b0466955695a85324e6a2e2d9e43bb8f6bcab2730cd2ecdffc07c85` |
| `c7_probe_w1.apk` (wave-1 probe, aapt2-linked) | `00b012b77636022fea99be6ee6e2eb21b2775d1bff7b52b823f9e57de14b8d33` |
| `c7_probe_w2.apk` (wave-2 probe, 24 ops) | `a2d45093fc049a154d8039352d04bb3a2a7ba76a7f68171d7fe182547d24d6df` |
| `gate_a_probe.apk` (regression input) | `6980fc1a9797c313e1ac5f43d068d728465ffac84d123756bb4c579e177f8933` |
| canonical patch `c7_w1w2_on_s170.patch` | `d1cf984824caf83ef2c7f2fdeb100052c47ff4cf53d5ddcfae3da65d0ab5ac3e` |
| R0 results file (×3 identical) | `684ccab83d61517cb2e7bb28f2a6225659996a529a8e8accdf1d5e1dac0342e7` |
| R1 results file | `75921fca97f94132a2d82b409ce4fe0c0df9edba5e851e397a397b3a2c0aad05` |
| R2 results file | `70a10d7b7c4037baedfbcf36f6b76ee7efccb6f364295f6604bd512be69ecf9a` |
| W1-after results file (wave-1 12/12, byte-matches original record) | `a248cab28075521d198550713d9763dff1fa67db0c892cea6ceb9bd98c0c114d` |
| gate_a results file on W2 | `c24389805896c81f3431730abf18ff832c979bc8ee18c5fc6aa362223f0af17b` |

## 6. Exact build & test commands (this sandbox)

```bash
# toolchain: repo tools/ (aapt2, ecj.jar, d8/r8.jar) + android-34 stubs jar
#   (maven-central 429s in this sandbox; fetched via the aliyun central mirror)
#   https://maven.aliyun.com/repository/central/org/robolectric/android-all/\
#     14-robolectric-10818077/android-all-14-robolectric-10818077.jar → tools/android-34.jar

# 1) build runtime
cd miniandroid && make -j2          # g++ 14.2, -O2; "Build complete: build/miniandroid"

# 2) build probes — aapt2-LINK path (binary AXML manifest) — see §3.10 law
aapt2 link -o base.apk -I tools/android-34.jar --manifest FIX/AndroidManifest.xml --java gen
ecj -1.8 -d obj -cp tools/android-34.jar @sources.txt
d8 --release --lib tools/android-34.jar --output dex @classes.txt; zip -j base.apk dex/classes.dex

# 3) BEFORE / AFTER runs (same APK SHA, same capture protocol)
./build/miniandroid install c7_probe.apk --data-root /tmp/store_X
./build/miniandroid run --package com.probe.c7runtime --data-root /tmp/store_X
cat /tmp/store_X/data/data/com.probe.c7runtime/files/c7_results.jsonl

# 4) modeled-sender modes (wave-2 exported/permission laws)
MINIANDROID_C7_SENDER_PKG=com.probe.c7runtime.foreign ./build/miniandroid run ...          # R1
MINIANDROID_C7_SENDER_PKG=com.probe.c7runtime.foreign \
MINIANDROID_C7_SENDER_PERMS="com.probe.c7runtime.PERMISSION,android.permission.BROADCAST_STICKY" \
./build/miniandroid run ...                                                                 # R2

# 5) machine-readable dispatch trace
MINIANDROID_FILE_IO=/tmp/fio.jsonl ./build/miniandroid run --package com.probe.c7runtime --data-root /tmp/store_X
grep -E '"op":"(SVC|BCAST|PM)-' /tmp/fio.jsonl
```

## 7. OBSERVED before/after (same probe APKs, same capture protocol)

**c7_probe_w2.apk (24 ops = 19 verdict + 3 OBS + 2 shared-final rows):**

| Tree | Result | Wave-2-op signature |
|---|---|---|
| BASE (S170 pristine) | 2 PASS / 17 FAIL | SVC-10 unbinds=0; ORD-08 deliveries=1; ORD-10 perm=1; STK caught=0; EXP all delivered (no laws); results stream label-garbled (base dispatch disorder) |
| W1 (wave-1 rebase) | 13 PASS / 6 FAIL | exactly the wave-2 gaps: SVC-10 `unbinds=0 destroys=1`; ORD-08 `MFA,MFH,MFL,FINAL deliveries=1`; ORD-10 `perm=1 ctrl=1`; STK-01/02/04 `caught=0`; EXP OBS all delivered |
| W2 R0 (same-pkg) | **19 PASS / 0 FAIL** | SVC-10 ✓ ORD-08 `MFA,MFH,MFB,MFL,FINAL deliveries=2` ✓ ORD-09 ✓ ORD-10 ✓ STK ✓ |
| W2 R1 (foreign, no perms) | 16 PASS / 3 FAIL (all three = the LAWS working) | EXP-01 denied, EXP-02 denied, EXP-03 delivered, sticky sends denied (BROADCAST_STICKY missing), ORD-06 held-case denied (foreign law) |
| W2 R2 (foreign + perms) | **19 PASS / 0 FAIL** | EXP-02 now delivered; EXP-01 still denied; sticky pass |

Cold-run reproducibility: **3× fresh install+run of R0 → results-file SHA-256 `684ccab8…342e7` identical every time.**

Machine-readable dispatch evidence (one R0 run, `MINIANDROID_FILE_IO`): `BCAST-SEND ×18`, `BCAST-DENY ×19`, `BCAST-REGISTER ×11`, `SVC-START ×7`, `SVC-BIND ×6`, `SVC-UNBIND ×6` (incl. `bring-down (stopService): onUnbind delivered`), `SVC-STOP ×5`, `SVC-INIT ×6`, `BCAST-STICKY ×5`.

**Regression (gate_a_probe):** op/verdict stream **byte-identical W1→W2** (`diff` empty; 95 PASS / 2 FAIL — the two FAILs are the pre-existing environment-scoped ops already present at S170 base, outside component-runtime scope). Content SHA of the W2 run's results file: `c2438980…f17b`.


---

# WAVE-3 — twenty generic problems solved (base: the W2 integration tree)

## W3.0 The twenty-problem work list (each row = one implemented + tested law)

| # | Problem (base behavior) | AOSP law | Status |
|---|---|---|---|
| 1 | `getCallingActivity()`/`getCallingPackage()` hard-coded null (fabricated negative) | `Activity.getCallingActivity`: the `startActivityForResult` caller identity, null only without a caller | **IMPLEMENTED/TESTED** (W3-A1a/b) |
| 2 | Non-Activity-context `startActivity` silently dead-ended (no NEW_TASK check) | `ContextImpl.startActivity` AndroidRuntimeException without `FLAG_ACTIVITY_NEW_TASK`; legal with it | **IMPLEMENTED/TESTED** (W3-A2a) |
| 3 | No launchMode enforcement — top re-launch created a duplicate instance | `ActivityInfo.launchMode=singleTop` + `FLAG_ACTIVITY_SINGLE_TOP` → `onNewIntent`, no new instance | **IMPLEMENTED/TESTED** (W3-A3) |
| 4 | `FLAG_ACTIVITY_CLEAR_TOP` ignored — target relaunched on top, nothing closed | CLEAR_TOP closes everything above the target; singleTop shape → `onNewIntent`, standard shape → destroy+recreate | **IMPLEMENTED/TESTED** (W3-A4) |
| 5 | `isFinishing()` answered false in onDestroy (flag reset at cascade start) | `Activity.mFinished` persists through the teardown | **IMPLEMENTED/TESTED** (W3-A5) |
| 6 | `startActivities(Intent[])` had NO handler anywhere (silent dead-end) | `Context.startActivities`: the array launches as a FIFO sequence | **IMPLEMENTED/TESTED** (W3-A6) |
| 7 | `bindService` always created the service (flags argument ignored) | `ActiveServices.bindServiceLocked`: without `BIND_AUTO_CREATE` the connection is QUEUED until bring-up | **IMPLEMENTED/TESTED** (W3-S11) |
| 8 | start/bind of a not-installed service fabricated `IllegalArgumentException` | "Unable to start service … not found": `startService` → null ComponentName, `bindService` → false | **IMPLEMENTED/TESTED** (W3-S12) |
| 9 | `stopSelf(int)` ignored the startId argument (always stopped) | `Service.stopSelf(int)` → same `getLastStartId` guard as `stopSelfResult` | **IMPLEMENTED/TESTED** (W3-S13) |
| 10 | `unregisterReceiver` of an unknown receiver was a silent no-op | `ContextImpl.unregisterReceiver`: `IllegalArgumentException("Receiver not registered")` | **IMPLEMENTED/TESTED** (W3-B11) |
| 11 | `unregisterReceiver` removed only the FIRST registration | the receiver's whole dispatcher goes — every registration dies on one unregister | **IMPLEMENTED/TESTED** (W3-B12) |
| 12 | Zero-receiver ordered sends: evidence-only (law already held) | the final `resultReceiver` still runs with the seeded values | **TESTED (evidence)** (W3-B3ev) |
| 13 | MIME data filters (`<data android:mimeType>`) never matched | `IntentFilter.matchData` type half: exact / `type/*` / `*/*` | **IMPLEMENTED/TESTED** (W3-B14) |
| 14 | Data-scheme filters never matched | `matchData` data half: scheme/host/pathPrefix set membership | **IMPLEMENTED/TESTED** (W3-B15) |
| 15 | `sendStickyOrderedBroadcast` unrouted | ordered chain + final receiver + sticky cache applied AFTER the chain | **IMPLEMENTED/TESTED** (W3-B16) |
| 16 | `acquireContentProviderClient` returned the provider's CURSOR (wrong type) | it answers a real `ContentProviderClient`; `release()` detaches; use-after-release → `IllegalStateException` | **IMPLEMENTED/TESTED** (W3-P10) |
| 17 | `ContentProviderClient` had NO method dispatch (dead object) | client.query/insert/update/delete/getType/call/openFile route through the provider; client law | **IMPLEMENTED/TESTED** (W3-P10) |
| 18 | `openTypedAssetFileDescriptor` unrouted | routes to `openFile`; error propagation (`FileNotFoundException`) preserved | **IMPLEMENTED/TESTED** (W3-P11) |
| 19 | `resolveActivity`/`resolveService` hard null; `queryIntentActivities`/`Services`/`BroadcastReceivers` ALWAYS empty (fabricated negatives) | `PackageManagerService/IntentResolver`: real manifest-filter resolution; resolve* answer the best-match `ResolveInfo`; query* the full list; `MATCH_DEFAULT_ONLY` requires `CATEGORY_DEFAULT` on the MATCHING filter | **IMPLEMENTED/TESTED** (W3-R01/R02) |
| 20 | `android:enabled` was not even parsed — disabled components fully live | `PackageItemInfo.isEnabled`: disabled receivers undelivered, services not startable/bindable (null/false), activities unresolvable/unlaunchable, providers unpublished (`resolveContentProvider` null) | **IMPLEMENTED/TESTED** (W3-R03 + W3-R04) |

Supporting fixes folded into the laws: `Intent.setType/setData/setDataAndType/getType` natives (the matchData intent side — previously absent), `IntentFilter.addDataScheme/addDataType` state, and the `Intent`(String, Uri) ctor now parses scheme/host/path match dimensions.

## W3.1 Implementation map (all generic — no package names, no fabricated objects)

| Area | Files | What landed |
|---|---|---|
| manifest model | `apk/manifest_reader.{h,cpp}`, `apk/apk_parser.{h,cpp}` | `android:enabled` per component (typed BOOL + string fallback); `<data>` capture (mimeType/scheme/host/pathPrefix) into per-filter records for receivers, activities AND services; activity/service per-filter matchable records |
| engine transfer | `runtime/execution_engine.cpp` | normalized activity/service filter tables (`set_manifest_activity/service_filters`), per-provider enabled, receiver enabled + filter datas |
| broadcast dispatch | `dex/dalvik_engine.cpp` | matchData law over dynamic (`intent_filter_datas_`) and manifest filters; disabled-receiver skip (`BCAST-SKIP` rows); unregister IAE + full-set removal; `sendStickyOrderedBroadcast` (overload-shape parse + post-chain sticky cache) |
| service laws | `dex/dalvik_engine.cpp` | `ConnBinding.needs_connect` queued-connection state + bring-up flush; not-installed → null/false; disabled service → null/false; `stopSelf(int)` guard |
| provider laws | `dex/dalvik_engine.cpp` | `acquireContentProviderClient` returns a real bound client (`c7_provider_client_authority_`); the full `ContentProviderClient` law block; `openTypedAssetFileDescriptor` routing; disabled provider unpublished |
| task/launch laws | `runtime/execution_engine.cpp` (launch drain), `dex/dalvik_engine.cpp` (startActivity/startActivities gate) | disabled-activity refusal; singleTop-onNewIntent; CLEAR_TOP both shapes (current-top destruction included); NEW_TASK gate (non-Activity receivers only); startActivities FIFO queue (`IntentShadow.pending_queue_`) |
| caller identity | `framework/android_shadows.{h,cpp}` | per-record `launched_by_cls` capture/restore; `getCallingActivity/getCallingPackage` real law (removed from the early fall-through list that pre-empted it); per-activity `mFinished` (`finished_by_oid_`); `runtime_package` binding |
| resolution laws | `dex/dalvik_engine.cpp` (PM block), `framework/android_shadows.{h,cpp}` | the real-resolution law set with MATCH_DEFAULT_ONLY + enabled exclusion; shadow-side `register_activity_filter` + `resolve_activity_target` with the CATEGORY_DEFAULT strict pass and a LOUD lax fallback (corpus-compat, `[C7-CAT]` log) |

## W3.2 Test inputs, binaries, exact commands

| Artifact | SHA-256 |
|---|---|
| W3 binary (final, S170+w1+w2+w3) | `4898c19a4a95f26f58ddd54825b0974044bd90323484b93859c44693522dae66` |
| W2 binary (BEFORE for every W3 op) | `a4c8ff214b0466955695a85324e6a2e2d9e43bb8f6bcab2730cd2ecdffc07c85` |
| `c7_probe_w3.apk` (34 ops, aapt2-linked) | `3693f702ef20efa47ef886c5e6f652bdb3cee258c2a7d404417fbca43ba6b754` |
| `c7_probe_act.apk` (8 ops, activity-chain) | `4dd8b9b700af9098d16f0e84887cd1e55473728c50456afa485ee61eacfc4185` |
| `gate_a_probe.apk` (regression) | `6980fc1a9797c313e1ac5f43d068d728465ffac84d123756bb4c579e177f8933` |
| canonical patch `c7_w3_on_w2.patch` (concat parts 6–11 below) | `942ba8936cce3e5d4097e3adfa3eeecaca98f7675b3fd2ad406db85afd965ebf` |
| c7 results file (×3 identical) | `4aa8f51c87291783…` (full `4aa8f51c87291783` prefix; 34/34) |
| act results file (×3 identical) | `60b4a75acd3a223f…` (8/8) |
| gate_a results file on W3 | verdict stream identical to the W2 baseline (95 PASS / 2 FAIL, same two pre-existing env-scoped ops) |

```bash
# build (unchanged recipe): cd miniandroid && make -j   # "Build complete: build/miniandroid"
# probes: aapt2-link/ECJ/D8 recipe (issue §3.10 law) — saved as scripts/c7_build_probe.sh
bash scripts/c7_build_probe.sh fixtures/c7_bcast_service_probe c7_probe_w3.apk
bash scripts/c7_build_probe.sh fixtures/c7_activity_probe    c7_probe_act.apk
# BEFORE/AFTER (same APK, two binaries):
./build/miniandroid install c7_probe_w3.apk --data-root /tmp/sA
./build/miniandroid run --package com.probe.c7runtime --data-root /tmp/sA
cat /tmp/sA/data/data/com.probe.c7runtime/files/c7_results.jsonl
# activity chain (frame-budget law — the chain needs pump rounds):
./build/miniandroid install c7_probe_act.apk --data-root /tmp/sB
./build/miniandroid run --package com.probe.c7act --data-root /tmp/sB --frames 40
cat /tmp/sB/data/data/com.probe.c7act/files/act_results.jsonl
# modeled foreign sender (R1/R2): MINIANDROID_C7_SENDER_PKG[+MINIANDROID_C7_SENDER_PERMS] as in §6
# machine-readable dispatch: MINIANDROID_FILE_IO=/tmp/fio.jsonl … (grep '"op":"(SVC|BCAST|PM|PROVIDER|ACT)-')
```

## W3.3 OBSERVED before/after (same probe APKs, same capture protocol)

**c7_probe_w3.apk (34 ops = 19 wave-1/2 verdicts + 15 new):**

| Tree | Result | New-op signature |
|---|---|---|
| W2 binary (BEFORE) | 20 PASS / 14 FAIL (all 15 new ops FAIL except W3-B3ev — evidence-op) | B11 no-exception; B12 after=3; B14/B15 ILE; B16 nothing; S11 earlyC=true; S12 IAE; S13 staleOk=false; P10 UOE; P11 no-exception; R01/R02 `?`/0; R03 dis=1 dcn non-null dprov non-null; IT1 null |
| W3 binary (AFTER) | **34 PASS / 0 FAIL** (×3 cold runs, results SHA identical) | every op passes; W3-B3ev passes at BOTH trees (the zero-receiver final law already held — recorded as evidence) |

**c7_probe_act.apk (8 ops, cross-activity chains, `--frames 40`):** W2 binary: 8/8 FAIL (no caller, no NEW_TASK law, duplicate instances, no CLEAR_TOP, no multi-launch, disabled activity launches). W3 binary: **8/8 PASS ×3** (results SHA identical).

**R1 (foreign, no perms): 30 PASS / 4 FAIL** — exactly the deny-matrix rows (ORD-06 held-case, STK-01/04, W3-B16 sticky-perm) = the LAWS working. **R2 (foreign + perms): 34/34 PASS.**

**Regression (gate_a):** 95 PASS / 2 FAIL — verdict stream identical to the W2 baseline; the only stream diff between the two W3-era builds is a wall-clock-seeded row id inside DB-01 (pre-existing nondeterminism, not behavior). The two FAILs (NAT-03/04) are the S170-base environment-scoped ops, outside this domain.

**Machine dispatch rows (one R0 run):** `BCAST-SEND ×34`, `BCAST-SKIP ×34` (disabled receiver), `BCAST-DENY ×35`, `BCAST-REGISTER ×19`, `BCAST-STICKY ×8` (incl. `sticky cached post-chain (sendStickyOrderedBroadcast)`), `SVC-BIND ×10` (incl. `queued (bind without BIND_AUTO_CREATE…)`), `SVC-START ×15`, `SVC-STOP ×8` (incl. `stopSelf(int) startId=1 != last=2 → no stop`), `PM-RESOLVE ×2`, `PROVIDER-CLIENT ×4`, `PROVIDER-openTypedAssetFileDescriptor ×1`, `ACT-START` rows (disabled refusal + NEW_TASK launches).

## W3.4 Status labels (this round)

- W3 laws 1–9, 13–20: **IMPLEMENTED / TESTED** (op + cold-run evidence above).
- W3-12 (zero-receiver final): **TESTED (evidence)** — the law already held at base; the op pins it against regressions.
- W3 corpus-compat note: the CATEGORY_DEFAULT startActivity law keeps a documented LAX fallback (loud `[C7-CAT]` log) when NO filter declares DEFAULT — legacy corpus action-string launches keep working; the strict law is probe-asserted (W3-R01).
- AOSP signature correction found by the stub: `PackageManager.resolveActivity/resolveService` answer **ResolveInfo** (not ComponentName — that is `Intent.resolveActivity`); the engine law follows the real signature.

## W3.5 Known limitations / remaining work

- CLEAR_TOP standard shape skips the beneath-activity `onRestart/onStart` before the pause (single-pass dispatch simplification, loud log); the singleTop shape delivers the full onRestart/onStart/onNewIntent/onResume set.
- The implicit-resolution best-match is manifest-order-first (AOSP IntentResolver's priority/best-match refinement is not modeled).
- Sticky matching remains per-ACTION (unchanged wave-2 note); `sendStickyOrderedBroadcast` caches the ORIGINAL intent (the AOSP sticky slot), not the result chain.
- `getInstalledPackages`/`getInstalledApplications`/`queryContentProviders`/`getPreferredActivities` remain typed-empty stubs (out of this round's twenty).
- The activity-chain probe requires `--frames 40` (the drain chain consumes frame rounds — documented in the commands).
- gate_a's 2 FAILs (ASSET/FD/NAT family, environment-scoped) pre-date this work and sit outside the five owned domains.

## W3.6 Recommended next steps

1. Manager applies patch parts 6–11 (concatenate → `c7_w3_on_w2.patch`, sha `942ba893…`), rebuilds, re-runs the §W3.2 commands — expected: c7 34/34 ×3 identical, act 8/8 ×3 identical, R1 = the documented deny set, gate_a verdict stream unchanged.
2. `onNewIntent` getIntent() semantics (AOSP: getIntent() returns the ORIGINAL intent unless setIntent — subtle, worth a probe op).
3. `resolveActivity` best-match refinement (priority ordering) + `getPreferredActivities` real model.
4. Cross-package stores (carried from wave-2 §10): the modeled-sender laws become live.
5. `PendingIntent` grant/resolve semantics if/when a corpus app needs them.

## 8. Status labels (wave-1/2 rounds)

- WAVE-1 laws (14): **IMPLEMENTED / TESTED** (re-verified on S170, results byte-identical to the original record). Old 25b5a01b patch comments: **SUPERSEDED** by parts 1–5.
- W2-1 bring-down onUnbind: **IMPLEMENTED / TESTED** (SVC-10 + trace order).
- W2-2 per-filter resolution: **IMPLEMENTED / TESTED** (ORD-08/09).
- W2-3 sticky cache/catch-up/remove: **IMPLEMENTED / TESTED** (STK-01/02/04).
- W2-4 isInitialStickyBroadcast: **IMPLEMENTED / TESTED** (STK-01).
- W2-5 sticky-send permission: **IMPLEMENTED / TESTED** (R0/R1/R2 deny matrix).
- W2-6 registration permission: **IMPLEMENTED / TESTED** (ORD-10).
- W2-7 exported/foreign-sender model: **IMPLEMENTED / TESTED as a modeled law** (EXP-01..03 across R0/R1/R2) — the sender identity is an env-gated model (documented in §3.7), not a multi-package store.
- W2-8 getReceiverInfo: **IMPLEMENTED (engine) / PARTIAL evidence** — stub-jar class gap recorded; no VERIFIED claim.
- StringBuilder.setLength silent no-op: **OBSERVED** (core-lib frontier, outside Coder-7 ownership).
- Plain-text-manifest probe gap: **OBSERVED / documented** (fixture build law, §3.10).

## 9. Known limitations / remaining work

- Sticky model is per-ACTION (the BroadcastQueue per-action slot); data/type/MIME refinements of sticky matching are not modeled (documented simplification).
- `sendStickyOrderedBroadcast` and UserHandle overloads remain PENDING.
- The foreign sender is a modeled identity (env-gated) — real cross-package receiver resolution (multi-APK stores: reading OTHER installed packages' manifests into the dispatch) remains the structural next step; §3.7's laws are the contract it must satisfy.
- getReceiverInfo awaits a stub set that ships `android.content.pm.ReceiverInfo` for probe-level verification.
- FGS has no ANR clock: `startForegroundService` contract stays tracked-and-reported (wave-1 law), `onTimeout` PENDING.
- Multi-filter per-filter dispatch covers actions/categories/priority; data-URI/MIME filter dimensions are a separate (larger) resolution law, not exercised here.
- Ordered dispatch remains synchronous inside the send call (wave-1 limitation, unchanged).
- gate_a's 2 FAILs (ASSET/FD-family, environment-scoped) pre-date this work and sit outside the five owned domains.

## 10. Recommended next steps

1. Manager applies patch parts 1–5 (concatenate → `c7_w1w2_on_s170.patch`, sha `d1cf9848…`), rebuilds, re-runs §6 commands — expected: R0/R2 19/19 PASS, R1 exactly the §3.7 deny matrix, gate_a stream unchanged.
2. Upgrade the ECJ/D8 stub set with `android.content.pm.ReceiverInfo` (and the API-33 `ComponentInfoFlags` overloads) so getReceiverInfo gets a probe-level op.
3. Cross-package stores: load OTHER installed packages' manifest receivers into the dispatch (the exported/permission laws of §3.7 become live instead of modeled).
4. ContentProvider round (owned domain ④): attachInfo/onCreate ordering, Cursor close-after lifecycle and openFile error-propagation contract probes on top of the PROV-02..09 base evidence.
5. Activity/task-stack round (owned domain ①): launchMode (singleTop/singleTask), FLAG_ACTIVITY_NEW_TASK|CLEAR_TOP and config-change recreation probes.

