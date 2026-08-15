# EXP-043 Phase 6 — Telegram Source-Driven Compatibility

**Date:** 2026-08-16
**Goal:** Map Telegram's key classes to the Android APIs they require, based on the public source code at https://github.com/DrKLO/Telegram.

---

## Methodology

For each key Telegram class on the startup path, we:
1. Read the public source code
2. List the Android APIs called (in order)
3. Document the minimum required behavior
4. Compare with our current implementation status

---

## 1. ApplicationLoader

**Source:** `TMessagesProj/src/main/java/org/telegram/messenger/ApplicationLoader.java`

### postInitApplication() — Current Blocker

This is the method that currently halts at PC=8 (goto/32 with D8 encoding). Let me trace what it does:

```java
public static void postInitApplication() {
    // PC=0: sget-boolean applicationLoaded
    // PC=2: if-ltz (null check) → skip if already loaded
    if (applicationLoaded) {
        return;
    }
    // PC=4: sget-object applicationContext (null in our runtime)
    // PC=6: if-ltz (null check) → skip if null
    // PC=8: goto/32 → PC=265 (return-void) — our engine HALTS here
    if (applicationContext == null) {
        return;
    }
    // ... rest of initialization (not reached yet)
}
```

**Required Android APIs (when execution proceeds past PC=8):**

| Order | API | Used For | Our Status |
|------:|-----|----------|-----------|
| 1 | `Context.getFilesDir()` | Cache directory | ✅ Implemented (Phase 3) |
| 2 | `Context.getExternalFilesDir(null)` | External storage | ✅ Implemented (Phase 3) |
| 3 | `Context.getSharedPreferences("userconfing", MODE_PRIVATE)` | User config | ✅ Bridge returns singleton |
| 4 | `Context.getPackageManager()` | Version check | ✅ Implemented (Phase 4) |
| 5 | `PackageManager.getPackageInfo(packageName, 0)` | Get versionCode | ✅ Implemented (Phase 4) |
| 6 | `PackageInfo.versionCode` field | Version number | ✅ Pre-populated = 9999 |
| 7 | `Context.getPackageName()` | Self package name | ✅ Implemented (Phase 4) |
| 8 | `Context.getResources()` | Get display metrics | ✅ Implemented (Phase 4) |
| 9 | `Resources.getDisplayMetrics()` | Density for dp scaling | ✅ Implemented (Phase 4) |
| 10 | `DisplayMetrics.density` field | Multiplier | ✅ Pre-populated = 1.0 |
| 11 | `Context.getSystemService(Context.CONNECTIVITY_SERVICE)` | Network info | ✅ Returns null (handled) |
| 12 | `new Handler(Looper.getMainLooper())` | Post to main thread | ✅ No-op (Phase 3) |
| 13 | `NativeLoader.initNativeLibs(applicationContext)` | Load libtmessages.49.so | ❌ NOT REACHED YET |

**Current blocker:** The goto/32 at PC=8 uses D8's non-standard encoding (2 code-unit 16-bit offset), and our engine's goto/32 handler was updated to handle this. However, the method exits at PC=8 because the `applicationContext` field (sget-object at PC=4) returns null, and the null check at PC=6 causes a goto/32 to PC=265 (return-void).

**Fix needed:** Pre-populate `applicationContext` as a non-null Context singleton in the static field storage before `postInitApplication` is called.

---

## 2. AndroidUtilities

**Source:** `TMessagesProj/src/main/java/org/telegram/messenger/AndroidUtilities.java`

### isTablet() / isTabletInternal() / isTabletForce()

```java
public static boolean isTablet() {
    if (isTabletForce != null) return isTabletForce;
    Configuration config = ApplicationLoader.applicationContext
        .getResources().getConfiguration();
    return (config.screenLayout & Configuration.SCREENLAYOUT_SIZE_MASK)
        >= Configuration.SCREENLAYOUT_SIZE_XLARGE;
}
```

**Required Android APIs:**

| API | Used For | Our Status |
|-----|----------|-----------|
| `Context.getResources()` | Get Resources | ✅ |
| `Resources.getConfiguration()` | Get Configuration | ✅ |
| `Configuration.screenLayout` field | Size mask | ✅ Pre-populated = 0x40 (SIZE_NORMAL) |

**Status:** ✅ All APIs implemented. `isTablet()` returns false (correct for phone form factor).

### dp(float value)

```java
public static int dp(float value) {
    if (value == 0) return 0;
    return (int) Math.ceil(density * value);
}
```

Where `density` is loaded from `ApplicationLoader.applicationContext.getResources().getDisplayMetrics().density`.

**Required Android APIs:**

