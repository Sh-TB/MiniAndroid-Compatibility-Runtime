# MINIANDROID EXTERNAL RUNTIME INDEX — (mirror of WS-C5 index for repo placement)

این فایل آینه‌ی ایندکس `MINIANDROID_EXTERNAL_RUNTIME_INDEX.md` پک تحویلی است و در
repo تحت `docs/knowledge/` قرار می‌گیرد تا جستجوی `*RUNTIME*` charter (§11) پیدا کند.

| پروژه | CPU-only headless؟ | APK واقعی؟ | کلاس |
|---|---|---|---|
| Robolectric | ✅ | ❌ (JVM) | ARCHITECTURE TEMPLATE |
| Paparazzi | ✅ | ❌ | RENDER REFERENCE |
| Roborazzi | ✅ | ❌ | CAPTURE PATTERN |
| DSH Android | ❌ | — | AGENT TOOL SURFACE |
| J-Code Android | ❌ | ✅ روی دستگاه | LOW VALUE |
| Emulator Harness/Cuttlefish | ❌ (KVM) | ✅ | OPS FEATURES (snapshot) |
| Redroid | ⚠️ kernel binder/memfd | ✅ | KERNEL-DEP MAP |
| roidy | ❌ | — | VIRTUAL-DISPLAY PATTERN |
| VirtualApp | ❌ | ✅ روی دستگاه | SERVICE PROXY MAP |
| Evoke | ❌ | ✅ روی دستگاه | MODERN VA REFERENCE (0BSD) |
| AppManager | ❌ | — | DEX TOOLING (dexlib2) |
| GameNative | ❌ | ❌ (Wine) | OUT OF SCOPE |

نتیجه کلیدی: **هیچ پروژه‌ای APK واقعی را CPU-only بدون Android اجرا نمی‌کند — نیچ MiniAndroid تأیید شد.**
