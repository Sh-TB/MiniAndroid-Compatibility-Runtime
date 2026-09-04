# MINIANDROID EXTERNAL RUNTIME INDEX (WS-C5)

**جدول ایندکس سریع — جزئیات در `MINIANDROID_EXTERNAL_RUNTIME_KNOWLEDGE.md`**

| # | پروژه | اجرای APK واقعی؟ | Android OS؟ | Emulator/KVM؟ | CPU-only headless؟ | اسکرین‌شات | UI tree | Input | Deterministic | Sandbox | لایسنس | کلاس برای ما |
|---|-------|-------------------|-------------|----------------|---------------------|------------|---------|-------|----------------|---------|--------|---------------|
| 1 | Robolectric | ❌ (JVM bytecode اپ، نه APK) | ❌ | ❌ | ✅ | ✅ (RNG) | ✅ | ✅ (synthetic) | ✅ (@Resetter/paused looper) | sandbox classloader | MIT | **ARCHITECTURE TEMPLATE** |
| 2 | Paparazzi | ❌ (View/Compose JVM) | ❌ | ❌ | ✅ (layoutlib) | ✅ PNG/APNG | ✅ (a11y overlay) | ❌ | ✅ (pinned env) | in-process | Apache-2.0 | RENDER REFERENCE |
| 3 | Roborazzi | ❌ (روی Robolectric) | ❌ | ❌ | ✅ | ✅ | (از Robolectric) | (از Robolectric) | ✅ | ✅ | Apache-2.0 | CAPTURE PATTERN |
| 4 | DSH Android | ❌ (adb harness) | ✅ لازم | AVD/دستگاه | ❌ | ✅ (stream) | ✅ (+OCR) | ✅ | ❌ | ❌ | MIT | AGENT TOOL SURFACE |
| 5 | J-Code Android | ✅ (روی دستگاه) | ✅ | ❌ | ❌ | (device capture) | ❌ | ❌ | ❌ | ❌ | UNVERIFIED | LOW VALUE |
| 6 | Emulator Harness/Cuttlefish | ✅ (سیستم کامل) | ✅ | ✅ KVM | ❌ | ✅ | (instrumentation) | ✅ | snapshot/restore | ✅ | Apache-2.0 | OPS FEATURES |
| 7a | Redroid | ✅ (ART واقعی) | ✅ (کانتینر) | ❌ KVM لازم نیست | ⚠️ نیاز kernel binder+memfd | ✅ scrcpy | ❌ | ✅ adb | ❌ | کانتینر | Apache-2.0* | KERNEL-DEP MAP |
| 7b | roidy | ❌ (adb frontend) | ✅ (دستگاه) | ❌ | ❌ | ✅ terminal | ❌ | ✅ | ❌ | ❌ | MIT | VIRTUAL-DISPLAY PATTERN |
| 8 | VirtualApp | ✅ (روی دستگاه، host ART) | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | VA-space | dual/commercial | SERVICE PROXY MAP |
| 9 | Evoke | ✅ (روی دستگاه، API 31+) | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | stub processes | **0BSD** | MODERN VA REFERENCE |
| 10 | AppManager | ❌ (inspector) | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | — | — | GPLv3+ | DEX TOOLING (dexlib2) |
| 11 | GameNative | ❌ (بازی ویندوزی/Wine) | ✅ (میزبان) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | MIT | OUT OF SCOPE |

*Redroid license UNVERIFIED at file level.

## خلاصه آماری
- «APK واقعی بدون Android»: **صفر پروژه** در کل تحقیق (تأیید نیچ MiniAndroid)
- نزدیک‌ترین الگوهای قابل اقتباس: Robolectric (معماری) · RNG/Paparazzi (رندر) · cuttlefish (snapshot) · DSH/roidy (agent tools) · Evoke 0BSD (کد مرجع کپی‌پذیر)

# WS-C5 PRIMARY TRANSFER

**به:** Primary Coder · **از:** WS-C5 · **تاریخ:** 2026-08-27

## P1. معماری «Environment» را در سطح runtime بسازید (الگوی Robolectric)
- clock کنترل‌پذیر + paused-looper mode + reset-complete-state بین اجراها
  → determinism مستحکم‌تر از «3-run SHA» فعلی (که خوشبختانه کار می‌کند ولی
  ساختاری تضمین نیست). CONFIDENCE: HIGH · RISK: MED (بازسازی داخلی)
- EVIDENCE: Robolectric AndroidTestEnvironment/@Resetter (§1 knowledge)

## P2. فهرست Interception را یکجا فهرست کنید
- VirtualApp proxies/ + Evoke hooks + 607 shadow خوشه Robolectric →
  نقشه «service هایی که باید شبیه‌سازی شوند». بعدش F007/F010 را هدفمند ببندید.
- ACTION: doc یک‌صفحه‌ای `SERVICE_INTERCEPTION_MAP.md` در repo.

## P3. Snapshot/restore بین اجراها
- state حافظه/heap/sandbox → فایل؛ بارگذاری مجدد برای debug سریع‌تر
  (الگوی cuttlefish). CONFIDENCE: MEDIUM (کار مهندسی واقعی)

## P4. سطح ابزار agent-facing
- install/launch/screenshot/input-by-id/logcat/memory به‌صورت subcommand های
  CLI مجزا (الگوی DSH). MiniAndroid همین حالا تقریباً همه را دارد — فقط
  یکدست شود. BENEFIT: استفاده LLM-agent (دقیقاً کاربرد شما).

## P5. Native-as-data مسیر تاییدشده است
- Robolectric `libnativeruntime.so` (SQLite+Skia) را dlopen می‌کند →
  نگرانی «lib C در C++ runtime» بی‌مبناست؛ D1 (SQLite) را انجام دهید.

## THINGS NOT TO DO
- سراغ KVM/container نروید (redroid/cuttlefish) — خارج از mission هدلس CPU-only
  و دقیقاً همان چیزی که MiniAndroid لازم ندارد.
- VirtualApp را به‌عنوان dependency استفاده نکنید (فریز/dual-license) — فقط
  چک‌لیست proxy هایش بخوانید. Evoke (0BSD) برای مطالعه کد آزاد است.