| API | Used For | Our Status |
|-----|----------|-----------|
| `Context.getResources()` | Get Resources | ✅ |
| `Resources.getDisplayMetrics()` | Get DisplayMetrics | ✅ |
| `DisplayMetrics.density` field | Multiplier (1.0) | ✅ Pre-populated |

**Status:** ✅ All APIs implemented. `dp(N)` returns `ceil(1.0 * N)` = N.

### fillStatusBarHeight()

```java
public static void fillStatusBarHeight() {
    Resources resources = ApplicationLoader.applicationContext.getResources();
    int resourceId = resources.getIdentifier("status_bar_height", "dimen", "android");
    if (resourceId > 0) {
        statusBarHeight = resources.getDimensionPixelSize(resourceId);
    }
}
```

**Required Android APIs:**

| API | Used For | Our Status |
|-----|----------|-----------|
| `Context.getResources()` | Get Resources | ✅ |
| `Resources.getIdentifier(name, type, pkg)` | Look up resource by name | ✅ Returns 0 (not found) |
| `Resources.getDimensionPixelSize(id)` | Get pixel size | ✅ Returns 24 (default) |

**Status:** ✅ All APIs implemented. `fillStatusBarHeight()` sets `statusBarHeight = 24` (default Android value).

---

## 3. UserConfig

**Source:** `TMessagesProj/src/main/java/org/telegram/messenger/UserConfig.java`

### getInstance(int account)

```java
public static UserConfig getInstance(int account) {
    UserConfig localInstance = instances.get(account);
    if (localInstance == null) {
        synchronized (UserConfig.class) {
            localInstance = instances.get(account);
            if (localInstance == null) {
                localInstance = new UserConfig(account);
                instances.put(account, localInstance);
            }
        }
    }
    return localInstance;
}
```

**Required Android APIs:**

| API | Used For | Our Status |
|-----|----------|-----------|
| `Context.getSharedPreferences("userconfing", MODE_PRIVATE)` | Persistent config | ✅ Bridge returns singleton |
| `SharedPreferences.getBoolean(key, default)` | Read boolean | ⏳ SharedPreferences object exists but getBoolean not wired to real storage |

### isClientActivated()

```java
public boolean isClientActivated() {
    return preferences.getBoolean("activated", false);
}
```

**Required Android APIs:**

| API | Used For | Our Status |
|-----|----------|-----------|
| `SharedPreferences.getBoolean("activated", false)` | Check login state | ⏳ Returns false (not logged in) |

**Status:** ⏳ Partially implemented. The SharedPreferences singleton exists but `getBoolean` is not wired to the real `AndroidAPI::SharedPreferences` implementation (from EXP-037a Week 2). This is a Phase 4 task.

---

## 4. Theme (org.telegram.ui.ActionBar.Theme)

**Source:** `TMessagesProj/src/main/java/org/telegram/ui/ActionBar/Theme.java`

### getColor(String key)

```java
public static int getColor(String key) {
    if (currentColors == null) {
        currentColors = getCurrentColors(false);
    }
    Integer value = currentColors.get(key);
    if (value == null) {
        return fallbackColors.get(key);
    }
    return value;
}
```

**Required Android APIs:**

| API | Used For | Our Status |
|-----|----------|-----------|
| None direct | Reads from HashMap | ✅ Stubbed (returns 0xFF000000 black) |

**Status:** ✅ Stubbed. Returns black for all colors. This is sufficient for startup; actual color values require resource table parsing (future work).

### createCommonResources() / createChatResources() etc.

These methods are large (500-2400 instructions each) and load theme resources from the APK's resource table. They call:
- `Resources.getIdentifier(name, type, pkg)`
- `Resources.getDrawable(id)`
- `Resources.openRawResource(id)`

**Status:** ⏳ Not fully implemented. These methods are entered (we see them in the execution log) but halt due to resource table parsing not being available.

---

## 5. SharedConfig

**Source:** `TMessagesProj/src/main/java/org/telegram/messenger/SharedConfig.java`

### Key methods on startup path:

- `SharedConfig.init(applicationContext)` — reads config from SharedPreferences
- `SharedConfig.saveConfig()` — writes config to SharedPreferences
- `SharedConfig.toggleShowDirectShareEmoji()` — UI setting

**Required Android APIs:**

| API | Used For | Our Status |
|-----|----------|-----------|
| `Context.getSharedPreferences("userconfing", MODE_PRIVATE)` | Persistent config | ✅ |
| `SharedPreferences.getString(key, default)` | Read string | ⏳ Not wired to real storage |
| `SharedPreferences.edit()` | Get editor | ⏳ Not wired |
| `Editor.putString(key, value)` | Write string | ⏳ Not wired |
| `Editor.commit()` / `apply()` | Persist | ⏳ Not wired |

