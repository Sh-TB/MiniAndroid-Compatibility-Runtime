# MINIANDROID EXTERNAL RUNTIME KNOWLEDGE (WS-C5)

**تاریخ:** 2026-08-27 · منبع: تحقیق WS-C5-RESEARCH (وب + ریپوها) · موارد نامطمئن: UNVERIFIED
**سوال مرکزی charter:** کدام معماری‌های بیرونی APK واقعی را بدون Android OS / KVM / GPU اجرا می‌کنند و چه درسی برای MiniAndroid دارند؟

## جمع‌بندی راهبردی (مهم‌ترین نتیجه کمپین)

**هیچ پروژه شناخته‌شده‌ای APK/DEX واقعی را روی لینوکس ساده بدون Android اجرا نمی‌کند.** فضا سه‌تکه است:
1. **شبیه‌سازی JVM** — Robolectric/Paparazzi/Roborazzi: کد Java واقعی فریمورک + بایت‌کد JVM اپ + intercept در مرز native/service.
2. **کانتینر/VM** — redroid/Waydroid/cuttlefish/emulator: ART واقعی ولی نیاز به binder/memfd یا KVM.
3. **نیچ MiniAndroid** — تفسیر DEX در C++ + lifecycle واقعی + رندر + اسکرین‌شات، بدون هیچ‌کدام از آن وابستگی‌ها → **فضای خالی واقعی**؛ نزدیک‌ترین قالب‌ها: معماری Robolectric (sandbox/intercept/reset) + رندر RNG/Paparazzi (rasterizer واقعی + فونت/ICU به‌عنوان data).

---

## 1. Robolectric — عمیق‌ترین تحلیل
- github.com/robolectric/robolectric · MIT · 4.16.1 (2026-01) · بسیار فعال (Google) · ~110,646 LOC Java، **607 کلاس Shadow**، پشتیبانی API 23–36.
- **اجرا:** کد فریمورک واقعی AOSP (jar های `android-all-instrumented` که در زمان publish با `ClassInstrumentor` بازنویسی شده‌اند: هر متد → invokedynamic delegator؛ native ها → shadowable) + اپ به‌صورت JVM bytecode. **APK parse نمی‌کند.**
- **بدون OS/emulator/KVM/GPU** — فقط JVM؛ native ها: SQLite واقعی (`SQLiteMode.NATIVE` → `libnativeruntime.so`) + Robolectric Native Graphics (RNG، Skia) به‌صورت `.so` per-OS داخل resource، dlopen در اجرا.
- **مکانیزم:** `SandboxClassLoader` (بارگذاری اول فریمورک instrumented، جلوگیری از stub "Android!") · `ShadowMap`+`ShadowWrangler` (dispatch به shadow) · `AndroidTestEnvironment` (Looper/Resource/Manifest/display/ActivityThread simulation) · `@Resetter` (ریست state بین تست → determinism) · scheduler پیش‌فرض PAUSED با clock کنترل‌پذیر.
- **خروجی:** View hierarchy واقعی، LayoutInflater واقعی، رندر واقعی CPU + اسکرین‌شات (Roborazzi مصرف می‌کند)، Simulator رسمی UI.
- **درس‌ها برای MiniAndroid:**
  a) intercept فقط در مرزهای باریک (system services، JNI، libcore-delta) — سطح کوچک و شمارش‌پذیر؛
  b) Environment simulation باید کامپوننت درجه‌یک باشد (clock/resource/display)؛
  c) native واقعی (SQLite/Skia) به‌صورت باینری+dlopen روی CPU ساده شدنی است؛
  d) reset کامل state = determinism.

## 2. Paparazzi (cashapp) — رندر headless با layoutlib
- 2.0.0-alpha05 (2026-05، layoutlib v16.2.1) · Apache-2.0 (UNVERIFIED at file) · فعال.
- اجرای View/Compose واقعی روی JVM و رندر با **layoutlib** (همان موتور Android Studio) — بدون emulator/GPU.
- فایل‌های کلیدی (master): `Paparazzi.kt`, `PaparazziSdk.kt`, `internal/Renderer.kt`, `agent/InterceptorRegistrar.kt` (ByteBuddy)، diff engines `PixelPerfect/Mssim/DeltaE2000`.
- اسکرین‌شات PNG/APNG + accessibility-tree overlay؛ **بدون input injection** (تک‌فریم).
- **درس:** رندر Studio-کیفیت بدون Android ممکن است با «framework jar + Skia native + fonts/ICU به‌عنوان data + SessionParams»؛ diff engines الگوی مقایسه تصویر ما.

## 3. Roborazzi (takahirom) — اثبات «real UI → real pixels → PNG» روی CPU
- 1.73.0 (2026-08) · Apache-2.0 (verified) · فوق‌فعال.
- روی Robolectric + **RNG** (`@GraphicsMode(NATIVE)`)؛ capture در سطح Canvas/Bitmap → PNG/GIF + record/verify/compare در CI.
- **درس:** capture را در سطح canvas/bitmap بگذارید نه «کل صفحه».

## 4. DSH Android (ZSeven-W/dsh-android)
- 0.1.0-rc.4 (2026-08) · MIT. **پلاگین ابزار LLM برای adb** (نه runtime): 20 ابزار (build/run/screenshot/tap-by-id/OCR/logcat/memory) روی دستگاه واقعی.
- **درس:** چیدمان سطح ابزار agent-facing برای MiniAndroid (install→launch→screenshot→input→logcat→memory) + الگوی streaming فریم با URL امضاشده.

