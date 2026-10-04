# ANDROID ENVIRONMENT COMPATIBILITY MATRIX — OS / API / CPU / ABI / HARDWARE / SOFTWARE PREREQUISITES

## Mission
This is the generic environment/prerequisite campaign to run with #364–#372.

Central question:
When an APK fails, is MiniAndroid missing an Android semantic/runtime capability, or is the APK asking for an Android OS/API level, ABI/CPU, native library, system service, graphics/media capability, permission, provider, device configuration, or hardware feature that the current environment does not provide?

Do not guess. Build a machine-readable prerequisite model and prove it against real APKs.

Do not use prerequisites as an excuse to declare apps unsupported. First determine whether the capability is already present, can be supplied generically, can be reused from OSS, or is a genuine external boundary.

## 0 — READ THE WHOLE CAMPAIGN FIRST

Read and reconcile:
#364, #365, #366, #367, #368, #369, #370, #371, #372, current root registry/worklist/capability registry, Constitution/runtime laws, current HEAD and worklog.

Do not create duplicate roots.

Every finding must be classified:
A DUPLICATE
B SAME ROOT / NEW EVIDENCE
C NEW SUB-LAW
D NEW ROOT
E NOT APPLICABLE
F EXTERNAL/FUTURE BOUNDARY.

Only C/D may create new runtime work.

## 1 — DEFINE MINANDROID'S DEFAULT DEVICE

[ ] ENV-001 — Explicitly define default Android API level/version.
[ ] ENV-002 — Define default device/model/product/board profile.
[ ] ENV-003 — Define screen width/height/density/orientation/refresh rate.
[ ] ENV-004 — Define RAM/storage characteristics.
[ ] ENV-005 — Define CPU architecture and supported ABIs.
[ ] ENV-006 — Define GPU/graphics backend/OpenGL ES/Vulkan capabilities.
[ ] ENV-007 — Define codec/media capabilities.
[ ] ENV-008 — Define camera/sensor/network/telephony/touch capabilities.
[ ] ENV-009 — Expose the complete profile machine-readably.
[ ] ENV-010 — Record immutable environment profile SHA/version for every test.

If any default is currently implicit or unknown, treat that as a foundation gap and fix/document it.

## 2 — APK PREREQUISITE EXTRACTION

For representative APKs:

[ ] APK-001 minSdkVersion
[ ] APK-002 targetSdkVersion
[ ] APK-003 maxSdkVersion
[ ] APK-004 uses-sdk compatibility
[ ] APK-005 requested permissions
[ ] APK-006 dangerous/runtime permissions
[ ] APK-007 required/optional features
[ ] APK-008 OpenGL ES/Vulkan requirements
[ ] APK-009 native ABIs
[ ] APK-010 native libraries
[ ] APK-011 DT_NEEDED closure
[ ] APK-012 JNI requirements
[ ] APK-013 activities/services/receivers/providers
[ ] APK-014 metadata
[ ] APK-015 resource configurations/qualifiers
[ ] APK-016 density/locale/orientation requirements
[ ] APK-017 WebView requirement
[ ] APK-018 media/codec requirements
[ ] APK-019 database/storage requirements
[ ] APK-020 external storage requirements

No APK may be labelled simply "runtime bug" before this preflight exists.

## 3 — ANDROID VERSION / API MATRIX

[ ] OS-001 API-level compatibility
[ ] OS-002 API introduced after default level
[ ] OS-003 removed/deprecated behavior
[ ] OS-004 targetSdk behavior changes
[ ] OS-005 permission behavior by targetSdk
[ ] OS-006 scoped storage
[ ] OS-007 background execution
[ ] OS-008 notifications
[ ] OS-009 foreground services
[ ] OS-010 exported component rules
[ ] OS-011 PendingIntent semantics
[ ] OS-012 receiver restrictions
[ ] OS-013 File URI restrictions
[ ] OS-014 network/security behavior
[ ] OS-015 WebView behavior
[ ] OS-016 graphics behavior
[ ] OS-017 media behavior
[ ] OS-018 resources/configuration
[ ] OS-019 lifecycle/component behavior

Do not implement every Android release independently. Identify the minimum semantic compatibility layer covering multiple API levels.

## 4 — CPU / ABI / NATIVE MATRIX

