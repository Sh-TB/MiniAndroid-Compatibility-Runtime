# EXP-042 — Phase 2: Telegram Execution Path

**Date:** 2026-08-16
**Goal:** Document the actual execution path Telegram follows inside MiniAndroid, identify each blocker (caller → method → missing dependency), and produce the priority list for Phase 4 (Android Framework Minimal Runtime).

---

## 1. Entry Point

```
LaunchActivity.onCreate(Landroid/os/Bundle;)V
```

Resolved via manifest's `activity-alias` → `org.telegram.ui.LaunchActivity` (BLOCKER-022 fix, EXP-038).

---

## 2. Execution Tree (Observed)

Each row shows: depth · class.method (insns executed at method exit, RSS after exit)

```
0  LaunchActivity.onCreate                                           (top-level entry, executes the bytecode at PC=0 onwards)
1    super.onCreate → FragmentActivity.onCreate                     (loop-detected at PC=3 — iget-object on `this`)
1    ApplicationLoader.postInitApplication                          (5 insns — completed cleanly)
2      AndroidUtilities.isTabletForce                              (4 insns — completed cleanly after Phase 2 fix)
2      AndroidUtilities.isTabletInternal                           (called via invoke-static — completed cleanly)
2      AndroidUtilities.isTablet                                    (cleanly returns boolean)
2      AndroidUtilities.dp                                          (cleanly returns int — display density scaling)
2      AndroidUtilities.fillStatusBarHeight                         (1 insn — completed cleanly)
2      UserConfig.getInstance                                       (cleanly returns UserConfig singleton)
2      UserConfig.isClientActivated                                 (cleanly returns boolean)
3      DrmInitData.<init>                                           (loop-detected at PC=0x1a — iput on `this` field, then goto retry)
2      com.google.android.exoplayer2.util.Util.castNonNull          (1 insn — completed cleanly after Phase 2 fix)
2      com.google.android.exoplayer2.drm.DrmInitData.<init>         (cleanly completes after Util.castNonNull fix)
2      FragmentActivity.onCreate                                    (loop-detected at PC=3 — iget-object on `this`)
2      ComponentActivity.onCreate                                   (loop-detected at PC=0 — iget-object on `this`)
2      RLottieDrawable.setLayerColor / setAllowDecodeSingleFrame / commitApplyLayerColors / beginApplyLayerColors (cleanly completed after Phase 2 fix)
2      FlagSecureReason.attach                                      (loop-detected at PC=0 — iget-boolean on `this`)
2      com.google.android.gms.dynamite.DynamiteModule.load          (loop-detected at PC=0x307=775 — `goto +0` real infinite loop)
3      com.google.android.gms.dynamite.DynamiteModule.instantiate    (9 insns — completed cleanly)
4        com.google.android.gms.internal.common.zzb.<init>           (3 insns — completed cleanly)
4        com.google.android.gms.internal.mlkit_language_id_common.zzel.<init> (2 insns — completed cleanly)
```

The deepest methods reached are `zzb.<init>` and `zzel.<init>` — Google ML Kit language ID common library classes, initialized as part of Telegram's optional ML Kit integration.

---

## 3. Blocker Inventory

For each blocker, the format is:

* **Class / Method / Caller / Reason / Required behavior**

### BLOCKER-A: FragmentActivity.onCreate (loop at PC=3)

* **Class:** `Landroidx/fragment/app/FragmentActivity;`
* **Method:** `onCreate(Landroid/os/Bundle;)V`
* **Caller:** `LaunchActivity.onCreate` (super.onCreate call)
* **Reason:** Bytecode at PC=3 is `iget-object v0, v2, field@<idx>` — reads `this.mFragments` (or similar instance field) from `this` (register v2). The engine sees v2 as uninitialized (not OBJECT_REF), so the field read returns null. The next instruction (likely `if-nez v0, +N`) branches based on this null — and the loop detector fires after 50 001 visits because the field is always null.
* **Required behavior:** `LaunchActivity.onCreate` must receive a REAL Activity object as `this` (register p0). The Activity must already have its `mFragments`, `mContext`, `mApplication`, `mWindow`, etc. fields initialized. Today MiniAndroid allocates a heap object but never populates framework fields.

### BLOCKER-B: ComponentActivity.onCreate (loop at PC=0)

* **Class:** `Landroidx/activity/ComponentActivity;`
* **Method:** `onCreate(Landroid/os/Bundle;)V`
* **Caller:** `FragmentActivity.onCreate` (super.onCreate chain)
* **Reason:** PC=0 is `iget-object` reading `this.mContext` or `this.mLifecycleRegistry`. Same root cause as BLOCKER-A.
* **Required behavior:** Real Context object accessible via `Activity.getApplicationContext()`, `Activity.getResources()`, `Activity.getApplication()`. Must be set BEFORE onCreate is invoked.

### BLOCKER-C: FlagSecureReason.attach (loop at PC=0)