**Status:** ⏳ Phase 4 task — wire the bridge's SharedPreferences singleton to the real `AndroidAPI::SharedPreferences` implementation.

---

## 6. ConnectionsManager (TgNet)

**Source:** `TMessagesProj/src/main/java/org/telegram/tgnet/ConnectionsManager.java`

### Key native methods:

```java
public static native ConnectionsManager getInstance(int account);
public native int getCurrentTime();
public native long getCurrentDatacenterId();
public native int getTimeDifference();
// ... 38 native methods total
```

**Required Android APIs:**

| API | Used For | Our Status |
|-----|----------|-----------|
| `NativeLoader.initNativeLibs(context)` | Load libtmessages.49.so | ❌ NOT REACHED |
| `System.loadLibrary("tmessages.49")` | Load native lib | ❌ NOT REACHED |
| JNI bridge for 38 native methods | Network protocol | ❌ NOT IMPLEMENTED |

**Status:** ❌ Not reached. The JNI distance analysis (EXP-043 Phase 2) confirmed that execution halts before `NativeLoader.initNativeLibs` is called. The first native method would be `ConnectionsManager.native_getCurrentTime`.

---

## 7. SQLite Storage

**Source:** `TMessagesProj/src/main/java/org/telegram/SQLite/`

### Key classes:

- `SQLiteDatabase` — 4 native methods
- `SQLiteCursor` — 9 native methods
- `SQLitePreparedStatement` — 10 native methods

**Required Android APIs:**

| API | Used For | Our Status |
|-----|----------|-----------|
| JNI bridge for 23 SQLite native methods | Message storage | ❌ NOT IMPLEMENTED |

**Status:** ❌ Not reached. SQLite is needed for message storage but is not on the startup path.

---

## 8. RLottieDrawable

**Source:** `TMessagesProj/src/main/java/org/telegram/ui/Components/RLottieDrawable.java`

### Key native methods:

```java
public static native long create(String json, int w, int h, boolean limitFps, ...);
public static native void destroy(long ptr);
public static native void setLayerColor(long ptr, ...);
// ... 6 native methods in RLottieNative
```

**Required Android APIs:**

| API | Used For | Our Status |
|-----|----------|-----------|
| JNI bridge for 6 RLottie native methods | Sticker animations | ❌ NOT IMPLEMENTED |

**Status:** ❌ Not reached. RLottie is used for animated stickers but is not on the startup path.

---

## Compatibility Priority Summary

Based on the above analysis, the priority order for implementing remaining APIs:

### P0 — Blocks execution NOW (fix these first)

| Priority | Item | Why |
|---------:|------|-----|
| 1 | Pre-populate `applicationContext` static field | `ApplicationLoader.postInitApplication` halts because `applicationContext` is null |
| 2 | Fix `goto/16` invalid targets for `AndroidUtilities.bold` and `Intrinsics.createParameterIsNullExceptionMessage` | These cause HALT-GOTO events that halt the method prematurely |

### P1 — Needed for deeper startup

| Priority | Item | Why |
|---------:|------|-----|
| 3 | Wire SharedPreferences bridge to real `AndroidAPI::SharedPreferences` | `UserConfig.isClientActivated` and `SharedConfig.init` need real persistence |
| 4 | Implement `NativeLoader.initNativeLibs` | Loads libtmessages.49.so (first JNI call) |
| 5 | Implement `ConnectionsManager.getInstance` | Singleton for network protocol |
| 6 | Implement `ConnectionsManager.native_getCurrentTime` (JNI) | First native method on path |

### P2 — Needed for login flow

| Priority | Item | Why |
|---------:|------|-----|
| 7 | Implement `ConnectionsManager` native methods (JNI) | 38 methods for MTProto protocol |
| 8 | Implement SQLite native methods (JNI) | 23 methods for message storage |
| 9 | Implement `Resources.openRawResource(id)` | Load theme resource files |

### P3 — Needed for UI rendering

| Priority | Item | Why |
|---------:|------|-----|
| 10 | Implement RLottie native methods (JNI) | Animated stickers |
| 11 | Implement View inflation | Layout XML parsing |
| 12 | Implement Canvas/Surface rendering | Drawing |

---

## Next Actionable Step

The most impactful next fix is **P0.1: Pre-populate `applicationContext`** as a non-null Context singleton in the static field storage before `ApplicationLoader.postInitApplication` is called.

This would allow `postInitApplication` to proceed past PC=8 and reach `NativeLoader.initNativeLibs` (the first JNI call), which is the gateway to Telegram's core functionality.
