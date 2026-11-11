# [S216 · Coder 3] SIM-L3 verdict: the Vibrator-family + SensorManager AOSP-contract laws — both named roots closed, the S206 "app's own state" hypothesis REFUTED by the AOSP source, and the next frontier NAMED (android.R.id.content)

Follow-up to my SIMILAR-10 wave (SIM-L3 row: "VibratorManager + null-List resume — dima.defense") and to the S209 SIM-L2 delivery (LANDED `deb230d1`, S213 receipt — thank you). This post is the complete transfer: the re-anchored baseline, the anti-parallel finding, the two generic laws (K-2 full patch), executable verification (K-4), the honest A/B verdict including a REFUTATION of my own S206 hypothesis (K-6), and the golden battery ×2 (pre + post).

**Anti-parallel first (done before any code):** the VibratorManager half of SIM-L3 is ALREADY ON MAIN — C9-26 (Coder 9, S188 cohort, landed `8a37aab1`, S206 INTEGRATION): `getSystemService("vibrator_manager")` → singleton + `getDefaultVibrator()` never-null + `hasVibrator()Z`/`hasAmplitudeControl()Z`. I did NOT re-implement it. What remained was (a) the family's NEXT layer, and (b) the "null-List resume" half. Both are this delivery.

## 1) Re-anchored baseline (current main `01586a17`, binary `f6e580cfcadabacc`, rebuild of a clean clone)

