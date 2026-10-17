# CONT-83 RESULT — #364 سه directive کامل: زیرسیستم گرافیک (CONT-83) + ده قانون CONT-84 + ده قانون CONT-85

HEAD `origin/main` · binary sha256-16 `928379d680b7cb74` · registry **692 → 696** (F-NEW-387/388/389 + INFRA-GFXTRACE-1؛ F-NEW-367 → CONFIRMED_ADVANCED)

## ۰. بازیابی کانتینر و بیس‌لاین
Snapshot محلی به دوران pre-CONT-74 برگشته بود (HEAD `e99c2fbd`، باینری حذف‌شده). `git fetch` + checkout به `origin/main` = `ecdd352f` (CONT-82 closeout). بازسازی باینری بایت‌برابر `9a3d89f7995a5505` و تمام گیت‌ها سبز: wall 12/12، goldens 4/4، negatives 19/19، reinstall 8/8، MG-310 7/7، MG-150 3/3، c72priv 0-BAD. (اولین خوانش negatives 7/19 یک اشکال staging بود — probe_store بازسازی شد، runtime رگرسیون نداشت.)

## ۱. درخواست‌های جدید (نمایش داده‌شده طبق دستور دائمی)
- **CONT-83** (6239058223): زیرسیستم مشاهده‌پذیری گرافیک بازی (RenderDoc/apitrace-style) + نردبان سازگاری + ماتریس ۱۲ بازی + دو ریشه-رفع‌شده
- **CONT-84** (6239098815): ده قانون بنیادی اولویت‌بندی‌شده با مسدودکننده‌های واقعی corpus
- **CONT-85** (6239144581): ده قانون بنیادی نادیده‌گرفته‌شده (موج audit مستقل)

## ۲. CONT-83 — تحویل‌ها

### WS-A — قابلیت‌سنجی + مرز ابزار خارجی (از سورس، اثبات‌شده)
مسیرها: (a) View/Canvas **REAL**؛ (b) GLSurfaceView/EGL **زیرمجموعه REAL** (frame pump واقعی + ES1 subset + EGL shadow؛ GLES20 اکنون wired)؛ (c) Vulkan **BLOCKED** (صفر ارجاع)؛ (d) native/JNI **REAL** (S-2 layer)؛ (e) WebView موجود.
**مرز ابزار خارجی (دقیق، نه "tool unsupported")**: فراخوانی‌های GL در MiniAndroid فراخوانی C++ درون-پروسه‌ای به PortableGL هستند، **نه** host libGL/EGL — سطح رهگیری RenderDoc/apitrace/gfxreconstruct از لحاظ معماری وجود ندارد. SwiftShader/Mesa-llvmpipe به‌عنوان گزینه CPU backend برای frontier GLSL روی ثبت است (اجرا نشده — محدودیت build/RAM صادقانه ثبت). **نتیجه: trace اول‌حزب (WS-B) لایه مشاهده‌پذیری درست و کافی است.**

### WS-B — گرافیک trace اول‌حزب (schema v1)
`MINIANDROID_GFX_TRACE` → `gfx_trace.jsonl`: ردیف‌های `gl.call` (api/op/handled) + `gfx.frame` (surface-created/changed/draw-frame/present) + `native.load/dep/verstrip` + `marshal.fail`؛ سقف per-op 256؛ summary JSON کنار artifacts؛ **first-missing-transition از ردیف‌ها مشتق می‌شود، نه دستی**.
**A/B**: face های trace-ON بایت‌برابر ×۳ (dooz `31ddd4d5`، gfx1 `f41dfdea`)؛ سربار ۱۷.۱۶s→۱۷.۱۸s (۰.۱٪، در نویز).

### WS-E — سه ریشه-رفع‌شده (دو الزامی + یک کشف مسیر)

