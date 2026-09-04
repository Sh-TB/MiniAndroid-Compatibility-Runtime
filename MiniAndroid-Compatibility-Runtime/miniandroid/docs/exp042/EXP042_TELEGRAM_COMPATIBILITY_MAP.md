# EXP-042 — Phase 3: Telegram Open-Source Compatibility Map

**Date:** 2026-08-16
**Goal:** Compare MiniAndroid execution with the real Telegram Android source
code (publicly available at https://github.com/DrKLO/Telegram) and identify the
SMALLEST set of Android framework APIs that must be implemented first.

The principle is: **do NOT implement the entire Android framework.** Implement
only the APIs that Telegram's `LaunchActivity.onCreate` actually calls, in
the order they are called.

---

## 1. Methodology

1. MiniAndroid executed `LaunchActivity.onCreate` against the production
   Telegram APK. Phase 2 documented the actual execution path.
2. The public Telegram source on GitHub defines the actual onCreate code path
   for these key classes. We compare the production APK's bytecode against
   the public source to confirm the expected API surface.
3. For each Telegram class on the current execution path, we list the Android
   APIs that class's source code calls, in the order they appear.

The reference sources used (latest stable as of the APK's build):

* `org.telegram.ui.LaunchActivity` — Telegram's main Activity
* `org.telegram.messenger.ApplicationLoader` — Application init
* `org.telegram.messenger.AndroidUtilities` — utility methods
* `org.telegram.ui.ActionBar.Theme` — color theming
* `org.telegram.messenger.UserConfig` — session state

---

## 2. Expected API Surface — by Telegram Class

### 2.1 LaunchActivity.onCreate (in order)

```
1.  super.onCreate(bundle)                       // androidx FragmentActivity.onCreate
2.  if (AndroidUtilities.isTablet()) { ... }     // configuration check
3.  AndroidUtilities.dp(N)                       // density scaling
4.  AndroidUtilities.fillStatusBarHeight(...)    // resources.getDisplayMetrics()
5.  ApplicationLoader.postInitApplication()      // global init
6.  UserConfig.getInstance(...)                  // singleton access
7.  UserConfig.isClientActivated()               // session state
8.  Theme.getColor(...)                           // color cache lookup
9.  FlagSecureReason.attach(this)                // window flags
10. getWindow().setFlags(...)                     // window manager
11. setContentView(...)                           // view inflation
12. RLottieDrawable.init()                       // lottie cache
```

Each of these calls down into specific Android framework APIs.

### 2.2 ApplicationLoader.postInitApplication

Public source shows this method:

```java
public static void postInitApplication() {
    if (currentInstance != null) {
        currentInstance = null;
    }
    if (applicationHandler == null) {
        applicationHandler = new Handler(applicationContext.getMainLooper());
    }
    if (preferences == null) {
        preferences = applicationContext.getSharedPreferences("userconfing", Activity.MODE_PRIVATE);
    }
    // ... File directory setup using applicationContext.getFilesDir()
    // ... DisplayMetrics via Resources.getDisplayMetrics()
    // ... ConnectivityManager via Context.getSystemService(CONNECTIVITY_SERVICE)
}
```

Required Android APIs (in call order):

| Order | API                                                         | Used For                              |
|------:|-------------------------------------------------------------|---------------------------------------|
| 1     | `Context.getMainLooper()` → Looper                          | Handler construction                  |
| 2     | `new Handler(Looper)`                                       | Post messages to main thread          |
| 3     | `Context.getSharedPreferences("userconfing", MODE_PRIVATE)` | Persist user config (EXP-037a already implements this) |
| 4     | `Context.getFilesDir()` → File                              | Cache directory for media             |
| 5     | `Context.getExternalFilesDir(null)` → File                  | External storage for media            |
| 6     | `Context.getResources()` → Resources                        | Get display metrics                   |
| 7     | `Resources.getDisplayMetrics()` → DisplayMetrics             | Read densityDpi for dp scaling        |
| 8     | `Context.getSystemService(Context.CONNECTIVITY_SERVICE)`     | Network info (not critical for startup) |
| 9     | `Context.getPackageName()` → String                        | Self package name                     |
| 10    | `Context.getPackageManager()` → PackageManager              | Self version check                    |
| 11    | `PackageManager.getPackageInfo(name, 0)` → PackageInfo      | Get versionCode / versionName         |

### 2.3 AndroidUtilities.isTablet / isTabletInternal / isTabletForce

```java
public static boolean isTablet() {
    if (isTabletForce != null) return isTabletForce;
    Configuration config = ApplicationLoader.applicationContext.getResources().getConfiguration();
    return (config.screenLayout & Configuration.SCREENLAYOUT_SIZE_MASK) >= Configuration.SCREENLAYOUT_SIZE_XLARGE;
}
```

Required Android APIs:

| Order | API                                              | Used For                            |
|------:|--------------------------------------------------|-------------------------------------|
| 1     | `Context.getResources()` → Resources              | Get configuration                   |
| 2     | `Resources.getConfiguration()` → Configuration    | Read screenLayout bitfield          |
| 3     | `Configuration.screenLayout` field               | Must contain SIZE_MASK bits         |

Default for stub: `screenLayout = Configuration.SCREENLAYOUT_SIZE_NORMAL` (0x40 | 0 = 64). This makes `isTablet()` return `false`, matching the most common device.

### 2.4 AndroidUtilities.dp

```java
public static int dp(float value) {
    if (value == 0) return 0;
    return (int) Math.ceil(density * value);
}
```

Where `density` is loaded lazily:

```java
density = AndroidUtilities.density = ApplicationLoader.applicationContext
    .getResources().getDisplayMetrics().density;
```

Required Android APIs:

| Order | API                                                          | Used For                              |
|------:|--------------------------------------------------------------|---------------------------------------|
| 1     | `Context.getResources()` → Resources                         | Get display metrics                   |
| 2     | `Resources.getDisplayMetrics()` → DisplayMetrics             | Read density field                    |
| 3     | `DisplayMetrics.density` field (float, default 1.0)          | Multiplier for dp→px conversion       |

Default: `density = 1.0` (mdpi / 160 dpi).

### 2.5 AndroidUtilities.fillStatusBarHeight

```java
public static void fillStatusBarHeight(...) {
    Resources resources = ApplicationLoader.applicationContext.getResources();
    int resourceId = resources.getIdentifier("status_bar_height", "dimen", "android");
    if (resourceId > 0) {
        statusBarHeight = resources.getDimensionPixelSize(resourceId);
    }
}
```

Required Android APIs:

| Order | API                                                          | Used For                              |
|------:|--------------------------------------------------------------|---------------------------------------|
| 1     | `Context.getResources()` → Resources                         | Get resource resolver                |
| 2     | `Resources.getIdentifier("status_bar_height", "dimen", "android")` → int | Look up resource ID by name |
| 3     | `Resources.getDimensionPixelSize(id)` → int                  | Get dimension in pixels               |

Default: return `status_bar_height = 24` (px) for the standard Android resource.

### 2.6 UserConfig.isClientActivated / getInstance

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

public boolean isClientActivated() {
    return preferences.getBoolean("activated", false);
}
```

Required Android APIs:

| Order | API                                                          | Used For                              |
|------:|--------------------------------------------------------------|---------------------------------------|
| 1     | `Context.getSharedPreferences("userconfing", MODE_PRIVATE)` | Already implemented (EXP-037a)        |
| 2     | `SharedPreferences.getBoolean(key, default)` → boolean        | Already implemented                   |

### 2.7 Theme.getColor

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

`Theme.getColor` reads from `currentColors`, a `HashMap<String, Integer>` populated by `Theme.loadDefaults()`. The load happens lazily via `Theme.getCurrentColors(false)`. If the cache is null (because no theme is loaded yet), it falls back to `fallbackColors` (also a HashMap).

Required Android APIs:

| Order | API                                                          | Used For                              |
|------:|--------------------------------------------------------------|---------------------------------------|
| 1     | None direct — but `Theme.loadDefaults()` reads from Resources | Required if Theme is not pre-loaded   |

MiniAndroid approach: stub `Theme.getColor` to return a default color value (e.g. `0xFF000000` black) when the cache is empty. This unblocks UI code that calls `getColor` 6000+ times during onCreate.

### 2.8 FlagSecureReason.attach

```java
public void attach(Activity activity) {
    this.activity = activity;
    Window window = activity.getWindow();
    if (window != null) {
        window.setFlags(FLAG_SECURE, FLAG_SECURE);
    }
}
```

Required Android APIs:

| Order | API                                              | Used For                              |
|------:|--------------------------------------------------|---------------------------------------|
| 1     | `Activity.getWindow()` → Window                   | Get window for flag manipulation      |
| 2     | `Window.setFlags(int, int)`                      | Set window flag                        |

### 2.9 LaunchActivity's call chain to DynamiteModule

This comes from ML Kit language ID integration, which Telegram uses for "Automatic message translation":

```java
// In LaunchActivity.onCreate:
Translator.setContext(this);  // sets up ML Kit
// ... which triggers:
DynamiteModule.load(this, "com.google.mlkit.dynamite.language_id", ...);
// which has the while(true) loop BLOCKER-D.
```

Required Android APIs (or stubs):

| Order | API                                                          | Used For                              |
|------:|--------------------------------------------------------------|---------------------------------------|
| 1     | `Context.getApplicationContext()` → Context                | ML Kit singleton init                 |
| 2     | `DynamiteModule.load(...)` → DynamiteModule                 | Load Play Services module — must be STUBBED to throw on devices without Play Services |

---

## 3. Consolidated Priority List (Phase 4 implementation order)

Based on the above analysis, the absolute minimum Android framework that unblocks Telegram's LaunchActivity.onCreate:

### P0 — Blocks execution (MUST implement)

| Priority | API                                                          | Why                                                                   |
|---------:|--------------------------------------------------------------|-----------------------------------------------------------------------|
| P0.1     | `Activity.this` instance fields                              | Every `iget-object v0, v2, ...` reads from `this`. Today MiniAndroid leaves `this` uninitialized → all subsequent field reads return null → loops. |
| P0.2     | `Context.getResources()` → Resources singleton              | Called by `AndroidUtilities.dp`, `isTablet`, `fillStatusBarHeight` and dozens of other places. |
| P0.3     | `Resources.getDisplayMetrics()` → DisplayMetrics             | Required by `AndroidUtilities.dp`.                                   |
| P0.4     | `DisplayMetrics.density` field (float, default 1.0)          | Multiplier for dp→px conversion. Default `1.0` matches mdpi.          |
| P0.5     | `Resources.getConfiguration()` → Configuration               | Required by `AndroidUtilities.isTablet`.                              |
| P0.6     | `Configuration.screenLayout` field (int, default 0x40)       | `SCREENLAYOUT_SIZE_NORMAL`. Makes `isTablet()` return false.          |
| P0.7     | `Context.getApplicationContext()` → Context                 | Called by every singleton init (ApplicationLoader, UserConfig, etc.). |
| P0.8     | `Context.getPackageName()` → String                         | Required by version check in ApplicationLoader.                       |
| P0.9     | `Context.getPackageManager()` → PackageManager              | Required by version check.                                            |
| P0.10    | `PackageManager.getPackageInfo(name, 0)` → PackageInfo       | Required by version check.                                            |
| P0.11    | `PackageInfo.versionCode` / `versionName` fields             | Required by version check.                                            |
| P0.12    | `Context.getSharedPreferences(name, mode)` → SharedPreferences | Already implemented (EXP-037a). Wire into Context.                  |
| P0.13    | `Context.getFilesDir()` → File                              | Required by ApplicationLoader for cache dir.                          |

### P1 — Allows deeper startup (SHOULD implement)

| Priority | API                                                          | Why                                                                   |
|---------:|--------------------------------------------------------------|-----------------------------------------------------------------------|
| P1.1     | `Activity.getWindow()` → Window                              | Required by FlagSecureReason.attach and decor-view setup.            |
| P1.2     | `Window.setFlags(int, int)`                                  | Required by FlagSecureReason.attach.                                  |
| P1.3     | `Window.getDecorView()` → View                              | Required for content-view setup.                                       |
| P1.4     | `Resources.getIdentifier(name, type, pkg)` → int             | Required by `fillStatusBarHeight`.                                    |
| P1.5     | `Resources.getDimensionPixelSize(id)` → int                  | Required by `fillStatusBarHeight`.                                    |
| P1.6     | `Context.getSystemService(CONNECTIVITY_SERVICE)`             | Network info (not critical for first frame).                          |
| P1.7     | `Context.getExternalFilesDir(null)` → File                   | External cache dir (not critical for first frame).                   |
| P1.8     | `Context.getMainLooper()` → Looper                           | Required by ApplicationLoader for Handler construction.              |
| P1.9     | `new Handler(Looper)`                                        | Required by ApplicationLoader.                                         |

### P2 — Only UI/rendering (DEFER)

| Priority | API                                                          | Why                                                                   |
|---------:|--------------------------------------------------------------|-----------------------------------------------------------------------|
| P2.1     | `LayoutInflater.inflate(int, ViewGroup)` → View              | Layout rendering — Phase 5+.                                          |
| P2.2     | `View.findViewById(int)` → View                              | View binding — Phase 5+.                                              |
| P2.3     | `TextView.setText(CharSequence)`                            | UI rendering — Phase 5+.                                              |
| P2.4     | `WindowManager.getDefaultDisplay()` → Display                 | UI rendering — Phase 5+.                                              |
| P2.5     | `Display.getMetrics(DisplayMetrics)`                         | UI rendering — Phase 5+.                                              |

### Stub-only APIs (NO real impl needed)

| API                                                          | Why                                                                   |
|--------------------------------------------------------------|-----------------------------------------------------------------------|
| `DynamiteModule.load(Context, String, int)`                  | Throw `LoadingException` immediately. Matches devices without Play Services. |
| `DynamiteModule.instantiate(Context, String, DynamiteModule)` | Catch the exception, return null.                                     |
| `Theme.getColor(String)` (when `currentColors == null`)       | Return `0xFF000000` (black) as default.                                |
| `Context.getSystemService(Context.NOTIFICATION_SERVICE)`     | Return null — Telegram handles null gracefully.                        |
| `Context.getSystemService(Context.ALARM_SERVICE)`            | Return null.                                                          |

---

## 4. Difference from Real Android

These are the **deliberate simplifications** we will make in Phase 4, with the rationale:

| Simplification                                   | Real Android                          | MiniAndroid                            | Rationale                                                |
|--------------------------------------------------|---------------------------------------|----------------------------------------|----------------------------------------------------------|
| DisplayMetrics.density                           | Read from system resources            | Hardcoded 1.0                          | Default matches mdpi; sufficient for `dp(N)` to work.    |
| Configuration.screenLayout                       | Read from system WindowManager        | Hardcoded SIZE_NORMAL (0x40)           | Makes `isTablet()` deterministically return false.       |
| Resources.getIdentifier                          | Searches the resource table           | Returns 0 (resource not found)         | `fillStatusBarHeight` then falls back to default 24px.   |
| PackageInfo.versionCode                          | Read from APK manifest                | Hardcoded 9999                         | Lets version-check branches pass.                        |
| DynamiteModule.load                              | Loads Play Services module            | Throws LoadingException                | Matches devices without Play Services; Telegram has fallback. |
| Handler.<init>                                   | Binds to Looper's MessageQueue        | Stores Looper ref, no actual queue     | Sufficient for `Handler.post(Runnable)` to be a no-op.   |

---

## 5. Phase 4 Implementation Order

Concrete implementation sequence:

1. **`MiniandroidContext` class** — implements `Context`. Holds `Resources`,
   `PackageManager`, `SharedPreferences` factory, `File` paths.
   Real C++ object backed by a heap ID.

2. **`MiniandroidResources` class** — implements `Resources`. Holds
   `DisplayMetrics` and `Configuration` singletons with sensible defaults.

3. **`MiniandroidDisplayMetrics` class** — has `density=1.0`, `densityDpi=160`,
   `widthPixels=1080`, `heightPixels=1920`.

4. **`MiniandroidConfiguration` class** — has `screenLayout=0x40`,
   `orientation=ORIENTATION_PORTRAIT`, `locale=en_US`.

5. **`MiniandroidPackageManager` class** — returns a `PackageInfo` with
   `versionCode=9999`, `versionName="9.9.9"`.

6. **`MiniandroidWindow` class** — has `setFlags(int, int)` no-op,
   `getDecorView()` returns null.

7. **Bridge integration** — when `bridge_to_api` sees a method on a known
   Android class, dispatch to the appropriate `Miniandroid*` object.
   Critical: `Activity.this` must be backed by a `MiniandroidContext`-
   typed heap object so `iget-object` on `mContext` returns the real
   Context.

8. **`DynamiteModule.load` stub** — special-case in the bridge to throw.

9. **`Theme.getColor` stub** — special-case in the bridge to return `0xFF000000`
   when called with no currentColors cache.

---

## 6. Success Criteria for Phase 4

After Phase 4:

* `LaunchActivity.onCreate` reaches `setContentView` without hitting any
  loop detector.
* Memory stays bounded (< 500 MB).
* Instruction count exceeds 5 M (we are currently at ~1 M after Phase 2).
* The execution path no longer halts at `DynamiteModule.load`.
