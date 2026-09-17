# s52_asc — ASC reconnaissance evidence cards (compact, reproducible)

Tool provenance: Droid ASC (**MG1937/ASC**) `droidasc` 0.1.1.post1, source
commit `3279d9dd6ffb9c844f8599bd2bf69a13bb602480`, installed into a gitignored
local venv (`local/ASC/venv`). ASC output is NEVER committed; these cards carry
only the distilled, reproducible results. Every card lists the exact command to
re-derive it.

## Card 1 — Telegram v12 startup path (recon for the 540 s init frontier)

```bash
droidasc getmanifest  Telegram-official-current.apk   # 0.32 s on 73,028,244 B APK
droidasc getclass     Telegram-official-current.apk org.telegram.messenger.ApplicationLoader
droidasc getclass     Telegram-official-current.apk org.telegram.messenger.ApplicationLoaderImpl
droidasc findrefs     Telegram-official-current.apk type Landroidx/arch/core/internal/SafeIterableMap;
```

APK SHA256 `f5e1192725772960cc94b83e54ffd8939f876b2b6e5f21d4a8537eb6fcba50e6`
(registry "Telegram v12").

Facts (distilled):
- Manifest application = `org.telegram.messenger.ApplicationLoaderImpl`;
  MAIN entry = `org.telegram.ui.LaunchActivity` (+ 6 launcher icon aliases).
- `ApplicationLoader.onCreate` startup chain (decompiled, 799-line class):
  static `applicationContext` → `getSystemService("connectivity")` →
  `getFilesDir()` / `ApplicationInfo.dataDir/files` → `registerReceiver`
  (`CONNECTIVITY_CHANGE`, `ScreenReceiver`) → `NativeLoader.initNativeLibs(...)`
  → `SharedConfig.loadConfig()` → `SharedPrefsHelper.init(...)` → push path
  sets `__NO_GOOGLE_PLAY_SERVICES__` → `ILocationServiceProvider.init` /
  mapsProvider.
- `SafeIterableMap` consumers = `androidx.lifecycle.LiveData.<init>` and
  `androidx.savedstate.SavedStateRegistry.<init>` — consistent with the S51
  runtime observation (SafeIterableMap cycle-stub ≥18k calls during init).

Root-cause targets ranked for the 540 s init: (1) REC-MISS surface along the
ApplicationLoader static-init chain (400 REC-MISS observed); (2) SafeIterableMap
iterator law; (3) NativeLoader boundary (stub vs skip decision — engine has no
native .so loader).

## Card 2 — Dooz v18 `Lh/r;` = androidx.collection ScatterMap.set (R-NEW-361)

```bash
droidasc getclass io.github.yamin8000.dooz_18.apk 'Lh/r;'
# APK SHA256 d81292cd346dcb23b04488bca400ca95af0f6eaa4aefefd31f847fe535cbdc17
```

Runtime signature being investigated (reproduced at HEAD `1b37afd1`):
`[HALT-LOOP] Lh/r;.c PC=0x1c 50001 visits` + `aput-oob index=613985991
LP/v$a;.c pc=28`.

Distilled structure of `c(Object)` (set/put path) — the four engine-law
candidates the decompile pins down:

1. **Growth-metadata sentinel writes** in `d(int)`: `long` array byte-slot
   writes `255 << ((cap & 7) << 3)` with `shl-long/and-long/or-long` — wrong
   64-bit shift-amount masking poisons the empty-sentinel the probe loop scans
   for (same law family as the S38 shift-law fixture / R-NEW-335).
2. **Probe wrap**: `idx = (idx + stride) & capacityMask` — stride grows
   `+8` per group; a wrong `and-int` (negative mask handling) or a corrupted
   capacity field makes the index grow unbounded → the observed 613,985,991
   aput index.
3. **`Long.numberOfTrailingZeros`** slot resolution — wrong tz ⇒ wrong slot ⇒
   loop never terminates on a match.
4. **`h.x.c(p10)` capacity normalization** (`Math.max(7, c(p10))`) — wrong
   `numberOfLeadingZeros` law ⇒ capacity/mask pair broken from the start.

Next action: law-probe fixture driving ScatterMap.set across a capacity growth
boundary with hardcoded expected metadata longs (JVM-cross-checked), one
candidate at a time.

## Card 3 — WhatsApp BLOCKED made provable

`local cache real_apps/WhatsApp.apk` = **0 bytes**, SHA256
`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` (SHA256 of
the empty string). Same for local `Signal.apk`. Verdict stays
`BLOCKED — APK unavailable`; no runtime claims.
