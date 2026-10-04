# #373 ENVIRONMENT/PREREQUISITE MATRIX — IMPLEMENTED+TESTED (commit 58b5c14e, binary 4c01757e8f11c8a0)

## The 15 final questions (§15) — answered with evidence

1. **API level**: 34 / "14" (seed_framework_device_statics; EXT-01 branch evidence).
2. **Device profile**: MiniAndroid/miniandroid/miniandroid:14 (fingerprint `MiniAndroid/miniandroid/miniandroid:14/MINI.20260905/0:userdebug/test-keys`), deterministic ANDROID_ID.
3. **CPU architecture actually executed**: x86_64 host.
4. **Honestly supported ABIs**: executable = [x86_64]; advertised = [arm64-v8a, armeabi-v7a, armeabi] with the mismatch now EXPLICIT (ENV-005).
5. **Can ARM-only APKs run?** NO — proven live: com.yepgoryo.EggReturnsHome (arm64-only libgodot.so) installs rc=0 then stops DEFAULT_BACKGROUND_ONLY with 0 app draw ops.
6. **Blocker layer**: CPU translation (no native bridge), NOT linker/loader — the S-2 dlopen/JNI_OnLoad layer works for x86_64 (NATX 10/10 ×3, fib=610). Dual cause on Godot class: arm64 lib + Fragment materialization frontier.
7. **Reasonable target range**: minSdk ≤ 34 corpus-compatible; per-APK minSdk/targetSdk served machine-readably.
8. **Version-specific laws missing**: none newly implicated this wave; per-APK `environmentMismatches[]` reports them.
9. **Hardware emulated**: touchscreen (real input pipeline), accelerometer/wifi EMULATED-DEFAULT.
10. **Hardware absent (truthful)**: camera, GPS, telephony, bluetooth, NFC, microphone, compass.
11. **System services available**: PM/AM/WM surfaces, ActiveServices started-vs-bound, broadcasts (SVC-01..04/BCAST-01..04), ContentResolver/provider dispatch, SQLite, notifications surface.
12. **Graphics**: PortableGL software GLES2 facade (JSR-239 EGL), 1080×1920 RGBA; NO Vulkan.
13. **Media**: PNG/JPEG/GIF(replay)/WebP/MP3/WAV decoders; no MediaCodec API surface.
14. **Agent pre-flight**: YES — `pkginspect --apk <p> --what prerequisites` (#373 §12 API-001..005 schema: minSdk/targetSdk/features/permissions/abis/ELF machines/webview/nativeAbiVerdict/environmentMismatches/missingCapabilities/recommendedNextProbe).
15. **50-title env-vs-runtime split**: docs/EXECUTION_LEVEL_MATRIX.jsonl + docs/WS_PREREQUISITE_AUDIT.md — environment-caused 2/8 classified white faces (ARM-only, Vulkan); the rest are ordinary runtime roots with prereq-clean profiles.

## Artifacts

- `docs/ENVIRONMENT_PROFILE.json` (ENV-001..010, profile sha16 56e6347116942bfc, ENV-010 immutable stamp)
- `docs/ENV_PREREQUISITE_MATRIX.jsonl` (30 corpus APKs: 16 NO_NATIVE / 10 EXECUTABLE_NATIVE / 2 ABI_MISMATCH)
- `docs/WS_PREREQUISITE_AUDIT.md/.jsonl` (WS-001/WS-002)
- R-NEW-465 in root_registry.json (IMPLEMENTED+TESTED)
- CPU translation classified F EXTERNAL/FUTURE boundary, quantified (2/30 corpus APKs blocked) — reused-OSS research remains a pre-implementation requirement per §5.

Machine-readable profile answer to the §14 DoD question is served per-APK by the prerequisites section (require → provide → missing → generic-suppliable? → env-or-runtime divergence).