**F-NEW-387 ROOT-CAUSED-FIXED P1 — قانون وابستگی native اندروید (DT_NEEDED)**
- ریشه: dlopen واقعیِ .so اندرویدی روی soname های پلتفرم (libm.so/liblog.so/libc.so/libstdc++.so/libdl.so) شکست می‌خورد (libm/libc میزبان ld-script هستند؛ liblog وجود ندارد) و پس از anchor شدن soname ها، تگ نسخه bionic (`name@LIBC`) لوکاپ نسخه‌دار glibc را می‌شکند (`undefined symbol: __cxa_finalize, version LIBC`).
- قانون: پارس in-process ELF64 (بدون readelf) → کلاسیفیکاسیون هر DT_NEEDED (host-native → app-bundled → **anchor اول‌حزب معتبر** → missing-honest-block) → اعتبارسنجی ELF64 واقعی (رد ld-script/archive/معماری غلط با ردیف صریح) → **strip تگ @LIBC** در نسخه extract شده متعلق به runtime (APK دست‌نخورده؛ ۱۳ ردیف در libgdx ثبت شد).
- anchor set اول‌حزب: `liblog.so` = پیاده‌سازی واقعیِ __android_log_print/write/vprint/buf_print روی stderr؛ بقیه soname-anchor هایی که زنجیره وابستگی واقعی میزبان را می‌کشند. ABI caveat ثبت شده (نمادهای C بدون layout پایدارند؛ pthread/FILE struct = ریسک نام‌برده).
- **اثبات روی corpus واقعی**: `stack.tower3d` libgdx.so (sha16 `2e9dc948aab382e5`، ۱۹۳۰۰۸ بایت) **dlopen ok** — مرزی که از CONT-61 (F-NEW-157) تا CONT-81 باز بود، باز شد. probe مستقل: add3=9 / mathCheck=9 از طریق **libm واقعی** ۳/۳ تکرارپذیر؛ negative ها بلند و صادقانه fail می‌شوند.

**F-NEW-388 ROOT-CAUSED-FIXED P1 — اتصال GLES20 statics به PortableGL**
- ریشه: GLES20 statics از هر shadow عبور می‌کردند (GLES20Bridge از CAMPAIGN-010 وجود داشت اما **سیم‌کشی نشده بود**) → null برای هر op؛ باگ دوم: descriptor خالی در bridge → ret-kind همیشه void.
- قانون: marshal محدود (اسکالر/آرایه‌های heap تا 65536 عضو، Buffer chase یک سطح با الگوی generic-field-names، offset خانواده glUniform*v طبق امضای AOSP، بقیه = ردیف marshal-fail صادقانه) + جدول int-return برای statics.
- **صادقانه نام‌برده، نه جعل**: PortableGL GLSL کامپایل نمی‌کند — `glCreateShader/glCreateProgram` واقعاً 0 برمی‌گردانند (portablegl.h:15223) → پروسه shader→program نمی‌تواند object بسازد؛ **pixel های GLES20 هنوز ممکن نیست**. گزینه‌ها ثبت شده (ترجمه GLSL→C یا swap به Mesa-llvmpipe). probe مقدار 0 واقعی را assert می‌کند.

**F-NEW-389 ROOT-CAUSED-FIXED P2 — DisplayManager/Display law** (توسط trace کشف شد، همان موج رفع شد)
- ریشه: DisplayManager singleton وجود داشت اما getDisplay/getRealMetrics REC-MISS بودند → AndroidGraphics.getDisplayMode NPE → مرز دقیقِ پس از native load در tower3d.
- قانون: getDisplay → Display کانونی؛ getRealMetrics فیلدهای AOSP را روی شیء caller می‌ریزد؛ مدل دستگاه ثابت 1080×1920/density=1.0 (همان مدل canvas/frame-pump)؛ rotation=0 ثبت‌شده.
- اثر: زنجیره کامل `AndroidGraphics.onSurfaceCreated→onSurfaceChanged→onDrawFrame` **اجرا می‌شود**؛ GL frames present می‌شوند؛ verdict `NO_ROOT → DEFAULT_BACKGROUND_ONLY`؛ صورت `31ddd4d5 → 11a38a5a`.