[ ] CPU-001 — x86_64 native baseline explicitly defined.
[ ] CPU-002 — x86 native APK support tested.
[ ] CPU-003 — ARM32 native APK support tested.
[ ] CPU-004 — ARM64 native APK support tested.
[ ] CPU-005 — ABI advertisement equals actual execution/translation capability.
[ ] CPU-006 — ABI selection semantics verified.
[ ] CPU-007 — native bridge availability verified.
[ ] CPU-008 — native bridge version/API compatibility verified.
[ ] CPU-009 — linker namespace/path semantics verified.
[ ] CPU-010 — DT_NEEDED dependency closure verified.
[ ] CPU-011 — symbol/relocation compatibility verified.
[ ] CPU-012 — TLS/thread-local storage verified.
[ ] CPU-013 — atomics verified.
[ ] CPU-014 — syscall boundary classified.
[ ] CPU-015 — signal semantics classified.
[ ] CPU-016 — pthread behavior verified.
[ ] CPU-017 — executable ELF requirements classified.
[ ] CPU-018 — JNI ABI verified.
[ ] CPU-019 — native constructors verified.
[ ] CPU-020 — JNI_OnLoad verified.
[ ] CPU-021 — native-created threads verified.
[ ] CPU-022 — ARM-only APK behavior proven.
[ ] CPU-023 — multi-ABI APK behavior proven.
[ ] CPU-024 — no-compatible-ABI behavior is explicit and truthful.

## 5 — SHOULD WE EMULATE THE CPU?

[ ] CPU-025 — Classify each native failure: Java/DEX, JNI, native library, native executable, JIT/runtime, graphics backend, external process.
[ ] CPU-026 — Research reusable local/open-source CPU/native-translation options.
[ ] CPU-027 — Compare CPU/RAM cost on the 16 GB CPU-only environment.
[ ] CPU-028 — Determine whether full CPU emulation is actually required.
[ ] CPU-029 — Define layered strategy: native execution → translation → honest unsupported boundary.

Investigate relevant reusable technologies such as QEMU user-mode, Dynarmic/Unicorn where appropriate, Android native bridge projects, emulator/translation work, ELF/linker compatibility, and existing MiniAndroid-compatible source.

Do not implement a full CPU emulator unless evidence proves it is the highest-fanout generic blocker.

## 6 — HARDWARE FEATURE MATRIX

[ ] HW-001 camera
[ ] HW-002 autofocus/flash
[ ] HW-003 microphone
[ ] HW-004 GPS/location
[ ] HW-005 accelerometer
[ ] HW-006 gyroscope
[ ] HW-007 magnetometer
[ ] HW-008 proximity/light sensors
[ ] HW-009 touchscreen/multitouch
[ ] HW-010 Bluetooth
[ ] HW-011 NFC
[ ] HW-012 telephony
[ ] HW-013 Wi-Fi/network
[ ] HW-014 vibration
[ ] HW-015 biometric
[ ] HW-016 USB
[ ] HW-017 external storage

For each: DECLARED / PRESENT / EMULATED / ABSENT / OPTIONAL / BLOCKED.

## 7 — GRAPHICS HARDWARE / BACKEND

[ ] GFX-001 GPU identity
[ ] GFX-002 OpenGL ES version
[ ] GFX-003 EGL extensions
[ ] GFX-004 framebuffer formats
[ ] GFX-005 texture formats
[ ] GFX-006 shader capabilities/limits
[ ] GFX-007 GLES limits
[ ] GFX-008 Vulkan availability/extensions
[ ] GFX-009 software renderer/SwiftShader
[ ] GFX-010 backend capability negotiation
[ ] GFX-011 gralloc compatibility
[ ] GFX-012 buffer usage compatibility
[ ] GFX-013 HWC capability
[ ] GFX-014 fence support
[ ] GFX-015 display mode/refresh rate
[ ] GFX-016 resolution/rotation
[ ] GFX-017 colorspace
[ ] GFX-018 protected content

Never report "GPU supported" as a single boolean.

## 8 — SOFTWARE / SYSTEM SERVICES

[ ] SW-001 PackageManager
[ ] SW-002 ActivityManager
[ ] SW-003 WindowManager
[ ] SW-004 SurfaceFlinger/compositor equivalent
[ ] SW-005 Binder
[ ] SW-006 ServiceManager
[ ] SW-007 InputManager
[ ] SW-008 DisplayManager
[ ] SW-009 ContentResolver/providers
[ ] SW-010 media services
[ ] SW-011 notification services
[ ] SW-012 clipboard
[ ] SW-013 location
[ ] SW-014 connectivity/network
[ ] SW-015 PowerManager
[ ] SW-016 AlarmManager
[ ] SW-017 JobScheduler
[ ] SW-018 StorageManager
[ ] SW-019 WebView provider
[ ] SW-020 SQLite

For each service:
DISCOVERABLE → AVAILABLE → CORRECT API → CORRECT SEMANTICS → REAL APP PROOF.

## 9 — DEVICE CONFIGURATION / RESOURCES

