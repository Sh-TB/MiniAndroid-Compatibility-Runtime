# EXP-043 — Stub Debt Register

**Rule: NO BLIND STUBS.** Every stub must be documented here with STUB-ID, class, method, reason, real Android behavior, current fake behavior, and future implementation plan.

---

## Active Stubs

### STUB-001: DynamiteModule.load

| Field | Value |
|-------|-------|
| STUB-ID | STUB-001 |
| Class | `Lcom/google/android/gms/dynamite/DynamiteModule;` |
| Method | `load(Landroid/content/Context;Ljava/lang/String;I)Lcom/google/android/gms/dynamite/DynamiteModule;` |
| Reason | Real Android busy-waits on Play Services IPC (the bytecode has `while(true){}` at PC=775). MiniAndroid has no IPC, so this would loop forever. |
| Real Android behavior | Loads a Google Play Services module via IPC. Throws `LoadingException` on devices without Play Services. |
| Current fake behavior | Returns null immediately via `try_recursive_invoke` stub-only check. Caller (`instantiate`) catches the null and returns null. |
| Future implementation plan | Implement `LoadingException` throwing semantics in the bridge so callers can catch it properly. Or implement a stub Play Services module loader that returns a fake module. |

### STUB-002: Theme.getColor (default color)

| Field | Value |
|-------|-------|
| STUB-ID | STUB-002 |
| Class | `Lorg/telegram/ui/ActionBar/Theme;` |
| Method | `getColor(Ljava/lang/String;)I` |
| Reason | Real Android reads from `currentColors` HashMap populated by `loadDefaults()`. The HashMap is null because no theme is loaded yet, so `getColor` falls back to `fallbackColors`. MiniAndroid has no resource loading. |
| Real Android behavior | Returns the ARGB color value for the given key, or a fallback default. |
| Current fake behavior | Returns `0xFF000000` (black) for all keys. |
| Future implementation plan | Implement `Theme.loadDefaults()` which reads from `Resources` and populates `currentColors`. Requires resource table parsing (EXP-006 partial). |

### STUB-003: Context.getSystemService (returns null)

| Field | Value |
|-------|-------|
| STUB-ID | STUB-003 |
| Class | `Landroid/content/Context;` |
| Method | `getSystemService(Ljava/lang/String;)Ljava/lang/Object;` |
| Reason | Real Android returns system service singletons (ConnectivityManager, WindowManager, etc.). MiniAndroid has no system services. |
| Real Android behavior | Returns the appropriate singleton for the service name, or null if not found. |
| Current fake behavior | Returns null for all service names. Telegram handles null gracefully in most paths. |
| Future implementation plan | Implement stub system services: ConnectivityManager (returns offline state), WindowManager (returns default display), NotificationManager (no-op). |

### STUB-004: Resources.getIdentifier (returns 0)

| Field | Value |
|-------|-------|
| STUB-ID | STUB-004 |
| Class | `Landroid/content/res/Resources;` |
| Method | `getIdentifier(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)I` |
| Reason | Real Android searches the resource table by name. MiniAndroid has no resource table. |
| Real Android behavior | Returns the resource ID for the given name/type/package, or 0 if not found. |
| Current fake behavior | Returns 0 for all queries. Telegram's `fillStatusBarHeight` falls back to default 24px. |
| Future implementation plan | Implement resource table parsing from APK's `resources.arsc`. |

### STUB-005: Resources.getDimensionPixelSize (returns 24)

| Field | Value |
|-------|-------|
| STUB-ID | STUB-005 |
| Class | `Landroid/content/res/Resources;` |
| Method | `getDimensionPixelSize(I)I` |
| Reason | Real Android reads from resource table. MiniAndroid has no resource table. |
| Real Android behavior | Returns the pixel size for the given dimension resource ID. |
| Current fake behavior | Returns 24 for all resource IDs. Matches default `status_bar_height`. |
| Future implementation plan | Requires resource table parsing. |

### STUB-006: Window.setFlags (no-op)

| Field | Value |
|-------|-------|
| STUB-ID | STUB-006 |
| Class | `Landroid/view/Window;` |
| Method | `setFlags(II)V` |
| Reason | Real Android sets window flags (e.g. FLAG_SECURE). MiniAndroid has no window manager. |
| Real Android behavior | Sets the specified window flags. |
| Current fake behavior | No-op. |
| Future implementation plan | Implement a stub Window object that tracks flag state for diagnostic purposes. No rendering needed. |

---

## Resolved Stubs (moved to real implementation)

(none yet)

---

## Stub Debt Summary

| Count | Description |
|-------|-------------|
| 6 | Active stubs |
| 0 | Resolved stubs |
| 0 | Blind stubs (undocumented) |

All stubs are documented. No blind stubs.