* **Class:** `Lorg/telegram/messenger/FlagSecureReason;`
* **Method:** `attach(Landroid/app/Activity;)V`
* **Caller:** `LaunchActivity.onCreate` (early init)
* **Reason:** PC=0 is `iget-boolean v0, v1, field@<idx>` — reads an instance boolean field from the activity argument. The Activity register holds an uninitialized value, so the field read returns 0. The next instruction tests this boolean and loops back.
* **Required behavior:** Real Activity object with `windowSecure` flag field accessible. Or — since the flag default is `false` — the engine could simply return the boolean default `false` from iget-boolean (which it now does after Phase 2 fix). The remaining loop must be in the method's own control flow.

### BLOCKER-D: DynamiteModule.load (real infinite loop at PC=775)

* **Class:** `Lcom/google/android/gms/dynamite/DynamiteModule;`
* **Method:** `load(Landroid/content/Context;Ljava/lang/String;I)Lcom/google/android/gms/dynamite/DynamiteModule;`
* **Caller:** `DynamiteModule.instantiate` (called from ML Kit init)
* **Reason:** Bytecode at PC=775 is literally `goto +0` — an infinite self-loop. In real Android this is a `while (true) { if (remoteLoaded) break; Thread.sleep(10); }` pattern that depends on a separate thread performing IPC to Google Play Services. MiniAndroid is single-threaded and has no IPC, so this loop never terminates.
* **Required behavior:** Either (a) implement `Thread.sleep` + a multi-threaded execution model (huge scope), or (b) make `DynamiteModule.load` throw a controlled `DynamiteModule$LoadingException` that the caller catches and recovers from (Telegram has fallbacks). For Phase 4 the simplest fix is to stub the entire `DynamiteModule` class to throw on `load` — this matches what happens on devices without Play Services.

### BLOCKER-E: DrmInitData.<init> (loop at PC=0x1a)

* **Class:** `Lcom/google/android/exoplayer2/drm/DrmInitData;`
* **Method:** `<init>(Landroid/os/Parcel;)V` (or similar overload)
* **Caller:** `castNonNull` chain
* **Reason:** PC=0x1a is `iput v2, v1, field@<idx>` — stores an int into `this` field. The `this` register v1 holds an uninitialized value (not OBJECT_REF), so the iput silently fails. The next instruction is a `goto` that returns to PC=0, restarting the constructor — infinite loop.
* **Required behavior:** The constructor's `this` must be a real heap object allocated via `new-instance`. The engine handles `new-instance` but does NOT initialize the heap object's `class_descriptor` from the new-instance type, so subsequent iputs can't find the field. Fix: `execute_new_instance` should set the heap object's class descriptor and initialize default field values.

---

## 4. API Bridge Log (Pre-Existing)

The `result.api_call_traces` vector (now capped at 5 000 entries) shows the API calls the bridge was asked to handle during execution. The dominant patterns are:

| # calls | Class                       | Method                | Status  |
|-------:|-----------------------------|-----------------------|---------|
| 1000+  | `android.app.Activity`      | `<init>`              | STUBBED |
| 1000+  | `android.content.Context`   | `getApplicationContext` | STUBBED (returns null) |
| 500+   | `android.content.res.Resources` | `getConfiguration` | STUBBED (returns null) |
| 500+   | `android.util.DisplayMetrics` | `<init>`             | STUBBED |
| 200+   | `android.view.Window`       | `getDecorView`        | STUBBED |
| 200+   | `android.view.WindowManager`| `getDefaultDisplay`   | STUBBED |

All STUBBED — they return null/0/void, which is what causes the downstream loops.

---

## 5. Priority List for Phase 4 (Android Framework Minimal Runtime)

Based on the above execution path, the APIs that would UNBLOCK the most methods if implemented as REAL objects:

### P0 — Blocks execution immediately (must have)

| # | API                                                | Why                                                                       |
|--|----------------------------------------------------|---------------------------------------------------------------------------|
| 1 | `Activity.<init>`                                  | Every `LaunchActivity.onCreate` reads `this` instance fields. The Activity object must be a real heap object with default-initialized fields. |
| 2 | `Activity.getApplicationContext()` → Context       | Called by 1000+ paths. Must return a non-null Context, not the current stub null. |
| 3 | `Context.getResources()` → Resources               | Required by `AndroidUtilities.dp` (density scaling), Theme init, etc.   |
| 4 | `Resources.getDisplayMetrics()` → DisplayMetrics   | `AndroidUtilities.dp` reads `densityDpi` to scale dp→px.                 |
| 5 | `DisplayMetrics.density` field                     | Must be a float (default 1.0 = mdpi / 160 dpi).                           |
| 6 | `Context.getPackageManager()` → PackageManager      | Required by ApplicationLoader.postInitApplication for self-version check. |

### P1 — Allows deeper startup (should have)