[ ] CFG-001 density/dpi
[ ] CFG-002 width/height
[ ] CFG-003 smallestWidthDp
[ ] CFG-004 orientation
[ ] CFG-005 locale
[ ] CFG-006 layout direction
[ ] CFG-007 uiMode/night mode
[ ] CFG-008 font scale
[ ] CFG-009 screen-size bucket
[ ] CFG-010 keyboard/navigation
[ ] CFG-011 touchscreen
[ ] CFG-012 color mode
[ ] CFG-013 refresh rate

For suspicious visuals, prove the selected resource configuration and provenance.

## 10 — PERMISSION / SECURITY / IDENTITY

[ ] SEC-001 package UID
[ ] SEC-002 app sandbox
[ ] SEC-003 permission grant state
[ ] SEC-004 runtime permissions
[ ] SEC-005 signature permissions
[ ] SEC-006 provider permissions
[ ] SEC-007 exported component rules
[ ] SEC-008 URI grants
[ ] SEC-009 SELinux-like assumptions
[ ] SEC-010 user/profile identity
[ ] SEC-011 foreground-user identity
[ ] SEC-012 overlay-user identity

Do not fake security by simply returning true.

## 11 — VERSIONED ROOT LAWS

Build:
API LEVEL → SEMANTIC DIFFERENCE → AFFECTED API → MINANDROID BEHAVIOR → TEST.

At minimum inspect:
Context storage, permissions, package parsing, exported components, PendingIntent, storage, WebView, graphics, media, resources, lifecycle, notifications, background execution and service binding.

Goal: emulate semantic laws, not entire Android OS releases.

## 12 — AGENT PRE-FLIGHT API

The Agent must eventually be able to request an apk-requirements operation and receive:

package
version
min_sdk
target_sdk
max_sdk
required_features
optional_features
required_permissions
abis
native_libs
native_dependencies
graphics_requirements
media_requirements
providers
services
receivers
resource_configs
storage_requirements
webview_requirement
estimated_compatibility
missing_capabilities
environment_mismatches
recommended_next_probe

[ ] API-001 — Implement/verify apk requirements operation.
[ ] API-002 — Machine-readable schema.
[ ] API-003 — Missing-capability report.
[ ] API-004 — Environment comparison.
[ ] API-005 — Recommended next probe.
[ ] API-006 — Evidence bundle.

## 13 — REAL APK VALIDATION

Use at least:
- simple app
- complex app
- WebView app
- native-heavy app
- ARM-only/native game
- libGDX game
- media app
- filesystem-heavy app
- random corpus app
- random corpus game
- Telegram.

For each compare:
APK REQUIREMENTS vs DEFAULT ENVIRONMENT vs ACTUAL FAILURE vs FIRST DIVERGENCE.

## 14 — DO NOT OVER-SIMULATE

Every missing prerequisite must be classified:
A already provided
B easy generic semantic implementation
C reusable OSS/backend candidate
D requires translation/emulation
E external physical hardware boundary
F optional and can truthfully be absent
G not actually required by APK

Only implement what real compatibility evidence justifies.

## 15 — FINAL QUESTIONS

The coder MUST explicitly answer:

1. What Android API level does MiniAndroid emulate by default?
2. What device/model/profile does it emulate?
3. What CPU architecture is actually executed?
4. Which ABIs are honestly supported?
5. Can ARM-only APKs run?
6. If not, is the blocker CPU translation, native library, linker, or another layer?
7. What Android versions can current APKs reasonably target?
8. Which version-specific laws are missing?
9. Which hardware features are emulated?
10. Which are absent?
11. Which system services are available?
12. Which graphics capabilities are available?
13. Which media capabilities are available?
14. Can an Agent query APK prerequisites before running?
15. Can it receive a machine-readable missing-capability report?
16. Which prerequisites should be emulated?
17. Which should not be emulated?
18. Which can be reused from existing OSS?
19. What remains an external dependency?
20. Which 50-title failures are environment/prerequisite failures rather than runtime semantic bugs?

## REQUIRED EVIDENCE

For every prerequisite:

STATUS:
SOURCE:
LAW:
APK:
REQUIREMENT:
DEFAULT ENVIRONMENT:
MISMATCH:
FIRST DIVERGENCE:
IMPLEMENTATION:
TEST:
REAL APP:
TRACE/SCREENSHOT:
3-RUN:
REGRESSION:
COMMIT:

Static APK inspection alone is never VERIFIED.

## DEFINITION OF DONE

MiniAndroid must have a truthful machine-readable answer to:

"What does this APK require, what does the current MiniAndroid environment provide, what is missing, can the missing capability be supplied generically, and if the APK fails, is the first divergence caused by the environment or by a runtime semantic defect?"

If a capability is genuinely external, prove that conclusion.
If implementable, identify the generic law and test it.
If CPU translation is the highest-fanout blocker, quantify its impact before choosing a solution.