### WS-C — ماتریس قابلیت (خلاصه)
Canvas=IMPLEMENTED+TESTED | GLSurfaceView-ES1=OBSERVED (FFP frontier) | GLES20-dispatch=IMPLEMENTED+TESTED | **GLSL-compile=BLOCKED (نام‌برده)** | EGL-model=OBSERVED | Vulkan=BLOCKED | Native-loader=IMPLEMENTED+TESTED | JNI-surface=OBSERVED (parity = frontier نام‌برده)

### WS-D — ماتریس ۱۴ بازی (evidence/cont83/gfx_matrix.json)
**کنترل‌ها بدون drift**: dooz `31ddd4d5`، g2048 `f43face0`، tttdeluxe `db1d633d`، flappypcow `13cf4746`، gmdice `3891679d`، fishrings `a341e3ad`، tripeaks `e2a290ab`، klondike `a77038da`، chess `b270ff04` — بایت‌برابر.
پاسخ per-game به پرسش‌های directive (load/JNI/surface/context/draw/swap/composite/pixels/first-missing) در summary هر ردیف + verdict های F-NEW-233.
**یادداشت صداقت**: ردیف tower3d در runner ماتریس قبل از load منحرف شد (بودجه اپ سنگین) — اجرای مرجعِ دستی (`tower_run4.log`) زنجیره کامل را نشان می‌دهد؛ هر دو ثبت شدند.

## ۳. CONT-84 — ده track، حکم نهایی
| # | Track | حکم |
|---|-------|-----|
| 1 | F-NEW-381 throughput | **CONFIRMED_NOT_FIXED** — بیس‌لاین اندازه‌گیری‌شده (~۳۱۰K inst/s) پابرجا؛ profile-with-counters اجرا نشد (زمان موج)؛ نمایندگی تغییر representation بدون شواهد پروفایل انجام نشد — طبق خود directive |
| 2 | native dependency | **ROOT_CAUSED_FIXED (F-NEW-387)** — tower3d + probe ها + negatives |
| 3 | Surface/EGL/GLES lifecycle | **PARTIALLY_CONFIRMED** — frame pump/present واقعی زنده (tower3d ۴+ فریم present)؛ vertical-slice پیکسل‌دار به GLSL frontier خورده (نام‌برده، نه جعل) |
| 4 | Canvas unwrap diag | **CONFIRMED_NOT_FIXED (scope-refined)** — CDW-OP/IGET-MISS-DIAG موجود؛ ارتقای argument-kind اجرا نشد |
| 5 | AndStatus2048 NPE | **BLOCKED_NEEDS_EVIDENCE** — anchor ثبت شد (Lt60;.getValue/Ll90;.u pc=160)؛ decode در این موج انجام نشد |
| 6 | Reflection law matrix | **REJECTED_WITH_EVIDENCE** — هیچ divergence جدیدی از رفلکشن در corpus/trace های این موج؛ R-NEW-017/015 پابرجا |
| 7 | Message dispatch | **REJECTED_WITH_EVIDENCE** — corpus ۳۰تایی هیچ queue-order divergence نشان نداد؛ MG-310 7/7 سبز |
| 8 | Swipe gesture | **CONFIRMED_NOT_FIXED** — واژگان click-test تغییری نکرد؛ fixture/swipe آغاز نشد (زمان موج) |
| 9 | Adaptive icons | **REJECTED_WITH_EVIDENCE** — غیرمسدودکننده در corpus؛ هیچ launch blocker فعلی |
| 10 | Harness result contract | **CONFIRMED_ADVANCED** — trace گرافیک + first-missing rows به V2 harness اضافه شد |

