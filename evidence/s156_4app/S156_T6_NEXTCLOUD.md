# S156-T6 — Nextcloud (com.nextcloud.client_350000290) five-stage frontier

Engine chain: S155 rebuild `35cd06374f3c457b` → S156 anchor law
`a9b58de1d4e56f01`. APK pin `c9ba2e85b13fee45`, vc=350000290, v35.0.2,
minSdk 28, targetSdk 36, 7 dexes, main
`com.nmc.android.ui.LauncherActivity`, app class
`com.owncloud.android.MainApp` (androguard-verified).

## Stage 1 — PIN

sha16 `c9ba2e85b13fee45`, zip magic OK, 7 dexes. Heaviest Compose of the
four (compose/ui=7617, foundation=5378, material=3676, runtime=2983).

## Stage 2 — androguard profile

Families: compose/ui=7617, coroutines=1956, material(google)=1586, okhttp=871,
glide=816, work=794, lifecycle=596, appcompat=558, fragment=324, gson=261.
org.apache.http.legacy + window extensions libs present.

## Stage 3 — BOOT (both engines)

0 frames, process death at wall 2.2 s. Pre-anchor engine: same signature.
[S100-CRASH-FORENSICS]: SIGABRT — #5 `libconscrypt_jni.so` modoff=0x10186e,
reached through `okhttp3/internal/platform/android/Android10SocketAdapter$Companion.buildIfSupported`
→ `Conscrypt.<clinit>` (OK) → `NativeCryptoJni.init` (REC-MISS
`Class.getPackage` right before the abort).

## Stage 4 — ROOT CAUSE

Two-layer frontier:
1. dlopen boundary — SOLVED by the S156 anchor law (F-NEW-484): the symbol
   table now resolves; `NativeCryptoJni.init` RUNS (this is the progression
   from the pre-anchor state where the load itself failed).
2. **F-NEW-487 (pinned, next lever): conscrypt native-init abort.**
   `libconscrypt_jni.so` abort()s inside its own init at modoff=0x10186e —
   the JNI registration surface (JNI_OnLoad/RegisterNatives/env function
   table) is the missing engine capability. Honest verdict kept: a native
   abort during library init is process death; masking it as a Java
   exception would fabricate a success signal.

## Stage 5 — VERDICT

BLOCKED (native TLS-init frontier, evidence-complete). L0 true, L1 false
(process dies before executing app runtime). Next lever: engine JNI
registration surface for app-native JNI_OnLoad (F-NEW-487), then okhttp
falls back to the platform default exactly as Tusky's post-fix boot
demonstrates.

---
**S226 re-census (a4516511, S225-M):** the native TLS-init abort is GONE —
Nextcloud renders its FIRST FRAME (face b5a7a35d5fe0564b, verdict
SAFE+DEFAULT_BACKGROUND_ONLY, 20 residual uncaught) where the S155 lineage
died at 0 frames. Status: F-NEW-487 RESOLVED-BY-MAINLINE (verified live).
