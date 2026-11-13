# S156-T4 — Thunderbird (net.thunderbird.android_33) five-stage frontier

Engine: S155 main rebuild `35cd06374f3c457b` (reproduces all 7 available
anchor pins byte-exact — see BASELINE_WALL.json). APK pin `473b33da5963d0a4`
(sha256 473b33da5963d0a4…, vc=33, v24.0, minSdk 23, targetSdk 36, 2 dexes,
main `net.thunderbird.app.common.MainActivity`, app class
`net.thunderbird.android.ThunderbirdApp`, androguard-verified).

## Stage 1 — PIN (PIN_LEDGER.json)

sha16 `473b33da5963d0a4`, zip magic OK, 2 dexes, markers: koin=38 refs,
compose=2446, kotlin=293. F-Droid canonical APK, byte-exact.

## Stage 2 — androguard profile (PROFILE.json + TB_KOIN_XREF.json)

Families: compose/ui=999, compose/foundation=703, compose/material=325,
coroutines=311, appcompat=253, glide=252, material=213, work=191, okhttp=172,
navigation=128, fragment=78. Application class `ThunderbirdApp`.

XREF (androguard disassembly, decisive):
- `ThunderbirdApp.attachBaseContext` IS the startKoin site — R8 inlined it:
  pc=38 `KoinApplication.<init>` → pc=60 `DI$$ExternalSyntheticLambda0.invoke`
  (module DSL) → pc=70 `Koin.createEagerInstances()`.
- `okhttp3/CacheControl$Companion;.get$default` is an R8 horizontal-merge
  artifact: `Reflection.getOrCreateKotlinClass` → `Scope.get(...)` — i.e. the
  app-wide `getKoin().get<T>()` helper.
- `androidx.startup.InitializationProvider` carries exactly 4 initializers
  (emoji2 / process-lifecycle / profileinstaller / okhttp platform) — NO Koin
  initializer; Koin start is solely the attachBaseContext path.

## Stage 3 — BOOT (BOOT_thunderbird.json, console in run/s156_4app/)

12/12 frames, wall 3.7 s, verdict DEFAULT_BACKGROUND_ONLY, face
`b270ff040b3601dc`, 38 uncaught, 1 NPE row, zero NDFE/CNFE. The UI pipeline
works deep (AppCompat decor inflation, ContentFrameLayout hierarchy,
[F-NEW-175] obtainStyledAttributes theme-backed, FitWindowsFrameLayout
findViewById FOUND) — the frame is chrome-only because app content never
composes.

## Stage 4 — ROOT CAUSE (console-evidenced, full chain)

1. `ThunderbirdApp.attachBaseContext` runs the inlined startKoin: module DSL
   bodies EXECUTE — 463 `Module.indexPrimaryType` puts observed
   ([F527-HMAP]/[F089-MAP] rows, keys like
   `net.thunderbird.core.featureflag…::_root_`), LoggerModuleKt.<clinit> OK.
2. `Koin.createEagerInstances()` (pc=70) → `Scope.resolveFromContext`
   throws `NoDefinitionFoundException` for **net.thunderbird.core.logging.Logger**
   (name-derivation rows R347/STR right before the throw; the Logger family
   Logger/Log/LogSink never appears among the indexed primary keys).
3. The abort kills attachBaseContext BEFORE `GlobalContext._koin` is stored —
   console `SGET GlobalContext;._koin → obj_id=0` everywhere after.
4. CASCADE (all evidenced): `IllegalStateException "KoinApplication has not
   been started"` from the R8-merged `get$default` helper inside
   `DecryptedFileProvider.<clinit>` / `AttachmentTempFileProvider.<clinit>`
   (content-provider boot), `ThunderbirdApp.attachBaseContext` inject,
   `BaseActivity.attachBaseContext`, `BaseApplication.onCreate`
   (NoDefinitionFoundException rows) → DI-empty app → chrome-only frame.

Root-cause registry entry: **F-NEW-485** (Koin eager-instance registry
divergence) — engine law candidate: definitions declared through the
binds/default-arg bridge family (`$inlined$singleListOf$default$1`,
`single$default`) must land in the SAME registry surface that
`Scope.resolveFromContext` consults. Next lever: trace the engine's
LinkedHashMap shadow across the module-map → registry merge
(put rows land on 6+ distinct map objects; the merge step is silent).

## Stage 5 — VERDICT

BLOCKED-with-root-cause. The blocker is NOT a TB bug: real Android resolves
`Logger` because its definition is registered; the engine drops exactly that
declaration family from the consulted registry. Fix queued as F-NEW-485
(S157 frontier). Engine-side conscrypt dlopen boundary fixed in the same
wave (bionic FORTIFY anchors — see S156_T5 evidence) so the native-lib layer
no longer masks the DI layer.

---
**S226 re-census (a4516511, S225-M):** the NDFE + `_koin` SGET-MISS still
reproduce LIVE (6 NDFE rows in run/s226_transfer/thunderbird.console.log) but
the downstream "KoinApplication has not been started" cascade is absorbed by
the S156→S225 mainline laws — face moved b270ff04→43bfdac6, uncaught 38→9.
Status: F-NEW-485 LIVE-REDUCED; the registry-merge lever stays open.