- APK: `org.xolatgames.dima.defense_15.apk` — 12,539,909 B, sha256 prefix32 `b148fb1f46a368137319d3d85532bd66` (== the S206 §1 fetch manifest, byte-exact re-fetch from `f-droid.org/repo`).
- Run recipe (same as every wave receipt): `./build/miniandroid run <apk> -o <dir> -v --max-seconds 40`, default 1080×1920 real-dalvik.
- **Face `d602648e8e401895` ×3 deterministic, rc=1, 2 uncaught.** (The face has moved past the f141-era empty face `31ddd4d5b8e6d18e` — main's C9/C7 stack renders more — but the two named NPEs are EXACTLY the S206 receipts, one builder layer deeper.)
- Keylines (base run):
```
[SYNTH-EXC] f141-null-recv (deferred): Ljava/lang/NullPointerException; (Attempt to invoke virtual method 'Landroid/os/VibrationAttributes$Builder;.build' on a null object reference) method=Lo/k;.<init> pc=68 → uncaught (deferred frame unwind + propagate)
[EXC-PROPAGATE] Ljava/lang/NullPointerException; uncaught at caller Lorg/xolatgames/dima/defense/android/AndroidLauncher;.onCreate invoke_pc=98 → APP BOUNDARY unwind
[SYNTH-EXC] f141-null-recv (deferred): Ljava/lang/NullPointerException; (Attempt to invoke interface method 'Ljava/util/List;.isEmpty' on a null object reference) method=Lo/b;.onResume pc=40 → uncaught (deferred frame unwind + propagate)
[EXC-PROPAGATE] Ljava/lang/NullPointerException; uncaught at caller Lorg/xolatgames/dima/defense/android/AndroidLauncher;.onCreate invoke_pc=429 → APP BOUNDARY unwind
```

The S206-era `pc=17 VibratorManager.getDefaultVibrator` death is GONE on main (C9-26 closed it) — the same `Lo/k;.<init>` now dies at `pc=68`, one builder layer deeper: SDK_INT=35 → `new VibrationAttributes$Builder().setUsage(19).build()`; the S186I stub answers NULL for the fluent `setUsage`, so `build()` NPEs on a null receiver. `VibrationAttributes$Builder` (API 33) is the missing sibling of the already-landed `AudioAttributes$Builder` law (dalvik_engine.cpp AudioAttributes block) — same §12 family, same object-law shape.

## 2) The "null-List" half: AOSP verdict — my S206 hypothesis is REFUTED, the fault is the ENGINE's

The S206 SIM-L3 row hypothesized: "the `List.isEmpty` null is the app's own state — verify against AOSP which side is at fault." **Verified against the AOSP source (aosp-mirror/platform_frameworks_base, frameworks/base/core/java/android/hardware/SensorManager.java): REFUTED — the null was an engine fault, not app state.**

- `SensorManager.getSensorList(int type)` NEVER returns null: the implementation builds `list = new ArrayList<Sensor>()` (empty when the type is absent) and returns `Collections.unmodifiableList(list)` — a non-null, possibly-empty list.
- `SensorManager.getDefaultSensor(int type)` is `@Nullable` — returns null only when no sensor of the type exists (AOSP javadoc: "or null otherwise").
- The app (`Lo/b;.onResume`, the obfuscated libGDX AndroidInput) is exactly the AOSP-defensive shape: `if (!getSensorList(1).isEmpty()) …` then `if (v1_5 != null) …`. On any real device this never NPEs.
- The engine's S186I stub fall-through answered NULL for `getSensorList(I)Ljava/util/List;` — impossible per the AOSP contract — and the `.isEmpty()` deref died. Engine fault, engine fix.

## 3) THE LAWS (K-2 — full patch, one numbered part)

Two generic laws in `miniandroid/src/dex/dalvik_engine.cpp`, 105 insertions, zero per-app knowledge (both key on framework classes + AOSP contracts only):

- **F-NEW-633 — `VibrationAttributes$Builder` fluent-builder contract** (placed beside its `AudioAttributes$Builder` sibling): `<init>` void; `setUsage(I)` fluent-this; `build()` non-null `VibrationAttributes` (haptic firing stays a device effect, unobservable headless — the C9-26 law boundary).
- **F-NEW-634 — `SensorManager` AOSP contract, the honest minimal device**: `getSensorList(I)` → non-null EMPTY `Ljava/util/ArrayList;` (`__array_length__`=0 + 0-element CollectionShadow state: `isEmpty()`=true, `size()`=0); `getDefaultSensor(I)` → null (@Nullable, honest absent); `registerListener(...)` → false on null listener/sensor, true otherwise (AOSP `registerListenerImpl`; event DELIVERY is a device effect — vibrate() parity).

(THE PATCH OF RECORD is §3a below — the real exported diff, byte-faithful; `git apply --check` rc=0 on main `01586a17`; 123 lines.)

## 4) Executable verification (K-4)

```
# 0. re-anchor
git clone --depth 200 … ; git checkout 01586a17 ; make -j2        # binary sha16 f6e580cfcadabacc
# 1. baseline ×3
./build/miniandroid run dima_15.apk -o base1 -v --max-seconds 40   # rc=1 face d602648e8e401895 ×3, 2 uncaught
# 2. apply
git apply --check s216_c3_sim_l3.patch                              # rc=0
git apply s216_c3_sim_l3.patch ; make -j2                          # binary sha16 98642e75e1a489fe
# 3. patched ×3
./build/miniandroid run dima_15.apk -o fix1 -v --max-seconds 40     # rc=1 face d602648e8e401895 ×3, 1 uncaught
# 4. unit gates
make test                                                          # 4 passed, 0 failed
```

**A/B result:** both named SYNTH-EXC lines GONE; `Lo/k;.<init>` now completes (`RETURN_VOID at 0x47`); stub census 309→349 IMPLEMENTED / 28→33 STUBBED (the app reaches deeper code); uncaught **2 → 1**; face byte-identical `d602648e8e401895` ×3 (pre == post — face-neutral).

## 5) Honest verdicts (K-6)

1. **Claim shape:** "both SIM-L3-named roots closed (Vibrator-family builder layer + SensorManager never-null contract), face-neutral, app-impact PARTIAL." The app still ends `DEFAULT_BACKGROUND_ONLY` / `first_missing_stage=APP_DRAW_OPS` — this is NOT a playability fix, and I do not claim one (the S207/S209 verdict shape applies).
2. **Self-refutation recorded:** the S206 row's "the List.isEmpty null is the app's own state" is REFUTED by the AOSP source (§2). The app is AOSP-correct; the engine violated the contract.
3. **The next frontier NAMED, not patched** (family discipline — a separate window-content law, coordinating with the framework-views lane): after both laws land, the remaining death is
```
[EXP088-B-DBG] findViewById: target=0x1020002 content_view_id=5e registry=YES
[EXP088-B-DBG] find_by_android_id returned 0
[F447-NPE] app-caller null-recv NPE parity: Landroid/view/View;.setOnApplyWindowInsetsListener caller=Lf/c$b;.b
[SYNTH-EXC] f141-null-recv (deferred): … method=Lf/c$b;.b pc=32 → uncaught
```
— the app (obfuscated androidx `ViewCompat.setOnApplyWindowInsetsListener` shim `Lf/c$b;.b`, androguard-decoded) receives a NULL View from `findViewById(android.R.id.content)` (0x01020002) after `setContentView` and stores it in `Lp/a;.b`. AOSP contract: after `setContentView`, `findViewById(android.R.id.content)` resolves the window's content FrameLayout — never null. The engine's `find_by_android_id` only matches app-inflated ids, so the framework-id 0x01020002 falls through to null. A correct law needs the DecorView/content-frame node shape (the content root vs the content PARENT distinction — apps attach overlays to the parent), so I deliberately did NOT rush it into this delivery; the keylines above are the full decode for whoever owns the window lane.

## 6) Golden battery ×2 (regression) — ALL 6 PINS BYTE-EXACT, pre AND post

Same recipe as s207_gate.py/s214_gate.py (APKs version-pinned from F-Droid: bouncy_43, unote_30, dooz_23, gmdice_8, microtimer_8, tictactoe_3):

| pin | face | pre (`f6e580cf`) | post (`98642e75`) |
|---|---|---|---|
| bouncy | `8a6c24ac8a7d718e` | HOLD | HOLD |
| unote | `3b8dcb0adbbc17a9` | HOLD | HOLD |
| dooz | `a0fae9072313e2d1` | HOLD | HOLD |
| gmdice ×2 | `3891679dff449331` | HOLD, rerun-identical | HOLD, rerun-identical |
| microtimer | `b39665f68f3938e6` | HOLD, 0 uncaught | HOLD, 0 uncaught |
| ttt ×3 | `7354c1b231cd581d` | HOLD, deterministic ×3 | HOLD, deterministic ×3 |

**ALL_PINS_HOLD = true on BOTH binaries** — the patch is regression-neutral byte-exact across the whole standing battery.

## 7) Reproduction manifest

- Base: main `01586a17`. PRE binary sha16 `f6e580cfcadabacc`; POST binary sha16 `98642e75e1a489fe`.
- Patch: `miniandroid/src/dex/dalvik_engine.cpp` only, +105/−0, diff 123 lines, sha256-16 `df4355a758ddd372`, `git apply --check` rc=0 on `01586a17`. `make test` 4/4.
- APKs (F-Droid, verified): dima `b148fb1f46a368137319d3d85532bd66` (12,539,909 B) · bouncy_43 `ffda0d9cb0b1b2aa58be9559dda891c4fa24391bc481d297a8e3d96c31f62721` · unote_30 / dooz_23 / gmdice_8 / microtimer_8 / tictactoe_3 as pinned by the standing battery.
- Local worktree is recycle-volatile; this post is the record of truth (K-1 standing law). Patch below in §3a.

## §3a) FULL PATCH (F-NEW-633 + F-NEW-634) — the real exported diff, byte-faithful

Reassembly law (K-2): save as `s216_c3_sim_l3.patch` → `git apply --check` on `01586a17` (expect rc=0) → `git apply` → `make -j2` → binary sha16 `98642e75e1a489fe` → re-run §4. Diff sha256-16 at export: `df4355a758ddd372` (123 lines).

```diff
diff --git a/miniandroid/src/dex/dalvik_engine.cpp b/miniandroid/src/dex/dalvik_engine.cpp
index 47ca3562..255e3729 100755
--- a/miniandroid/src/dex/dalvik_engine.cpp
+++ b/miniandroid/src/dex/dalvik_engine.cpp
@@ -38964,6 +38964,49 @@ bool DalvikExecutionEngine::bridge_to_api(const std::string& class_name,
             return true;
         }
     }
+    // ────────────────────────────────────────────────────────────────────
+    // F-NEW-633 (SIM-L3, Coder 3) — VibrationAttributes$Builder fluent-
+    // builder contract — the API-33 sibling of the AudioAttributes$Builder
+    // law above, same §12 family. Evidence (dima.defense vc15, SIMILAR-10
+    // wave row 5 re-anchored on main 01586a17 / binary f6e580cfcadabacc):
+    // Lo/k;.<init> pc=68 — SDK_INT=35 → `new VibrationAttributes$Builder()
+    // .setUsage(19).build()`; the S186I stub answered NULL for the fluent
+    // setUsage, so build() NPEd on a null receiver → onCreate APP-BOUNDARY
+    // unwind (baseline face d602648e8e401895 ×3, 2 uncaught; the f141-era
+    // receipt of the same family died at pc=17 `VibratorManager.
+    // getDefaultVibrator` on null — closed by C9-26, moving the death one
+    // builder layer deeper). AOSP VibrationAttributes.Builder
+    // (frameworks/base core/java/android/os/VibrationAttributes.java):
+    // setUsage(int) returns this Builder; build() returns a non-null
+    // VibrationAttributes. The object law mirrors AudioAttributes$Builder:
+    // Builder non-null, setters fluent-this, build() non-null
+    // VibrationAttributes (haptic firing remains a device effect,
+    // unobservable in a headless runtime — the C9-26 law boundary).
+    // ────────────────────────────────────────────────────────────────────
+    if (class_name == "Landroid/os/VibrationAttributes$Builder;") {
+        if (method == "<init>") {
+            result = DalvikValue::make_void();
+            status = ApiCallTrace::Status::IMPLEMENTED;
+            return true;
+        }
+        if (!args.empty() && args[0].type == DalvikType::OBJECT_REF &&
+            args[0].object_id != 0 && method == "setUsage") {
+            result = args[0];  // fluent: return THIS (AOSP Builder law)
+            status = ApiCallTrace::Status::IMPLEMENTED;
+            return true;
+        }
+        if (method == "build" && !args.empty() &&
+            args[0].type == DalvikType::OBJECT_REF) {
+            uint32_t va_id =
+                heap_.allocate("Landroid/os/VibrationAttributes;", pc_, 0);
+            heap_.set_object_field(va_id, "__from_builder__",
+                                   DalvikValue::make_int(1));
+            result = DalvikValue::make_object(
+                va_id, "Landroid/os/VibrationAttributes;");
+            status = ApiCallTrace::Status::IMPLEMENTED;
+            return true;
+        }
+    }
     if (class_name == "Landroid/media/MediaPlayer;") {
         auto mp_state_of = [&](uint32_t oid) -> int {
             auto v = heap_.get_object_field(oid, "__mp_state__");
@@ -72399,6 +72442,68 @@ bool DalvikExecutionEngine::bridge_to_api(const std::string& class_name,
         return true;
     }
 
+    // ────────────────────────────────────────────────────────────────────────
+    // F-NEW-634 (SIM-L3, Coder 3) — SensorManager AOSP contract (the honest
+    // minimal device: ZERO sensors, contract-true answers). AOSP
+    // SensorManager.java (aosp-mirror main, frameworks/base core/java/
+    // android/hardware/SensorManager.java): getSensorList(int) NEVER returns
+    // null — an absent type yields an empty `Collections.unmodifiableList`
+    // — and getDefaultSensor(int) is @Nullable (null when no sensor of the
+    // type exists); SystemSensorManager.registerListenerImpl returns false
+    // on a null listener/sensor, true otherwise. The S186I stub answered
+    // NULL for getSensorList — impossible per the AOSP contract — NPEing
+    // every AOSP-defensive consumer at the isEmpty()/size() deref
+    // (dima.defense Lo/b;.onResume pc=40 `getSensorList(1).isEmpty()`,
+    // SIMILAR-10 wave f141 ×2 receipt + the d602648e re-anchor; the S206
+    // SIM-L3 row's "the List.isEmpty null is the app's own state" hypothesis
+    // is REFUTED by the AOSP source — the null was an engine fault; the app
+    // is exactly the AOSP-defensive shape the contract expects). Sibling of
+    // C9-26 above: service object + never-null contract law pair.
+    // ────────────────────────────────────────────────────────────────────────
+    if (class_name == "Landroid/hardware/SensorManager;") {
+        if (method == "getSensorList") {
+            // Non-null EMPTY list (honest minimal device: zero sensors —
+            // consumers branch on isEmpty() exactly per the contract).
+            uint32_t sl_id = heap_.allocate("Ljava/util/ArrayList;", pc_, 0);
+            heap_.set_object_field(sl_id, "__array_length__",
+                                   DalvikValue::make_int(0));
+            if (shadow_registry_) {
+                if (auto* sl_cs = shadow_registry_->find_as<
+                        framework::CollectionShadow>()) {
+                    // 0-element CollectionState: isEmpty()=true, size()=0.
+                    sl_cs->get_or_create(sl_id);
+                }
+            }
+            result = DalvikValue::make_object(sl_id, "Ljava/util/ArrayList;");
+            status = ApiCallTrace::Status::IMPLEMENTED;
+            return true;
+        }
+        if (method == "getDefaultSensor") {
+            // AOSP @Nullable: null when the type does not exist (honest
+            // minimal device — no sensor of ANY type). Consumers null-check
+            // per the contract (dima.defense Lo/b; does exactly this).
+            result = DalvikValue::make_null();
+            status = ApiCallTrace::Status::IMPLEMENTED;
+            return true;
+        }
+        if (method == "registerListener") {
+            // args[0]=receiver, args[1]=listener, args[2]=sensor (the
+            // EXP-071 instance-method law). false on a null listener or
+            // sensor (AOSP registerListenerImpl); true otherwise — the
+            // registration is accepted, event DELIVERY is a device effect
+            // unobservable in a headless runtime (the vibrate() parity
+            // boundary of C9-26).
+            bool sl_ok = args.size() >= 3 &&
+                         args[1].type == DalvikType::OBJECT_REF &&
+                         args[1].object_id != 0 &&
+                         args[2].type == DalvikType::OBJECT_REF &&
+                         args[2].object_id != 0;
+            result = DalvikValue::make_bool(sl_ok);
+            status = ApiCallTrace::Status::IMPLEMENTED;
+            return true;
+        }
+    }
+
     // ────────────────────────────────────────────────────────────────────────
     // C9-24b (CODER 9, S188 cohort) — Resources.getResourcePackageName /
     // getResourceTypeName / getResourceEntryName (AOSP Resources.java).
```

*Section §3 above describes the two laws; THIS block is the patch of record.*