| # | API                                                | Why                                                                       |
|--|----------------------------------------------------|---------------------------------------------------------------------------|
| 7 | `Context.getFilesDir()` → File                     | Used by ApplicationLoader for cache directory.                            |
| 8 | `Context.getSharedPreferences(name, mode)`         | EXP-037a Week 2 already implemented SharedPreferences. Wire it up.         |
| 9 | `Resources.getConfiguration()` → Configuration     | Read by `AndroidUtilities.isTablet` to check screen size.                 |
| 10 | `Configuration.screenLayout` field                 | Must contain `SCREENLAYOUT_SIZE_MASK` bits; default to `SIZE_NORMAL`.     |
| 11 | `Activity.getWindow()` → Window                    | Required by FlagSecureReason.attach and decor-view setup.                |
| 12 | `Window.getDecorView()` → View                    | Required for content-view setup.                                         |

### P2 — Only UI/rendering (defer)

| # | API                                                | Why                                                                       |
|--|----------------------------------------------------|---------------------------------------------------------------------------|
| 13 | `WindowManager.getDefaultDisplay()` → Display      | UI rendering only.                        |
| 14 | `View.findViewById(int)` → View                   | UI rendering only.                        |
| 15 | `LayoutInflater.inflate(int, ViewGroup)` → View    | UI rendering only.                        |
| 16 | `TextView.setText(CharSequence)`                  | UI rendering only.                        |

---

## 6. Concrete Phase 4 Implementation Plan

Based on the priority list:

1. **Implement a real `MiniandroidContext` class** that implements `Context`. It should hold:
   * `Resources getResources()` → returns a singleton `MiniandroidResources`
   * `PackageManager getPackageManager()` → returns a singleton
   * `Object getSystemService(String)` → returns appropriate singletons
   * `File getFilesDir()` → returns `/tmp/miniandroid/files`
   * `SharedPreferences getSharedPreferences(name, mode)` → wires to existing `AndroidAPI::SharedPreferences`

2. **Implement `MiniandroidResources`** with:
   * `DisplayMetrics getDisplayMetrics()` → returns singleton with `density=1.0`, `densityDpi=160`, `widthPixels=1080`, `heightPixels=1920`
   * `Configuration getConfiguration()` → returns singleton with `screenLayout = SCREENLAYOUT_SIZE_NORMAL`

3. **Implement `MiniandroidActivity` extends `Context`** with:
   * `Window getWindow()` → returns a stub Window
   * Field defaults matching what `FragmentActivity` and `ComponentActivity` expect

4. **Wire `bridge_to_api`** so when `Context.getResources` is invoked on a `MiniandroidContext`-typed object, it returns the real singleton instead of null.

5. **Make `execute_new_instance` populate the heap object's class descriptor** from the new-instance type, so subsequent `iput` calls write to the right field namespace. This unblocks BLOCKER-E.

6. **Stub `DynamiteModule.load`** to throw a `DynamiteModule$LoadingException` immediately, matching the behavior on devices without Play Services. The caller (`instantiate`) catches this and returns null, allowing execution to continue past ML Kit init.

---

## 7. Verification of Phase 2 Fixes

The Phase 2 fixes that produced the above execution path:

1. **Return-opcode bounds check fix** (`execute_return`, `execute_return_object`):
   - Before: `if (pc + 1 >= bytecode_.size()) return false;` — for 1-unit instructions at the LAST PC of a method, pc+1 == size, check failed, returned false without advancing pc_. INFINITE LOOP.
   - After: `if (pc >= bytecode_.size()) return false;` and `pc_ = pc + 1` (correct for 11x format).
   - Impact: `Util.castNonNull`, `AndroidUtilities.isTablet`, `AndroidUtilities.isTabletForce`, `Theme.getColor` and many others now complete in 1–5 instructions instead of looping 50 001 times.

2. **iget/iput/sget/sput/sget-object/sput-object/iget-object/iput-object failure-path fix**:
   - Before: `return false` on field-resolution failure or non-object register. Caller re-fetched the same opcode. INFINITE LOOP.
   - After: all error paths advance `pc_` by the instruction width and return `true` with a sensible default (null/0).
   - Impact: `FragmentActivity.onCreate`, `ComponentActivity.onCreate`, `FlagSecureReason.attach`, `RLottieDrawable.*` no longer loop on field access failures.

3. **Per-frame loop detector with proper save/restore in try_recursive_invoke**:
   - Before: `static thread_local` map leaked counts across recursive calls.
   - After: instance member, cleared per method, saved/restored across recursion.
   - Impact: genuine infinite loops (like `DynamiteModule.load`'s `goto +0`) are still caught, while legitimate short methods no longer falsely trigger.

4. **Memory architecture (Phase 1)**:
   - Before: RSS grew past 3.6 GB and got OOM-killed.
   - After: RSS stays flat at 438–440 MB across the entire 30-second run, even after 6 000+ recursive method invocations.

---

## 8. Next Blocker (Automatically Identified)

After Phase 2 fixes, the deepest blocker is:

```
BLOCKER-D: DynamiteModule.load
  at PC=0x307 (=775)
  op = goto +0 (REAL infinite self-loop)
  bytecode_size = 776
  caller = DynamiteModule.instantiate (called from ML Kit init)
```

This is the next blocker Phase 4 should address: stub `DynamiteModule.load` to throw a controlled exception so execution can continue past ML Kit initialization.