## 5. J-Code Android (blamspotdev/j-code-android)
- IDE اندرویدی (2026-05، 8 stars)؛ اجرای APK از طریق **runtime عادی خود دستگاه + ADB bridge + JDWP**؛ proot برای toolchain. خارج از دامنه headless. **درس:** UX «اجرا در تب» و JDWP؛ کم‌ارزش معماری.

## 6. Android Emulator Harness (google/android-emulator-container-scripts + Cuttlefish)
- اجرای **سیستم کامل Android**؛ نیاز: Docker + **KVM** (nested-virt در cloud) · WebRTC streaming · snapshot/restore (cuttlefish).
- **درس:** کفِ fidelity؛ feature های harness ارزش‌مند: snapshot/restore، کنترل‌plane سازگار adb، streaming.

## 7a. Redroid (remote-android/redroid)
- Android 11–16 در Docker **بدون KVM**؛ نیاز kernel: `binder_linux` + ashmem/memfd؛ GPU اختیاری (software fallback ~15fps).
- نصب/اجرا: `adb install` + `am start`؛ تصویر: scrcpy/screencap؛ overlayfs برای data هار instance.
- **درس:** لیست دقیق وابستگی‌های kernel که «Android واقعی» لازم دارد → معادل‌های IPC/shared-mem که MiniAndroid باید شبیه‌سازی کند؛ الگوی عملیاتی per-instance.

## 7b. roidy (sanohiro/roidy)
- MIT، 2026-03. فرانت‌اند adb ترمینالی: per-app virtual display + kitty-graphics.
- **درس:** «یک display مجازی به‌ازای هر task/Activity» الگوی خوبی برای runtime هدلس.

## 8. VirtualApp (asLody) — repo عمومی فریز 2017، نسخه تجاری جدا
- اجرای APK واقعی **روی دستگاه** با import به VA-space؛ `VirtualCore`/`InvocationStubManager`/`VClientImpl` + stub-component swap در H-messages؛ proxy های per-service.
- **درس:** کامل‌ترین چک‌لیست تجربی «اپ در runtime چه لمس می‌کند» (AMS/PMS/H-order/Provider/AppOps/clipboard) → نقشه راه simulation services.

## 9. Evoke (smartdone/Evoke)
- 0BSD! (verified) · 2026-03 · minSdk 31، تست‌شده روی Android 16. جانشین مدرن VirtualApp با `core-virtual` + `core-native` (Frida Gum، I/O redirect).
- **درس:** مرز جدید Java-proxy ↔ native-hook در Android جدید؛ کد کپی‌پذیر (0BSD) برای الگوها.

## 10. AppManager (MuntashirAkon/AppManager)
- GPLv3+ · بازرس APK روی دستگاه؛ از **dexlib2/baksmali** + jadx-fork + apksig-fork استفاده می‌کند.
- **درس:** dexlib2 به‌عنوان مدل مرجع فرمت DEX برای cross-check پارسر ما (§ WS-C4→C3).

## 11. GameNative (utkarshdalal/GameNative)
- MIT، 10.1k stars · لانچر بازی‌های **ویندوزی** روی Android (Wine) — خارج از دامنه DEX. درس: بسته‌بندی runtime سنگین.

---

## 12. کشفیات تکمیلی (BONUS)
| پروژه | چیست | درس |
|---|---|---|
| jserv/simple-dvm | mini Dalvik VM آموزشی C | هسته interpreter کوچک و قابل‌فهم |
| IlyaGulya/rust-dalvik-vm | DVM در Rust (2024) | اثبات viability رویکرد ما |
| wangziqi2013/Android-Dalvik-Analysis | پارسر/disassembler C++ DEX | مرجع مستقیم C++ برای loader |
| WanghongLin/StandaloneDVM | dalvikvm standalone | تاریخچه portability Dalvik (UNVERIFIED جزئیات) |
| akavel/dali | Nim assembler دکس | مرجع فرمت |
| Waydroid / Anbox | Android کامل در LXC + binder + Wayland | چرا مناسب نیستند: kernel/Wayland/سنگین؛ Anbox متروک |
| DroidRun (9.1k) / arbigent (633) / Mobile-Agent | agent های LLM تست UI با accessibility/screenshot | مصرف‌کننده‌های آینده runtime ما؛ arbigent حالت Robolectric هم دارد |

---

## GAP ANALYSIS برای MiniAndroid (از synthesis)
1. **Environment simulation** (clock/Looper پاز‌شونده/resource/display) — الگو: Robolectric AndroidTestEnvironment.
2. **Interception map** — فهرست واحد از service های قابل proxy (VirtualApp proxies/ + Evoke hooks + 607 shadow Robolectric → خوشه‌های کم‌شمار).
3. **Native واقعی به‌صورت data** — SQLite (D1)، بعداً Skia-class raster (REFERENCE: RNG).
4. **Capture در سطح canvas** — الگوی Roborazzi.
5. **Snapshot/restore** — الگوی cuttlefish برای state بين اجراها.
6. **Agent tool surface** — install/launch/screenshot/input/logcat/memory به‌صورت ابزارهای مجزا (DSH/roidy/DroidRun).
