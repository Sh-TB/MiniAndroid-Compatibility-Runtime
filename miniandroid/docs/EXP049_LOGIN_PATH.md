# EXP-049 Login Path Discovery

**Date:** 2026-08-17

## Current Execution State

LaunchActivity.onCreate completes successfully with 200 unique methods.
The execution reaches deep into Telegram's startup:

```
LaunchActivity.onCreate (1330 insns)
├── ApplicationLoader.postInitApplication (266 insns)
│   ├── NativeLoader.initNativeLibs (234 insns)
│   │   └── System.loadLibrary("tmessages.49") [STUBBED]
│   ├── LocaleController.getInstance
│   ├── SharedConfig.loadConfig (1278 insns)
│   │   └── SharedPreferences.getBoolean × 68
│   │   └── SharedPreferences.getInt × 36
│   │   └── SharedPreferences.getString × 8
│   │   └── SharedPreferences.getLong × 8
│   ├── SharedPrefsHelper.init
│   ├── UserConfig.getInstance
│   ├── UserConfig.loadConfig (492 insns)
│   ├── MessagesController.getInstance
│   ├── ConnectionsManager.getInstance
│   │   └── native_getCurrentTime [JNI STUB] × 5
│   ├── SendMessagesHelper.getInstance
│   │   └── checkUnsentMessages
│   ├── ContactsController.getInstance
│   │   └── checkAppAccount
│   ├── DownloadController.getInstance
│   └── BillingController.startConnection
├── Theme.reloadAllResources → createCommonResources → createChatResources
│   └── RLottieDrawable initialization
└── ComponentActivity.onCreate → FragmentActivity.onCreate → Fragment lifecycle
```

## Login Decision Point

In LaunchActivity.onCreate, after ApplicationLoader.postInitApplication returns,
the code checks `UserConfig.isClientActivated()`:

```java
if (UserConfig.getInstance().isClientActivated()) {
    // Show main UI
} else {
    // Show LoginActivity or IntroActivity
}
```

### UserConfig.isClientActivated()

This method reads `SharedPreferences.getBoolean("activated", false)`.
Since our SharedPreferences returns `false` for `activated` (no persisted
state yet), the code should take the LOGIN path, not the main UI path.

### Current Behavior

`UserConfig.isClientActivated` IS reached (bytecode_size=15, METHOD-IN logged).
It calls `SharedPreferences.getBoolean("activated", false)` which returns `false`
(our SharedPreferences returns defaults).

The execution then continues to check which Activity to show.
However, `LaunchActivity.onCreate` completes (SUCCESS) without reaching
LoginActivity or IntroActivity. This means the login path code exists
within onCreate but either:

1. The branch is taken but the code to show LoginActivity is stubbed
2. The branch is not taken because isClientActivated returns wrong value
3. The code to switch to LoginActivity is beyond the 1330 instructions

## Static Analysis: Login-Related Classes

### LoginActivity
- Exists in classes4.dex
- Would be reached via `Intent` or `Activity.startActivity`
- Requires real `Intent` and `Activity` framework support

### IntroActivity
- Would be shown on first launch
- Requires View hierarchy and animation support

### What Would Need to Happen

For Login UI to be reached:
1. `UserConfig.isClientActivated()` must return `false` ✓ (already does)
2. The code must check this and decide to show login
3. A new Activity (LoginActivity) must be started
4. LoginActivity.onCreate must execute
5. Login Views must be created

### Current Blockers for Login Path

1. **Activity.startActivity** — not implemented. LaunchActivity can't
   start LoginActivity.
2. **Intent** — not implemented. Can't pass data between Activities.
3. **View hierarchy** — not implemented. LoginActivity would need to
   create Views.
4. **setContentView** — currently returns void. Would need to track
   the View hierarchy.
5. **FragmentManager** — partially stubbed. Fragment-based UIs won't work.

## SharedPreferences Write Path

### SharedConfig.saveConfig

This method IS in the DEX with 402 instructions and calls:
- `Context.getSharedPreferences` (creates/loads prefs object)
- `SharedPreferences.edit()` (returns Editor)
- `Editor.putBoolean()` × many
- `Editor.putString()` × many
- `Editor.putInt()` × many
- `Editor.putLong()` × many
- `Editor.apply()` ← THIS IS THE PERSISTENCE CALL

### Callers of SharedConfig.saveConfig

Static analysis found these callers on the startup path:
- `AppStartReceiver.lambda$onReceive$0` — not on startup path
- `FileRefController` — not on startup path
- `MediaController` — not reached yet
- `PushListenerController` — not reached yet
- `SendMessagesHelper` — reached but saveConfig not called
- `SharedConfig.checkPasscode` — not reached
- `SharedConfig.setNewAppVersionAvailable` — not reached
- `UserConfig.lambda$saveConfig$0` — called by UserConfig.saveConfig

### UserConfig.saveConfig Callers

None of the callers of UserConfig.saveConfig are on the current execution
path. They all require:
- Network responses (processLoadedDialogs, loadContacts)
- Media operations (prepareSendingMedia, finishRecordingVideo)
- Push registration
- Stories operations

### Conclusion

The SharedPreferences WRITE path exists in the DEX but is NOT reached
during the current execution because:
1. `SharedConfig.saveConfig` is only called when config changes occur
2. `UserConfig.saveConfig` is only called after network responses
3. The current execution path reads config (loadConfig) but doesn't
   modify it, so saveConfig is never triggered

### Next Steps for Persistence

To prove persistence, we need to either:
1. **Reach a code path that calls saveConfig** — requires network/UI
2. **Create a test that directly exercises the SharedPreferences write path**
   — write a small test APK that calls edit().putString().commit()
3. **Modify SharedConfig.loadConfig to trigger saveConfig** — e.g., by
   making it detect a config migration needed

Option 2 (test APK) is the most practical for proving persistence works.