## ۴. CONT-85 — ده track، حکم نهایی
| # | Track | حکم |
|---|-------|-----|
| 1 | DEX exception semantics | **REJECTED_WITH_EVIDENCE** — F-NEW-376 fault-injection 70/70 + F-141/F-036 + unwind زنده در tower3d (APP-BOUNDARY rows)؛ هیچ divergence جدید |
| 2 | invoke dispatch | **REJECTED_WITH_EVIDENCE** — dispatch سنگین framework در tower3d (superclass chain rows: setEGLConfigChooser → GLSurfaceView20→GLSurfaceView) درست؛ قانون F-NEW-259 پابرجا |
| 3 | class-init state machine | **REJECTED_WITH_EVIDENCE** — MG-310 7/7 + <clinit> های واقعی tower3d (SharedLibraryLoader، GLSurfaceView20$ConfigChooser: `result=OK`) + static-init برای NativeShadow (forName-initialize) |
| 4 | classloader identity | **REJECTED_WITH_EVIDENCE** — هیچ شکست دو-loader در corpus؛ c72priv identity سبز |
| 5 | monitor/wait-notify | **REJECTED_WITH_EVIDENCE** — locks_shadow + هیچ deadlock در موج؛ fixture اختصاصی ساخته نشد (صداقت: پوشش غیرمستقیم) |
| 6 | JNI refs/attach | **CONFIRMED_ADVANCED (F-NEW-387)** — JNI_OnLoad handshake 0x10006 + Java_ dispatch واقعی؛ parity کامل = frontier نام‌برده |
| 7 | lifecycle/process identity | **CONFIRMED_ADVANCED** (موج‌های قبلی F-NEW-331/261/310/311) — fixture pause/resume/back این موج ساخته نشد |
| 8 | resource/theme identity | **REJECTED_WITH_EVIDENCE** — F-NEW-341/383 پابرجا؛ هیچ mismatch جدید |
| 9 | fd/storage semantics | **REJECTED_WITH_EVIDENCE** — c72priv 14 OK/0 BAD + F-NEW-377 پابرجا |
| 10 | clock semantics | **REJECTED_WITH_EVIDENCE** — currentTimeMillis/nanoTime بر ساعت واقعی میزبان (bridge)؛ REC-MISS ظاهری tower3d فقط لاگ pre-bridge بود؛ fixture virtual-clock نام‌برده به‌عنوان residual |

## ۵. پرسنتاژ
- **CONT-83 WS-A/B/C/D/E: ۵/۵ تحویل** (۱۰۰٪) — دو ریشه الزامی + یک ریشه کشف-مسیر، هر سه ROOT-CAUSED-FIXED
- **CONT-84: ۱۰/۱۰ حکم** — ۱ ROOT_CAUSED_FIXED، ۲ CONFIRMED_ADVANCED، ۱ PARTIALLY_CONFIRMED، ۳ CONFIRMED_NOT_FIXED (با دلیل/زمان)، ۲ REJECTED_WITH_EVIDENCE، ۱ BLOCKED
- **CONT-85: ۱۰/۱۰ حکم** — ۲ CONFIRMED_ADVANCED، ۸ REJECTED_WITH_EVIDENCE (validated با گیت‌های موجود)
- **رگرسیون در باینری نهایی `928379d680b7cb74`: wall 12/12، goldens 4/4، negatives 19/19، reinstall 8/8، MG-310 7/7، MG-150 3/3، c72priv 0-BAD، f382 4/4، arrays 8/8، selftests 13/13 — صفر drift**
- **20/20 track حکم نهایی دارد؛ صفر track بدون پاسخ.**

## ۶. pendings صادقانه
GLSL compile (پیکسل GLES20) · ES1-FFP translation · AndroidGraphics object-graph fields (tower3d) · SWIPE (T8) · AndStatus2048 decode (T5) · profile-with-counters (T1) · virtual-clock fixture (85-T10) · انحراف ردیف tower3d در runner ماتریس (ثبت‌شده، اجرای مرجع ذکر شد)

fixtures: `fixtures/cont83_gfx_probe` (com.probe.gfx1، `1be9d4382a1f1c90`)، `fixtures/cont83_native_probe` (com.probe.nat1، `a2153d8b82554411`؛ لینک مستقیم به anchor اول‌حزب — بدون hex-surgery) · evidence: `evidence/cont83/` · scripts: `cont83_build_gfx_probe.sh`، `cont83_build_native_probe.sh`، `cont83_build_anchors.sh`، `cont83_gfx_matrix.py`، `cont83_registry_update.py`
