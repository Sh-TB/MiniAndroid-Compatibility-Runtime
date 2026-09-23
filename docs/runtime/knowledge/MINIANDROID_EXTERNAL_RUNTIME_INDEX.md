# MINIANDROID EXTERNAL RUNTIME INDEX — (mirror of WS-C5 index for repo placement)

This file mirrors the `MINIANDROID_EXTERNAL_RUNTIME_INDEX.md` of the delivery pack and is placed
in the repo under `docs/knowledge/` so the `*RUNTIME*` charter search (§11) can find it.

| Project | CPU-only headless? | Real APK? | Class |
|---|---|---|---|
| Robolectric | ✅ | ❌ (JVM) | ARCHITECTURE TEMPLATE |
| Paparazzi | ✅ | ❌ | RENDER REFERENCE |
| Roborazzi | ✅ | ❌ | CAPTURE PATTERN |
| DSH Android | ❌ | — | AGENT TOOL SURFACE |
| J-Code Android | ❌ | ✅ on device | LOW VALUE |
| Emulator Harness/Cuttlefish | ❌ (KVM) | ✅ | OPS FEATURES (snapshot) |
| Redroid | ⚠️ kernel binder/memfd | ✅ | KERNEL-DEP MAP |
| roidy | ❌ | — | VIRTUAL-DISPLAY PATTERN |
| VirtualApp | ❌ | ✅ on device | SERVICE PROXY MAP |
| Evoke | ❌ | ✅ on device | MODERN VA REFERENCE (0BSD) |
| AppManager | ❌ | — | DEX TOOLING (dexlib2) |
| GameNative | ❌ | ❌ (Wine) | OUT OF SCOPE |

Key result: **no project executes a real APK CPU-only without Android — MiniAndroid's niche is confirmed.**
